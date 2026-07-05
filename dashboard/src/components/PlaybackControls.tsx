import './PlaybackControls.css'

interface PlaybackControlsProps {
  isPlaying: boolean
  currentIndex: number
  totalItems: number
  onPlay: () => void
  onStop: () => void
  disabled?: boolean
}

/**
 * Minimal playback controls component.
 * 
 * Provides play/stop buttons only.
 * 
 * This is a proof-of-existence spike - NOT production-ready.
 * Does NOT include: reverse playback, speed controls, timeline, keyboard shortcuts.
 */
export default function PlaybackControls({
  isPlaying,
  currentIndex,
  totalItems,
  onPlay,
  onStop,
  disabled = false,
}: PlaybackControlsProps) {
  return (
    <div className="playback-controls">
      <div className="playback-controls-buttons">
        <button
          className={`playback-btn playback-btn-play ${isPlaying ? 'active' : ''}`}
          onClick={onPlay}
          disabled={disabled || totalItems === 0}
          title={isPlaying ? 'Playing...' : 'Play'}
        >
          ▶
        </button>
        <button
          className={`playback-btn playback-btn-stop ${!isPlaying ? 'active' : ''}`}
          onClick={onStop}
          disabled={disabled}
          title="Stop"
        >
          ⏹
        </button>
      </div>
      
      <div className="playback-controls-info">
        <span className="playback-position">
          {totalItems > 0 ? currentIndex + 1 : 0} / {totalItems}
        </span>
      </div>
    </div>
  )
}
