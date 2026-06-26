'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import AppLayout from '@/components/layout/AppLayout'
import { jobsApi } from '@/lib/api'
import { Plus, Trash2, ArrowRight } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import toast from 'react-hot-toast'

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    jobsApi.list().then(r => { setJobs(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this job and all its data?')) return
    try {
      await jobsApi.delete(id)
      setJobs(jobs.filter(j => j.id !== id))
      toast.success('Job deleted')
    } catch { toast.error('Failed to delete') }
  }

  return (
    <AppLayout>
      <div style={{ padding: '2rem 2.5rem', maxWidth: 960 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h1>Jobs</h1>
            <p style={{ marginTop: '0.25rem' }}>Manage your job postings and screening pipelines.</p>
          </div>
          <Link href="/jobs/new" className="btn btn-primary">
            <Plus size={16} /> New Job
          </Link>
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading ? (
            <div style={{ padding: '1.25rem' }}>
              {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 52, marginBottom: 4 }} />)}
            </div>
          ) : jobs.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>No jobs yet. Create one to get started.</p>
              <Link href="/jobs/new" className="btn btn-primary btn-sm">Create Job</Link>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Company</th>
                  <th>Resumes</th>
                  <th>Experience</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr key={job.id}>
                    <td>
                      <Link href={`/jobs/${job.id}`} style={{ color: 'var(--brand)', fontWeight: 500, textDecoration: 'none' }}>
                        {job.title}
                      </Link>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{job.company || '—'}</td>
                    <td><span className="badge badge-neutral">{job.resume_count || 0}</span></td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                      {job.min_years_exp ? `${job.min_years_exp}+ years` : '—'}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{formatDate(job.created_at)}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Link href={`/jobs/${job.id}`} className="btn btn-ghost btn-sm">
                          <ArrowRight size={14} />
                        </Link>
                        <button onClick={() => handleDelete(job.id)} className="btn btn-ghost btn-sm"
                          style={{ color: 'var(--danger)' }}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
