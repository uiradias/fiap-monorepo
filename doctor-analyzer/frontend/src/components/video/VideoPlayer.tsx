import { useRef, useState, useEffect } from 'react'
import { Play, Pause, Volume2, VolumeX } from 'lucide-react'
import { VideoOverlay } from './VideoOverlay'
import type { EmotionUpdateMessage } from '../../types/analysis'

interface VideoPlayerProps {
  videoUrl: string
  detections: EmotionUpdateMessage[]
  isAnalyzing: boolean
}

export function VideoPlayer({ videoUrl, detections, isAnalyzing }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleTimeUpdate = () => setCurrentTime(video.currentTime)
    const handleLoadedMetadata = () => setDuration(video.duration)
    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)

    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('loadedmetadata', handleLoadedMetadata)
    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('loadedmetadata', handleLoadedMetadata)
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
    }
  }, [])

  const togglePlay = () => {
    const video = videoRef.current
    if (!video) return

    if (isPlaying) {
      video.pause()
    } else {
      video.play()
    }
  }

  const toggleMute = () => {
    const video = videoRef.current
    if (!video) return

    video.muted = !video.muted
    setIsMuted(video.muted)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current
    if (!video) return

    const time = parseFloat(e.target.value)
    video.currentTime = time
    setCurrentTime(time)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-3">
      {/* Video container with overlay */}
      <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
        <video
          ref={videoRef}
          src={videoUrl}
          className="w-full h-full object-contain"
          playsInline
        />
        <VideoOverlay
          videoRef={videoRef}
          detections={detections}
          isPlaying={isPlaying}
        />

        {/* Analysis indicator */}
        {isAnalyzing && (
          <div className="absolute top-3 right-3 px-3 py-1 bg-red-600 text-white text-sm rounded-full flex items-center gap-2">
            <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
            Analyzing
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
        >
          {isPlaying ? (
            <Pause className="w-5 h-5 text-gray-700" />
          ) : (
            <Play className="w-5 h-5 text-gray-700" />
          )}
        </button>

        <span className="text-sm text-gray-600 w-12">
          {formatTime(currentTime)}
        </span>

        <input
          type="range"
          min="0"
          max={duration || 0}
          value={currentTime}
          onChange={handleSeek}
          className="flex-1 h-2 bg-gray-200 rounded-full appearance-none cursor-pointer"
        />

        <span className="text-sm text-gray-600 w-12 text-right">
          {formatTime(duration)}
        </span>

        <button
          onClick={toggleMute}
          className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
        >
          {isMuted ? (
            <VolumeX className="w-5 h-5 text-gray-700" />
          ) : (
            <Volume2 className="w-5 h-5 text-gray-700" />
          )}
        </button>
      </div>

      {/* Detection count */}
      <div className="text-sm text-gray-500">
        {detections.length} emotion detections captured
      </div>
    </div>
  )
}
