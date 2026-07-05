import { useState, useEffect, useCallback, useRef } from 'react'

export type PlaybackMode = 'stopped' | 'playing' | 'paused'
export type PlaybackSpeed = 0.5 | 1 | 2 | 4

export const PLAYBACK_SPEEDS: PlaybackSpeed[] = [0.5, 1, 2, 4]
export const DEFAULT_PLAYBACK_SPEED: PlaybackSpeed = 1

export interface PlaybackState {
  mode: PlaybackMode
  currentIndex: number
  totalItems: number
}

/**
 * Playback controller hook with pause/resume and speed control.
 * 
 * Provides play, pause, resume, stop functionality with configurable speed.
 * Speed changes take effect immediately without restarting playback.
 * 
 * State machine:
 * - 'stopped': idle, index at 0
 * - 'playing': actively advancing frames
 * - 'paused': stopped but index preserved
 */
export function usePlaybackController(totalItems: number) {
  const [mode, setMode] = useState<PlaybackMode>('stopped')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const [playbackSpeed, setPlaybackSpeedState] = useState<PlaybackSpeed>(DEFAULT_PLAYBACK_SPEED)
  const intervalRef = useRef<number | null>(null)

  // Clear interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
      }
    }
  }, [])

  // Calculate interval based on speed
  const getIntervalMs = useCallback(() => {
    return 1000 / playbackSpeed
  }, [playbackSpeed])

  // Handle play - start from current position
  const play = useCallback(() => {
    if (totalItems === 0) return
    
    // Start from beginning if at end
    if (currentIndex >= totalItems - 1) {
      setCurrentIndex(0)
    }
    
    setMode('playing')
    setIsPaused(false)
  }, [currentIndex, totalItems])

  // Handle pause - preserve current position
  const pause = useCallback(() => {
    if (mode !== 'playing') return
    
    setMode('paused')
    setIsPaused(true)
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [mode])

  // Handle resume - continue from paused position
  const resume = useCallback(() => {
    if (mode !== 'paused') return
    if (totalItems === 0) return
    
    setMode('playing')
    setIsPaused(false)
  }, [mode, totalItems])

  // Handle stop - reset to idle state
  const stop = useCallback(() => {
    setMode('stopped')
    setIsPaused(false)
    setCurrentIndex(0)
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  // Handle speed change - takes effect immediately
  const setSpeed = useCallback((speed: PlaybackSpeed) => {
    setPlaybackSpeedState(speed)
  }, [])

  // Effect: manage interval based on mode and speed
  useEffect(() => {
    if (mode === 'playing' && totalItems > 0) {
      // Clear any existing interval
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
      }

      const intervalMs = getIntervalMs()
      
      // Set up advancement interval
      intervalRef.current = window.setInterval(() => {
        setCurrentIndex(prev => {
          const next = prev + 1
          // Stop at end
          if (next >= totalItems) {
            setMode('stopped')
            setIsPaused(false)
            if (intervalRef.current) {
              window.clearInterval(intervalRef.current)
              intervalRef.current = null
            }
            return prev
          }
          return next
        })
      }, intervalMs)
    }

    return () => {
      if (intervalRef.current && mode !== 'playing') {
        window.clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [mode, totalItems, getIntervalMs])

  // Effect: restart interval when speed changes during playback
  useEffect(() => {
    if (mode === 'playing' && totalItems > 0) {
      // Clear existing interval
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
      }
      
      const intervalMs = getIntervalMs()
      
      // Restart with new speed
      intervalRef.current = window.setInterval(() => {
        setCurrentIndex(prev => {
          const next = prev + 1
          if (next >= totalItems) {
            setMode('stopped')
            setIsPaused(false)
            if (intervalRef.current) {
              window.clearInterval(intervalRef.current)
              intervalRef.current = null
            }
            return prev
          }
          return next
        })
      }, intervalMs)
    }
  }, [playbackSpeed, mode, totalItems, getIntervalMs])

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
    isPaused,
    playbackSpeed,
    play,
    pause,
    resume,
    stop,
    setSpeed,
  }
}
