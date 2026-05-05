/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PARTNER_ID?: string
  readonly VITE_WALLET_USER_ID?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
