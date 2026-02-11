import { AlertTriangle, CheckCircle, Clock, FileText, Mic, Brain } from 'lucide-react'
import type {
  AnalysisSession,
  AnalysisStatus,
  TranscriptionUpdateMessage,
  SentimentUpdateMessage,
  AnalysisSessionFull,
} from '../../types/analysis'

interface AnalysisPanelProps {
  session: AnalysisSession
  status: AnalysisStatus | null
  transcriptions: TranscriptionUpdateMessage[]
  sentiments: SentimentUpdateMessage[]
  results: AnalysisSessionFull | null
  emotionCount: number
}

export function AnalysisPanel({
  session,
  status,
  transcriptions,
  sentiments,
  results,
  emotionCount,
}: AnalysisPanelProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <AlertTriangle className="w-5 h-5 text-red-500" />
      default:
        return <Clock className="w-5 h-5 text-blue-500" />
    }
  }

  const getClinicalIndicators = () => {
    if (results?.clinical_indicators) {
      return results.clinical_indicators
    }
    // Derive from emotion summary if available
    const indicators = []
    const summary = results?.emotion_summary || session.emotion_summary
    if (summary) {
      if (summary.discomfort > 0.3) {
        indicators.push({ indicator_type: 'discomfort', confidence: summary.discomfort })
      }
      if (summary.anxiety > 0.3) {
        indicators.push({ indicator_type: 'anxiety', confidence: summary.anxiety })
      }
      if (summary.depression > 0.3) {
        indicators.push({ indicator_type: 'depression', confidence: summary.depression })
      }
      if (summary.fear > 0.4) {
        indicators.push({ indicator_type: 'fear', confidence: summary.fear })
      }
    }
    return indicators
  }

  return (
    <div className="space-y-4">
      {/* Status card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-3 mb-4">
          {getStatusIcon()}
          <h2 className="text-lg font-semibold">Analysis Status</h2>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Status</p>
            <p className="font-medium capitalize">
              {(status || session.status).replace(/_/g, ' ')}
            </p>
          </div>
          <div>
            <p className="text-gray-500">Emotion Detections</p>
            <p className="font-medium">{emotionCount}</p>
          </div>
          <div>
            <p className="text-gray-500">Transcription Segments</p>
            <p className="font-medium">{transcriptions.length}</p>
          </div>
          <div>
            <p className="text-gray-500">Documents</p>
            <p className="font-medium">{session.documents_count}</p>
          </div>
        </div>
      </div>

      {/* Clinical Indicators */}
      {getClinicalIndicators().length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-4">
            <Brain className="w-5 h-5 text-purple-500" />
            <h2 className="text-lg font-semibold">Clinical Indicators</h2>
          </div>

          <div className="space-y-3">
            {getClinicalIndicators().map((indicator, index) => (
              <div key={index} className="flex items-center gap-3">
                <div
                  className={`px-2 py-1 rounded text-sm font-medium ${
                    indicator.confidence > 0.5
                      ? 'bg-red-100 text-red-700'
                      : 'bg-yellow-100 text-yellow-700'
                  }`}
                >
                  {indicator.indicator_type.toUpperCase()}
                </div>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      indicator.confidence > 0.5 ? 'bg-red-500' : 'bg-yellow-500'
                    }`}
                    style={{ width: `${indicator.confidence * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600">
                  {(indicator.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transcription */}
      {transcriptions.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-4">
            <Mic className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold">Transcription</h2>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-2">
            {transcriptions.map((t, index) => (
              <div key={index} className="flex gap-2 text-sm">
                <span className="text-gray-400 text-xs whitespace-nowrap">
                  {t.start_time.toFixed(1)}s
                </span>
                <p className="text-gray-700">{t.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sentiment Analysis */}
      {sentiments.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-5 h-5 text-green-500" />
            <h2 className="text-lg font-semibold">Sentiment Analysis</h2>
          </div>

          <div className="space-y-3">
            {sentiments.map((s, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500 capitalize">{s.source}</span>
                  <span
                    className={`text-sm font-medium ${
                      s.sentiment.sentiment === 'POSITIVE'
                        ? 'text-green-600'
                        : s.sentiment.sentiment === 'NEGATIVE'
                        ? 'text-red-600'
                        : 'text-gray-600'
                    }`}
                  >
                    {s.sentiment.sentiment}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-xs">
                  <div>
                    <p className="text-gray-500">Positive</p>
                    <p className="font-medium text-green-600">
                      {(s.sentiment.positive_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Negative</p>
                    <p className="font-medium text-red-600">
                      {(s.sentiment.negative_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Neutral</p>
                    <p className="font-medium text-gray-600">
                      {(s.sentiment.neutral_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Mixed</p>
                    <p className="font-medium text-yellow-600">
                      {(s.sentiment.mixed_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completed Results */}
      {status === 'completed' && results && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="font-semibold text-green-800">Analysis Complete</h3>
          </div>
          <p className="text-sm text-green-700">
            All analysis results have been saved and are ready for review.
          </p>
        </div>
      )}
    </div>
  )
}
