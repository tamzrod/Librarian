import { useState, useEffect, useCallback, useRef } from 'react'

export type PlaybackMode = 'stopped' | 'playing'

export interface PlaybackState {
  mode: PlaybackMode
  currentIndex: number
  totalItems: number
}

/**
 * Minimal playback controller hook.
 * 
 * Provides basic play/stop functionality with automatic advancement
 * through a sequence of items at 1-second intervals.
 * 
 * This is a proof-of-existence spike - NOT production-ready.
 * Does NOT include: reverse playback, speed controls, keyboard shortcuts, persistence.
 */
export function usePlaybackController(totalItems: number) {
  const [mode, setMode] = useState<PlaybackMode>('stopped')
  const [currentIndex, setCurrentIndex] = useState(0)
  const intervalRef = useRef<number | null>(null)
  const lastUpdateRef = useRef<number>(0)

  // Clear interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
      }
    }
  }, [])

  // Handle play - advance every second
  const play = useCallback(() => {
    if (totalItems === 0) return
    
    // Start from beginning if at end
    if (currentIndex >= totalItems - 1) {
      setCurrentIndex(0)
    }
    
    setMode('playing')
  }, [currentIndex, totalItems])

  // Handle stop
  const stop = useCallback(() => {
    setMode('stopped')
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  // Effect: manage interval based on mode
  useEffect(() => {
    if (mode === 'playing' && totalItems > 0) {
      // Clear any existing interval
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
      }

      // Set up 1-second advancement interval
      intervalRef.current = window.setInterval(() => {
        const now = Date.now()
        // Throttle to avoid multiple updates in same frame
        if (now - lastUpdateRef.current >= 900) {
          lastUpdateRef.current = now
          setCurrentIndex(prev => {
            const next = prev + 1
            // Stop at end
            if (next >= totalItems) {
              setMode('stopped')
              if (intervalRef.current) {
                window.clearInterval(intervalRef.current)
                intervalRef.current = null
              }
              return prev
            }
            return next
          })
        }
      }, 1000)
    }

    return () => {
      if (intervalRef.current && mode !== 'playing') {
        window.clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [mode, totalItems])

  // Reset index when total items changes
  useEffect(() => {
    if (currentIndex >= totalItems && totalItems > 0) {
      setCurrentIndex(totalItems - 1)
    }
  }, [totalItems, currentIndex])

  return {
    mode,
    currentIndex,
    totalItems,
    isPlaying: mode === 'playing',
    play,
    stop,
  }
}
