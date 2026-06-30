/// <reference types="vite/client" />

interface ImportMetaEnv {
  // API Configuration
  readonly VITE_API_URL: string
  readonly VITE_API_VERSION: string
  
  // Build Metadata (injected at build time)
  readonly VITE_BUILD_SHA: string
  readonly VITE_BUILD_TIME: string
  readonly VITE_DASHBOARD_VERSION: string
  readonly VITE_API_CONTRACT_VERSION: string
  readonly VITE_ENVIRONMENT: 'development' | 'production' | 'staging'
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
