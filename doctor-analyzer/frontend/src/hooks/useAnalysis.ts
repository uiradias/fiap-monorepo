import { useState, useCallback } from 'react'
import { useWebSocket } from './useWebSocket'
import { api } from '../services/api'
import type {
  EmotionUpdateMessage,
  TranscriptionUpdateMessage,
  AnalysisSessionFull,
  AnalysisStatus,
} from '../types/analysis'

export interface StartAnalysisOptions {
  enableInjuryCheck?: boolean
}

interface UseAnalysisOptions {
  sessionId: string
  onEmotionUpdate?: (update: EmotionUpdateMessage) => void
}

export function useAnalysis({ sessionId, onEmotionUpdate }: UseAnalysisOptions) {
  const [progress, setProgress] = useState(0)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [transcriptions, setTranscriptions] = useState<TranscriptionUpdateMessage[]>([])
  const [results, setResults] = useState<AnalysisSessionFull | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleStatusUpdate = useCallback(
    (update: { status: AnalysisStatus; progress?: number; message?: string }) => {
      if (update.progress !== undefined) {
        setProgress(update.progress)
      }
      if (update.message !== undefined) {
        setStatusMessage(update.message)
      }
    },
    []
  )

  const handleTranscriptionUpdate = useCallback(
    (update: TranscriptionUpdateMessage) => {
      setTranscriptions((prev) => [...prev, update])
    },
    []
  )

  const handleComplete = useCallback((results: AnalysisSessionFull) => {
    setResults(results)
    setProgress(1)
  }, [])

  const handleError = useCallback((message: string) => {
    setError(message)
  }, [])

  const {
    disconnect,
    isConnected,
    status,
  } = useWebSocket({
    sessionId,
    onEmotionUpdate,
    onStatusUpdate: handleStatusUpdate,
    onTranscriptionUpdate: handleTranscriptionUpdate,
    onComplete: handleComplete,
    onError: handleError,
  })

  const startAnalysis = useCallback(
    async (options?: StartAnalysisOptions) => {
      if (!sessionId) return

      try {
        setError(null)
        setProgress(0)
        setStatusMessage(null)
        setTranscriptions([])
        setResults(null)
        await api.startAnalysis(sessionId, options)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start analysis')
      }
    },
    [sessionId]
  )

  const reset = useCallback(() => {
    disconnect()
    setProgress(0)
    setStatusMessage(null)
    setTranscriptions([])
    setResults(null)
    setError(null)
  }, [disconnect])

  return {
    // State
    status,
    progress,
    statusMessage,
    transcriptions,
    results,
    error,
    isConnected,

    // Actions
    disconnect,
    startAnalysis,
    reset,
  }
}
