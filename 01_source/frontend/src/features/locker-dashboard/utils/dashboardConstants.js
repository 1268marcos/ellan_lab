// 01_source/frontend/src/features/locker-dashboard/utils/dashboardConstants.js

export const SLOT_STATES = [
  "AVAILABLE",
  "RESERVED",
  "PAID_PENDING_PICKUP",
  "PICKED_UP",
  "OUT_OF_STOCK",
];

export const LOCKER_REGISTRY_FALLBACK = {
  "SP-OSASCO-CENTRO-LK-001": {
    region: "SP",
    site_id: "SP-OSASCO-CENTRO",
    display_name: "ELLAN Locker Osasco Centro 001",
    backend_region: "SP",
    slots: 24,
    channels: ["ONLINE", "KIOSK"],
    payment_methods: ["PIX", "CARTAO", "NFC"],
    address: {
      address: "Rua Primitiva Vianco",
      number: "77",
      additional_information: "Sala 21",
      locality: "Centro",
      city: "Osasco",
      federative_unit: "SP",
      postal_code: "06001-000",
      country: "BR",
    },
    active: true,
  },
  "SP-CARAPICUIBA-JDMARILU-LK-001": {
    region: "SP",
    site_id: "SP-CARAPICUIBA-JDMARILU",
    display_name: "ELLAN Locker Carapicuíba Jardim Marilu 001",
    backend_region: "SP",
    slots: 24,
    channels: ["ONLINE", "KIOSK"],
    payment_methods: ["PIX", "CARTAO", "NFC"],
    address: {
      address: "Estrada Aldeinha",
      number: "7509",
      additional_information: "Apto 45",
      locality: "Jardim Marilu",
      city: "Carapicuíba",
      federative_unit: "SP",
      postal_code: "06343-040",
      country: "BR",
    },
    active: true,
  },
  "PT-MAIA-CENTRO-LK-001": {
    region: "PT",
    site_id: "PT-MAIA-CENTRO",
    display_name: "ELLAN Locker Maia Centro 001",
    backend_region: "PT",
    slots: 24,
    channels: ["ONLINE", "KIOSK"],
    payment_methods: ["CARTAO", "MBWAY", "MULTIBANCO_REFERENCE", "NFC"],
    address: {
      address: "Rua Padre Antonio",
      number: "12",
      additional_information: "",
      locality: "Centro",
      city: "Maia",
      federative_unit: "Porto",
      postal_code: "4400-001",
      country: "PT",
    },
    active: true,
  },
  "PT-GUIMARAES-AZUREM-LK-001": {
    region: "PT",
    site_id: "PT-GUIMARAES-AZUREM",
    display_name: "ELLAN Locker Guimarães Azurém 001",
    backend_region: "PT",
    slots: 24,
    channels: ["ONLINE", "KIOSK"],
    payment_methods: ["CARTAO", "MBWAY", "MULTIBANCO_REFERENCE", "NFC"],
    address: {
      address: "Rua Dona Maria",
      number: "258",
      additional_information: "Sub-cave",
      locality: "Azurém",
      city: "Guimarães",
      federative_unit: "Braga",
      postal_code: "4582-052",
      country: "PT",
    },
    active: true,
  },
  "ES-MADRID-CENTRO-LK-001": {
    region: "ES",
    site_id: "ES-MADRID-CENTRO",
    display_name: "ELLAN Locker Madrid Praça 001",
    backend_region: "ES",
    slots: 24,
    channels: ["ONLINE", "KIOSK", "APP"],
    payment_methods: ["CARTAO", "NFC", "CASH"],
    address: {
      address: "Praça Central",
      number: "1",
      additional_information: "",
      locality: "Centro",
      city: "Madrid",
      federative_unit: "MD",
      postal_code: "1111-111",
      country: "ES",
    },
    active: true,
  },
  "SP-VILAOLIMPIA-FOOD-LK-001": {
    region: "SP",
    site_id: "SP-VILAOLIMPIA-FOOD",
    display_name: "ELLAN Locker São Paulo Vila Olímpia 001",
    backend_region: "SP",
    slots: 24,
    channels: ["ONLINE", "KIOSK", "APP"],
    payment_methods: ["CARTAO", "NFC", "CASH"],
    address: {
      address: "Rua Portugal",
      number: "211",
      additional_information: "",
      locality: "Vila Olímpia",
      city: "São Paulo",
      federative_unit: "SP",
      postal_code: "01000-000",
      country: "BR",
    },
    active: true,
  },
};

export const STATE_STYLE = {
  AVAILABLE: { bg: "#1f7a3f", fg: "white", label: "Disponível" },
  RESERVED: { bg: "#c79200", fg: "black", label: "Reservada" },
  PAID_PENDING_PICKUP: { bg: "#1b5883", fg: "white", label: "Pago (aguardando)" },
  PICKED_UP: { bg: "#6b6b6b", fg: "white", label: "Retirado" },
  OUT_OF_STOCK: { bg: "#b3261e", fg: "white", label: "Indisponível" },
};

export const ORDER_STATUS_META = {
  PAYMENT_PENDING: {
    label: "Pagamento pendente",
    tone: "warning",
    bg: "linear-gradient(135deg, rgba(199,146,0,0.22), rgba(199,146,0,0.10))",
    border: "rgba(199,146,0,0.42)",
  },
  PAID_PENDING_PICKUP: {
    label: "Pago / aguardando retirada",
    tone: "info",
    bg: "linear-gradient(135deg, rgba(27,88,131,0.28), rgba(27,88,131,0.12))",
    border: "rgba(27,88,131,0.45)",
  },
  PICKED_UP: {
    label: "Retirado",
    tone: "neutral",
    bg: "linear-gradient(135deg, rgba(107,107,107,0.24), rgba(107,107,107,0.10))",
    border: "rgba(107,107,107,0.40)",
  },
  EXPIRED: {
    label: "Expirado",
    tone: "danger",
    bg: "linear-gradient(135deg, rgba(179,38,30,0.26), rgba(179,38,30,0.12))",
    border: "rgba(179,38,30,0.42)",
  },
  EXPIRED_CREDIT_50: {
    label: "Expirado / crédito 50%",
    tone: "danger",
    bg: "linear-gradient(135deg, rgba(179,38,30,0.26), rgba(179,38,30,0.12))",
    border: "rgba(179,38,30,0.42)",
  },
  DISPENSED: {
    label: "Dispensado no KIOSK",
    tone: "info",
    bg: "linear-gradient(135deg, rgba(95,61,196,0.28), rgba(95,61,196,0.10))",
    border: "rgba(95,61,196,0.42)",
  },
  SEM_PEDIDO: {
    label: "Sem pedido",
    tone: "neutral",
    bg: "linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))",
    border: "rgba(255,255,255,0.14)",
  },
};

export const PICKUP_STATUS_META = {
  ACTIVE: {
    label: "Pickup ativo",
    bg: "rgba(27,88,131,0.22)",
    border: "rgba(27,88,131,0.45)",
  },
  REDEEMED: {
    label: "Pickup retirado",
    bg: "rgba(31,122,63,0.22)",
    border: "rgba(31,122,63,0.45)",
  },
  EXPIRED: {
    label: "Pickup expirado",
    bg: "rgba(179,38,30,0.20)",
    border: "rgba(179,38,30,0.45)",
  },
  CANCELLED: {
    label: "Pickup cancelado",
    bg: "rgba(107,107,107,0.22)",
    border: "rgba(107,107,107,0.45)",
  },
};

export const ALLOCATION_STATUS_META = {
  RESERVED_PENDING_PAYMENT: {
    label: "Reserva pendente",
    bg: "rgba(199,146,0,0.22)",
    border: "rgba(199,146,0,0.45)",
  },
  RESERVED_PAID_PENDING_PICKUP: {
    label: "Reservado / pago",
    bg: "rgba(27,88,131,0.22)",
    border: "rgba(27,88,131,0.45)",
  },
  OPENED_FOR_PICKUP: {
    label: "Aberto para retirada",
    bg: "rgba(95,61,196,0.22)",
    border: "rgba(95,61,196,0.45)",
  },
  PICKED_UP: {
    label: "Retirada concluída",
    bg: "rgba(31,122,63,0.22)",
    border: "rgba(31,122,63,0.45)",
  },
  EXPIRED: {
    label: "Alocação expirada",
    bg: "rgba(179,38,30,0.20)",
    border: "rgba(179,38,30,0.45)",
  },
  RELEASED: {
    label: "Alocação liberada",
    bg: "rgba(107,107,107,0.22)",
    border: "rgba(107,107,107,0.45)",
  },
  CANCELLED: {
    label: "Alocação cancelada",
    bg: "rgba(107,107,107,0.22)",
    border: "rgba(107,107,107,0.45)",
  },
};

export const CHANNEL_META = {
  ONLINE: {
    label: "ONLINE",
    bg: "rgba(27,88,131,0.22)",
    border: "rgba(27,88,131,0.45)",
  },
  KIOSK: {
    label: "KIOSK",
    bg: "rgba(95,61,196,0.22)",
    border: "rgba(95,61,196,0.45)",
  },
};

export const OPERATIONAL_HIGHLIGHT_LEGEND = [
  {
    key: "KIOSK_DISPENSED",
    label: "KIOSK • DISPENSED",
    bg: "linear-gradient(135deg, rgba(95,61,196,0.18), rgba(95,61,196,0.06))",
    border: "rgba(95,61,196,0.70)",
  },
  {
    key: "ONLINE_PENDING_PICKUP",
    label: "ONLINE • PAID_PENDING_PICKUP",
    bg: "linear-gradient(135deg, rgba(27,88,131,0.22), rgba(27,88,131,0.08))",
    border: "rgba(27,88,131,0.70)",
  },
  {
    key: "ONLINE_PICKED_UP",
    label: "ONLINE • PICKED_UP",
    bg: "linear-gradient(135deg, rgba(31,122,63,0.18), rgba(31,122,63,0.06))",
    border: "rgba(31,122,63,0.70)",
  },
];

export const DIGITAL_WALLET_PROVIDER_BY_METHOD = {
  APPLE_PAY: "applePay",
  GOOGLE_PAY: "googlePay",
  MERCADO_PAGO_WALLET: "mercadoPago",
};

export const DEFAULT_GROUP_SIZE = 4;

export const DEFAULT_SLOT_STATE = {
  state: "AVAILABLE",
  product_id: null,
  updated_at: null,
};