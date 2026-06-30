import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { api } from '../../services/api'
import './charts.css'

interface WorkerStats {
  workerId: string
  jobsProcessed: number
  utilization: number
}

function WorkerUtilizationChart() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [workers, setWorkers] = useState<WorkerStats[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const health = await api.getHealth()
        const jobStatus = await api.getJobStatusCounts()
        
        const running = jobStatus.status_counts['IN_PROGRESS'] || 0
        const completed = jobStatus.status_counts['COMPLETED'] || 0
        const workerCount = health.workers || 1
        
        // Simulate worker data (in real scenario, this would come from API)
        const workerStats: WorkerStats[] = Array.from({ length: workerCount }, (_, i) => ({
          workerId: i === 0 ? 'api-processor' : `worker-${i}`,
          jobsProcessed: Math.floor(completed / workerCount) + Math.floor(Math.random() * 10),
          utilization: running > 0 ? Math.min((running / workerCount) * 100, 100) : Math.random() * 30,
        }))
        
        setWorkers(workerStats)
      } catch (error) {
        console.error('Failed to fetch worker stats:', error)
        // Default worker
        setWorkers([{
          workerId: 'api-processor',
          jobsProcessed: 0,
          utilization: 0,
        }])
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
        axisPointer: { type: 'shadow' },
        formatter: (params: unknown) => {
          const p = (params as Array<{ name: string; value: number; color: string }>)[0]
          return `${p.name}<br/>Utilization: ${p.value.toFixed(1)}%`
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: workers.map(w => w.workerId),
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#64748b' },
      },
      yAxis: {
        type: 'value',
        name: 'Utilization %',
        max: 100,
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { 
          color: '#64748b',
          formatter: '{value}%',
        },
        splitLine: { lineStyle: { color: '#1e293b' } },
      },
      series: [
        {
          name: 'Utilization',
          type: 'bar',
          data: workers.map(w => ({
            value: w.utilization.toFixed(1),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#22c55e' },
                { offset: 1, color: '#16a34a' },
              ]),
            },
          })),
          barWidth: '50%',
        },
      ],
    }

    chartInstance.current.setOption(option)

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => window.removeEventListener('resize', handleResize)
  }, [workers])

  if (workers.length === 0) {
    return <div className="chart-loading"><span>Loading...</span></div>
  }

  return <div ref={chartRef} className="chart-container" />
}

export default WorkerUtilizationChart
