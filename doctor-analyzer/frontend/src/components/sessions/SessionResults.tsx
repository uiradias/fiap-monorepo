import { useState, useEffect, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { MessageSquare } from 'lucide-react'
import { api } from '../../services/api'
import { VideoPlayer } from '../video/VideoPlayer'
import { AnalysisPanel } from '../analysis/AnalysisPanel'
import { Breadcrumb } from '../layout/Breadcrumb'
import type { AnalysisSessionFull, EmotionUpdateMessage, Patient, TranscriptionUpdateMessage } from '../../types/analysis'

export function SessionResults() {
  const { patientId, sessionId } = useParams<{ patientId: string; sessionId: string }>()

  const [patient, setPatient] = useState<Patient | null>(null)
  const [session, setSession] = useState<AnalysisSessionFull | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [faceDetections, setFaceDetections] = useState<EmotionUpdateMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!patientId || !sessionId) return

    const fetchData = async () => {
      try {
        const [patientData, sessionData, videoUrlData, detectionsData] = await Promise.allSettled([
          api.getPatient(patientId),
          api.getAnalysisResults(sessionId),
          api.getVideoUrl(sessionId),
          api.getFaceDetections(sessionId),
        ])

        if (patientData.status === 'fulfilled') {
          setPatient(patientData.value)
        }
        if (sessionData.status === 'fulfilled') {
          setSession(sessionData.value)
        } else {
          setError('Failed to load session results')
          return
        }
        if (videoUrlData.status === 'fulfilled') {
          setVideoUrl(videoUrlData.value)
        }
        if (detectionsData.status === 'fulfilled') {
          setFaceDetections(detectionsData.value)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [patientId, sessionId])

  const audioAnalysis = session?.audio_analysis
  const sentiment = audioAnalysis?.overall_sentiment

  const transcriptions: TranscriptionUpdateMessage[] = useMemo(() => {
    if (audioAnalysis?.segments && audioAnalysis.segments.length > 0) {
      return audioAnalysis.segments.map((seg) => ({
        type: 'transcription_update' as const,
        text: seg.text,
        start_time: seg.start_time,
        end_time: seg.end_time,
      }))
    }
    if (audioAnalysis?.full_transcript) {
      return [{
        type: 'transcription_update' as const,
        text: audioAnalysis.full_transcript,
        start_time: 0,
        end_time: 0,
      }]
    }
    return []
  }, [audioAnalysis])

  if (!patientId || !sessionId) return null

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500">Loading session results...</div>
      </div>
    )
  }

  if (error || !session) {
    return (
      <div className="space-y-4">
        <Breadcrumb
          items={[
            { label: 'Patients', href: '/' },
            { label: patient?.codename ?? '...', href: `/patients/${patientId}/sessions` },
            { label: `Session ${sessionId}` },
          ]}
        />
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error || 'Session not found'}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: 'Patients', href: '/' },
          { label: patient?.codename ?? '...', href: `/patients/${patientId}/sessions` },
          { label: `Session ${session.session_id}` },
        ]}
      />

      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900">
          Session Results {patient ? `- ${patient.codename}` : ''}
        </h2>
        <p className="text-sm text-gray-500 font-mono">{session.session_id}</p>
      </div>

      {/* Two-column grid: Video + Transcription */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left column: Video player */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h2 className="text-lg font-semibold mb-4">Video</h2>
          {videoUrl ? (
            <VideoPlayer
              videoUrl={videoUrl}
              detections={faceDetections}
              isAnalyzing={false}
            />
          ) : (
            <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center text-gray-400">
              Video not available
            </div>
          )}
        </div>

        {/* Right column: Transcription */}
        <div className="h-full">
          <AnalysisPanel
            session={session}
            status={session.status}
            transcriptions={transcriptions}
            results={session}
            emotionDetections={[]}
            mode="sidebar"
          />
        </div>
      </div>

      {/* Full-width sections */}
      <AnalysisPanel
        session={session}
        status={session.status}
        transcriptions={[]}
        results={session}
        emotionDetections={[]}
        mode="main"
      />

      {/* Sentiment */}
      {sentiment && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-4">
            <MessageSquare className="w-5 h-5 text-indigo-500" />
            <h2 className="text-lg font-semibold">Overall Sentiment</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Sentiment</p>
              <p className="font-medium capitalize">{sentiment.sentiment.toLowerCase()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Positive</p>
              <p className="font-medium">{(sentiment.positive_score * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Negative</p>
              <p className="font-medium">{(sentiment.negative_score * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Neutral</p>
              <p className="font-medium">{(sentiment.neutral_score * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
