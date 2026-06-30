import { ReactNode } from 'react'
import './ChartCard.css'

interface ChartCardProps {
  title: string
  children: ReactNode
  className?: string
}

function ChartCard({ title, children, className = '' }: ChartCardProps) {
  return (
    <div className={`chart-card ${className}`}>
      <div className="chart-card-header">
        <h3 className="chart-card-title">{title}</h3>
      </div>
      <div className="chart-card-content">
        {children}
      </div>
    </div>
  )
}

export default ChartCard
