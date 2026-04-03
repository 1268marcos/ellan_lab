# 01_source/order_pickup_service/app/models/order.py
# 02/04/2026 - Enhanced Version with Global Markets Support
# veja fim do arquivo
# 03/04/2026

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, Enum, Index, String, Integer, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db import Base


# ==================== Enums ====================

class OrderStatus(str, enum.Enum):
    """Status do pedido"""
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID_PENDING_PICKUP = "PAID_PENDING_PICKUP"
    DISPENSED = "DISPENSED"
    PICKED_UP = "PICKED_UP"
    EXPIRED_CREDIT_50 = "EXPIRED_CREDIT_50"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"  # Adicionado
    REFUNDED = "REFUNDED"    # Adicionado
    FAILED = "FAILED"        # Adicionado


class OrderChannel(str, enum.Enum):
    """Canal do pedido"""
    ONLINE = "ONLINE"
    KIOSK = "KIOSK"
    MARKETPLACE = "MARKETPLACE"      # Adicionado
    SOCIAL_COMMERCE = "SOCIAL_COMMERCE"  # Adicionado
    WHATSAPP = "WHATSAPP"            # Adicionado


class PaymentMethod(str, enum.Enum):
    """Métodos de pagamento - Expandido para mercados globais"""
    
    # Brasil
    PIX = "PIX"
    BOLETO = "BOLETO"
    
    # Cartões
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    GIFT_CARD = "GIFT_CARD"
    PREPAID_CARD = "PREPAID_CARD"
    
    # Legacy (para compatibilidade)
    CARTAO = "CARTAO"  # Mantido para compatibilidade
    
    # América Latina
    MERCADO_PAGO_WALLET = "MERCADO_PAGO_WALLET"
    OXXO = "OXXO"
    SPEI = "SPEI"
    RAPIPAGO = "RAPIPAGO"
    PAGOFACIL = "PAGOFACIL"
    SERVIPAG = "SERVIPAG"
    KHIPU = "KHIPU"
    EFECTY = "EFECTY"
    PSE = "PSE"
    
    # América do Norte
    ACH = "ACH"
    VENMO = "VENMO"
    CASHAPP = "CASHAPP"
    ZELLE = "ZELLE"
    INTERAC = "INTERAC"
    
    # Europa
    MBWAY = "MBWAY"
    MULTIBANCO_REFERENCE = "MULTIBANCO_REFERENCE"
    SOFORT = "SOFORT"
    GIROPAY = "GIROPAY"
    KLARNA = "KLARNA"
    TRUSTLY = "TRUSTLY"
    IDEAL = "IDEAL"
    BANCONTACT = "BANCONTACT"
    TWINT = "TWINT"
    VIABILL = "VIABILL"
    MOBILEPAY = "MOBILEPAY"
    BLIK = "BLIK"
    PRZELEWY24 = "PRZELEWY24"
    SATISPAY = "SATISPAY"
    SEPA = "SEPA"
    PAYPAL = "PAYPAL"
    REVOLUT = "REVOLUT"
    
    # Wallets digitais
    NFC = "NFC"
    APPLE_PAY = "APPLE_PAY"
    GOOGLE_PAY = "GOOGLE_PAY"
    SAMSUNG_PAY = "SAMSUNG_PAY"
    
    # África
    M_PESA = "M_PESA"
    AIRTEL_MONEY = "AIRTEL_MONEY"
    MTN_MONEY = "MTN_MONEY"
    ORANGE_MONEY = "ORANGE_MONEY"
    VODAFONE_CASH = "VODAFONE_CASH"
    PAYSTACK = "PAYSTACK"
    FLUTTERWAVE = "FLUTTERWAVE"
    YOCO = "YOCO"
    
    # China
    ALIPAY = "ALIPAY"
    WECHAT_PAY = "WECHAT_PAY"
    UNIONPAY = "UNIONPAY"
    DCEP = "DCEP"  # Yuan digital
    
    # Japão
    PAYPAY = "PAYPAY"
    LINE_PAY = "LINE_PAY"
    RAKUTEN_PAY = "RAKUTEN_PAY"
    MERPAY = "MERPAY"
    KONBINI = "KONBINI"
    
    # Coreia do Sul
    KAKAO_PAY = "KAKAO_PAY"
    NAVER_PAY = "NAVER_PAY"
    TOSS = "TOSS"
    
    # Tailândia
    PROMPTPAY = "PROMPTPAY"
    TRUEMONEY = "TRUEMONEY"
    
    # Indonésia
    GO_PAY = "GO_PAY"
    OVO = "OVO"
    DANA = "DANA"
    
    # Singapura
    GRABPAY = "GRABPAY"
    DBS_PAYLAH = "DBS_PAYLAH"
    
    # Filipinas
    GCASH = "GCASH"
    PAYMAYA = "PAYMAYA"
    
    # Emirados Árabes
    TABBY = "TABBY"
    PAYBY = "PAYBY"
    
    # Turquia
    TROY = "TROY"
    BKM_EXPRESS = "BKM_EXPRESS"
    
    # Rússia
    MIR = "MIR"
    YOOMONEY = "YOOMONEY"
    QIWI = "QIWI"
    WEBMONEY = "WEBMONEY"
    
    # Austrália
    AFTERPAY = "AFTERPAY"
    ZIP = "ZIP"
    BPAY = "BPAY"
    POLI = "POLI"
    
    # Globais
    CRYPTO = "CRYPTO"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"
    BANK_TRANSFER = "BANK_TRANSFER"
    DIRECT_DEBIT = "DIRECT_DEBIT"
    
    @property
    def requires_wallet_provider(self) -> bool:
        """Verifica se o método requer um provedor de carteira"""
        wallet_methods = {
            self.APPLE_PAY, self.GOOGLE_PAY, self.SAMSUNG_PAY,
            self.MERCADO_PAGO_WALLET, self.PAYPAL, self.VENMO,
            self.CASHAPP, self.ZELLE, self.REVOLUT, self.ALIPAY,
            self.WECHAT_PAY, self.PAYPAY, self.LINE_PAY, self.KAKAO_PAY,
            self.GO_PAY, self.OVO, self.DANA, self.GRABPAY, self.GCASH,
            self.PAYMAYA, self.TABBY, self.AFTERPAY, self.ZIP,
            self.M_PESA, self.AIRTEL_MONEY, self.MTN_MONEY, self.YOOMONEY
        }
        return self in wallet_methods
    
    @property
    def is_instant(self) -> bool:
        """Verifica se o método é instantâneo"""
        instant_methods = {
            self.PIX, self.CREDIT_CARD, self.DEBIT_CARD, self.PREPAID_CARD,
            self.APPLE_PAY, self.GOOGLE_PAY, self.SAMSUNG_PAY,
            self.MERCADO_PAGO_WALLET, self.PAYPAL, self.VENMO,
            self.CASHAPP, self.ALIPAY, self.WECHAT_PAY, self.PAYPAY,
            self.M_PESA, self.GCASH, self.PAYMAYA
        }
        return self in instant_methods
    
    @property
    def is_bnpl(self) -> bool:
        """Verifica se é Buy Now Pay Later"""
        bnpl_methods = {
            self.KLARNA, self.AFTERPAY, self.ZIP, self.TABBY
        }
        return self in bnpl_methods
    
    @property
    def region(self) -> str:
        """Retorna a região primária do método"""
        region_map = {
            self.PIX: "BR", self.BOLETO: "BR",
            self.MBWAY: "PT", self.MULTIBANCO_REFERENCE: "PT",
            self.OXXO: "MX", self.SPEI: "MX",
            self.ALIPAY: "CN", self.WECHAT_PAY: "CN",
            self.PAYPAY: "JP", self.KONBINI: "JP",
            self.M_PESA: "KE", self.GCASH: "PH",
            self.AFTERPAY: "AU", self.ZIP: "AU",
        }
        return region_map.get(self, "GLOBAL")


class CardType(str, enum.Enum):
    """Tipo de cartão"""
    CREDIT = "creditCard"
    DEBIT = "debitCard"
    GIFT = "giftCard"
    PREPAID = "prepaidCard"  # Adicionado


class PaymentStatus(str, enum.Enum):
    """Status do pagamento"""
    CREATED = "CREATED"
    PENDING_CUSTOMER_ACTION = "PENDING_CUSTOMER_ACTION"
    PENDING_PROVIDER_CONFIRMATION = "PENDING_PROVIDER_CONFIRMATION"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    AWAITING_INTEGRATION = "AWAITING_INTEGRATION"
    REFUNDED = "REFUNDED"      # Adicionado
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"  # Adicionado
    
    @property
    def is_terminal(self) -> bool:
        """Verifica se é um status terminal"""
        terminal_statuses = {
            self.APPROVED, self.DECLINED, self.EXPIRED, 
            self.CANCELLED, self.REFUNDED
        }
        return self in terminal_statuses
    
    @property
    def requires_action(self) -> bool:
        """Verifica se requer ação do cliente"""
        action_statuses = {
            self.PENDING_CUSTOMER_ACTION, self.PENDING_PROVIDER_CONFIRMATION
        }
        return self in action_statuses


class PaymentInterface(str, enum.Enum):
    """Interface de pagamento"""
    NFC = "nfc"
    QR_CODE = "qr_code"
    CHIP = "chip"
    WEB_TOKEN = "web_token"
    MANUAL = "manual"
    DEEP_LINK = "deep_link"
    API = "api"
    USSD = "ussd"
    FACE_RECOGNITION = "face_recognition"
    FINGERPRINT = "fingerprint"
    BARCODE = "barcode"


class WalletProvider(str, enum.Enum):
    """Provedores de carteira digital"""
    # Internacionais
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    SAMSUNG_PAY = "samsungPay"
    PAYPAL = "paypal"
    
    # América Latina
    MERCADO_PAGO = "mercadoPago"
    PICPAY = "picpay"
    
    # América do Norte
    VENMO = "venmo"
    CASHAPP = "cashapp"
    
    # Europa
    REVOLUT = "revolut"
    MBWAY = "mbway"
    
    # África
    M_PESA = "mPesa"
    
    # China
    ALIPAY = "alipay"
    WECHAT_PAY = "wechatPay"
    
    # Japão
    PAYPAY = "paypay"
    LINE_PAY = "linePay"


# ==================== Model Order ====================

class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        Index("idx_orders_status", "status"),
        Index("idx_orders_channel_status", "channel", "status"),
        Index("idx_orders_region_status", "region", "status"),
        Index("idx_orders_region_totem_status", "region", "totem_id", "status"),
        Index("idx_orders_region_totem_created_at", "region", "totem_id", "created_at"),
        Index("idx_orders_paid_at", "paid_at"),
        Index("idx_orders_picked_up_at", "picked_up_at"),
        Index("idx_orders_status_picked_up", "status", "picked_up_at"),
        Index("idx_orders_totem_picked_up", "totem_id", "picked_up_at"),
        Index("idx_orders_public_access_token_hash", "public_access_token_hash"),
        Index("idx_orders_user_id_created_at", "user_id", "created_at"),
        Index("idx_orders_guest_session_id", "guest_session_id"),
        Index("idx_orders_payment_method_status", "payment_method", "status"),
        Index("idx_orders_created_at", "created_at"),
    )

    # Identificação
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    
    # Canal e região
    channel = Column(Enum(OrderChannel), nullable=False)
    region = Column(String, nullable=False)
    
    # Produto e locker
    totem_id = Column(String, nullable=False)
    sku_id = Column(String, nullable=False)
    
    # Valores
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, nullable=True, default="BRL")  # Adicionado
    
    # Status
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PAYMENT_PENDING)
    
    # Pagamento
    gateway_transaction_id = Column(String, nullable=True)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.CREATED,
    )
    payment_interface = Column(Enum(PaymentInterface), nullable=True)  # Adicionado
    wallet_provider = Column(Enum(WalletProvider), nullable=True)  # Adicionado
    card_type = Column(Enum(CardType), nullable=True)
    payment_updated_at = Column(DateTime, nullable=True)
    
    # Timestamps de eventos
    paid_at = Column(DateTime, nullable=True)
    pickup_deadline_at = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)  # Adicionado
    refunded_at = Column(DateTime, nullable=True)  # Adicionado
    
    # Identificação do cliente
    guest_session_id = Column(String, nullable=True)
    public_access_token_hash = Column(String, nullable=True)
    
    # Contato
    receipt_email = Column(String, nullable=True)
    receipt_phone = Column(String, nullable=True)
    consent_marketing = Column(Integer, nullable=False, default=0)
    guest_phone = Column(String, nullable=True)
    guest_email = Column(String, nullable=True)
    
    # Dispositivo e rastreamento
    device_id = Column(String, nullable=True)  # Adicionado
    ip_address = Column(String, nullable=True)  # Adicionado
    user_agent = Column(String, nullable=True)  # Adicionado
    
    # Idempotência
    idempotency_key = Column(String, nullable=True, unique=True)  # Adicionado
    
    # Metadados
    order_metadata = Column(JSONB, nullable=True, default={})  # Adicionado
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ==================== Métodos de instância ====================
    
    def touch(self) -> None:
        """Atualiza timestamp de modificação"""
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_payment_pending_customer_action(self) -> None:
        """Marca pagamento aguardando ação do cliente"""
        self.payment_status = PaymentStatus.PENDING_CUSTOMER_ACTION
        self.payment_updated_at = datetime.now(timezone.utc)
        self.touch()
    
    def mark_payment_pending_provider_confirmation(self) -> None:
        """Marca pagamento aguardando confirmação do provedor"""
        self.payment_status = PaymentStatus.PENDING_PROVIDER_CONFIRMATION
        self.payment_updated_at = datetime.now(timezone.utc)
        self.touch()
    
    def mark_payment_approved(self, transaction_id: Optional[str] = None) -> None:
        """Marca pagamento como aprovado"""
        self.payment_status = PaymentStatus.APPROVED
        self.payment_updated_at = datetime.now(timezone.utc)
        self.paid_at = self.paid_at or datetime.now(timezone.utc)
        if transaction_id:
            self.gateway_transaction_id = transaction_id
        self.touch()
    
    def mark_payment_declined(self, reason: Optional[str] = None) -> None:
        """Marca pagamento como recusado"""
        self.payment_status = PaymentStatus.DECLINED
        self.payment_updated_at = datetime.now(timezone.utc)
        if reason and self.metadata:
            self.metadata["decline_reason"] = reason
        self.touch()
    
    def mark_payment_expired(self) -> None:
        """Marca pagamento como expirado"""
        self.payment_status = PaymentStatus.EXPIRED
        self.payment_updated_at = datetime.now(timezone.utc)
        self.touch()
    
    def mark_payment_failed(self, error: Optional[str] = None) -> None:
        """Marca pagamento como falho"""
        self.payment_status = PaymentStatus.FAILED
        self.payment_updated_at = datetime.now(timezone.utc)
        if error and self.metadata:
            self.metadata["failure_error"] = error
        self.touch()
    
    def mark_payment_cancelled(self) -> None:
        """Marca pagamento como cancelado"""
        self.payment_status = PaymentStatus.CANCELLED
        self.payment_updated_at = datetime.now(timezone.utc)
        self.cancelled_at = datetime.now(timezone.utc)
        self.touch()
    
    def mark_payment_refunded(self) -> None:
        """Marca pagamento como reembolsado"""
        self.payment_status = PaymentStatus.REFUNDED
        self.payment_updated_at = datetime.now(timezone.utc)
        self.refunded_at = datetime.now(timezone.utc)
        self.touch()
    
    def mark_payment_awaiting_integration(self) -> None:
        """Marca pagamento aguardando integração"""
        self.payment_status = PaymentStatus.AWAITING_INTEGRATION
        self.payment_updated_at = datetime.now(timezone.utc)
        self.touch()
    
    def mark_as_paid(self) -> None:
        """Marca pedido como pago"""
        self.status = OrderStatus.PAID_PENDING_PICKUP
        self.paid_at = self.paid_at or datetime.now(timezone.utc)
        self.touch()
    
    def mark_as_dispensed(self) -> None:
        """Marca pedido como dispensado (slot liberado)"""
        self.status = OrderStatus.DISPENSED
        self.touch()
    
    def mark_as_picked_up(self) -> None:
        """Marca pedido como retirado"""
        self.status = OrderStatus.PICKED_UP
        self.picked_up_at = datetime.now(timezone.utc)
        self.touch()
    
    def mark_as_expired(self, credit_50: bool = False) -> None:
        """Marca pedido como expirado"""
        if credit_50:
            self.status = OrderStatus.EXPIRED_CREDIT_50
        else:
            self.status = OrderStatus.EXPIRED
        self.touch()
    
    def mark_as_cancelled(self) -> None:
        """Marca pedido como cancelado"""
        self.status = OrderStatus.CANCELLED
        self.cancelled_at = datetime.now(timezone.utc)
        self.touch()
    
    # ==================== Propriedades ====================
    
    @property
    def is_picked_up(self) -> bool:
        """Verifica se o pedido foi retirado"""
        return self.status == OrderStatus.PICKED_UP and self.picked_up_at is not None
    
    @property
    def is_paid(self) -> bool:
        """Verifica se o pedido foi pago"""
        return self.payment_status == PaymentStatus.APPROVED
    
    @property
    def is_expired(self) -> bool:
        """Verifica se o pedido expirou"""
        return self.status in {OrderStatus.EXPIRED, OrderStatus.EXPIRED_CREDIT_50}
    
    @property
    def is_cancelled(self) -> bool:
        """Verifica se o pedido foi cancelado"""
        return self.status == OrderStatus.CANCELLED
    
    @property
    def pickup_delay_minutes(self) -> int | None:
        """Calcula atraso na retirada em minutos"""
        if self.paid_at and self.picked_up_at:
            delta = self.picked_up_at - self.paid_at
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def payment_time_to_approval_seconds(self) -> int | None:
        """Tempo entre criação e aprovação do pagamento"""
        if self.created_at and self.paid_at:
            delta = self.paid_at - self.created_at
            return int(delta.total_seconds())
        return None
    
    @property
    def picked_up_within_deadline(self) -> bool | None:
        """Verifica se foi retirado dentro do prazo"""
        if self.pickup_deadline_at and self.picked_up_at:
            return self.picked_up_at <= self.pickup_deadline_at
        return None
    
    @property
    def amount_float(self) -> float:
        """Valor em float (centavos para decimal)"""
        return self.amount_cents / 100.0
    
    @property
    def amount_formatted(self) -> str:
        """Valor formatado como moeda"""
        return f"{self.amount_float:.2f} {self.currency or 'BRL'}"
    
    @property
    def is_test_order(self) -> bool:
        """Verifica se é pedido de teste"""
        return self.metadata and self.metadata.get("is_test", False)
    
    # ==================== Métodos de classe ====================
    
    @classmethod
    def create_idempotency_key(cls, prefix: str, identifier: str) -> str:
        """Gera chave de idempotência"""
        import hashlib
        raw = f"{prefix}:{identifier}:{datetime.utcnow().date()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    
"""
1. Enums Expandidos:
OrderStatus: Adicionados CANCELLED, REFUNDED, FAILED

OrderChannel: Adicionados MARKETPLACE, SOCIAL_COMMERCE, WHATSAPP

PaymentMethod: +50 novos métodos (China, Japão, África, Austrália, etc.)

PaymentStatus: Adicionados REFUNDED, PARTIALLY_REFUNDED

CardType: Adicionado PREPAID

Novos enums: PaymentInterface, WalletProvider

2. Novas Colunas:
currency: Moeda do pedido

payment_interface: Interface de pagamento usada

wallet_provider: Provedor da carteira digital

cancelled_at, refunded_at: Timestamps de eventos

device_id, ip_address, user_agent: Rastreamento

idempotency_key: Chave de idempotência (única)

metadata: JSONB para dados flexíveis

3. Propriedades dos Enums:
PaymentMethod.requires_wallet_provider: Verifica se requer wallet

PaymentMethod.is_instant: Verifica se é instantâneo

PaymentMethod.is_bnpl: Verifica se é BNPL

PaymentMethod.region: Região primária do método

PaymentStatus.is_terminal: Status terminal

PaymentStatus.requires_action: Requer ação do cliente

4. Novos Métodos de Instância:
mark_payment_refunded(): Marcar reembolso

mark_as_paid(): Marcar como pago

mark_as_dispensed(): Marcar como dispensado

mark_as_cancelled(): Marcar como cancelado

mark_as_expired(): Marcar como expirado

5. Novas Propriedades:
is_paid: Verifica se foi pago

is_expired: Verifica se expirou

is_cancelled: Verifica se foi cancelado

payment_time_to_approval_seconds: Tempo até aprovação

amount_float: Valor em float

amount_formatted: Valor formatado

is_test_order: Identifica pedido de teste

6. Índices Adicionais:
idx_orders_user_id_created_at: Para consultas por usuário

idx_orders_guest_session_id: Para sessões de convidado

idx_orders_payment_method_status: Para relatórios

idx_orders_created_at: Para consultas temporais

7. Suporte a Mercados:
Métodos específicos por região com propriedade region

Suporte a moedas diferentes via currency

Metadados flexíveis para requisitos regionais

8. Idempotência:
Campo idempotency_key único

Método create_idempotency_key() para geração

9. Rastreabilidade:
Campos de dispositivo (device_id, ip_address, user_agent)

Metadados para informações adicionais

Timestamps para todos os eventos

10. Compatibilidade:
Mantém enum CARTAO para compatibilidade

Colunas existentes preservadas

Novas colunas opcionais (nullable)

"""

