import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { api } from '../../services/api'
import './charts.css'

interface DataPoint {
  timestamp: number
  queued: number
  running: number
  completed: number
  failed: number
}

function QueueDepthChart() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [history, setHistory] = useState<DataPoint[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const jobStatus = await api.getJobStatusCounts()
        const now = Date.now()
        
        setHistory(prev => {
          const newPoint: DataPoint = {
            timestamp: now,
            queued: jobStatus.status_counts['QUEUED'] || 0,
            running: jobStatus.status_counts['IN_PROGRESS'] || 0,
            completed: jobStatus.status_counts['COMPLETED'] || 0,
            failed: (jobStatus.status_counts['FAILED'] || 0) + (jobStatus.status_counts['FAILED_PERMANENT'] || 0),
          }
          
          // Keep last 60 data points (5 minutes at 5-second intervals)
          const updated = [...prev, newPoint].slice(-60)
          return updated
        })
      } catch (error) {
        console.error('Failed to fetch job status:', error)
      }
    }

    // Initial fetch
    fetchData()
    
    // Poll every 5 seconds
    const interval = setInterval(fetchData, 5000)
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!chartRef.current) return

    // Initialize chart
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['Queued', 'Running', 'Completed', 'Failed'],
        textStyle: {
          color: '#94a3b8',
        },
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
        axisLabel: { color: '#64748b', formatter: '{HH}:{mm}:{ss}' },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        name: 'Jobs',
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#1e293b' } },
      },
      series: [
        {
          name: 'Queued',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.queued]),
          lineStyle: { color: '#f59e0b', width: 2 },
          itemStyle: { color: '#f59e0b' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245, 158, 11, 0.3)' },
            { offset: 1, color: 'rgba(245, 158, 11, 0)' },
          ])},
        },
        {
          name: 'Running',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.running]),
          lineStyle: { color: '#0ea5e9', width: 2 },
          itemStyle: { color: '#0ea5e9' },
        },
        {
          name: 'Completed',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.completed]),
          lineStyle: { color: '#22c55e', width: 2 },
          itemStyle: { color: '#22c55e' },
        },
        {
          name: 'Failed',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.failed]),
          lineStyle: { color: '#ef4444', width: 2 },
          itemStyle: { color: '#ef4444' },
        },
      ],
    }

    chartInstance.current.setOption(option)

    // Handle resize
    const handleResize = () => {
      chartInstance.current?.resize()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [history])

  if (history.length === 0) {
    return (
      <div className="chart-loading">
        <span>Collecting data...</span>
      </div>
    )
  }

  return <div ref={chartRef} className="chart-container" />
}

export default QueueDepthChart
