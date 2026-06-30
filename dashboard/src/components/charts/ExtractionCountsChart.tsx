import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { api } from '../../services/api'
import './charts.css'

interface ExtractionCounts {
  entities: number
  events: number
  locations: number
  embeddings: number
}

function ExtractionCountsChart() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [counts, setCounts] = useState<ExtractionCounts>({
    entities: 0,
    events: 0,
    locations: 0,
    embeddings: 0,
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const stats = await api.getStats()
        setCounts({
          entities: stats.entities.total || 0,
          events: stats.events.total || 0,
          locations: stats.locations.total || 0,
          embeddings: 0, // Not available in current API
        })
      } catch (error) {
        console.error('Failed to fetch extraction counts:', error)
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

    const data = [
      { name: 'Entities', value: counts.entities, color: '#6366f1' },
      { name: 'Events', value: counts.events, color: '#8b5cf6' },
      { name: 'Locations', value: counts.locations, color: '#f59e0b' },
      { name: 'Embeddings', value: counts.embeddings, color: '#0ea5e9' },
    ]

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#94a3b8' },
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#0f172a',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}\n{c}',
            color: '#e2e8f0',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
            },
          },
          data: data.map(d => ({
            value: d.value,
            name: d.name,
            itemStyle: { color: d.color },
          })),
        },
      ],
    }

    chartInstance.current.setOption(option)

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => window.removeEventListener('resize', handleResize)
  }, [counts])

  return <div ref={chartRef} className="chart-container" />
}

export default ExtractionCountsChart
