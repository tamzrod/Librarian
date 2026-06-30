import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

function getGitCommit(): string {
  try {
    const gitDir = resolve(__dirname, '..', '.git')
    const head = readFileSync(resolve(gitDir, 'HEAD'), 'utf-8').trim()
    if (head.startsWith('ref: ')) {
      const ref = head.slice(5)
      return readFileSync(resolve(gitDir, ref), 'utf-8').trim().slice(0, 7)
    }
    return head.slice(0, 7)
  } catch {
    return 'unknown'
  }
}

function getApiContractVersion(): string {
  try {
    const contractPath = resolve(__dirname, '..', 'docs', 'api-contract', 'v1.0.md')
    const content = readFileSync(contractPath, 'utf-8')
    const match = content.match(/^# API Contract (v[\d.]+)/m)
    return match ? match[1] : 'v1.0'
  } catch {
    return 'v1.0'
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  const buildSha = env.VITE_BUILD_SHA || getGitCommit()
  const buildTime = env.VITE_BUILD_TIME || new Date().toISOString()
  const dashboardVersion = env.VITE_DASHBOARD_VERSION || 'dev'
  const apiContractVersion = env.VITE_API_CONTRACT_VERSION || getApiContractVersion()
  const environment = env.VITE_ENVIRONMENT || (mode === 'production' ? 'production' : 'development')

  return {
    plugins: [react()],
    define: {
      'import.meta.env.VITE_BUILD_SHA': JSON.stringify(buildSha),
      'import.meta.env.VITE_BUILD_TIME': JSON.stringify(buildTime),
      'import.meta.env.VITE_DASHBOARD_VERSION': JSON.stringify(dashboardVersion),
      'import.meta.env.VITE_API_CONTRACT_VERSION': JSON.stringify(apiContractVersion),
      'import.meta.env.VITE_ENVIRONMENT': JSON.stringify(environment),
    },
    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
    },
  }
})
