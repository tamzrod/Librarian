import './PlaybackControls.css'
import type { PlaybackSpeed } from '../hooks/usePlaybackController'

interface PlaybackControlsProps {
  isPlaying: boolean
  isPaused: boolean
  currentIndex: number
  totalItems: number
  playbackSpeed: PlaybackSpeed
  onPlay: () => void
  onPause: () => void
  onResume: () => void
  onStop: () => void
  onSpeedChange: (speed: PlaybackSpeed) => void
  disabled?: boolean
}

const SPEED_OPTIONS: PlaybackSpeed[] = [0.5, 1, 2, 4]

/**
 * Playback controls component with play, pause, resume, stop, and speed control.
 * 
 * Button behavior:
 * - Play: Shows when stopped or paused, starts playback from current position
 * - Pause: Shows when playing, freezes playback
 * - Resume: Shows when paused, continues from paused position  
 * - Stop: Stops playback and resets position
 */
export default function PlaybackControls({
  isPlaying,
  isPaused,
  currentIndex,
  totalItems,
  playbackSpeed,
  onPlay,
  onPause,
  onResume,
  onStop,
  onSpeedChange,
  disabled = false,
}: PlaybackControlsProps) {
  const isStopped = !isPlaying && !isPaused
  const canInteract = !disabled && totalItems > 0

  const handlePlayPauseClick = () => {
    if (isStopped) {
      onPlay()
    } else if (isPlaying) {
      onPause()
    } else if (isPaused) {
      onResume()
    }
  }

  return (
    <div className="playback-controls">
      <div className="playback-controls-buttons">
        {/* Play/Pause/Resume button */}
        <button
          className={`playback-btn playback-btn-play ${isPlaying ? 'active' : ''}`}
          onClick={handlePlayPauseClick}
          disabled={canInteract === false}
          title={isPlaying ? 'Pause' : isPaused ? 'Resume' : 'Play'}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>
        
        {/* Stop button */}
        <button
          className={`playback-btn playback-btn-stop ${isStopped ? 'active' : ''}`}
          onClick={onStop}
          disabled={canInteract === false}
          title="Stop"
        >
          ⏹
        </button>
      </div>

      {/* Speed selector */}
      <div className="playback-controls-speed">
        <span className="playback-speed-label">Speed:</span>
        <div className="playback-speed-options">
          {SPEED_OPTIONS.map(speed => (
            <button
              key={speed}
              className={`playback-speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
              onClick={() => onSpeedChange(speed)}
              disabled={disabled}
              title={`${speed}x playback speed`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
      
      <div className="playback-controls-info">
        <span className="playback-position">
          {totalItems > 0 ? currentIndex + 1 : 0} / {totalItems}
        </span>
      </div>
    </div>
  )
}
