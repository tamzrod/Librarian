import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { api } from '../../services/api'
import './charts.css'

interface GrowthPoint {
  timestamp: number
  documents: number
  entities: number
  events: number
}

function DocumentGrowthChart() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [history, setHistory] = useState<GrowthPoint[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const stats = await api.getStats()
        const now = Date.now()
        
        setHistory(prev => {
          const newPoint: GrowthPoint = {
            timestamp: now,
            documents: stats.documents.total || 0,
            entities: stats.entities.total || 0,
            events: stats.events.total || 0,
          }
          
          const updated = [...prev, newPoint].slice(-60)
          return updated
        })
      } catch (error) {
        console.error('Failed to fetch growth data:', error)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 10000)
    
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
        data: ['Documents', 'Entities', 'Events'],
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
          name: 'Documents',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.documents]),
          lineStyle: { color: '#6366f1', width: 2 },
          itemStyle: { color: '#6366f1' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0)' },
          ])},
        },
        {
          name: 'Entities',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.entities]),
          lineStyle: { color: '#22c55e', width: 2 },
          itemStyle: { color: '#22c55e' },
        },
        {
          name: 'Events',
          type: 'line',
          smooth: true,
          data: history.map(d => [d.timestamp, d.events]),
          lineStyle: { color: '#f59e0b', width: 2 },
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

export default DocumentGrowthChart
