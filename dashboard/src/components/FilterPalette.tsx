import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { TraceFilterGroup } from '../types/api'
import './FilterPalette.css'

interface FilterPaletteProps {
  onFiltersChange?: (filters: FilterState) => void
}

export interface FilterState {
  cameras: string[]
  collections: string[]
  sources: string[]
  startDate: string | null
  endDate: string | null
  includeUnknownDevice: boolean
  timePreset?: TimePreset | null
}

export type TimePreset =
  | 'last24h'
  | 'last7d'
  | 'last30d'
  | 'today'
  | 'yesterday'
  | 'thisWeek'
  | 'lastWeek'
  | 'thisMonth'
  | 'lastMonth'
  | 'thisYear'
  | 'allTime'
  | 'custom'

export interface TimePresetOption {
  id: TimePreset
  label: string
}

export const TIME_PRESETS: TimePresetOption[] = [
  { id: 'last24h', label: 'Last 24 Hours' },
  { id: 'last7d', label: 'Last 7 Days' },
  { id: 'last30d', label: 'Last 30 Days' },
  { id: 'today', label: 'Today' },
  { id: 'yesterday', label: 'Yesterday' },
  { id: 'thisWeek', label: 'This Week' },
  { id: 'lastWeek', label: 'Last Week' },
  { id: 'thisMonth', label: 'This Month' },
  { id: 'lastMonth', label: 'Last Month' },
  { id: 'thisYear', label: 'This Year' },
  { id: 'allTime', label: 'All Time' },
  { id: 'custom', label: 'Custom Range' },
]

function calculatePresetDates(preset: TimePreset): { startDate: string | null; endDate: string | null } {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const endOfToday = new Date(today)
  endOfToday.setHours(23, 59, 59, 999)

  const startOfDay = (date: Date): Date => {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate())
  }

  const endOfDay = (date: Date): Date => {
    const d = new Date(date.getFullYear(), date.getMonth(), date.getDate())
    d.setHours(23, 59, 59, 999)
    return d
  }

  const getStartOfWeek = (date: Date, weekStart: number = 0): Date => {
    const d = new Date(date)
    const day = d.getDay()
    const diff = (day < weekStart ? 7 : 0) + day - weekStart
    d.setDate(d.getDate() - diff)
    return startOfDay(d)
  }

  const getEndOfWeek = (date: Date, weekStart: number = 0): Date => {
    const start = getStartOfWeek(date, weekStart)
    const end = new Date(start)
    end.setDate(end.getDate() + 6)
    return endOfDay(end)
  }

  const getStartOfMonth = (date: Date): Date => {
    return new Date(date.getFullYear(), date.getMonth(), 1)
  }

  const getEndOfMonth = (date: Date): Date => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59, 999)
  }

  const getStartOfYear = (date: Date): Date => {
    return new Date(date.getFullYear(), 0, 1)
  }

  const getEndOfYear = (date: Date): Date => {
    return new Date(date.getFullYear(), 11, 31, 23, 59, 59, 999)
  }

  switch (preset) {
    case 'last24h': {
      const start = new Date(now)
      start.setHours(start.getHours() - 24)
      return {
        startDate: start.toISOString(),
        endDate: now.toISOString()
      }
    }
    case 'last7d': {
      const start = new Date(today)
      start.setDate(start.getDate() - 6)
      return {
        startDate: start.toISOString(),
        endDate: endOfToday.toISOString()
      }
    }
    case 'last30d': {
      const start = new Date(today)
      start.setDate(start.getDate() - 29)
      return {
        startDate: start.toISOString(),
        endDate: endOfToday.toISOString()
      }
    }
    case 'today':
      return {
        startDate: today.toISOString(),
        endDate: endOfToday.toISOString()
      }
    case 'yesterday': {
      const yest = new Date(today)
      yest.setDate(yest.getDate() - 1)
      return {
        startDate: startOfDay(yest).toISOString(),
        endDate: endOfDay(yest).toISOString()
      }
    }
    case 'thisWeek':
      return {
        startDate: getStartOfWeek(today).toISOString(),
        endDate: getEndOfWeek(today).toISOString()
      }
    case 'lastWeek': {
      const lastWeekStart = getStartOfWeek(today)
      lastWeekStart.setDate(lastWeekStart.getDate() - 7)
      return {
        startDate: lastWeekStart.toISOString(),
        endDate: endOfDay(new Date(lastWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000)).toISOString()
      }
    }
    case 'thisMonth':
      return {
        startDate: getStartOfMonth(today).toISOString(),
        endDate: getEndOfMonth(today).toISOString()
      }
    case 'lastMonth': {
      const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      return {
        startDate: getStartOfMonth(lastMonth).toISOString(),
        endDate: getEndOfMonth(lastMonth).toISOString()
      }
    }
    case 'thisYear':
      return {
        startDate: getStartOfYear(today).toISOString(),
        endDate: getEndOfYear(today).toISOString()
      }
    case 'allTime':
    case 'custom':
    default:
      return {
        startDate: null,
        endDate: null
      }
  }
}

export default function FilterPalette({ onFiltersChange }: FilterPaletteProps) {
  const [filterGroups, setFilterGroups] = useState<TraceFilterGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['devices', 'collections', 'timeRange']))
  const [filters, setFilters] = useState<FilterState>({
    cameras: [],
    collections: [],
    sources: [],
    startDate: null,
    endDate: null,
    includeUnknownDevice: false,
    timePreset: null
  })
  const [timeRange, setTimeRange] = useState<{ minDate: string | null; maxDate: string | null }>({
    minDate: null,
    maxDate: null
  })
  const [totalItems, setTotalItems] = useState(0)
  const [selectedCounts, setSelectedCounts] = useState<Record<string, number>>({})

  useEffect(() => {
    loadFilters()
  }, [])

  const loadFilters = async () => {
    try {
      setLoading(true)
      const response = await api.getTraceFilters()
      setFilterGroups(response.groups)
      setTotalItems(response.total_items)

      // Initialize selected filters from groups
      const initialFilters: FilterState = {
        cameras: [],
        collections: [],
        sources: [],
        startDate: null,
        endDate: null,
        includeUnknownDevice: false,
        timePreset: null
      }
      const counts: Record<string, number> = {}
      let foundTimeRange = false

      for (const group of response.groups) {
        if (group.id === 'timeRange') {
          // Extract time range bounds
          setTimeRange({
            minDate: group.min_date || null,
            maxDate: group.max_date || null
          })
          foundTimeRange = true
        } else {
          const selected = group.options
            .filter(opt => opt.checked)
            .map(opt => opt.id)
          ;(initialFilters as any)[group.id] = selected
          counts[group.id] = selected.length
        }
      }

      // Set default time range if not found
      if (!foundTimeRange) {
        setTimeRange({ minDate: null, maxDate: null })
      }

      setFilters(initialFilters)
      setSelectedCounts(counts)
    } catch (error) {
      console.error('Failed to load filters:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePresetSelect = (preset: TimePreset) => {
    if (preset === 'custom') {
      // Custom range - just update the preset, keep existing dates or clear them
      setFilters(prev => {
        const newFilters: FilterState = {
          ...prev,
          timePreset: 'custom' as TimePreset,
          startDate: prev.startDate,
          endDate: prev.endDate
        }
        onFiltersChange?.(newFilters)
        return newFilters
      })
    } else {
      // Calculate dates for the preset
      const dates = calculatePresetDates(preset)
      setFilters(prev => {
        const newFilters: FilterState = {
          ...prev,
          timePreset: preset,
          startDate: dates.startDate,
          endDate: dates.endDate
        }
        onFiltersChange?.(newFilters)
        return newFilters
      })
    }
  }

  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev)
      if (next.has(groupId)) {
        next.delete(groupId)
      } else {
        next.add(groupId)
      }
      return next
    })
  }

  const toggleOption = (groupId: string, optionId: string) => {
    setFilters(prev => {
      // Handle special fields
      if (groupId === 'startDate' || groupId === 'endDate') {
        const newFilters = { ...prev }
        newFilters[groupId as 'startDate' | 'endDate'] = optionId || null
        onFiltersChange?.(newFilters)
        return newFilters
      }

      if (groupId === 'includeUnknownDevice') {
        const newFilters = { ...prev }
        newFilters.includeUnknownDevice = !prev.includeUnknownDevice
        onFiltersChange?.(newFilters)
        return newFilters
      }

      // Handle regular options
      const groupFilters = (prev as any)[groupId] as string[]
      const newFilters = { ...prev }

      if (groupFilters.includes(optionId)) {
        (newFilters as any)[groupId] = groupFilters.filter(id => id !== optionId)
      } else {
        (newFilters as any)[groupId] = [...groupFilters, optionId]
      }

      // Update selected counts
      const counts = { ...selectedCounts }
      counts[groupId] = ((newFilters as any)[groupId] as string[]).length
      setSelectedCounts(counts)

      // Notify parent of changes
      onFiltersChange?.(newFilters)

      return newFilters
    })
  }

  const handleStartDateChange = (value: string) => {
    toggleOption('startDate', value)
  }

  const handleEndDateChange = (value: string) => {
    toggleOption('endDate', value)
  }

  const toggleUnknownDevice = () => {
    toggleOption('includeUnknownDevice', '')
  }

  const clearTimeRange = () => {
    setFilters(prev => {
      const newFilters: FilterState = { ...prev, startDate: null, endDate: null, timePreset: null }
      onFiltersChange?.(newFilters)
      return newFilters
    })
  }

  const clearAll = () => {
    const clearedFilters: FilterState = {
      cameras: [],
      collections: [],
      sources: [],
      startDate: null,
      endDate: null,
      includeUnknownDevice: false,
      timePreset: null
    }
    setFilters(clearedFilters)
    setSelectedCounts({})
    onFiltersChange?.(clearedFilters)
  }

  const getGroupSelectedCount = (group: TraceFilterGroup): number => {
    if (group.id === 'timeRange') {
      return (filters.startDate || filters.endDate) ? 1 : 0
    }
    const groupFilters = (filters as any)[group.id] as string[] || []
    return groupFilters.length
  }

  // Format date for display
  const formatDateForInput = (isoString: string | null): string => {
    if (!isoString) return ''
    try {
      return isoString.split('T')[0]
    } catch {
      return ''
    }
  }

  if (loading) {
    return (
      <div className="filter-palette">
        <div className="filter-palette-header">
          <h2><span className="icon">🔍</span> Filter Palette</h2>
        </div>
        <div className="filter-palette-content" style={{ padding: '16px', textAlign: 'center' }}>
          Loading filters...
        </div>
      </div>
    )
  }

  return (
    <div className="filter-palette">
      <div className="filter-palette-header">
        <h2><span className="icon">🔍</span> Filter Palette</h2>
      </div>
      <div className="filter-palette-content">
        {filterGroups.map(group => (
          <div key={group.id} className="filter-group">
            <div
              className="filter-group-header"
              onClick={() => toggleGroup(group.id)}
            >
              <span className="filter-group-title">
                {group.label}
                {getGroupSelectedCount(group) > 0 && (
                  <span style={{ color: 'var(--accent-primary)', marginLeft: '4px' }}>
                    ({getGroupSelectedCount(group)})
                  </span>
                )}
              </span>
              <span className={`filter-group-toggle ${expandedGroups.has(group.id) ? 'expanded' : ''}`}>
                ▶
              </span>
            </div>
            <div className={`filter-group-options ${expandedGroups.has(group.id) ? 'expanded' : ''}`}>
              {group.id === 'timeRange' ? (
                <div className="time-range-filters">
                  {/* Time Presets */}
                  <div className="time-presets">
                    <div className="time-presets-row">
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'last24h' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('last24h')}
                      >
                        Last 24h
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'last7d' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('last7d')}
                      >
                        Last 7d
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'last30d' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('last30d')}
                      >
                        Last 30d
                      </button>
                    </div>
                    <div className="time-presets-divider">
                      <span>Relative</span>
                    </div>
                    <div className="time-presets-grid">
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'today' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('today')}
                      >
                        Today
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'yesterday' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('yesterday')}
                      >
                        Yesterday
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'thisWeek' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('thisWeek')}
                      >
                        This Week
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'lastWeek' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('lastWeek')}
                      >
                        Last Week
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'thisMonth' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('thisMonth')}
                      >
                        This Month
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'lastMonth' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('lastMonth')}
                      >
                        Last Month
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'thisYear' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('thisYear')}
                      >
                        This Year
                      </button>
                      <button
                        className={`time-preset-btn ${filters.timePreset === 'allTime' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('allTime')}
                      >
                        All Time
                      </button>
                    </div>
                    <div className="time-presets-divider">
                      <span>Absolute</span>
                    </div>
                    <button
                      className={`time-preset-btn time-preset-custom ${filters.timePreset === 'custom' ? 'active' : ''}`}
                      onClick={() => handlePresetSelect('custom')}
                    >
                      Custom Range
                    </button>
                  </div>

                  {/* Custom Range Date Pickers */}
                  {(filters.timePreset === 'custom' || (!filters.timePreset && (filters.startDate || filters.endDate))) && (
                    <div className="custom-range-pickers">
                      <div className="time-range-field">
                        <label>From</label>
                        <input
                          type="date"
                          value={formatDateForInput(filters.startDate)}
                          min={formatDateForInput(timeRange.minDate)}
                          max={formatDateForInput(timeRange.maxDate)}
                          onChange={(e) => {
                            handleStartDateChange(e.target.value)
                            setFilters(prev => ({ ...prev, timePreset: 'custom' as TimePreset }))
                          }}
                        />
                      </div>
                      <div className="time-range-field">
                        <label>To</label>
                        <input
                          type="date"
                          value={formatDateForInput(filters.endDate)}
                          min={formatDateForInput(timeRange.minDate)}
                          max={formatDateForInput(timeRange.maxDate)}
                          onChange={(e) => {
                            handleEndDateChange(e.target.value)
                            setFilters(prev => ({ ...prev, timePreset: 'custom' as TimePreset }))
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Clear button */}
                  {(filters.startDate || filters.endDate) && (
                    <button className="time-range-clear" onClick={() => {
                      clearTimeRange()
                    }}>
                      Clear
                    </button>
                  )}
                </div>
              ) : (
                <>
                  {group.options.map(option => (
                    <label key={option.id} className="filter-option">
                      <input
                        type="checkbox"
                        checked={(filters as any)[group.id]?.includes(option.id) ?? false}
                        onChange={() => toggleOption(group.id, option.id)}
                      />
                      <span className="filter-option-label">{option.label}</span>
                      <span className="filter-option-count">({option.count})</span>
                    </label>
                  ))}
                  {/* Unknown Device Toggle for devices group */}
                  {group.id === 'devices' && group.has_unknown && (
                    <label className="filter-option unknown-device-toggle">
                      <input
                        type="checkbox"
                        checked={filters.includeUnknownDevice}
                        onChange={toggleUnknownDevice}
                      />
                      <span className="filter-option-label">Include Unknown Device</span>
                    </label>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="filter-footer">
        <div className="filter-footer-stats">
          {totalItems > 0 ? `Showing ${totalItems} items` : 'No items'}
        </div>
        <div className="filter-footer-actions">
          <button className="btn-clear-all" onClick={clearAll}>
            Clear All
          </button>
          <button className="btn-save-preset">
            Save Preset
          </button>
        </div>
      </div>
    </div>
  )
}
