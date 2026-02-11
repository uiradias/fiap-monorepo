import { useEffect, useState, RefObject } from 'react'
import type { EmotionUpdateMessage } from '../../types/analysis'

interface VideoOverlayProps {
  videoRef: RefObject<HTMLVideoElement>
  detections: EmotionUpdateMessage[]
  isPlaying: boolean
}

const EMOTION_COLORS: Record<string, string> = {
  discomfort: '#ef4444',
  depression: '#6366f1',
  anxiety: '#f59e0b',
  fear: '#dc2626',
  calm: '#22c55e',
  happy: '#10b981',
  confused: '#8b5cf6',
  angry: '#b91c1c',
  sad: '#6366f1',
  surprised: '#f97316',
  disgusted: '#84cc16',
  neutral: '#94a3b8',
}

export function VideoOverlay({ videoRef, detections, isPlaying }: VideoOverlayProps) {
  const [currentDetections, setCurrentDetections] = useState<EmotionUpdateMessage[]>([])

  useEffect(() => {
    if (!videoRef.current) return

    const video = videoRef.current

    const updateOverlay = () => {
      const currentTimeMs = video.currentTime * 1000
      const tolerance = 500

      const activeDetections = detections.filter(
        (d) => Math.abs(d.timestamp_ms - currentTimeMs) <= tolerance
      )

      setCurrentDetections(activeDetections)
    }

    video.addEventListener('timeupdate', updateOverlay)

    let animationId: number
    const animate = () => {
      if (isPlaying) {
        updateOverlay()
        animationId = requestAnimationFrame(animate)
      }
    }

    if (isPlaying) {
      animationId = requestAnimationFrame(animate)
    }

    return () => {
      video.removeEventListener('timeupdate', updateOverlay)
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    }
  }, [videoRef, detections, isPlaying])

  const getPrimaryEmotion = (emotions: EmotionUpdateMessage['emotions']) => {
    if (!emotions || emotions.length === 0) return null
    return emotions.reduce((prev, curr) =>
      curr.confidence > prev.confidence ? curr : prev
    )
  }

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {currentDetections.map((detection, index) => {
        const { bounding_box, emotions } = detection
        const primaryEmotion = getPrimaryEmotion(emotions)
        const color = primaryEmotion
          ? EMOTION_COLORS[primaryEmotion.emotion] || '#94a3b8'
          : '#94a3b8'

        return (
          <div
            key={index}
            className="absolute border-2 rounded transition-all duration-100"
            style={{
              left: `${bounding_box.left * 100}%`,
              top: `${bounding_box.top * 100}%`,
              width: `${bounding_box.width * 100}%`,
              height: `${bounding_box.height * 100}%`,
              borderColor: color,
            }}
          >
            {/* Emotion label */}
            {primaryEmotion && (
              <div
                className="absolute -top-6 left-0 px-2 py-0.5 rounded text-xs font-medium text-white whitespace-nowrap"
                style={{ backgroundColor: color }}
              >
                {primaryEmotion.emotion}: {(primaryEmotion.confidence * 100).toFixed(0)}%
              </div>
            )}

            {/* Emotion bars */}
            <div className="absolute -right-24 top-0 w-20 space-y-0.5">
              {emotions
                .filter((e) => e.confidence > 0.1)
                .sort((a, b) => b.confidence - a.confidence)
                .slice(0, 3)
                .map((emotion, i) => (
                  <div key={i} className="flex items-center gap-1">
                    <div
                      className="h-1.5 rounded"
                      style={{
                        width: `${emotion.confidence * 100}%`,
                        backgroundColor: EMOTION_COLORS[emotion.emotion] || '#94a3b8',
                      }}
                    />
                    <span className="text-[8px] text-white drop-shadow-lg">
                      {emotion.emotion.slice(0, 3)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
