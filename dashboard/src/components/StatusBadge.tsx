import './StatusBadge.css'

interface StatusBadgeProps {
  status: 'healthy' | 'degraded' | 'inactive' | 'warning' | 'error'
  label: string
  size?: 'small' | 'medium'
}

function StatusBadge({ status, label, size = 'small' }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-${status} size-${size}`}>
      <span className="status-badge-dot" />
      <span className="status-badge-label">{label}</span>
    </span>
  )
}

export default StatusBadge
