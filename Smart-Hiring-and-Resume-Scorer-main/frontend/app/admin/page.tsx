'use client'
import { useEffect, useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import { analyticsApi } from '@/lib/api'
import { Briefcase, Users, BarChart3, TrendingUp, AlertCircle } from 'lucide-react'

export default function AdminPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    analyticsApi.admin()
      .then(r => { setData(r.data); setLoading(false) })
      .catch(() => { setLoading(false); setError(true) })
  }, [])

  if (loading) return (
    <AppLayout>
      <div style={{ padding: '2rem 2.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
          {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 90 }} />)}
        </div>
      </div>
    </AppLayout>
  )

  if (error) return (
    <AppLayout>
      <div style={{ padding: '2rem 2.5rem', maxWidth: 500 }}>
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }}>
          <AlertCircle size={24} color="var(--danger)" style={{ marginBottom: '0.75rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>Access denied</h3>
          <p>You may not have admin permissions.</p>
          <button className="btn btn-primary btn-sm" onClick={() => window.location.reload()} style={{ marginTop: '1rem' }}>
            Retry
          </button>
        </div>
      </div>
    </AppLayout>
  )

  const stats = [
    { icon: Briefcase, label: 'Total Jobs', value: data?.total_jobs ?? 0, color: 'var(--brand)' },
    { icon: Users, label: 'Resumes', value: data?.total_resumes ?? 0, color: 'var(--success)' },
    { icon: BarChart3, label: 'Screenings', value: data?.total_screenings ?? 0, color: 'var(--warning)' },
    { icon: TrendingUp, label: 'Avg Score', value: data?.avg_score ?? 0, color: 'var(--info)' },
  ]

  return (
    <AppLayout>
      <div style={{ padding: '2rem 2.5rem', maxWidth: 960 }}>
        <div style={{ marginBottom: '2rem' }}>
          <h1>Admin Dashboard</h1>
          <p style={{ marginTop: '0.25rem' }}>System-wide analytics and recruiter activity.</p>
        </div>

        {/* Stats */}
        <div className="stat-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
          {stats.map(stat => (
            <div key={stat.label} className="stat-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.5rem' }}>
                <stat.icon size={15} color={stat.color} />
                <span className="stat-label" style={{ marginTop: 0 }}>{stat.label}</span>
              </div>
              <div className="stat-value" style={{ color: stat.color }}>{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Recruiter Activity */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border)' }}>
            <h3>Recruiter Activity</h3>
          </div>
          {data?.recruiter_activity?.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Jobs Created</th>
                </tr>
              </thead>
              <tbody>
                {data.recruiter_activity.map((r: any, i: number) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{r.name || '—'}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{r.recruiter}</td>
                    <td><span className="badge badge-brand">{r.jobs_created}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No recruiter activity yet.
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
