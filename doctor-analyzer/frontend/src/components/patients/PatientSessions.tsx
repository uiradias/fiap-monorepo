import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Play, Eye } from 'lucide-react'
import { api } from '../../services/api'
import { Breadcrumb } from '../layout/Breadcrumb'
import type { AnalysisSession, Patient } from '../../types/analysis'

export function PatientSessions() {
  const { patientId } = useParams<{ patientId: string }>()
  const navigate = useNavigate()

  const [patient, setPatient] = useState<Patient | null>(null)
  const [sessions, setSessions] = useState<AnalysisSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!patientId) return

    const fetchData = async () => {
      try {
        const [patientData, sessionsData] = await Promise.all([
          api.getPatient(patientId),
          api.getPatientSessions(patientId),
        ])
        setPatient(patientData)
        setSessions(sessionsData.sessions)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [patientId])

  if (!patientId) return null

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'pending':
      case 'uploading':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-blue-100 text-blue-800'
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: 'Patients', href: '/' },
          { label: patient?.codename ?? '...' },
        ]}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        {patient && (
          <h2 className="text-xl font-semibold text-gray-900">
            Sessions for {patient.codename}
          </h2>
        )}
        <button
          onClick={() => navigate(`/patients/${patientId}/upload`)}
          className="inline-flex items-center gap-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          <Play className="w-4 h-4" />
          New Session
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Sessions Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {loading ? (
          <p className="text-gray-500 text-center py-8">Loading sessions...</p>
        ) : sessions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No sessions yet. Click "New Session" to get started.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="pb-3 text-sm font-medium text-gray-500">Session ID</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Status</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Created</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Updated</th>
                  <th className="pb-3 text-sm font-medium text-gray-500"></th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((session) => (
                  <tr
                    key={session.session_id}
                    onClick={() => navigate(`/patients/${patientId}/sessions/${session.session_id}`)}
                    className="border-b border-gray-100 last:border-0 hover:bg-gray-50 cursor-pointer transition"
                  >
                    <td className="py-3 font-mono text-sm text-gray-600">
                      {session.session_id.slice(0, 8)}...
                    </td>
                    <td className="py-3">
                      <span
                        className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${statusColor(session.status)}`}
                      >
                        {session.status}
                      </span>
                    </td>
                    <td className="py-3 text-sm text-gray-600">
                      {new Date(session.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 text-sm text-gray-600">
                      {session.updated_at
                        ? new Date(session.updated_at).toLocaleString()
                        : '—'}
                    </td>
                    <td className="py-3 text-right">
                      <span className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800">
                        <Eye className="w-4 h-4" />
                        View
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
