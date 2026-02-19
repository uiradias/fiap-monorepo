import axios from 'axios'
import type {
  AnalysisSession,
  AnalysisSessionFull,
  EmotionUpdateMessage,
  Patient,
  UploadVideoResponse,
} from '../types/analysis'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_URL,
})

export const api = {
  // Patient endpoints
  async createPatient(
    id: string,
    codename: string
  ): Promise<Patient> {
    const response = await client.post<Patient>('/api/patients', { id, codename })
    return response.data
  },

  async getPatients(): Promise<{ patients: Patient[]; total: number }> {
    const response = await client.get('/api/patients')
    return response.data
  },

  async getPatient(patientId: string): Promise<Patient> {
    const response = await client.get<Patient>(`/api/patients/${patientId}`)
    return response.data
  },

  async getPatientSessions(
    patientId: string
  ): Promise<{ sessions: AnalysisSession[]; total: number }> {
    const response = await client.get(`/api/patients/${patientId}/sessions`)
    return response.data
  },

  // Upload endpoints
  async uploadVideo(
    file: File,
    patientId: string
  ): Promise<UploadVideoResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('patient_id', patientId)

    const response = await client.post<UploadVideoResponse>(
      '/api/upload/video',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },

  // Session endpoints
  async getSession(sessionId: string): Promise<AnalysisSession> {
    const response = await client.get<AnalysisSession>(
      `/api/sessions/${sessionId}`
    )
    return response.data
  },

  async getSessions(): Promise<{ sessions: AnalysisSession[]; total: number }> {
    const response = await client.get('/api/sessions')
    return response.data
  },

  async getVideoUrl(sessionId: string): Promise<string> {
    const response = await client.get<{ video_url: string }>(
      `/api/sessions/${sessionId}/video-url`
    )
    return response.data.video_url
  },

  async getFaceDetections(sessionId: string): Promise<EmotionUpdateMessage[]> {
    const response = await client.get(`/api/sessions/${sessionId}/face-detections`)
    return response.data.map((d: Record<string, unknown>) => ({
      type: 'emotion_update' as const,
      timestamp_ms: d.timestamp_ms,
      emotions: d.emotions,
      bounding_box: d.bounding_box,
    }))
  },

  async deleteSession(sessionId: string): Promise<void> {
    await client.delete(`/api/sessions/${sessionId}`)
  },

  // Analysis endpoints
  async startAnalysis(
    sessionId: string,
    options?: { enableInjuryCheck?: boolean }
  ): Promise<{ session_id: string; status: string }> {
    const response = await client.post(`/api/analysis/${sessionId}/start`, {
      enable_injury_check: options?.enableInjuryCheck ?? false,
    })
    return response.data
  },

  async getAnalysisStatus(
    sessionId: string
  ): Promise<{ session_id: string; status: string }> {
    const response = await client.get(`/api/analysis/${sessionId}/status`)
    return response.data
  },

  async getAnalysisResults(sessionId: string): Promise<AnalysisSessionFull> {
    const response = await client.get<AnalysisSessionFull>(`/api/analysis/${sessionId}/results`)
    return response.data
  },
}
