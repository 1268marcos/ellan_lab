# 01_source/order_pickup_service/app/routers/payment_capabilities.py
# 03/04/2026 - profissional / canônico (ONLINE)
#
# Objetivo:
# - expor capacidades canônicas de pagamento por região
# - sem duplicar contrato no frontend
# - sem fallback simplista "api para tudo"
# - usando regras explícitas do schema orders.py
#
# Observação honesta:
# - este arquivo cobre o contrato ONLINE canônico usando OnlineRegion /
#   OnlinePaymentMethod / OnlinePaymentInterface / OnlineWalletProvider.
# - para KIOSK, o caminho profissional é consumir a MESMA matriz contratual
#   em uma segunda etapa, mas o arquivo completo de kiosk.py ainda não veio
#   integral aqui; então não vou inventar regra.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Query

from app.core.config import settings
from app.schemas.orders import (
    OnlinePaymentInterface,
    OnlinePaymentMethod,
    OnlineRegion,
    OnlineWalletProvider,
)

router = APIRouter(prefix="/payment-capabilities", tags=["payment-capabilities"])


# =========================================================
# MODELOS INTERNOS
# =========================================================

@dataclass(frozen=True)
class MethodCapability:
    method: OnlinePaymentMethod
    regions: Optional[Set[OnlineRegion]] = None
    interfaces: Set[OnlinePaymentInterface] = field(default_factory=set)
    requires: Set[str] = field(default_factory=set)
    wallet_provider: Optional[OnlineWalletProvider] = None
    labels: Optional[Dict[str, str]] = None
    constraints: Dict[str, Any] = field(default_factory=dict)

    def is_allowed_in_region(self, region: OnlineRegion) -> bool:
        return self.regions is None or region in self.regions

    def get_label(self) -> str:
        if self.labels and "pt-BR" in self.labels:
            return self.labels["pt-BR"]
        return self.method.name.replace("_", " ").title()


# =========================================================
# CONSTANTES REGIONAIS
# =========================================================

BRAZIL_REGIONS: Set[OnlineRegion] = {
    OnlineRegion.SP,
    OnlineRegion.RJ,
    OnlineRegion.MG,
    OnlineRegion.RS,
    OnlineRegion.BA,
}

MEXICO_REGIONS: Set[OnlineRegion] = {OnlineRegion.MX}
ARGENTINA_REGIONS: Set[OnlineRegion] = {OnlineRegion.AR}
CHILE_REGIONS: Set[OnlineRegion] = {OnlineRegion.CL}
COLOMBIA_REGIONS: Set[OnlineRegion] = {OnlineRegion.CO}
PORTUGAL_REGIONS: Set[OnlineRegion] = {OnlineRegion.PT}
CHINA_REGIONS: Set[OnlineRegion] = {OnlineRegion.CN}
JAPAN_REGIONS: Set[OnlineRegion] = {OnlineRegion.JP}
THAILAND_REGIONS: Set[OnlineRegion] = {OnlineRegion.TH}
INDONESIA_REGIONS: Set[OnlineRegion] = {OnlineRegion.ID}
SINGAPORE_REGIONS: Set[OnlineRegion] = {OnlineRegion.SG}
PHILIPPINES_REGIONS: Set[OnlineRegion] = {OnlineRegion.PH}
UAE_REGIONS: Set[OnlineRegion] = {OnlineRegion.AE}
TURKEY_REGIONS: Set[OnlineRegion] = {OnlineRegion.TR}
RUSSIA_REGIONS: Set[OnlineRegion] = {OnlineRegion.RU}
AUSTRALIA_REGIONS: Set[OnlineRegion] = {OnlineRegion.AU}

AFRICAN_MPESA_REGIONS: Set[OnlineRegion] = {
    OnlineRegion.KE,
    OnlineRegion.TZ,
    OnlineRegion.EG,
    OnlineRegion.UG,
    OnlineRegion.RW,
}


# =========================================================
# MATRIZ CANÔNICA ONLINE
# =========================================================

ONLINE_CAPABILITIES: List[MethodCapability] = [
    # -------------------------
    # Cartões
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.CREDIT_CARD,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.MANUAL,
            OnlinePaymentInterface.CHIP,
            OnlinePaymentInterface.NFC,
            OnlinePaymentInterface.CONTACTLESS,
            OnlinePaymentInterface.API,
            OnlinePaymentInterface.FACE_RECOGNITION,
            OnlinePaymentInterface.FINGERPRINT,
        },
        requires={"amount_cents"},
        labels={"pt-BR": "Cartão de crédito"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.DEBIT_CARD,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.MANUAL,
            OnlinePaymentInterface.CHIP,
            OnlinePaymentInterface.NFC,
            OnlinePaymentInterface.CONTACTLESS,
            OnlinePaymentInterface.API,
            OnlinePaymentInterface.FACE_RECOGNITION,
            OnlinePaymentInterface.FINGERPRINT,
        },
        requires={"amount_cents"},
        labels={"pt-BR": "Cartão de débito"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PREPAID_CARD,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.MANUAL,
            OnlinePaymentInterface.CHIP,
            OnlinePaymentInterface.NFC,
            OnlinePaymentInterface.CONTACTLESS,
            OnlinePaymentInterface.API,
            OnlinePaymentInterface.FACE_RECOGNITION,
            OnlinePaymentInterface.FINGERPRINT,
        },
        requires={"amount_cents"},
        labels={"pt-BR": "Cartão pré-pago"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.GIFT_CARD,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.MANUAL,
            OnlinePaymentInterface.CHIP,
            OnlinePaymentInterface.NFC,
            OnlinePaymentInterface.CONTACTLESS,
            OnlinePaymentInterface.API,
            OnlinePaymentInterface.FACE_RECOGNITION,
            OnlinePaymentInterface.FINGERPRINT,
        },
        labels={"pt-BR": "Gift card"},
    ),

    # -------------------------
    # Brasil
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.PIX,
        regions=BRAZIL_REGIONS,
        interfaces={
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.DEEP_LINK,
        },
        requires={"amount_cents"},
        labels={"pt-BR": "PIX"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BOLETO,
        regions=BRAZIL_REGIONS,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.DEEP_LINK,
        },
        requires={"amount_cents"},
        labels={"pt-BR": "Boleto"},
    ),

    # -------------------------
    # América Latina
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.MERCADO_PAGO_WALLET,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.DEEP_LINK,
            OnlinePaymentInterface.API,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.MERCADO_PAGO,
        labels={"pt-BR": "Mercado Pago"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MERCADO_CREDITO,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Mercado Crédito"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.OXXO,
        regions=MEXICO_REGIONS,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.BARCODE,
        },
        labels={"pt-BR": "OXXO"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SPEI,
        regions=MEXICO_REGIONS,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
            OnlinePaymentInterface.WEB_TOKEN,
        },
        labels={"pt-BR": "SPEI"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.RAPIPAGO,
        regions=ARGENTINA_REGIONS,
        interfaces={
            OnlinePaymentInterface.BARCODE,
            OnlinePaymentInterface.WEB_TOKEN,
        },
        labels={"pt-BR": "Rapipago"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PAGOFACIL,
        regions=ARGENTINA_REGIONS,
        interfaces={
            OnlinePaymentInterface.BARCODE,
            OnlinePaymentInterface.WEB_TOKEN,
        },
        labels={"pt-BR": "Pago Fácil"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SERVIPAG,
        regions=CHILE_REGIONS,
        interfaces={
            OnlinePaymentInterface.BARCODE,
            OnlinePaymentInterface.WEB_TOKEN,
        },
        labels={"pt-BR": "Servipag"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.KHIPU,
        regions=CHILE_REGIONS,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Khipu"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.EFECTY,
        regions=COLOMBIA_REGIONS,
        interfaces={
            OnlinePaymentInterface.BARCODE,
            OnlinePaymentInterface.WEB_TOKEN,
        },
        labels={"pt-BR": "Efecty"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PSE,
        regions=COLOMBIA_REGIONS,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "PSE"},
    ),

    # -------------------------
    # América do Norte
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.ACH,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "ACH"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.VENMO,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.DEEP_LINK,
            OnlinePaymentInterface.QR_CODE,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.VENMO,
        labels={"pt-BR": "Venmo"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.CASHAPP,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.DEEP_LINK,
            OnlinePaymentInterface.QR_CODE,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.CASHAPP,
        labels={"pt-BR": "Cash App"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.ZELLE,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Zelle"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.AFTERPAY,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Afterpay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.AFFIRM,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Affirm"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.KLARNA_US,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Klarna US"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.INTERAC,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Interac"},
    ),

    # -------------------------
    # Europa
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.APPLE_PAY,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.NFC,
            OnlinePaymentInterface.DEEP_LINK,
            OnlinePaymentInterface.FACE_RECOGNITION,
            OnlinePaymentInterface.FINGERPRINT,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.APPLE_PAY,
        labels={"pt-BR": "Apple Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.GOOGLE_PAY,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.NFC,
            OnlinePaymentInterface.DEEP_LINK,
            OnlinePaymentInterface.FINGERPRINT,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.GOOGLE_PAY,
        labels={"pt-BR": "Google Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MBWAY,
        regions=PORTUGAL_REGIONS,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.DEEP_LINK,
        },
        requires={"customer_phone", "amount_cents"},
        labels={"pt-BR": "MB WAY"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MULTIBANCO_REFERENCE,
        regions=PORTUGAL_REGIONS,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.BANK_LINK,
        },
        requires={"amount_cents"},
        labels={"pt-BR": "Multibanco"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SOFORT,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Sofort"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.GIROPAY,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Giropay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.KLARNA,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Klarna"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.TRUSTLY,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Trustly"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.IDEAL,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "iDEAL"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BANCONTACT,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Bancontact"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.TWINT,
        interfaces={
            OnlinePaymentInterface.QR_BILL,
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.DEEP_LINK,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.TWINT,
        labels={"pt-BR": "TWINT"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.VIABILL,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.VIABILL,
        labels={"pt-BR": "ViaBill"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MOBILEPAY,
        interfaces={
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.DEEP_LINK,
            OnlinePaymentInterface.WEB_TOKEN,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.MOBILEPAY,
        labels={"pt-BR": "MobilePay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.VIPS,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "VIPS"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BLIK,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.BLIK,
        labels={"pt-BR": "BLIK"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PRZELEWY24,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Przelewy24"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SATISPAY,
        interfaces={
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.DEEP_LINK,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.SATISPAY,
        labels={"pt-BR": "Satispay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SEPA,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "SEPA"},
    ),

    # -------------------------
    # Reino Unido
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.PAYPAL,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.DEEP_LINK,
            OnlinePaymentInterface.API,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.PAYPAL,
        labels={"pt-BR": "PayPal"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.GOOGLE_PAY_UK,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.NFC,
            OnlinePaymentInterface.DEEP_LINK,
        },
        labels={"pt-BR": "Google Pay UK"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.APPLE_PAY_UK,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.NFC,
            OnlinePaymentInterface.DEEP_LINK,
        },
        labels={"pt-BR": "Apple Pay UK"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.FASTER_PAYMENTS,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Faster Payments"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BACS,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "BACS"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.CLEARPAY,
        interfaces={
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Clearpay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MONZO,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.MONZO,
        labels={"pt-BR": "Monzo"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.REVOLUT,
        interfaces={
            OnlinePaymentInterface.BANK_LINK,
            OnlinePaymentInterface.API,
            OnlinePaymentInterface.DEEP_LINK,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.REVOLUT,
        labels={"pt-BR": "Revolut"},
    ),

    # -------------------------
    # África
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.M_PESA,
        regions=AFRICAN_MPESA_REGIONS,
        interfaces={
            OnlinePaymentInterface.USSD,
            OnlinePaymentInterface.SMS,
            OnlinePaymentInterface.API,
            OnlinePaymentInterface.QR_CODE,
        },
        requires={"customer_phone", "ussd_session_id", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.M_PESA,
        labels={"pt-BR": "M-PESA"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.AIRTEL_MONEY,
        interfaces={
            OnlinePaymentInterface.USSD,
            OnlinePaymentInterface.SMS,
            OnlinePaymentInterface.API,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.AIRTEL_MONEY,
        labels={"pt-BR": "Airtel Money"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MTN_MONEY,
        interfaces={
            OnlinePaymentInterface.USSD,
            OnlinePaymentInterface.SMS,
            OnlinePaymentInterface.API,
        },
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.MTN_MONEY,
        labels={"pt-BR": "MTN Money"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.ORANGE_MONEY,
        interfaces={
            OnlinePaymentInterface.USSD,
            OnlinePaymentInterface.SMS,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Orange Money"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.VODAFONE_CASH,
        interfaces={
            OnlinePaymentInterface.USSD,
            OnlinePaymentInterface.SMS,
            OnlinePaymentInterface.API,
        },
        labels={"pt-BR": "Vodafone Cash"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.TELECASH,
        interfaces={OnlinePaymentInterface.USSD, OnlinePaymentInterface.API},
        labels={"pt-BR": "TeleCash"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.ECONET,
        interfaces={OnlinePaymentInterface.USSD, OnlinePaymentInterface.API},
        labels={"pt-BR": "Econet"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PAYSTACK,
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.WEB_TOKEN},
        labels={"pt-BR": "Paystack"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.FLUTTERWAVE,
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.WEB_TOKEN},
        labels={"pt-BR": "Flutterwave"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.YOCO,
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.POS},
        labels={"pt-BR": "Yoco"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PEACH_PAYMENTS,
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.WEB_TOKEN},
        labels={"pt-BR": "Peach Payments"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SNOOPY,
        interfaces={OnlinePaymentInterface.API},
        labels={"pt-BR": "Snoopy"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.UNITEL_MONEY,
        interfaces={OnlinePaymentInterface.USSD, OnlinePaymentInterface.API},
        labels={"pt-BR": "Unitel Money"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MOOV_MONEY,
        interfaces={OnlinePaymentInterface.USSD, OnlinePaymentInterface.API},
        labels={"pt-BR": "Moov Money"},
    ),

    # -------------------------
    # China
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.ALIPAY,
        regions=CHINA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE},
        requires={"qr_code_content", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.ALIPAY,
        labels={"pt-BR": "Alipay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.WECHAT_PAY,
        regions=CHINA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE},
        requires={"qr_code_content", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.WECHAT_PAY,
        labels={"pt-BR": "WeChat Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.UNIONPAY,
        regions=CHINA_REGIONS,
        interfaces={
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.CHIP,
            OnlinePaymentInterface.NFC,
        },
        requires={"qr_code_content"},
        labels={"pt-BR": "UnionPay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.JD_PAY,
        regions=CHINA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE},
        requires={"qr_code_content"},
        labels={"pt-BR": "JD Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BAIDU_WALLET,
        regions=CHINA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        labels={"pt-BR": "Baidu Wallet"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.DCEP,
        regions=CHINA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.API},
        requires={"qr_code_content"},
        labels={"pt-BR": "DCEP"},
    ),

    # -------------------------
    # Japão
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.PAYPAY,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.PAYPAY,
        labels={"pt-BR": "PayPay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.LINE_PAY,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.LINE_PAY,
        labels={"pt-BR": "LINE Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.RAKUTEN_PAY,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.RAKUTEN_PAY,
        labels={"pt-BR": "Rakuten Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MERPAY,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.MERPAY,
        labels={"pt-BR": "Merpay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.AU_PAY,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.AU_PAY,
        labels={"pt-BR": "au PAY"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.D_PAY,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.D_PAY,
        labels={"pt-BR": "d Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.JCB_PREPAID,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.API},
        labels={"pt-BR": "JCB Prepaid"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.KONBINI,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.BARCODE, OnlinePaymentInterface.KIOSK},
        requires={"konbini_code"},
        labels={"pt-BR": "Konbini"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BANK_TRANSFER_JP,
        regions=JAPAN_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "Bank Transfer JP"},
    ),

    # -------------------------
    # Coreia do Sul
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.KAKAO_PAY,
        regions={OnlineRegion.KR},
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.KAKAO_PAY,
        labels={"pt-BR": "Kakao Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.NAVER_PAY,
        regions={OnlineRegion.KR},
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.NAVER_PAY,
        labels={"pt-BR": "Naver Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SAMSUNG_PAY,
        regions={OnlineRegion.KR},
        interfaces={OnlinePaymentInterface.NFC, OnlinePaymentInterface.WEB_TOKEN},
        labels={"pt-BR": "Samsung Pay KR"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.TOSS,
        regions={OnlineRegion.KR},
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.TOSS,
        labels={"pt-BR": "Toss"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PAYCO,
        regions={OnlineRegion.KR},
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.PAYCO,
        labels={"pt-BR": "PAYCO"},
    ),

    # -------------------------
    # Tailândia
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.PROMPTPAY,
        regions=THAILAND_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE},
        requires={"qr_code_content"},
        labels={"pt-BR": "PromptPay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.TRUEMONEY,
        regions=THAILAND_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.TRUEMONEY,
        labels={"pt-BR": "TrueMoney"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.RABBIT_LINE_PAY,
        regions=THAILAND_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.RABBIT_LINE_PAY,
        labels={"pt-BR": "Rabbit LINE Pay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SCB_EASY,
        regions=THAILAND_REGIONS,
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.BANK_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.SCB_EASY,
        labels={"pt-BR": "SCB Easy"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.KPLUS,
        regions=THAILAND_REGIONS,
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.BANK_LINK},
        labels={"pt-BR": "K Plus"},
    ),

    # -------------------------
    # Indonésia
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.GO_PAY,
        regions=INDONESIA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"customer_phone", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.GO_PAY,
        labels={"pt-BR": "GoPay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.OVO,
        regions=INDONESIA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"customer_phone", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.OVO,
        labels={"pt-BR": "OVO"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.DANA,
        regions=INDONESIA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"customer_phone", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.DANA,
        labels={"pt-BR": "DANA"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.LINKAJA,
        regions=INDONESIA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"customer_phone", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.LINKAJA,
        labels={"pt-BR": "LinkAja"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SHOPEEPAY_ID,
        regions=INDONESIA_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        labels={"pt-BR": "ShopeePay ID"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.DOKU,
        regions=INDONESIA_REGIONS,
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.WEB_TOKEN},
        labels={"pt-BR": "DOKU"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.MANDIRI_BILLS,
        regions=INDONESIA_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "Mandiri Bills"},
    ),

    # -------------------------
    # Singapura
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.GRABPAY,
        regions=SINGAPORE_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.GRABPAY,
        labels={"pt-BR": "GrabPay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.DBS_PAYLAH,
        regions=SINGAPORE_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.DBS_PAYLAH,
        labels={"pt-BR": "DBS PayLah!"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.OCBC_PAY_ANYONE,
        regions=SINGAPORE_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "OCBC Pay Anyone"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SINGTEL_DASH,
        regions=SINGAPORE_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.SINGTEL_DASH,
        labels={"pt-BR": "Singtel Dash"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.NETSPAY,
        regions=SINGAPORE_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "NETSPay"},
    ),

    # -------------------------
    # Filipinas
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.GCASH,
        regions=PHILIPPINES_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"customer_phone", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.GCASH,
        labels={"pt-BR": "GCash"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PAYMAYA,
        regions=PHILIPPINES_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"customer_phone", "wallet_provider"},
        wallet_provider=OnlineWalletProvider.PAYMAYA,
        labels={"pt-BR": "PayMaya"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.GRABPAY_PH,
        regions=PHILIPPINES_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        labels={"pt-BR": "GrabPay PH"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.LANDBANK,
        regions=PHILIPPINES_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "Landbank"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PESONET,
        regions=PHILIPPINES_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "PESONet"},
    ),

    # -------------------------
    # Emirados Árabes
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.APPLE_PAY_AE,
        regions=UAE_REGIONS,
        interfaces={OnlinePaymentInterface.NFC, OnlinePaymentInterface.WEB_TOKEN},
        labels={"pt-BR": "Apple Pay AE"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SAMSUNG_PAY_AE,
        regions=UAE_REGIONS,
        interfaces={OnlinePaymentInterface.NFC, OnlinePaymentInterface.WEB_TOKEN},
        labels={"pt-BR": "Samsung Pay AE"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.PAYBY,
        regions=UAE_REGIONS,
        interfaces={OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.PAYBY,
        labels={"pt-BR": "PayBy"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.DP_WORLD,
        regions=UAE_REGIONS,
        interfaces={OnlinePaymentInterface.API},
        labels={"pt-BR": "DP World"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.TABBY,
        regions=UAE_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.API},
        requires={"customer_email", "wallet_provider", "amount_cents"},
        wallet_provider=OnlineWalletProvider.TABBY,
        labels={"pt-BR": "Tabby"},
    ),

    # -------------------------
    # Turquia
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.TROY,
        regions=TURKEY_REGIONS,
        interfaces={OnlinePaymentInterface.CHIP, OnlinePaymentInterface.NFC, OnlinePaymentInterface.WEB_TOKEN},
        requires={"turkish_id"},
        labels={"pt-BR": "Troy"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BKM_EXPRESS,
        regions=TURKEY_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.BKM_EXPRESS,
        labels={"pt-BR": "BKM Express"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.ININAL,
        regions=TURKEY_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.API},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.ININAL,
        labels={"pt-BR": "Ininal"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.TURKCELL_PAY,
        regions=TURKEY_REGIONS,
        interfaces={OnlinePaymentInterface.DEEP_LINK, OnlinePaymentInterface.API},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.TURKCELL_PAY,
        labels={"pt-BR": "Turkcell Pay"},
    ),

    # -------------------------
    # Rússia
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.MIR,
        regions=RUSSIA_REGIONS,
        interfaces={OnlinePaymentInterface.CHIP, OnlinePaymentInterface.NFC, OnlinePaymentInterface.WEB_TOKEN},
        requires={"national_id"},
        labels={"pt-BR": "MIR"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.SBERBANK_ONLINE,
        regions=RUSSIA_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "Sberbank Online"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.YOOMONEY,
        regions=RUSSIA_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.DEEP_LINK},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.YOOMONEY,
        labels={"pt-BR": "YooMoney"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.QIWI,
        regions=RUSSIA_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.API},
        labels={"pt-BR": "QIWI"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.WEBMONEY,
        regions=RUSSIA_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.API},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.WEBMONEY,
        labels={"pt-BR": "WebMoney"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.TINKOFF,
        regions=RUSSIA_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        requires={"wallet_provider"},
        wallet_provider=OnlineWalletProvider.TINKOFF,
        labels={"pt-BR": "Tinkoff"},
    ),

    # -------------------------
    # Austrália
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.POLI,
        regions=AUSTRALIA_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "POLi"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.AFTERPAY_AU,
        regions=AUSTRALIA_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.API},
        requires={"wallet_provider", "amount_cents"},
        wallet_provider=OnlineWalletProvider.AFTERPAY,
        labels={"pt-BR": "Afterpay AU"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.ZIP,
        regions=AUSTRALIA_REGIONS,
        interfaces={OnlinePaymentInterface.WEB_TOKEN, OnlinePaymentInterface.API},
        requires={"wallet_provider", "amount_cents"},
        wallet_provider=OnlineWalletProvider.ZIP,
        labels={"pt-BR": "Zip"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BPAY,
        regions=AUSTRALIA_REGIONS,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        requires={"customer_phone_or_customer_email"},
        labels={"pt-BR": "BPAY"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.OPAY,
        regions=AUSTRALIA_REGIONS,
        interfaces={OnlinePaymentInterface.API},
        labels={"pt-BR": "OPay"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BEEM_IT,
        regions=AUSTRALIA_REGIONS,
        interfaces={OnlinePaymentInterface.DEEP_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "Beem It"},
    ),

    # -------------------------
    # Globais
    # -------------------------
    MethodCapability(
        method=OnlinePaymentMethod.CRYPTO,
        interfaces={OnlinePaymentInterface.API, OnlinePaymentInterface.QR_CODE, OnlinePaymentInterface.WEB_TOKEN},
        labels={"pt-BR": "Crypto"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.CASH_ON_DELIVERY,
        interfaces={OnlinePaymentInterface.COD},
        labels={"pt-BR": "Cash on Delivery"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.BANK_TRANSFER,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "Transferência bancária"},
    ),
    MethodCapability(
        method=OnlinePaymentMethod.DIRECT_DEBIT,
        interfaces={OnlinePaymentInterface.BANK_LINK, OnlinePaymentInterface.API},
        labels={"pt-BR": "Débito direto"},
    ),
]


# =========================================================
# ÍNDICES / HELPERS
# =========================================================

CAPABILITY_BY_METHOD: Dict[OnlinePaymentMethod, MethodCapability] = {
    item.method: item for item in ONLINE_CAPABILITIES
}


def _serialize_interface(interface: OnlinePaymentInterface) -> Dict[str, str]:
    return {
        "code": interface.value,
        "label": interface.name.replace("_", " ").title(),
    }


def _build_context_constraints(region: OnlineRegion) -> Dict[str, Any]:
    return {
        "currency": settings.get_default_currency(region.value),
        "pickup_window_sec": settings.get_pickup_window_sec(region.value),
        "prepayment_timeout_sec": settings.get_prepayment_timeout_sec(region.value),
        "alloc_ttl_sec": settings.get_alloc_ttl_sec(region.value),
        "backend_timeout_sec": settings.get_backend_timeout_sec(region.value),
        "region_group": settings.get_region_group(region.value).value
        if settings.get_region_group(region.value)
        else None,
        "requires_qr_code_regionally": settings.requires_qr_code(region.value),
        "requires_identity_validation_regionally": settings.requires_identity_validation(region.value),
        "regional_features_enabled": settings.regional_features_enabled.get(region.value, []),
    }


def _serialize_method(cap: MethodCapability, region: OnlineRegion) -> Dict[str, Any]:
    interface_list = sorted(cap.interfaces, key=lambda i: i.value)
    return {
        "method": cap.method.value,
        "label": cap.get_label(),
        "interfaces": [_serialize_interface(i) for i in interface_list],
        "requires": sorted(cap.requires),
        "wallet_required": cap.wallet_provider is not None,
        "wallet_provider": cap.wallet_provider.value if cap.wallet_provider else None,
        "region_specific": cap.regions is not None,
        "constraints": {
            **cap.constraints,
            "allowed_in_region": True,
            "region": region.value,
        },
    }


def _build_methods_for_region(region: OnlineRegion) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for method in OnlinePaymentMethod:
        cap = CAPABILITY_BY_METHOD.get(method)
        if cap is None:
            continue
        if not cap.is_allowed_in_region(region):
            continue
        items.append(_serialize_method(cap, region))
    return items


# =========================================================
# ENDPOINT
# =========================================================

@router.get("/")
def get_payment_capabilities(
    region: OnlineRegion = Query(..., description="Região ONLINE"),
) -> Dict[str, Any]:
    return {
        "channel": "online",
        "region": region.value,
        "currency": settings.get_default_currency(region.value),
        "context": _build_context_constraints(region),
        "methods": _build_methods_for_region(region),
    }