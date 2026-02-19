import { useMemo, useState, useCallback, useEffect, useRef } from 'react'
import { AlertTriangle, CheckCircle, Clock, Mic, Brain, ShieldAlert, ChevronLeft, ChevronRight } from 'lucide-react'
import type {
  AnalysisSession,
  AnalysisStatus,
  TranscriptionUpdateMessage,
  AnalysisSessionFull,
  EmotionUpdateMessage,
  BedrockAggregation,
} from '../../types/analysis'

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

const ITEMS_PER_PAGE = 10

function TranscriptionCard({ transcriptions }: { transcriptions: TranscriptionUpdateMessage[] }) {
  const [page, setPage] = useState(0)
  const [sliderTime, setSliderTime] = useState(0)
  const [filterByTime, setFilterByTime] = useState(false)

  const maxTime = useMemo(() => {
    if (transcriptions.length === 0) return 0
    return Math.ceil(Math.max(...transcriptions.map((t) => t.end_time)))
  }, [transcriptions])

  const filtered = useMemo(() => {
    if (!filterByTime) return transcriptions
    return transcriptions.filter(
      (t) => t.start_time <= sliderTime && t.end_time >= sliderTime
    )
  }, [transcriptions, sliderTime, filterByTime])

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const currentPage = Math.min(page, totalPages - 1)
  const pageItems = filtered.slice(currentPage * ITEMS_PER_PAGE, (currentPage + 1) * ITEMS_PER_PAGE)

  const handleSliderChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value)
    setSliderTime(val)
    setFilterByTime(val > 0)
    setPage(0)
  }, [])

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex flex-col h-full">
      <div className="flex items-center gap-3 mb-3">
        <Mic className="w-5 h-5 text-blue-500" />
        <h2 className="text-lg font-semibold">Transcription</h2>
        {transcriptions.length > 0 && (
          <span className="text-xs text-gray-400 ml-auto">{filtered.length} segments</span>
        )}
      </div>

      {transcriptions.length === 0 ? (
        <p className="text-sm text-gray-400">Transcription not processed yet</p>
      ) : (
        <>
          {/* Time slider */}
          {maxTime > 0 && (
            <div className="mb-3">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>0:00</span>
                <span className="font-medium text-gray-700">
                  {filterByTime ? formatTime(sliderTime) : 'All'}
                </span>
                <span>{formatTime(maxTime)}</span>
              </div>
              <input
                type="range"
                min={0}
                max={maxTime}
                step={0.1}
                value={filterByTime ? sliderTime : 0}
                onChange={handleSliderChange}
                className="w-full h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer accent-blue-600"
              />
              {filterByTime && (
                <button
                  onClick={() => { setFilterByTime(false); setSliderTime(0); setPage(0) }}
                  className="text-xs text-blue-600 hover:underline mt-1"
                >
                  Show all
                </button>
              )}
            </div>
          )}

          {/* Transcription content */}
          <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
            {pageItems.length > 0 ? (
              pageItems.map((t, index) => (
                <div key={currentPage * ITEMS_PER_PAGE + index} className="flex gap-2 text-sm">
                  <span className="text-gray-400 text-xs whitespace-nowrap">
                    {t.start_time.toFixed(1)}s
                  </span>
                  <p className="text-gray-700">{t.text}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-400">No segments at this time</p>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-3 border-t border-gray-100 mt-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={currentPage === 0}
                className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
                Prev
              </button>
              <span className="text-xs text-gray-500">
                {currentPage + 1} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={currentPage >= totalPages - 1}
                className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

interface AnalysisPanelProps {
  session: AnalysisSession
  status: AnalysisStatus | null
  transcriptions: TranscriptionUpdateMessage[]
  results: AnalysisSessionFull | null
  emotionDetections: EmotionUpdateMessage[]
  mode?: 'sidebar' | 'main'
}

export function AnalysisPanel({
  session,
  status,
  transcriptions,
  results,
  emotionDetections,
  mode,
}: AnalysisPanelProps) {
  const topEmotions = useMemo(() => {
    if (emotionDetections.length > 0) {
      const totals: Record<string, { sum: number; count: number }> = {}
      for (const detection of emotionDetections) {
        for (const e of detection.emotions) {
          if (!totals[e.emotion]) {
            totals[e.emotion] = { sum: 0, count: 0 }
          }
          totals[e.emotion].sum += e.confidence
          totals[e.emotion].count += 1
        }
      }
      return Object.entries(totals)
        .map(([emotion, { sum, count }]) => ({ emotion, confidence: sum / count }))
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 10)
    }
    // Fallback: use emotion_summary from session/results for completed sessions
    const summary = results?.emotion_summary || session.emotion_summary
    if (summary && Object.keys(summary).length > 0) {
      return Object.entries(summary)
        .map(([emotion, confidence]) => ({ emotion, confidence }))
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 10)
    }
    return []
  }, [emotionDetections, results, session.emotion_summary])

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

  const showSidebar = !mode || mode === 'sidebar'
  const showMain = !mode || mode === 'main'

  const [bannerVisible, setBannerVisible] = useState(false)
  const [bannerFading, setBannerFading] = useState(false)
  const fadeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const dismissBanner = useCallback(() => {
    setBannerFading(true)
    fadeTimerRef.current = setTimeout(() => {
      setBannerVisible(false)
      setBannerFading(false)
    }, 500)
  }, [])

  useEffect(() => {
    if (showMain && status === 'completed' && results) {
      setBannerVisible(true)
      setBannerFading(false)
      closeTimerRef.current = setTimeout(dismissBanner, 5000)
    }
    return () => {
      if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current)
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    }
  }, [showMain, status, results, dismissBanner])

  return (
    <div className={`space-y-4${mode === 'sidebar' ? ' h-full' : ''}`}>
      {/* Status card */}
      {showMain && <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
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
            <p className="font-medium">{emotionDetections.length}</p>
          </div>
          {(results?.injury_check ?? session.injury_check) && (
            <div className="col-span-2">
              <p className="text-gray-500">Injury check</p>
              <p className="font-medium">
                {(() => {
                  const check = results?.injury_check ?? session.injury_check
                  if (!check) return '—'
                  if (check.error_message) return `Error: ${check.error_message}`
                  if (check.bedrock_has_signals) {
                    return `Potential signals (${(check.bedrock_confidence * 100).toFixed(0)}% confidence)`
                  }
                  return `No signals indicated (${(check.bedrock_confidence * 100).toFixed(0)}% confidence)`
                })()}
              </p>
            </div>
          )}
        </div>

        {/* Top 10 Emotions */}
        {topEmotions.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Top Emotions</h3>
            <div className="space-y-2">
              {topEmotions.map((item, index) => (
                <div key={item.emotion} className="flex items-center gap-2 text-sm">
                  <span className="text-gray-400 w-5 text-right text-xs">{index + 1}.</span>
                  <span className="w-20 font-medium capitalize truncate">{item.emotion}</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${item.confidence * 100}%`,
                        backgroundColor: EMOTION_COLORS[item.emotion] || '#94a3b8',
                      }}
                    />
                  </div>
                  <span className="text-gray-600 w-10 text-right text-xs">
                    {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>}

      {/* Transcription */}
      {showSidebar && (
        <TranscriptionCard transcriptions={transcriptions} />
      )}

      {/* Injury detection results */}
      {showMain && (results?.injury_check ?? session.injury_check) && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-4">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-semibold">Injury Detection Results</h2>
          </div>
          {(() => {
            const check = results?.injury_check ?? session.injury_check
            if (!check) return null
            if (check.error_message) {
              return (
                <p className="text-sm text-amber-700">
                  Check was requested but could not be completed: {check.error_message}
                </p>
              )
            }
            const severityColors: Record<string, string> = {
              critical: 'bg-red-200 text-red-900',
              high: 'bg-orange-200 text-orange-900',
              moderate: 'bg-yellow-200 text-yellow-900',
              low: 'bg-blue-200 text-blue-900',
            }
            return (
              <>
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span
                    className={`px-2 py-1 rounded text-sm font-medium ${
                      check.bedrock_has_signals
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {check.bedrock_has_signals
                      ? 'Potential signals noted'
                      : 'No signals indicated'}
                  </span>
                  {check.bedrock_severity && (
                    <span
                      className={`px-2 py-1 rounded text-xs font-bold ${
                        severityColors[check.bedrock_severity] || 'bg-gray-200 text-gray-900'
                      }`}
                    >
                      {check.bedrock_severity.toUpperCase()} SEVERITY
                    </span>
                  )}
                  <span className="text-sm text-gray-500">
                    (confidence: {(check.bedrock_confidence * 100).toFixed(0)}%)
                  </span>
                </div>
                <p className="text-sm text-gray-700">{check.bedrock_summary}</p>
                {check.bedrock_clinical_rationale && (
                  <p className="text-sm text-gray-600 mt-2 italic">
                    {check.bedrock_clinical_rationale}
                  </p>
                )}
                {check.bedrock_transcript_analysis?.has_verbal_signals && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-xs font-medium text-amber-600 mb-1">
                      Verbal indicators detected
                    </p>
                    <ul className="text-sm text-gray-700 list-disc pl-4">
                      {check.bedrock_transcript_analysis.findings.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                    {check.bedrock_transcript_analysis.evidence_quotes.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs text-gray-500">Evidence from transcript:</p>
                        {check.bedrock_transcript_analysis.evidence_quotes.map((q, i) => (
                          <blockquote
                            key={i}
                            className="text-xs text-gray-600 border-l-2 border-gray-300 pl-2 mt-1 italic"
                          >
                            &ldquo;{q}&rdquo;
                          </blockquote>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {check.rekognition_labels && check.rekognition_labels.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-xs font-medium text-gray-500 mb-1">Content moderation labels</p>
                    <div className="flex flex-wrap gap-1">
                      {Array.from(
                        check.rekognition_labels.reduce((map, l) => {
                          const prev = map.get(l.name)
                          if (!prev || l.confidence > prev.confidence) {
                            map.set(l.name, l)
                          }
                          return map
                        }, new Map<string, typeof check.rekognition_labels[number]>()).values()
                      ).map((l) => (
                        <span
                          key={l.name}
                          className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-xs text-gray-700"
                        >
                          {l.name} ({(l.confidence * 100).toFixed(0)}%)
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )
          })()}
        </div>
      )}

      {/* Clinical Indicators */}
      {showMain && getClinicalIndicators().length > 0 && (
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

      {/* AI Clinical Summary (Bedrock aggregation) */}
      {showMain && (() => {
        const aggregation: BedrockAggregation | null | undefined =
          results?.bedrock_aggregation ?? session.bedrock_aggregation
        if (!aggregation) return null
        const riskColors: Record<string, string> = {
          critical: 'bg-red-200 text-red-900',
          high: 'bg-orange-200 text-orange-900',
          moderate: 'bg-yellow-200 text-yellow-900',
          low: 'bg-green-200 text-green-900',
        }
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3 mb-4">
              <Brain className="w-5 h-5 text-indigo-500" />
              <h2 className="text-lg font-semibold">AI Clinical Summary</h2>
              <span
                className={`px-2 py-1 rounded text-xs font-bold ${
                  riskColors[aggregation.risk_level] || 'bg-gray-200 text-gray-900'
                }`}
              >
                {aggregation.risk_level.toUpperCase()} RISK
              </span>
            </div>
            <p className="text-sm text-gray-700 mb-3">{aggregation.clinical_summary}</p>

            {aggregation.cross_referenced_evidence.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-medium text-gray-500 mb-1">Cross-referenced evidence</p>
                <ul className="text-sm text-gray-700 list-disc pl-4 space-y-1">
                  {aggregation.cross_referenced_evidence.map((e, i) => (
                    <li key={i}>
                      <span className="font-medium">[{e.source}]</span> {e.finding}
                      {e.supporting_sources.length > 0 && (
                        <span className="text-gray-500">
                          {' '}(corroborated by: {e.supporting_sources.join(', ')})
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {aggregation.concordant_signals.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-medium text-green-600 mb-1">Concordant signals</p>
                <ul className="text-sm text-gray-700 list-disc pl-4">
                  {aggregation.concordant_signals.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {aggregation.discordant_signals.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-medium text-amber-600 mb-1">Discordant signals</p>
                <ul className="text-sm text-gray-700 list-disc pl-4">
                  {aggregation.discordant_signals.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {aggregation.recommendations.length > 0 && (
              <div className="pt-3 border-t border-gray-100">
                <p className="text-xs font-medium text-indigo-600 mb-1">Recommendations</p>
                <ul className="text-sm text-gray-700 list-disc pl-4">
                  {aggregation.recommendations.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )
      })()}

      {/* Floating completion banner */}
      {bannerVisible && (
        <div
          className={`fixed top-6 left-1/2 -translate-x-1/2 z-50 transition-opacity duration-500 ${
            bannerFading ? 'opacity-0' : 'opacity-100'
          }`}
        >
          <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-lg shadow-lg px-5 py-3">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-green-800 text-sm">Analysis Complete</h3>
              <p className="text-xs text-green-700">
                All results have been saved and are ready for review.
              </p>
            </div>
            <button
              onClick={dismissBanner}
              className="ml-4 px-2 py-1 text-xs font-medium text-green-700 hover:text-green-900 hover:bg-green-100 rounded transition flex-shrink-0"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
