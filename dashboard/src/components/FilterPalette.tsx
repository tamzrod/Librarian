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
  years: string[]
  sources: string[]
  startDate: string | null
  endDate: string | null
  includeUnknownDevice: boolean
}

export default function FilterPalette({ onFiltersChange }: FilterPaletteProps) {
  const [filterGroups, setFilterGroups] = useState<TraceFilterGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['devices', 'collections', 'years', 'timeRange']))
  const [filters, setFilters] = useState<FilterState>({
    cameras: [],
    collections: [],
    years: [],
    sources: [],
    startDate: null,
    endDate: null,
    includeUnknownDevice: false
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
        years: [],
        sources: [],
        startDate: null,
        endDate: null,
        includeUnknownDevice: false
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

  const toggleYear = (year: string) => {
    toggleOption('years', year)
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
      const newFilters = { ...prev, startDate: null, endDate: null }
      onFiltersChange?.(newFilters)
      return newFilters
    })
  }

  const clearAll = () => {
    const clearedFilters: FilterState = {
      cameras: [],
      collections: [],
      years: [],
      sources: [],
      startDate: null,
      endDate: null,
      includeUnknownDevice: false
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
              {group.id === 'years' ? (
                <div className="year-chips">
                  {group.options.map(option => (
                    <button
                      key={option.id}
                      className={`year-chip ${filters.years.includes(option.id) ? 'active' : ''}`}
                      onClick={() => toggleYear(option.id)}
                    >
                      {option.label} ({option.count})
                    </button>
                  ))}
                </div>
              ) : group.id === 'timeRange' ? (
                <div className="time-range-filters">
                  <div className="time-range-field">
                    <label>From</label>
                    <input
                      type="date"
                      value={formatDateForInput(filters.startDate)}
                      min={formatDateForInput(timeRange.minDate)}
                      max={formatDateForInput(timeRange.maxDate)}
                      onChange={(e) => handleStartDateChange(e.target.value)}
                    />
                  </div>
                  <div className="time-range-field">
                    <label>To</label>
                    <input
                      type="date"
                      value={formatDateForInput(filters.endDate)}
                      min={formatDateForInput(timeRange.minDate)}
                      max={formatDateForInput(timeRange.maxDate)}
                      onChange={(e) => handleEndDateChange(e.target.value)}
                    />
                  </div>
                  {(filters.startDate || filters.endDate) && (
                    <button className="time-range-clear" onClick={clearTimeRange}>
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
