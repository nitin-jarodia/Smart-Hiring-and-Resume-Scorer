'use client'
import { useEffect, useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import { analyticsApi } from '@/lib/api'
import { Briefcase, Users, BarChart3, TrendingUp } from 'lucide-react'

export default function AdminAnalyticsPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsApi.admin()
      .then(r => { setData(r.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const stats = [
    { icon: Briefcase, label: 'Total Jobs', value: data?.total_jobs ?? 0, color: 'var(--brand)' },
    { icon: Users, label: 'Total Resumes', value: data?.total_resumes ?? 0, color: 'var(--success)' },
    { icon: BarChart3, label: 'Screenings Run', value: data?.total_screenings ?? 0, color: 'var(--warning)' },
    { icon: TrendingUp, label: 'Avg Score', value: data?.avg_score ?? 0, color: 'var(--info)' },
  ]

  return (
    <AppLayout>
      <div style={{ padding: '2rem 2.5rem', maxWidth: 960 }}>
        <div style={{ marginBottom: '2rem' }}>
          <h1>Analytics</h1>
          <p style={{ marginTop: '0.25rem' }}>System-wide performance and activity metrics.</p>
        </div>

        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 90 }} />)}
          </div>
        ) : (
          <>
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

            {/* Recruiter Details */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border)' }}>
                <h3>Recruiter Details</h3>
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
          </>
        )}
      </div>
    </AppLayout>
  )
}
