'use client'
import { useEffect, useState, useCallback } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import { candidateApi } from '@/lib/api'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export default function CandidateResumePage() {
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)

  useEffect(() => { loadProfile() }, [])

  const loadProfile = async () => {
    try {
      const res = await candidateApi.getProfile()
      setProfile(res.data)
    } catch {} finally { setLoading(false) }
  }

  const onDrop = useCallback(async (files: File[]) => {
    if (files.length === 0) return
    setUploading(true)
    try {
      await candidateApi.uploadResume(files[0])
      toast.success('Resume uploaded successfully!')
      loadProfile()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally { setUploading(false) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
  })

  if (loading) return (
    <AppLayout>
      <div style={{ padding: '2rem 2.5rem' }}>
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    </AppLayout>
  )

  return (
    <AppLayout>
      <div style={{ padding: '2rem 2.5rem', maxWidth: 700 }}>
        <h1 style={{ marginBottom: '0.25rem' }}>My Resume</h1>
        <p style={{ marginBottom: '1.5rem' }}>Upload and manage your resume</p>

        {/* Upload Zone */}
        <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}
          style={{ padding: '2.5rem', textAlign: 'center', marginBottom: '1.5rem', cursor: 'pointer' }}>
          <input {...getInputProps()} />
          {uploading ? (
            <>
              <div className="spinner" style={{ marginBottom: '1rem' }} />
              <p>Processing resume...</p>
            </>
          ) : profile?.has_profile ? (
            <>
              <RefreshCw size={28} color="var(--accent)" style={{ marginBottom: '0.75rem' }} />
              <p style={{ fontWeight: 500 }}>Drop a new resume to update</p>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>PDF, DOCX, or TXT</p>
            </>
          ) : (
            <>
              <Upload size={28} color="var(--text-muted)" style={{ marginBottom: '0.75rem' }} />
              <p style={{ fontWeight: 500 }}>{isDragActive ? 'Drop file here' : 'Drag & drop your resume, or click to browse'}</p>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>PDF, DOCX, or TXT</p>
            </>
          )}
        </div>

        {/* Profile Info */}
        {profile?.has_profile && (
          <>
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <FileText size={20} color="var(--accent)" />
                <div>
                  <div style={{ fontWeight: 500 }}>{profile.filename}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Uploaded {new Date(profile.created_at).toLocaleDateString()}
                    {profile.updated_at && ` · Updated ${new Date(profile.updated_at).toLocaleDateString()}`}
                  </div>
                </div>
                <CheckCircle size={18} color="var(--teal)" style={{ marginLeft: 'auto' }} />
              </div>

              {/* Contact Info */}
              {profile.contact_info && Object.keys(profile.contact_info).length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ fontSize: '0.78rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Contact Info Detected</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {profile.contact_info.email && (
                      <span className="badge badge-neutral">📧 {profile.contact_info.email}</span>
                    )}
                    {profile.contact_info.phone && (
                      <span className="badge badge-neutral">📱 {profile.contact_info.phone}</span>
                    )}
                    {profile.contact_info.name && (
                      <span className="badge badge-neutral">👤 {profile.contact_info.name}</span>
                    )}
                  </div>
                </div>
              )}

              {/* Extracted Skills */}
              {(profile.extracted_skills || []).length > 0 && (
                <div>
                  <h4 style={{ fontSize: '0.78rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
                    Skills Extracted ({profile.extracted_skills.length})
                  </h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                    {profile.extracted_skills.map((s: string) => (
                      <span key={s} className="badge badge-success">{s}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Sections Detected */}
            {profile.sections && Object.keys(profile.sections).length > 0 && (
              <div className="card">
                <h4 style={{ fontSize: '0.78rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Resume Sections Detected</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                  {Object.keys(profile.sections).map(sec => (
                    <span key={sec} className="badge badge-neutral">{sec}</span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </AppLayout>
  )
}
