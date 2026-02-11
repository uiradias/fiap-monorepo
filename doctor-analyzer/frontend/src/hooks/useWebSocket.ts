import { useEffect, useRef, useCallback, useState } from 'react'
import type {
  WebSocketMessage,
  EmotionUpdateMessage,
  StatusUpdateMessage,
  TranscriptionUpdateMessage,
  SentimentUpdateMessage,
  AnalysisSessionFull,
  AnalysisStatus,
} from '../types/analysis'

interface UseWebSocketOptions {
  sessionId: string
  onEmotionUpdate?: (update: EmotionUpdateMessage) => void
  onStatusUpdate?: (update: StatusUpdateMessage) => void
  onTranscriptionUpdate?: (update: TranscriptionUpdateMessage) => void
  onSentimentUpdate?: (update: SentimentUpdateMessage) => void
  onComplete?: (results: AnalysisSessionFull) => void
  onError?: (message: string) => void
}

const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_BASE_DELAY_MS = 1000

export function useWebSocket({
  sessionId,
  onEmotionUpdate,
  onStatusUpdate,
  onTranscriptionUpdate,
  onSentimentUpdate,
  onComplete,
  onError,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [status, setStatus] = useState<AnalysisStatus | null>(null)

  // Keep callbacks in refs so the effect doesn't re-run when they change
  const callbacksRef = useRef({
    onEmotionUpdate,
    onStatusUpdate,
    onTranscriptionUpdate,
    onSentimentUpdate,
    onComplete,
    onError,
  })
  callbacksRef.current = {
    onEmotionUpdate,
    onStatusUpdate,
    onTranscriptionUpdate,
    onSentimentUpdate,
    onComplete,
    onError,
  }

  // Auto-connect when sessionId becomes available, cleanup on change/unmount
  useEffect(() => {
    if (!sessionId) return

    let disposed = false

    function createConnection() {
      if (disposed) return

      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
      const ws = new WebSocket(`${wsUrl}/ws/analysis/${sessionId}`)

      ws.onopen = () => {
        if (disposed) {
          ws.close()
          return
        }
        reconnectAttemptRef.current = 0
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          const cb = callbacksRef.current

          switch (message.type) {
            case 'emotion_update':
              cb.onEmotionUpdate?.(message)
              break

            case 'status_update':
              setStatus(message.status)
              cb.onStatusUpdate?.(message)
              break

            case 'transcription_update':
              cb.onTranscriptionUpdate?.(message)
              break

            case 'sentiment_update':
              cb.onSentimentUpdate?.(message)
              break

            case 'complete':
              setStatus('completed')
              cb.onComplete?.(message.results)
              break

            case 'error':
              cb.onError?.(message.message)
              break
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onerror = () => {
        callbacksRef.current.onError?.('WebSocket connection error')
      }

      ws.onclose = () => {
        setIsConnected(false)

        // Attempt reconnection unless the effect was cleaned up or analysis completed
        if (!disposed && reconnectAttemptRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_BASE_DELAY_MS * Math.pow(2, reconnectAttemptRef.current)
          reconnectAttemptRef.current += 1
          reconnectTimerRef.current = setTimeout(createConnection, delay)
        }
      }

      wsRef.current = ws
    }

    createConnection()

    return () => {
      disposed = true
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      setIsConnected(false)
    }
  }, [sessionId])

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    // Exhaust reconnect attempts so onclose won't try again
    reconnectAttemptRef.current = MAX_RECONNECT_ATTEMPTS
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const requestStatus = useCallback(() => {
    sendMessage({ action: 'get_status' })
  }, [sendMessage])

  return {
    disconnect,
    sendMessage,
    requestStatus,
    isConnected,
    status,
  }
}
