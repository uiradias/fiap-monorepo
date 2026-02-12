import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Users, Play } from 'lucide-react'
import { api } from '../../services/api'
import type { Patient } from '../../types/analysis'

interface PatientWithSessions extends Patient {
  sessionCount: number
}

export function PatientList() {
  const navigate = useNavigate()
  const [patients, setPatients] = useState<PatientWithSessions[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Add patient form state
  const [newId, setNewId] = useState('')
  const [newCodename, setNewCodename] = useState('')
  const [creating, setCreating] = useState(false)

  const fetchPatients = async () => {
    try {
      const { patients: list } = await api.getPatients()
      const withSessions = await Promise.all(
        list.map(async (p) => {
          try {
            const { total } = await api.getPatientSessions(p.id)
            return { ...p, sessionCount: total }
          } catch {
            return { ...p, sessionCount: 0 }
          }
        })
      )
      setPatients(withSessions)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patients')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPatients()
  }, [])

  const handleAddPatient = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newId.trim() || !newCodename.trim()) return

    setCreating(true)
    setError(null)
    try {
      await api.createPatient(newId.trim(), newCodename.trim())
      setNewId('')
      setNewCodename('')
      await fetchPatients()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create patient')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Add Patient Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-blue-600" />
          Add Patient
        </h2>
        <form onSubmit={handleAddPatient} className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Patient ID
            </label>
            <input
              type="text"
              value={newId}
              onChange={(e) => setNewId(e.target.value)}
              placeholder="UUID or identifier..."
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Codename
            </label>
            <input
              type="text"
              value={newCodename}
              onChange={(e) => setNewCodename(e.target.value)}
              placeholder="Patient codename..."
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            disabled={!newId.trim() || !newCodename.trim() || creating}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {creating ? 'Adding...' : 'Add Patient'}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Patient List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Users className="w-5 h-5 text-blue-600" />
          Patients
        </h2>

        {loading ? (
          <p className="text-gray-500 text-center py-8">Loading patients...</p>
        ) : patients.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No patients yet. Add one above to get started.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="pb-3 text-sm font-medium text-gray-500">Codename</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">ID</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Created</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Sessions</th>
                  <th className="pb-3 text-sm font-medium text-gray-500"></th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <tr key={patient.id} className="border-b border-gray-100 last:border-0">
                    <td className="py-3 font-medium text-gray-900">
                      {patient.codename}
                    </td>
                    <td className="py-3 font-mono text-sm text-gray-600">
                      {patient.id.length > 12
                        ? `${patient.id.slice(0, 12)}...`
                        : patient.id}
                    </td>
                    <td className="py-3 text-sm text-gray-600">
                      {new Date(patient.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 text-sm text-gray-600">
                      {patient.sessionCount}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => navigate(`/patients/${patient.id}/upload`)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                      >
                        <Play className="w-3.5 h-3.5" />
                        New Session
                      </button>
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
