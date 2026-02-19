import { useState } from 'react'
import { Routes, Route, useParams, useNavigate } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { PatientList } from './components/patients/PatientList'
import { PatientSessions } from './components/patients/PatientSessions'
import { SessionResults } from './components/sessions/SessionResults'
import { UploadZone } from './components/upload/UploadZone'
import { VideoPlayer } from './components/video/VideoPlayer'
import { AnalysisPanel } from './components/analysis/AnalysisPanel'
import { useAnalysis } from './hooks/useAnalysis'
import type { AnalysisSession, AnalysisStatus, EmotionUpdateMessage } from './types/analysis'

function AnalysisPage() {
  const { patientId } = useParams<{ patientId: string }>()
  const navigate = useNavigate()

  const [session, setSession] = useState<AnalysisSession | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [emotionDetections, setEmotionDetections] = useState<EmotionUpdateMessage[]>([])


  const {
    status,
    progress,
    statusMessage,
    isConnected,
    transcriptions,
    results,
    error,
    disconnect,
    startAnalysis,
  } = useAnalysis({
    sessionId: session?.session_id || '',
    onEmotionUpdate: (update) => {
      setEmotionDetections((prev) => [...prev, update])
    },
  })

  const handleSessionCreated = (newSession: AnalysisSession, videoUrl: string) => {
    setSession(newSession)
    setVideoUrl(videoUrl)
    setEmotionDetections([])
  }

  const canStartAnalysis =
    status === null || status === 'pending' || status === 'uploading' || status === 'failed'

  const isAnalyzing =
    status !== null &&
    status !== 'pending' &&
    status !== 'uploading' &&
    status !== 'failed' &&
    status !== 'completed'

  const handleStartAnalysis = () => {
    if (session) {
      startAnalysis()
    }
  }

  const handleReset = () => {
    disconnect()
    setSession(null)
    setVideoUrl(null)
    setEmotionDetections([])
    navigate('/')
  }

  if (!patientId) {
    return null
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Doctor Analyzer
      </h1>
      <p className="text-gray-600 mb-8">
        Upload patient videos for emotional and sentiment analysis
      </p>

      {!session ? (
        <UploadZone patientId={patientId} onSessionCreated={handleSessionCreated} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left column: Video player */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h2 className="text-lg font-semibold mb-4">Video Analysis</h2>
              {videoUrl && (
                <VideoPlayer
                  videoUrl={videoUrl}
                  detections={emotionDetections}
                  isAnalyzing={status === 'processing_video'}
                />
              )}
            </div>

            {/* Analysis controls */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Session ID</p>
                  <p className="font-mono text-sm">{session.session_id.slice(0, 8)}...</p>
                </div>
                <div className="flex gap-2">
                  {status === 'completed' && (
                    <button
                      onClick={() => navigate(`/patients/${patientId}/sessions`)}
                      className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                    >
                      Back to Sessions
                    </button>
                  )}
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                  >
                    New Session
                  </button>
                  <button
                    onClick={handleStartAnalysis}
                    disabled={!canStartAnalysis}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isAnalyzing ? 'Analyzing...' : 'Start Analysis'}
                  </button>
                </div>
              </div>

              {/* Pipeline stepper + progress */}
              {status && status !== 'pending' && status !== 'uploading' && (
                <div className="mt-4">
                  {/* Step indicator */}
                  {(() => {
                    const steps: { label: string; key: AnalysisStatus }[] = [
                      { label: 'Video Analysis', key: 'processing_video' },
                      { label: 'Injury check', key: 'processing_injury_check' },
                      { label: 'Audio Analysis', key: 'processing_audio' },
                      { label: 'Report', key: 'aggregating' },
                    ]
                    const statusOrder: AnalysisStatus[] = [
                      'processing_video', 'processing_injury_check', 'processing_audio', 'aggregating', 'completed',
                    ]
                    const currentIdx = statusOrder.indexOf(status as AnalysisStatus)

                    return (
                      <div className="flex items-center justify-between mb-3">
                        {steps.map((step, i) => {
                          const stepIdx = statusOrder.indexOf(step.key)
                          const isDone = currentIdx > stepIdx || status === 'completed'
                          const isActive = currentIdx === stepIdx && status !== 'completed' && status !== 'failed'

                          return (
                            <div key={step.key} className="flex items-center flex-1 last:flex-none">
                              <div className="flex flex-col items-center">
                                <div
                                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium ${
                                    isDone
                                      ? 'bg-green-500 text-white'
                                      : isActive
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-200 text-gray-500'
                                  }`}
                                >
                                  {isDone ? (
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                  ) : isActive ? (
                                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                                    </svg>
                                  ) : (
                                    <span className="w-2 h-2 rounded-full bg-gray-400" />
                                  )}
                                </div>
                                <span
                                  className={`mt-1 text-xs whitespace-nowrap ${
                                    isDone
                                      ? 'text-green-600 font-medium'
                                      : isActive
                                        ? 'text-blue-600 font-medium'
                                        : 'text-gray-400'
                                  }`}
                                >
                                  {step.label}
                                </span>
                              </div>
                              {i < steps.length - 1 && (
                                <div
                                  className={`flex-1 h-0.5 mx-2 mt-[-1rem] ${
                                    currentIdx > stepIdx ? 'bg-green-400' : 'bg-gray-200'
                                  }`}
                                />
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )
                  })()}

                  {/* Status message */}
                  {statusMessage && status !== 'completed' && (
                    <p className="text-sm text-gray-600 mb-2">{statusMessage}</p>
                  )}

                  {/* Progress bar */}
                  {status !== 'completed' && status !== 'failed' && (
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">
                          {status.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())}
                        </span>
                        <span className="text-gray-900">{Math.round(progress * 100)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${progress * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Error message */}
              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}

              {/* Connection status */}
              <div className="mt-4 flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-green-500' : 'bg-gray-400'
                  }`}
                />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>

          {/* Right column: Analysis results */}
          <div>
            <AnalysisPanel
              session={session}
              status={status}
              transcriptions={transcriptions}
              results={results}
              emotionDetections={emotionDetections}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function PatientSessionsPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Doctor Analyzer
      </h1>
      <p className="text-gray-600 mb-8">
        Upload patient videos for emotional and sentiment analysis
      </p>
      <PatientSessions />
    </div>
  )
}

function SessionResultsPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Doctor Analyzer
      </h1>
      <p className="text-gray-600 mb-8">
        Upload patient videos for emotional and sentiment analysis
      </p>
      <SessionResults />
    </div>
  )
}

function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Doctor Analyzer
      </h1>
      <p className="text-gray-600 mb-8">
        Upload patient videos for emotional and sentiment analysis
      </p>
      <PatientList />
    </div>
  )
}

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/patients/:patientId/sessions" element={<PatientSessionsPage />} />
        <Route path="/patients/:patientId/sessions/:sessionId" element={<SessionResultsPage />} />
        <Route path="/patients/:patientId/upload" element={<AnalysisPage />} />
      </Routes>
    </MainLayout>
  )
}

export default App
