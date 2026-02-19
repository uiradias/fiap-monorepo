import React, { useState, useEffect } from 'react'
import { Routes, Route, useParams } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { Breadcrumb } from './components/layout/Breadcrumb'
import { PatientList } from './components/patients/PatientList'
import { PatientSessions } from './components/patients/PatientSessions'
import { SessionResults } from './components/sessions/SessionResults'
import { UploadZone } from './components/upload/UploadZone'
import { VideoPlayer } from './components/video/VideoPlayer'
import { AnalysisPanel } from './components/analysis/AnalysisPanel'
import { useAnalysis } from './hooks/useAnalysis'
import { api } from './services/api'
import type { AnalysisSession, AnalysisStatus, EmotionUpdateMessage, Patient } from './types/analysis'

function AnalysisPage() {
  const { patientId } = useParams<{ patientId: string }>()

  const [patient, setPatient] = useState<Patient | null>(null)
  const [session, setSession] = useState<AnalysisSession | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [emotionDetections, setEmotionDetections] = useState<EmotionUpdateMessage[]>([])

  useEffect(() => {
    if (!patientId) return
    api.getPatient(patientId).then(setPatient).catch(() => {})
  }, [patientId])


  const {
    status,
    progress,
    statusMessage,
    isConnected,
    transcriptions,
    results,
    error,
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

  useEffect(() => {
    if (session) {
      startAnalysis()
    }
  }, [session])

  if (!patientId) {
    return null
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <Breadcrumb
        items={[
          { label: 'Patients', href: '/' },
          { label: patient?.codename ?? '...', href: `/patients/${patientId}/sessions` },
          { label: 'New Analysis' },
        ]}
      />
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Doctor Analyzer
      </h1>
      <p className="text-gray-600 mb-8">
        Upload patient videos for emotional and sentiment analysis
      </p>

      {!session ? (
        <UploadZone patientId={patientId} onSessionCreated={handleSessionCreated} />
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left column: Video player */}
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

            {/* Right column: Transcription */}
            <div>
              <AnalysisPanel
                session={session}
                status={status}
                transcriptions={transcriptions}
                results={results}
                emotionDetections={emotionDetections}
                mode="sidebar"
              />
            </div>
          </div>

          {/* Analysis controls */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div>
              <p className="text-sm text-gray-600">Session ID</p>
              <p className="font-mono text-sm">{session.session_id}</p>
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
                    { label: 'Compilation', key: 'processing_bedrock' },
                    { label: 'Report', key: 'aggregating' },
                  ]
                  const statusOrder: AnalysisStatus[] = [
                    'processing_video', 'processing_injury_check', 'processing_audio', 'processing_bedrock', 'aggregating', 'completed',
                  ]
                  const currentIdx = statusOrder.indexOf(status as AnalysisStatus)

                  return (
                    <div className="flex items-center mb-3">
                      {steps.map((step, i) => {
                        const stepIdx = statusOrder.indexOf(step.key)
                        const isDone = currentIdx > stepIdx || status === 'completed'
                        const isActive = currentIdx === stepIdx && status !== 'completed' && status !== 'failed'

                        return (
                          <React.Fragment key={step.key}>
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
                                className={`flex-1 h-0.5 mx-2 self-start mt-3.5 ${
                                  currentIdx > stepIdx ? 'bg-green-400' : 'bg-gray-200'
                                }`}
                              />
                            )}
                          </React.Fragment>
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

          {/* Full-width sections */}
          <AnalysisPanel
            session={session}
            status={status}
            transcriptions={transcriptions}
            results={results}
            emotionDetections={emotionDetections}
            mode="main"
          />
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
