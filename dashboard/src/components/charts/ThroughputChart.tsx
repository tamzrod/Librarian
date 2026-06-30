import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { api } from '../../services/api'
import './charts.css'

interface ThroughputPoint {
  timestamp: number
  jobsPerMinute: number
  docsPerMinute: number
}

function ThroughputChart() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [history, setHistory] = useState<ThroughputPoint[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const jobStatus = await api.getJobStatusCounts()
        const now = Date.now()
        
        // Calculate throughput from completed jobs
        // In a real scenario, this would compare current vs previous counts
        const completed = jobStatus.status_counts['COMPLETED'] || 0
        
        setHistory(prev => {
          const newPoint: ThroughputPoint = {
            timestamp: now,
            jobsPerMinute: completed > 0 ? completed / 60 : 0,
            docsPerMinute: completed > 0 ? completed / 120 : 0, // Estimate
          }
          
          const updated = [...prev, newPoint].slice(-60)
          return updated
        })
      } catch (error) {
        console.error('Failed to fetch throughput:', error)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
      },
      legend: {
        data: ['Jobs/min', 'Docs/min'],
        textStyle: { color: '#94a3b8' },
        top: 0,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'time',
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#64748b' },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        name: 'Items/min',
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#1e293b' } },
      },
      series: [
        {
          name: 'Jobs/min',
          type: 'bar',
          data: history.map(d => [d.timestamp, d.jobsPerMinute.toFixed(2)]),
          itemStyle: { color: '#6366f1' },
        },
        {
          name: 'Docs/min',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.docsPerMinute.toFixed(2)]),
          lineStyle: { color: '#22c55e', width: 2 },
          itemStyle: { color: '#22c55e' },
        },
      ],
    }

    chartInstance.current.setOption(option)

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => window.removeEventListener('resize', handleResize)
  }, [history])

  if (history.length === 0) {
    return <div className="chart-loading"><span>Collecting data...</span></div>
  }

  return <div ref={chartRef} className="chart-container" />
}

export default ThroughputChart
