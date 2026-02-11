import axios from 'axios'
import type {
  AnalysisSession,
  UploadVideoResponse,
  UploadDocumentsResponse,
  AddTextResponse,
} from '../types/analysis'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_URL,
})

export const api = {
  // Upload endpoints
  async uploadVideo(
    file: File,
    patientId?: string
  ): Promise<UploadVideoResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (patientId) {
      formData.append('patient_id', patientId)
    }

    const response = await client.post<UploadVideoResponse>(
      '/api/upload/video',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },

  async uploadDocuments(
    sessionId: string,
    files: File[]
  ): Promise<UploadDocumentsResponse> {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    files.forEach((file) => {
      formData.append('files', file)
    })

    const response = await client.post<UploadDocumentsResponse>(
      '/api/upload/documents',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },

  async addTextInput(
    sessionId: string,
    text: string
  ): Promise<AddTextResponse> {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('text', text)

    const response = await client.post<AddTextResponse>(
      '/api/upload/text',
      formData
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

  async deleteSession(sessionId: string): Promise<void> {
    await client.delete(`/api/sessions/${sessionId}`)
  },

  // Analysis endpoints
  async startAnalysis(
    sessionId: string
  ): Promise<{ session_id: string; status: string }> {
    const response = await client.post(`/api/analysis/${sessionId}/start`)
    return response.data
  },

  async getAnalysisStatus(
    sessionId: string
  ): Promise<{ session_id: string; status: string }> {
    const response = await client.get(`/api/analysis/${sessionId}/status`)
    return response.data
  },

  async getAnalysisResults(sessionId: string): Promise<AnalysisSession> {
    const response = await client.get(`/api/analysis/${sessionId}/results`)
    return response.data
  },
}
