import { useState, useCallback } from 'react'
import { Upload, FileVideo, X, Loader2 } from 'lucide-react'
import { api } from '../../services/api'
import type { AnalysisSession } from '../../types/analysis'

interface UploadZoneProps {
  patientId?: string
  onSessionCreated: (session: AnalysisSession, videoUrl: string) => void
}

export function UploadZone({ patientId: initialPatientId, onSessionCreated }: UploadZoneProps) {
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [patientId, setPatientId] = useState(initialPatientId || '')
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleVideoDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('video/')) {
      setVideoFile(file)
      setError(null)
    } else {
      setError('Please drop a valid video file')
    }
  }, [])

  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setVideoFile(file)
      setError(null)
    }
  }

  const handleSubmit = async () => {
    if (!videoFile) {
      setError('Please upload a video file')
      return
    }

    if (!patientId.trim()) {
      setError('Patient ID is required')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      // 1. Upload video and create session
      const uploadResult = await api.uploadVideo(videoFile, patientId)
      const sessionId = uploadResult.session_id

      // 2. Get session details and video URL
      const session = await api.getSession(sessionId)
      const videoUrl = await api.getVideoUrl(sessionId)

      onSessionCreated(session, videoUrl)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Video Upload */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileVideo className="w-5 h-5 text-blue-600" />
          Upload Video
        </h2>

        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleVideoDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
            videoFile
              ? 'border-green-300 bg-green-50'
              : 'border-gray-300 hover:border-blue-400'
          }`}
        >
          {videoFile ? (
            <div className="flex items-center justify-center gap-3">
              <FileVideo className="w-8 h-8 text-green-600" />
              <div className="text-left">
                <p className="font-medium text-gray-900">{videoFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(videoFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={() => setVideoFile(null)}
                className="p-1 hover:bg-gray-200 rounded"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          ) : (
            <>
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-2">
                Drag and drop your video here, or{' '}
                <label className="text-blue-600 hover:underline cursor-pointer">
                  browse
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleVideoSelect}
                    className="hidden"
                  />
                </label>
              </p>
              <p className="text-sm text-gray-400">MP4, MOV, AVI, WebM supported</p>
            </>
          )}
        </div>
      </div>

      {/* Patient ID - only show input if not provided via props */}
      {!initialPatientId && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Patient ID (Required)
          </label>
          <input
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="Enter patient identifier..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={!videoFile || !patientId.trim() || isUploading}
        className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isUploading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Uploading...
          </>
        ) : (
          <>
            <Upload className="w-5 h-5" />
            Upload and Prepare Analysis
          </>
        )}
      </button>
    </div>
  )
}
