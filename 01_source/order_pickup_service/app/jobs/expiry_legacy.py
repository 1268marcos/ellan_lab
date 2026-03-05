# Job expiração 2h + crédito 50%     - versão anterior expiry_py_v01.txt
# Escopo: somente ONLINE
# Presencial NÃO entra nessa regra
# Regra: passou 2h sem retirada -> EXPIRED + crédito de 50% + libera/ajusta slot (fica OUT_OF_STOCK aguardando reposição)
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import logging
from typing import Optional
import os

from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.models.credit import Credit, CreditStatus
from app.services import backend_client

logger = logging.getLogger(__name__)

# Configurações via environment variables com defaults
BATCH_SIZE = int(os.getenv("EXPIRY_BATCH_SIZE", "100"))
JOB_LOCK_TIMEOUT = int(os.getenv("EXPIRY_LOCK_TIMEOUT", "300"))  # 5 minutos
MAX_RETRIES = int(os.getenv("EXPIRY_MAX_RETRIES", "3"))


def run_expiry_once(db: Session) -> int:
    """
    Expira pedidos ONLINE que passaram da pickup_deadline_at:
    - marca Order como EXPIRED
    - marca Allocation como EXPIRED
    - cria crédito 50% (somente online)
    - set-state OUT_OF_STOCK no slot (cinza)
    - release allocation no backend do totem (para o backend não ficar preso)
    
    Returns:
        int: Número de pedidos processados
    """
    now = datetime.now(timezone.utc)
    changed = 0
    
    try:
        # 1) Buscar candidatos com LIMIT para evitar loop infinito
        expired_orders = (
            db.query(Order)
            .filter(
                Order.channel == OrderChannel.ONLINE,
                Order.status == OrderStatus.PAID_PENDING_PICKUP,
                Order.pickup_deadline_at.isnot(None),
                Order.pickup_deadline_at <= now,  # Filtro no banco, não em memória
            )
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)  # Lock otimista para múltiplos workers
            .all()
        )
        
        logger.info(f"Encontrados {len(expired_orders)} pedidos para expirar (batch size: {BATCH_SIZE})")
        
        if not expired_orders:
            return 0
        
        # Processar cada pedido em transações separadas
        processed_orders = []  # Guarda pedidos processados para efeitos externos
        
        for order in expired_orders:
            try:
                # Processa cada pedido em uma transação curta
                result = _process_expired_order(db, order)
                if result:
                    order_data, allocation = result
                    processed_orders.append((order_data, allocation))
                    changed += 1
                    db.commit()  # Commit por pedido para transações curtas
                    logger.info(f"Pedido {order.id} expirado com sucesso (commit realizado)")
                else:
                    db.rollback()
                    
            except Exception as e:
                db.rollback()
                logger.error(f"Erro ao processar pedido {order.id}: {str(e)}", exc_info=True)
                continue
        
        # Processa efeitos externos FORA da transação
        if processed_orders:
            logger.info(f"Processando efeitos externos para {len(processed_orders)} pedidos")
            for order, allocation in processed_orders:
                try:
                    _process_external_effects(order, allocation)
                except Exception as e:
                    logger.error(f"Erro nos efeitos externos do pedido {order.id}: {str(e)}", exc_info=True)
                    # Não revertemos o commit, apenas logamos
        
        logger.info(f"Batch finalizado: {changed}/{len(expired_orders)} pedidos expirados com sucesso")
        
    except Exception as e:
        logger.error(f"Erro crítico no job expiry: {str(e)}", exc_info=True)
        db.rollback()
        raise
    
    return changed


def _process_expired_order(db: Session, order: Order) -> Optional[tuple]:
    """
    Processa um pedido específico dentro de uma transação.
    Retorna tuple (order, allocation) se processado, None se não precisava processar.
    """
    # Verificação adicional de segurança
    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        logger.debug(f"Pedido {order.id} já não está mais PENDING_PICKUP")
        return None
    
    # Busca allocation com lock
    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .with_for_update()
        .first()
    )
    
    # Log para debug
    logger.debug(f"Processando pedido {order.id} com allocation: {allocation.id if allocation else 'None'}")
    
    # Se não tem allocation, apenas expira o pedido
    if not allocation:
        order.status = OrderStatus.EXPIRED
        logger.info(f"Pedido {order.id} expirado sem allocation")
        return (order, None)
    
    # 1) Cria crédito 50% se ainda não existir
    existing_credit = db.query(Credit).filter(Credit.order_id == order.id).first()
    if not existing_credit and order.amount_cents:
        credit_amount = int(order.amount_cents * 0.50)
        credit = Credit(
            id=Credit.new_id(),
            user_id=order.user_id,
            order_id=order.id,
            amount_cents=credit_amount,
            status=CreditStatus.AVAILABLE,
        )
        db.add(credit)
        logger.info(f"Crédito de {credit_amount} cents criado para pedido {order.id}")
    elif existing_credit:
        logger.debug(f"Crédito já existe para pedido {order.id}")
    
    # 2) Atualiza estados internos
    order.status = OrderStatus.EXPIRED
    allocation.state = AllocationState.EXPIRED
    
    logger.info(f"Pedido {order.id} e allocation {allocation.id} marcados como EXPIRED")
    
    return (order, allocation)


def _process_external_effects(order: Order, allocation: Optional[Allocation]) -> None:
    """
    Processa efeitos externos FORA da transação principal.
    Chamado após o commit da transação do pedido.
    """
    if not allocation:
        logger.debug(f"Pedido {order.id} sem allocation, pulando efeitos externos")
        return
    
    # Tenta obter região do pedido
    region = getattr(order, 'region', None)
    if not region:
        # Tenta obter região da allocation como fallback
        region = getattr(allocation, 'region', None)
    
    if not region:
        logger.error(f"Pedido {order.id} não tem região definida (order.region ou allocation.region)")
        return
    
    # 3) Atualiza estado da gaveta no backend do totem
    # (fica cinza/fora de estoque aguardando reposição do fresco)
    for attempt in range(MAX_RETRIES):
        try:
            backend_client.locker_set_state(region, allocation.slot, "OUT_OF_STOCK")
            logger.info(f"Slot {allocation.slot} setado como OUT_OF_STOCK para pedido {order.id}")
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Falha ao setar OUT_OF_STOCK após {MAX_RETRIES} tentativas: {str(e)}")
            else:
                logger.warning(f"Tentativa {attempt + 1} falhou, retentando: {str(e)}")
    
    # 4) Libera allocation no backend do totem
    for attempt in range(MAX_RETRIES):
        try:
            backend_client.locker_release(region, allocation.id)
            logger.info(f"Allocation {allocation.id} liberada no backend para pedido {order.id}")
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Falha ao liberar allocation após {MAX_RETRIES} tentativas: {str(e)}")
            else:
                logger.warning(f"Tentativa {attempt + 1} falhou, retentando: {str(e)}")


# Job principal com lock para múltiplos workers
def run_expiry_job(db: Session, lock_service: Optional[any] = None) -> int:
    """
    Versão com lock distribuído para múltiplos workers.
    
    Args:
        db: Sessão do banco de dados
        lock_service: Serviço de lock distribuído (opcional)
    
    Returns:
        int: Total de pedidos processados
    """
    lock_acquired = False
    lock_id = "expiry_job_lock"
    
    try:
        # Tenta adquirir lock (se serviço de lock disponível)
        if lock_service:
            lock_acquired = lock_service.acquire(lock_id, timeout=JOB_LOCK_TIMEOUT)
            if not lock_acquired:
                logger.info("Lock não adquirido, outro worker já está executando")
                return 0
        
        logger.info("Iniciando job expiry")
        
        # Executa o job em múltiplos batches
        total_processed = 0
        batch_count = 0
        
        while True:
            batch_count += 1
            processed = run_expiry_once(db)
            total_processed += processed
            
            logger.info(f"Batch #{batch_count}: processados {processed} pedidos")
            
            # Se processou menos que o batch size, não há mais trabalho
            if processed < BATCH_SIZE:
                break
        
        logger.info(f"Job expiry finalizado: {total_processed} pedidos processados em {batch_count} batches")
        return total_processed
        
    except Exception as e:
        logger.error(f"Erro no job expiry: {str(e)}", exc_info=True)
        raise
        
    finally:
        # Libera lock se adquirido
        if lock_service and lock_acquired:
            try:
                lock_service.release(lock_id)
                logger.debug("Lock liberado")
            except Exception as e:
                logger.error(f"Erro ao liberar lock: {str(e)}")


# Função de conveniência para chamada simplificada
def run_expiry(db: Session) -> int:
    """
    Versão simplificada do job expiry.
    
    Args:
        db: Sessão do banco de dados
    
    Returns:
        int: Total de pedidos processados
    """
    return run_expiry_job(db, lock_service=None)