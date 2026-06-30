import './StatsCard.css'

interface StatsCardProps {
  title: string
  value: number | string
  icon: string
  color: string
  format?: 'number' | 'bytes' | 'string'
  trend?: 'up' | 'down' | 'stable'
}

function formatValue(value: number | string, format: 'number' | 'bytes' | 'string'): string {
  if (typeof value === 'string') return value
  
  if (format === 'bytes') {
    if (value === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(value) / Math.log(k))
    return `${parseFloat((value / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
  }
  
  if (format === 'number') {
    return value.toLocaleString()
  }
  
  return String(value)
}

function StatsCard({ title, value, icon, color, format = 'number', trend }: StatsCardProps) {
  const formattedValue = formatValue(value, format)
  
  return (
    <div className="stats-card">
      <div className="stats-card-icon" style={{ backgroundColor: color }}>
        <span>{icon}</span>
      </div>
      <div className="stats-card-content">
        <span className="stats-card-title">{title}</span>
        <div className="stats-card-value-row">
          <span className="stats-card-value">{formattedValue}</span>
          {trend && (
            <span className={`stats-card-trend trend-${trend}`}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default StatsCard
