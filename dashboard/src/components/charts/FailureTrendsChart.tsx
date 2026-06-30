import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { api } from '../../services/api'
import './charts.css'

interface FailurePoint {
  timestamp: number
  failed: number
  retries: number
}

function FailureTrendsChart() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [history, setHistory] = useState<FailurePoint[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const jobStatus = await api.getJobStatusCounts()
        const now = Date.now()
        
        setHistory(prev => {
          const newPoint: FailurePoint = {
            timestamp: now,
            failed: (jobStatus.status_counts['FAILED'] || 0) + (jobStatus.status_counts['FAILED_PERMANENT'] || 0),
            retries: 0, // Would need retry tracking from API
          }
          
          const updated = [...prev, newPoint].slice(-60)
          return updated
        })
      } catch (error) {
        console.error('Failed to fetch failure trends:', error)
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
        data: ['Failed Jobs', 'Retries'],
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
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#1e293b' } },
      },
      series: [
        {
          name: 'Failed Jobs',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.failed]),
          lineStyle: { color: '#ef4444', width: 2 },
          itemStyle: { color: '#ef4444' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0)' },
          ])},
        },
        {
          name: 'Retries',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.retries]),
          lineStyle: { color: '#f59e0b', width: 2, type: 'dashed' },
          itemStyle: { color: '#f59e0b' },
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

export default FailureTrendsChart
