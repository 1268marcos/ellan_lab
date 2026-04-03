# 01_source/order_pickup_service/app/services/locker_service.py
# 02/04/2026 - Enhanced Version with Global Markets Support

from __future__ import annotations

import requests
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.orders import OnlineRegion, OnlinePaymentMethod
from app.schemas.kiosk import KioskRegion, KioskPaymentMethod


class LockerServiceErrorType(str, Enum):
    """Tipos de erro padronizados para o serviço de locker"""
    FETCH_FAILED = "RUNTIME_LOCKER_FETCH_FAILED"
    NOT_FOUND = "LOCKER_NOT_FOUND"
    CHANNEL_NOT_ALLOWED = "LOCKER_CHANNEL_NOT_ALLOWED"
    PAYMENT_METHOD_NOT_ALLOWED = "LOCKER_PAYMENT_METHOD_NOT_ALLOWED"
    REGION_NOT_SUPPORTED = "REGION_NOT_SUPPORTED"
    INTERFACE_NOT_ALLOWED = "LOCKER_INTERFACE_NOT_ALLOWED"
    SLOT_UNAVAILABLE = "SLOT_UNAVAILABLE"
    LOCKER_OFFLINE = "LOCKER_OFFLINE"
    MAINTENANCE_MODE = "LOCKER_MAINTENANCE"


class LockerService:
    """Serviço para validação e gerenciamento de lockers com suporte global"""

    def __init__(self):
        self._cache = {}  # Cache simples para lockers
        self._cache_ttl = 300  # 5 minutos

    def _get_runtime_lockers(self, region: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Busca lockers ativos por região via gateway interno.
        Implementa cache para reduzir chamadas externas.
        """
        cache_key = f"lockers_{region}"
        
        if not force_refresh and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            import time
            if time.time() - timestamp < self._cache_ttl:
                return cached_data

        url = f"{settings.payment_gateway_internal.rstrip('/')}/lockers"

        try:
            response = requests.get(
                url,
                params={"region": region, "active_only": True},
                timeout=settings.request_timeout if hasattr(settings, 'request_timeout') else 5,
            )
            response.raise_for_status()
            data = response.json()
            lockers = data.get("items", [])
            
            # Atualiza cache
            import time
            self._cache[cache_key] = (lockers, time.time())
            
            return lockers
        except requests.Timeout as exc:
            raise HTTPException(
                status_code=504,
                detail={
                    "type": LockerServiceErrorType.FETCH_FAILED,
                    "message": f"Timeout ao consultar lockers para região {region}",
                    "region": region,
                    "error": str(exc),
                },
            ) from exc
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "type": LockerServiceErrorType.FETCH_FAILED,
                    "message": f"Falha ao consultar runtime lockers via gateway para região {region}",
                    "region": region,
                    "error": str(exc),
                },
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "type": LockerServiceErrorType.FETCH_FAILED,
                    "message": "Erro inesperado ao consultar lockers",
                    "error": str(exc),
                },
            ) from exc

    @staticmethod
    def _normalize_upper_list(values: List[str] | None) -> List[str]:
        """Normaliza lista de strings para maiúsculas e remove espaços"""
        return [str(v).strip().upper() for v in (values or []) if str(v).strip()]

    @staticmethod
    def _normalize_region(region: str | None) -> str:
        """Normaliza código de região"""
        return str(region or "").strip().upper()

    @staticmethod
    def _normalize_channel(channel: str | None) -> str:
        """Normaliza canal com suporte a aliases"""
        value = str(channel or "").strip().upper()
        aliases = {
            "ONLINE": "ONLINE",
            "WEB": "ONLINE",
            "APP": "ONLINE",
            "KIOSK": "KIOSK",
            "TOTEM": "KIOSK",
            "SELF_SERVICE": "KIOSK",
            "VENDING_MACHINE": "KIOSK",
            "LOCKER_STATION": "KIOSK",
        }
        return aliases.get(value, value)

    @staticmethod
    def _normalize_fulfillment_type(fulfillment_type: str | None) -> str:
        """Normaliza tipo de fulfillment"""
        value = str(fulfillment_type or "").strip().upper()
        aliases = {
            "RESERVATION": "RESERVATION",
            "RESERVE": "RESERVATION",
            "INSTANT": "INSTANT",
            "LOCKER_DISPENSE": "INSTANT",
            "PICKUP": "INSTANT",
        }
        return aliases.get(value, value)

    def _map_payment_method_to_locker_capabilities(
        self, 
        payment_method: str, 
        region: Optional[str] = None
    ) -> List[str]:
        """
        Converte o payment_method canônico para as capacidades do locker/gateway/runtime.
        Suporta métodos globais e regionais.
        """
        normalized = str(payment_method or "").strip()

        # Mapeamento base
        mapping = {
            # Cartões
            "creditCard": ["CARTAO_CREDITO", "CREDIT_CARD"],
            "debitCard": ["CARTAO_DEBITO", "DEBIT_CARD"],
            "giftCard": ["CARTAO_PRESENTE", "GIFT_CARD"],
            "prepaidCard": ["CARTAO_PRE_PAGO", "PREPAID_CARD"],
            
            # Brasil
            "pix": ["PIX"],
            "boleto": ["BOLETO"],
            
            # América Latina
            "mercado_pago_wallet": ["MERCADO_PAGO_WALLET"],
            "oxxo": ["OXXO"],
            "spei": ["SPEI"],
            "rapipago": ["RAPIPAGO"],
            "pagofacil": ["PAGOFACIL"],
            "servipag": ["SERVIPAG"],
            "khipu": ["KHIPU"],
            "efecty": ["EFECTY"],
            "pse": ["PSE"],
            
            # América do Norte
            "ach": ["ACH"],
            "venmo": ["VENMO"],
            "cashapp": ["CASHAPP"],
            "zelle": ["ZELLE"],
            "interac": ["INTERAC"],
            
            # Europa
            "apple_pay": ["APPLE_PAY"],
            "google_pay": ["GOOGLE_PAY"],
            "samsung_pay": ["SAMSUNG_PAY"],
            "mbway": ["MBWAY"],
            "multibanco_reference": ["MULTIBANCO_REFERENCE"],
            "sofort": ["SOFORT"],
            "giropay": ["GIROPAY"],
            "klarna": ["KLARNA"],
            "ideal": ["IDEAL"],
            "bancontact": ["BANCONTACT"],
            "twint": ["TWINT"],
            "mobilepay": ["MOBILEPAY"],
            "blik": ["BLIK"],
            "paypal": ["PAYPAL"],
            
            # África
            "m_pesa": ["M_PESA"],
            "airtel_money": ["AIRTEL_MONEY"],
            "mtn_money": ["MTN_MONEY"],
            "orange_money": ["ORANGE_MONEY"],
            "vodafone_cash": ["VODAFONE_CASH"],
            "paystack": ["PAYSTACK"],
            "flutterwave": ["FLUTTERWAVE"],
            
            # China
            "alipay": ["ALIPAY"],
            "wechat_pay": ["WECHAT_PAY"],
            "unionpay": ["UNIONPAY"],
            
            # Japão
            "paypay": ["PAYPAY"],
            "line_pay": ["LINE_PAY"],
            "rakuten_pay": ["RAKUTEN_PAY"],
            "konbini": ["KONBINI"],
            
            # Tailândia
            "promptpay": ["PROMPTPAY"],
            "truemoney": ["TRUEMONEY"],
            
            # Indonésia
            "go_pay": ["GO_PAY"],
            "ovo": ["OVO"],
            "dana": ["DANA"],
            
            # Singapura
            "grabpay": ["GRABPAY"],
            "dbs_paylah": ["DBS_PAYLAH"],
            
            # Filipinas
            "gcash": ["GCASH"],
            "paymaya": ["PAYMAYA"],
            
            # Emirados Árabes
            "tabby": ["TABBY"],
            "payby": ["PAYBY"],
            
            # Turquia
            "troy": ["TROY"],
            "bkm_express": ["BKM_EXPRESS"],
            
            # Rússia
            "mir": ["MIR"],
            "yoomoney": ["YOOMONEY"],
            
            # Austrália
            "afterpay": ["AFTERPAY"],
            "zip": ["ZIP"],
            "bpay": ["BPAY"],
        }

        # Retorna capacidades mapeadas ou o método original em maiúsculo
        return mapping.get(normalized, [normalized.upper()])

    def _validate_region_support(self, region: str, channel_type: str) -> None:
        """
        Valida se a região é suportada para o canal específico.
        """
        from app.schemas.orders import OnlineRegion
        from app.schemas.kiosk import KioskRegion
        
        all_regions = set([r.value for r in OnlineRegion]) | set([r.value for r in KioskRegion])
        
        if region not in all_regions:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": LockerServiceErrorType.REGION_NOT_SUPPORTED,
                    "message": f"Região {region} não é suportada",
                    "region": region,
                    "supported_regions": list(all_regions),
                },
            )

    def _validate_locker_status(self, locker: Dict[str, Any]) -> None:
        """
        Valida se o locker está online e em modo de operação normal.
        """
        status = locker.get("status", "").upper()
        is_online = locker.get("is_online", False)
        is_maintenance = locker.get("is_maintenance", False)
        
        if not is_online or status == "OFFLINE":
            raise HTTPException(
                status_code=503,
                detail={
                    "type": LockerServiceErrorType.LOCKER_OFFLINE,
                    "message": f"Locker {locker.get('locker_id')} está offline",
                    "locker_id": locker.get("locker_id"),
                    "status": status,
                },
            )
        
        if is_maintenance or status == "MAINTENANCE":
            raise HTTPException(
                status_code=503,
                detail={
                    "type": LockerServiceErrorType.MAINTENANCE_MODE,
                    "message": f"Locker {locker.get('locker_id')} está em manutenção",
                    "locker_id": locker.get("locker_id"),
                },
            )

    def _validate_slot_availability(
        self, 
        locker: Dict[str, Any], 
        desired_slot: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Valida disponibilidade de slot no locker.
        """
        available_slots = locker.get("available_slots", [])
        total_slots = locker.get("total_slots", 0)
        
        if desired_slot is not None:
            if desired_slot < 1 or desired_slot > total_slots:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "type": LockerServiceErrorType.SLOT_UNAVAILABLE,
                        "message": f"Slot {desired_slot} inválido. Total de slots: {total_slots}",
                        "desired_slot": desired_slot,
                        "total_slots": total_slots,
                    },
                )
            
            if desired_slot not in available_slots:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "type": LockerServiceErrorType.SLOT_UNAVAILABLE,
                        "message": f"Slot {desired_slot} não está disponível",
                        "desired_slot": desired_slot,
                        "available_slots": available_slots,
                    },
                )
            
            return {"allocated_slot": desired_slot}
        
        # Se não especificado, retorna o primeiro slot disponível
        if available_slots:
            return {"allocated_slot": available_slots[0]}
        
        raise HTTPException(
            status_code=409,
            detail={
                "type": LockerServiceErrorType.SLOT_UNAVAILABLE,
                "message": "Nenhum slot disponível no momento",
                "locker_id": locker.get("locker_id"),
            },
        )

    def validate_locker_for_order(
        self,
        *,
        db=None,  # Mantido para compatibilidade
        locker_id: str,
        region: str,
        channel: str,
        payment_method: str,
        payment_interface: Optional[str] = None,
        fulfillment_type: Optional[str] = None,
        desired_slot: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Valida se o locker está disponível para o pedido.
        Retorna o locker validado com informações de slot.
        """
        # Normaliza parâmetros
        normalized_region = self._normalize_region(region)
        normalized_channel = self._normalize_channel(channel)
        normalized_fulfillment = self._normalize_fulfillment_type(fulfillment_type or "RESERVATION")
        
        # Valida suporte da região
        self._validate_region_support(normalized_region, normalized_channel)
        
        # Busca lockers da região
        lockers = self._get_runtime_lockers(normalized_region)
        
        # Encontra o locker específico
        locker = next(
            (item for item in lockers if item.get("locker_id") == locker_id),
            None,
        )
        
        if not locker:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": LockerServiceErrorType.NOT_FOUND,
                    "message": f"Locker não encontrado: {locker_id}",
                    "locker_id": locker_id,
                    "region": normalized_region,
                },
            )
        
        # Valida status do locker
        self._validate_locker_status(locker)
        
        # Valida canal
        allowed_channels = self._normalize_upper_list(locker.get("channels"))
        if normalized_channel not in allowed_channels:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": LockerServiceErrorType.CHANNEL_NOT_ALLOWED,
                    "message": f"Canal {normalized_channel} não permitido em {locker_id}",
                    "locker_id": locker_id,
                    "channel": normalized_channel,
                    "allowed_channels": allowed_channels,
                },
            )
        
        # Valida tipo de fulfillment
        allowed_fulfillment = self._normalize_upper_list(locker.get("fulfillment_types"))
        if allowed_fulfillment and normalized_fulfillment not in allowed_fulfillment:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "LOCKER_FULFILLMENT_NOT_ALLOWED",
                    "message": f"Fulfillment type {normalized_fulfillment} não permitido em {locker_id}",
                    "locker_id": locker_id,
                    "fulfillment_type": normalized_fulfillment,
                    "allowed_types": allowed_fulfillment,
                },
            )
        
        # Valida método de pagamento
        raw_methods = locker.get("payment_methods") or locker.get("allowed_payment_methods") or []
        allowed_methods = self._normalize_upper_list(raw_methods)
        
        normalized_inputs = self._map_payment_method_to_locker_capabilities(
            payment_method, 
            normalized_region
        )
        
        if not any(item in allowed_methods for item in normalized_inputs):
            raise HTTPException(
                status_code=409,
                detail={
                    "type": LockerServiceErrorType.PAYMENT_METHOD_NOT_ALLOWED,
                    "message": f"Método {payment_method} não permitido em {locker_id} para região {normalized_region}",
                    "locker_id": locker_id,
                    "payment_method": payment_method,
                    "region": normalized_region,
                    "allowed_methods": allowed_methods,
                    "normalized_input": normalized_inputs,
                },
            )
        
        # Valida interface de pagamento (se o locker tem restrições)
        allowed_interfaces = self._normalize_upper_list(locker.get("payment_interfaces"))
        if allowed_interfaces and payment_interface:
            normalized_interface = payment_interface.upper()
            if normalized_interface not in allowed_interfaces:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "type": LockerServiceErrorType.INTERFACE_NOT_ALLOWED,
                        "message": f"Interface {payment_interface} não permitida em {locker_id}",
                        "locker_id": locker_id,
                        "payment_interface": payment_interface,
                        "allowed_interfaces": allowed_interfaces,
                    },
                )
        
        # Valida disponibilidade de slot
        slot_result = self._validate_slot_availability(locker, desired_slot)
        
        # Retorna locker enriquecido com informações do slot
        return {
            "locker": locker,
            "allocated_slot": slot_result["allocated_slot"],
            "region": normalized_region,
            "channel": normalized_channel,
            "fulfillment_type": normalized_fulfillment,
        }

    def get_locker_by_id(
        self,
        locker_id: str,
        region: str,
    ) -> Dict[str, Any]:
        """
        Busca um locker específico por ID e região.
        """
        normalized_region = self._normalize_region(region)
        lockers = self._get_runtime_lockers(normalized_region)
        
        locker = next(
            (item for item in lockers if item.get("locker_id") == locker_id),
            None,
        )
        
        if not locker:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": LockerServiceErrorType.NOT_FOUND,
                    "message": f"Locker não encontrado: {locker_id}",
                    "locker_id": locker_id,
                    "region": normalized_region,
                },
            )
        
        return locker

    def get_available_lockers(
        self,
        region: str,
        channel: Optional[str] = None,
        payment_method: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retorna lista de lockers disponíveis com filtros opcionais.
        """
        normalized_region = self._normalize_region(region)
        lockers = self._get_runtime_lockers(normalized_region)
        
        # Filtra lockers online
        lockers = [l for l in lockers if l.get("is_online", False)]
        
        # Filtra por canal
        if channel:
            normalized_channel = self._normalize_channel(channel)
            lockers = [
                l for l in lockers 
                if normalized_channel in self._normalize_upper_list(l.get("channels"))
            ]
        
        # Filtra por método de pagamento
        if payment_method:
            normalized_methods = self._map_payment_method_to_locker_capabilities(payment_method, region)
            lockers = [
                l for l in lockers
                if any(
                    m in self._normalize_upper_list(l.get("payment_methods") or l.get("allowed_payment_methods") or [])
                    for m in normalized_methods
                )
            ]
        
        return lockers

    def invalidate_cache(self, region: Optional[str] = None) -> None:
        """
        Invalida o cache de lockers.
        """
        if region:
            cache_key = f"lockers_{self._normalize_region(region)}"
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()


# Instância singleton do serviço
_locker_service_instance = None


def get_locker_service() -> LockerService:
    """Factory function para obter instância do serviço de locker"""
    global _locker_service_instance
    if _locker_service_instance is None:
        _locker_service_instance = LockerService()
    return _locker_service_instance


# Funções de compatibilidade (mantêm a interface original)
def validate_locker_for_order(
    *,
    db,
    locker_id: str,
    region: str,
    channel: str,
    payment_method: str,
    payment_interface: str | None = None,
) -> dict:
    """
    Função de compatibilidade que mantém a assinatura original.
    Utiliza o serviço interno para validação.
    """
    service = get_locker_service()
    result = service.validate_locker_for_order(
        db=db,
        locker_id=locker_id,
        region=region,
        channel=channel,
        payment_method=payment_method,
        payment_interface=payment_interface,
    )
    # Retorna apenas o locker para compatibilidade com código existente
    return result["locker"]


# Funções auxiliares adicionais para compatibilidade
def _get_runtime_lockers(region: str) -> list[dict]:
    """Função de compatibilidade para código existente"""
    service = get_locker_service()
    return service._get_runtime_lockers(region)


def _normalize_upper_list(values: list[str] | None) -> list[str]:
    """Função de compatibilidade para código existente"""
    return LockerService._normalize_upper_list(values)


def _normalize_region(region: str | None) -> str:
    """Função de compatibilidade para código existente"""
    return LockerService._normalize_region(region)


def _normalize_channel(channel: str | None) -> str:
    """Função de compatibilidade para código existente"""
    return LockerService._normalize_channel(channel)


def _map_payment_method_to_locker_capabilities(payment_method: str) -> list[str]:
    """Função de compatibilidade para código existente"""
    service = get_locker_service()
    return service._map_payment_method_to_locker_capabilities(payment_method)