import { useState, useCallback } from 'react'
import './BuildInfo.css'

interface BuildInfoData {
  version: string
  buildSha: string
  buildTime: string
  apiContractVersion: string
  environment: string
}

const GITHUB_REPO = 'OpenHands/Librarian'

function formatTimestamp(isoString: string): string {
  if (!isoString) return 'Unknown'
  try {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
      timeZoneName: 'short',
    })
  } catch {
    return isoString
  }
}

function formatShortTime(isoString: string): string {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    return date.toISOString().replace('T', ' ').substring(0, 16) + ' UTC'
  } catch {
    return isoString
  }
}

function BuildInfo() {
  const [copied, setCopied] = useState(false)

  const buildInfo: BuildInfoData = {
    version: import.meta.env.VITE_DASHBOARD_VERSION || 'dev',
    buildSha: import.meta.env.VITE_BUILD_SHA || 'local',
    buildTime: import.meta.env.VITE_BUILD_TIME || '',
    apiContractVersion: import.meta.env.VITE_API_CONTRACT_VERSION || 'unknown',
    environment: import.meta.env.VITE_ENVIRONMENT || 'development',
  }

  const getGitHubCommitUrl = (sha: string): string => {
    return `https://github.com/${GITHUB_REPO}/commit/${sha}`
  }

  const copyToClipboard = useCallback(async () => {
    const infoText = [
      `Dashboard v${buildInfo.version}`,
      `Build ${buildInfo.buildSha}`,
      `Built ${formatShortTime(buildInfo.buildTime)}`,
      `API Contract ${buildInfo.apiContractVersion}`,
      `Environment: ${buildInfo.environment}`,
    ].join('\n')

    try {
      await navigator.clipboard.writeText(infoText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }, [buildInfo])

  const isProduction = buildInfo.environment === 'production'

  return (
    <footer className="build-info">
      <div className="build-info-content">
        <div className="build-info-left">
          <span className="build-info-item version">
            Dashboard v{buildInfo.version}
          </span>
          <span className="build-info-separator">|</span>
          <a
            href={getGitHubCommitUrl(buildInfo.buildSha)}
            target="_blank"
            rel="noopener noreferrer"
            className="build-info-item build-sha"
            title="View commit on GitHub"
          >
            Build {buildInfo.buildSha}
          </a>
          <span className="build-info-separator">|</span>
          <span className="build-info-item build-time" title={formatTimestamp(buildInfo.buildTime)}>
            Built {formatShortTime(buildInfo.buildTime)}
          </span>
        </div>
        <div className="build-info-right">
          <span className="build-info-item api-version">
            API Contract {buildInfo.apiContractVersion}
          </span>
          <span className="build-info-separator">|</span>
          <span className={`build-info-item environment ${isProduction ? 'production' : 'development'}`}>
            {buildInfo.environment}
          </span>
          <button
            className={`build-info-copy-btn ${copied ? 'copied' : ''}`}
            onClick={copyToClipboard}
            title="Copy build info to clipboard"
          >
            {copied ? '✓ Copied' : '📋 Copy'}
          </button>
        </div>
      </div>
    </footer>
  )
}

export default BuildInfo
