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
}

export default function FilterPalette({ onFiltersChange }: FilterPaletteProps) {
  const [filterGroups, setFilterGroups] = useState<TraceFilterGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['devices', 'collections', 'years']))
  const [filters, setFilters] = useState<FilterState>({
    cameras: [],
    collections: [],
    years: [],
    sources: []
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
        sources: []
      }
      const counts: Record<string, number> = {}

      for (const group of response.groups) {
        const selected = group.options
          .filter(opt => opt.checked)
          .map(opt => opt.id)
        initialFilters[group.id as keyof FilterState] = selected
        counts[group.id] = selected.length
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
      const groupFilters = prev[groupId as keyof FilterState]
      const newFilters = { ...prev }

      if (groupFilters.includes(optionId)) {
        newFilters[groupId as keyof FilterState] = groupFilters.filter(id => id !== optionId)
      } else {
        newFilters[groupId as keyof FilterState] = [...groupFilters, optionId]
      }

      // Update selected counts
      const counts = { ...selectedCounts }
      counts[groupId] = (newFilters[groupId as keyof FilterState] as string[]).length
      setSelectedCounts(counts)

      // Notify parent of changes
      onFiltersChange?.(newFilters)

      return newFilters
    })
  }

  const toggleYear = (year: string) => {
    toggleOption('years', year)
  }

  const clearAll = () => {
    const clearedFilters: FilterState = {
      cameras: [],
      collections: [],
      years: [],
      sources: []
    }
    setFilters(clearedFilters)
    setSelectedCounts({})
    onFiltersChange?.(clearedFilters)
  }

  const getGroupSelectedCount = (group: TraceFilterGroup): number => {
    const groupFilters = filters[group.id as keyof FilterState]
    return (groupFilters as string[] || []).length
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
              ) : (
                group.options.map(option => (
                  <label key={option.id} className="filter-option">
                    <input
                      type="checkbox"
                      checked={filters[group.id as keyof FilterState]?.includes(option.id) ?? false}
                      onChange={() => toggleOption(group.id, option.id)}
                    />
                    <span className="filter-option-label">{option.label}</span>
                    <span className="filter-option-count">({option.count})</span>
                  </label>
                ))
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
