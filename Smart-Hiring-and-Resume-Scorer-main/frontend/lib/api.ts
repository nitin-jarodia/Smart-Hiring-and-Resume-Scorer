import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      if (window.location.pathname !== '/auth/login') {
        window.location.href = '/auth/login'
      }
    }
    return Promise.reject(err)
  }
)

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  signup: (email: string, password: string, full_name: string, role?: string) =>
    api.post('/auth/signup', { email, password, full_name, role }),
  me: () => api.get('/auth/me'),
}

// Jobs
export const jobsApi = {
  list: () => api.get('/jobs'),
  get: (id: string) => api.get(`/jobs/${id}`),
  create: (data: object) => api.post('/jobs', data),
  delete: (id: string) => api.delete(`/jobs/${id}`),
}

// Resumes
export const resumesApi = {
  upload: (jobId: string, files: File[]) => {
    const fd = new FormData()
    files.forEach(f => fd.append('files', f))
    return api.post(`/jobs/${jobId}/resumes`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: (jobId: string) => api.get(`/jobs/${jobId}/resumes`),
  delete: (resumeId: string) => api.delete(`/resumes/${resumeId}`),
}

// Screening
export const screeningApi = {
  screen: (jobId: string) => api.post(`/jobs/${jobId}/screen`),
  getResults: (jobId: string, params?: object) =>
    api.get(`/jobs/${jobId}/results`, { params }),
  updateResult: (resultId: string, data: object) =>
    api.patch(`/results/${resultId}`, data),
}

// Analytics
export const analyticsApi = {
  job: (jobId: string) => api.get(`/analytics/jobs/${jobId}`),
  admin: () => api.get('/analytics/admin'),
}

// Interviews
export const interviewsApi = {
  schedule: (data: object) => api.post('/interviews', data),
  getByResult: (resultId: string) => api.get(`/interviews/result/${resultId}`),
  getMyInterviews: () => api.get('/interviews/my-interviews'),
  update: (id: string, data: object) => api.patch(`/interviews/${id}`, data),
}

// Candidate Portal
export const candidateApi = {
  getProfile: () => api.get('/candidate/profile'),
  uploadResume: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/candidate/profile', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  apply: (jobId: string) => api.post(`/candidate/apply/${jobId}`),
  getApplications: () => api.get('/candidate/applications'),
  getRecommendations: () => api.get('/candidate/recommendations'),
  getSkillSuggestions: () => api.get('/candidate/skills-suggestions'),
  getResumeTips: () => api.get('/candidate/resume-tips'),
  getPublicJobs: () => api.get('/jobs/public'),
}

// Search
export const searchApi = {
  semanticSearch: (query: string, topK: number = 5) => api.post('/search/candidates/semantic', { query, top_k: topK })
}

// GitHub
export const githubApi = {
  submitProfile: (githubUrl: string) => api.post('/candidate/github', { github_url: githubUrl }),
  getProfile: (candidateId: string) => api.get(`/candidate/github/${candidateId}`)
}

// Export
export const exportResults = (results: any[]) => {
  const headers = ['Candidate', 'Email', 'Score', 'Seniority', 'Status', 'Matched Skills', 'Missing Skills', 'Notes']
  const rows = results.map(r => [
    r.candidate_name || r.filename,
    r.candidate_email || '',
    r.score.toFixed(1),
    r.seniority,
    r.status,
    (r.matched_skills || []).join('; '),
    (r.missing_skills || []).join('; '),
    r.notes || '',
  ])
  const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'screening_results.csv'
  a.click()
  URL.revokeObjectURL(url)
}
