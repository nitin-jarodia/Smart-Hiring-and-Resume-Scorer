'use client'
import { useEffect, useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import { candidateApi } from '@/lib/api'
import { getScoreColor, formatDate } from '@/lib/utils'
import { FileCheck, Clock, CheckCircle, XCircle, Users, Zap } from 'lucide-react'

export default function CandidateApplicationsPage() {
  const [apps, setApps] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<any>(null)

  useEffect(() => { loadApps() }, [])

  const loadApps = async () => {
    try {
      const res = await candidateApi.getApplications()
      setApps(res.data)
    } catch {} finally { setLoading(false) }
  }

  const statusIcon = (status: string) => {
    if (status === 'shortlisted') return <CheckCircle size={14} color="var(--teal)" />
    if (status === 'rejected') return <XCircle size={14} color="var(--ember)" />
    if (status === 'interviewed') return <Users size={14} color="var(--accent)" />
    return <Clock size={14} color="var(--warning)" />
  }

  const statusLabel = (status: string) => {
    const cls = status === 'shortlisted' ? 'badge-success' : status === 'rejected' ? 'badge-danger' : status === 'interviewed' ? 'badge-info' : 'badge-warning'
    return <span className={`badge ${cls}`}>{status}</span>
  }

  if (loading) return (
    <AppLayout>
      <div className="p-8 md:px-10">
        {[1,2,3].map(i => <div key={i} className="skeleton h-16 mb-2" />)}
      </div>
    </AppLayout>
  )

  return (
    <AppLayout>
      <div className="p-8 md:px-10 max-w-[1000px] mx-auto">
        <h1 className="mb-1">My Applications</h1>
        <p className="mb-6 text-[var(--text-secondary)]">Track status of jobs you&apos;ve applied to</p>

        {apps.length === 0 ? (
          <div className="card text-center p-12">
            <div className="flex justify-center mb-3">
              <FileCheck size={32} color="var(--text-muted)" />
            </div>
            <h3 className="mb-2">No applications yet</h3>
            <p>Browse jobs and apply to get started!</p>
          </div>
        ) : (
          <div className={`grid gap-4 ${selected ? 'grid-cols-1 md:grid-cols-[1fr_380px]' : 'grid-cols-1'}`}>
            <div className="card p-0 overflow-hidden">
              <table className="table">
                <thead>
                  <tr>
                    <th>Job</th>
                    <th>Score</th>
                    <th>Match</th>
                    <th>Status</th>
                    <th>Applied</th>
                  </tr>
                </thead>
                <tbody>
                  {apps.map(app => (
                    <tr key={app.id} onClick={() => setSelected(app)}
                      className="cursor-pointer transition-colors duration-150"
                      style={{ background: selected?.id === app.id ? 'var(--hover-row)' : undefined }}>
                      <td>
                        <div className="font-medium">{app.job_title}</div>
                        {app.company && <div className="text-[0.72rem] text-[var(--text-muted)] mt-0.5">{app.company}</div>}
                      </td>
                      <td>
                        <span className={`${getScoreColor(app.score)} font-bold`}>
                          {app.score.toFixed(0)}
                        </span>
                      </td>
                      <td>
                        <span className={`${getScoreColor(app.match_percent)} font-semibold text-[0.82rem]`}>
                          {app.match_percent.toFixed(0)}%
                        </span>
                      </td>
                      <td>{statusLabel(app.status)}</td>
                      <td className="text-[0.75rem] text-[var(--text-muted)]">
                        {new Date(app.applied_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Detail Panel */}
            {selected && (
              <div className="card sticky top-4 self-start">
                <h3 className="mb-1">{selected.job_title}</h3>
                {selected.company && <p className="text-[0.78rem] mb-4">{selected.company}</p>}

                <div className="text-center py-4 border-b border-[var(--border)] mb-4">
                  <div className={`${getScoreColor(selected.score)} text-3xl font-bold leading-none`}>
                    {selected.score.toFixed(0)}
                  </div>
                  <div className="text-[0.75rem] text-[var(--text-muted)] mt-1.5 flex flex-col gap-1 items-center">
                    <span>Resume Score · {selected.match_percent.toFixed(0)}% skill match</span>
                    <span className="badge badge-neutral mt-0.5">{selected.seniority || 'Unknown'} Level</span>
                  </div>
                </div>

                {/* Strength Tags */}
                {selected.strength_tags && selected.strength_tags.length > 0 && (
                  <div className="mb-5">
                    <h4 className="text-[0.78rem] mb-2 font-semibold">Match Profile</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {selected.strength_tags.map((tag: string) => (
                        <span key={tag} className="px-2 py-1 rounded-full text-[0.6rem] font-bold tracking-wide uppercase border border-[var(--brand)] text-[var(--brand)] bg-[var(--brand)]/10">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Explanation Wrapper */}
                {selected.explanation && (
                  <div className="mb-5 p-4 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)]">
                    <h4 className="text-[0.78rem] mb-2 flex items-center gap-1.5 font-semibold text-[var(--brand)]">
                      <Zap size={14} /> AI Match Review
                    </h4>
                    <p className="text-[0.78rem] leading-relaxed text-[var(--text-secondary)] italic">
                      &quot;{selected.explanation}&quot;
                    </p>
                  </div>
                )}

                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    {statusIcon(selected.status)}
                    <span className="font-medium text-[0.8rem]">Status: </span>
                    {statusLabel(selected.status)}
                  </div>
                </div>

                {/* Skills */}
                {(selected.matched_skills?.length > 0 || selected.missing_skills?.length > 0) && (
                  <div className="mb-4">
                    <h4 className="text-[0.78rem] mb-2 font-semibold">Skills</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {selected.matched_skills?.map((s: string) => (
                        <span key={s} className="badge badge-success">{s}</span>
                      ))}
                      {selected.missing_skills?.map((s: string) => (
                        <span key={s} className="badge badge-danger">{s}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Project Analysis */}
                {selected.project_evaluations && selected.project_evaluations.length > 0 && (
                  <div className="mb-5">
                    <h4 className="text-[0.78rem] mb-3 flex items-center gap-1.5 font-semibold">
                      <span className="text-[var(--brand)]">✨</span> Analyzed Projects
                    </h4>
                    <div className="grid gap-3">
                      {selected.project_evaluations.map((proj: any, idx: number) => (
                        <div key={idx} style={{ 
                          background: 'var(--bg-secondary)', 
                          padding: '0.75rem', 
                          borderRadius: '0.5rem',
                          borderLeft: proj.complexity_level === 'High' ? '3px solid var(--purple)' : proj.complexity_level === 'Medium' ? '3px solid var(--brand)' : '3px solid var(--border)'
                        }}>
                          <div className="font-semibold text-[0.82rem] mb-1.5 flex justify-between items-start">
                            <span className="truncate max-w-[70%]">{proj.project_name}</span>
                            <span className="text-[0.75rem] text-[var(--text-muted)] shrink-0 ml-2">Score: {proj.innovation_impact_score}</span>
                          </div>
                          
                          <div className="flex flex-wrap gap-1.5 mb-2">
                            <span className="badge badge-neutral text-[0.62rem] px-1.5 py-0.5">{proj.complexity_level}</span>
                            <span className="badge badge-neutral text-[0.62rem] px-1.5 py-0.5">{proj.relevance_to_job}% Match</span>
                          </div>

                          {proj.core_technologies?.length > 0 && (
                            <div className="text-[0.72rem] text-[var(--text-secondary)] mt-2 border-t border-[var(--border)] pt-2">
                              <strong className="font-semibold">Tech:</strong> {proj.core_technologies.slice(0, 3).join(', ')}
                              {proj.core_technologies.length > 3 ? '...' : ''}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {selected.recommendations?.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-[0.78rem] mb-2 font-semibold">Improvement Tips</h4>
                    <ul className="pl-5 text-[0.78rem] leading-relaxed space-y-1.5 text-[var(--text-secondary)]">
                      {selected.recommendations.map((r: string, i: number) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
