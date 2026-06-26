'use client'
import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import AppLayout from '@/components/layout/AppLayout'
import { jobsApi, resumesApi, screeningApi, githubApi, exportResults } from '@/lib/api'
import { useDropzone } from 'react-dropzone'
import { getScoreColor, getScoreLabel, getProgressColor, formatDate } from '@/lib/utils'
import { ArrowLeft, Upload, Zap, Download, Search, X, ChevronRight, FileText, Calendar, AlertTriangle, Github, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import InterviewModal from '@/components/InterviewModal'

const BREAKDOWN_LABELS: Record<string, { label: string; weight: string }> = {
  semantic_similarity: { label: 'Semantic Match', weight: '40%' },
  skill_match: { label: 'Skill Match', weight: '35%' },
  experience_alignment: { label: 'Experience Fit', weight: '15%' },
  education_alignment: { label: 'Education', weight: '5%' },
  formatting_clarity: { label: 'Formatting', weight: '5%' },
}

export default function JobDetailPage() {
  const { id } = useParams()
  const [job, setJob] = useState<any>(null)
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [screening, setScreening] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [selected, setSelected] = useState<any>(null)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')

  const [githubInfo, setGithubInfo] = useState<any>(null)
  const [loadingGithub, setLoadingGithub] = useState(false)
  const [showInterviewModal, setShowInterviewModal] = useState(false)

  const loadData = async () => {
    try {
      const [jobRes, resultsRes] = await Promise.all([
        jobsApi.get(id as string),
        screeningApi.getResults(id as string).catch(() => ({ data: [] })),
      ])
      setJob(jobRes.data)
      setResults(resultsRes.data)
    } catch {} finally { setLoading(false) }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadData() }, [id])

  const onDrop = useCallback(async (files: File[]) => {
    setUploading(true)
    try {
      await resumesApi.upload(id as string, files)
      toast.success(`${files.length} resume(s) uploaded`)
      loadData()
    } catch { toast.error('Upload failed') }
    finally { setUploading(false) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'], 'text/plain': ['.txt'] },
  })

  const runScreening = async () => {
    if ((!job?.resume_count || job.resume_count === 0) && results.length === 0) {
      toast.error('No resumes to screen. Please upload resumes first.')
      return
    }
    
    setScreening(true)
    try {
      await screeningApi.screen(id as string)
      toast.success('Screening complete!')
      loadData()
    } catch { toast.error('Screening failed') }
    finally { setScreening(false) }
  }

  const updateStatus = async (resultId: string, status: string) => {
    try {
      await screeningApi.updateResult(resultId, { status })
      setResults(results.map(r => r.id === resultId ? {...r, status} : r))
      if (selected?.id === resultId) setSelected({...selected, status})
      toast.success(`Status updated to ${status}`)
    } catch { toast.error('Failed to update') }
  }

  const filtered = results
    .filter(r => filter === 'all' || r.status === filter)
    .filter(r => !search || (r.candidate_name || r.filename || '').toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => b.score - a.score)

  const statusBadge = (status: string) => {
    const cls = status === 'shortlisted' ? 'badge-success' : status === 'rejected' ? 'badge-danger' : status === 'interviewed' ? 'badge-info' : 'badge-warning'
    return <span className={`badge ${cls}`}>{status}</span>
  }

  if (loading) return (
    <AppLayout>
      <div className="p-8 md:px-10">
        {[1,2,3].map(i => <div key={i} className="skeleton h-20 mb-2" />)}
      </div>
    </AppLayout>
  )

  return (
    <AppLayout>
      <div className="p-8 md:px-10 max-w-[1100px] mx-auto">
        <Link href="/jobs" className="btn btn-ghost btn-sm mb-4 inline-flex items-center">
          <ArrowLeft size={14} className="mr-1.5" /> Back to Jobs
        </Link>

        {/* Job Header */}
        <div className="mb-6">
          <h1 className="mb-1">{job?.title}</h1>
          <p className="mt-1 text-[var(--text-secondary)]">
            {job?.company && `${job.company} · `}
            {job?.min_years_exp ? `${job.min_years_exp}+ years` : 'Any experience'}
            {job?.required_skills?.length > 0 && ` · ${job.required_skills.length} required skills`}
          </p>
        </div>

        {/* Upload + Screen */}
        <div className="grid grid-cols-[1fr_auto] gap-4 mb-6">
          <div {...getRootProps()} className={`dropzone flex items-center gap-4 py-5 px-6 ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            <Upload size={20} color="var(--text-muted)" className="shrink-0" />
            <div>
              <p className="text-[0.85rem] font-medium text-[var(--text-primary)]">
                {uploading ? 'Uploading...' : isDragActive ? 'Drop files here' : 'Drag & drop resumes, or click to browse'}
              </p>
              <p className="text-[0.75rem] text-[var(--text-muted)] mt-0.5">PDF, DOCX, or TXT</p>
            </div>
          </div>
          <button onClick={runScreening} className="btn btn-primary px-8 self-stretch" disabled={screening}>
            {screening ? <div className="spinner" /> : <><Zap size={16} className="mr-1.5" /> Run Screening</>}
          </button>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <>
            {/* Filters */}
            <div className="flex gap-3 items-center mb-4 flex-wrap">
              <div className="relative flex-1 max-w-[280px]">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                <input className="input pl-9" placeholder="Search candidates..."
                  value={search} onChange={e => setSearch(e.target.value)} />
              </div>
              {['all', 'pending', 'shortlisted', 'rejected', 'interviewed'].map(f => (
                <button key={f} onClick={() => setFilter(f)}
                  className={`btn btn-sm capitalize ${filter === f ? 'btn-primary' : 'btn-secondary'}`}>
                  {f}
                </button>
              ))}
              <button onClick={() => exportResults(results)} className="btn btn-secondary btn-sm ml-auto flex items-center gap-1.5">
                <Download size={14} /> Export CSV
              </button>
            </div>

            {/* Results Table + Detail Panel */}
            <div className={`grid gap-4 ${selected ? 'grid-cols-1 md:grid-cols-[1fr_380px]' : 'grid-cols-1'}`}>
              <div className="card p-0 overflow-hidden">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Score</th>
                      <th>Seniority</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map(r => (
                      <tr 
                        key={r.id} 
                        onClick={() => {
                          setSelected(r)
                          if(r.candidate_id) {
                            setLoadingGithub(true)
                            githubApi.getProfile(r.candidate_id)
                              .then(res => setGithubInfo(res.data))
                              .catch(() => setGithubInfo(null))
                              .finally(() => setLoadingGithub(false))
                          } else {
                            setGithubInfo(null)
                          }
                        }} 
                        className="cursor-pointer transition-colors duration-150" 
                        style={{ background: selected?.id === r.id ? 'var(--hover-row)' : undefined }}
                      >
                        <td>
                          <div className="font-medium">{r.candidate_name || r.filename}</div>
                          {r.candidate_email && <div className="text-[0.72rem] text-[var(--text-muted)] mt-0.5">{r.candidate_email}</div>}
                        </td>
                        <td>
                          <span className={`${getScoreColor(r.score)} font-bold text-[0.95rem]`}>
                            {r.score.toFixed(0)}
                          </span>
                        </td>
                        <td><span className="badge badge-neutral">{r.seniority}</span></td>
                        <td>{statusBadge(r.status)}</td>
                        <td><ChevronRight size={14} color="var(--text-muted)" /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filtered.length === 0 && (
                  <div className="p-8 text-center text-[var(--text-muted)]">
                    No candidates match your filters.
                  </div>
                )}
              </div>

              {/* Detail Panel */}
              {selected && (
                <div className="card sticky top-4 self-start max-h-[calc(100vh-2rem)] overflow-y-auto w-full">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg m-0">{selected.candidate_name || selected.filename}</h3>
                      {selected.candidate_email && <p className="text-[0.78rem] mt-1 text-[var(--text-secondary)]">{selected.candidate_email}</p>}
                    </div>
                    <button onClick={() => setSelected(null)} className="btn btn-ghost btn-sm p-1 ml-2 shrink-0" title="Close panel">
                      <X size={16} />
                    </button>
                  </div>

                  {/* Score */}
                  <div className="text-center py-4 border-b border-[var(--border)] mb-4">
                    <div className={`${getScoreColor(selected.score)} text-4xl font-bold leading-none`}>
                      {selected.score.toFixed(0)}
                    </div>
                    <div className="text-[0.78rem] text-[var(--text-muted)] mt-1.5 flex flex-col gap-1 items-center">
                      <span>{getScoreLabel(selected.score)} · {selected.confidence || 'Medium'} confidence</span>
                      <span className="badge badge-neutral mt-1">{selected.seniority || 'Unknown'} Seniority</span>
                    </div>
                  </div>

                  {/* Strength Tags */}
                  {selected.strength_tags && selected.strength_tags.length > 0 && (
                    <div className="mb-5">
                      <h3 className="text-[0.82rem] mb-2 font-semibold">Match Profile</h3>
                      <div className="flex flex-wrap gap-1.5">
                        {selected.strength_tags.map((tag: string) => (
                          <span key={tag} className="px-2 py-1 rounded-full text-[0.65rem] font-bold tracking-wide uppercase border border-[var(--brand)] text-[var(--brand)] bg-[var(--brand)]/10">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* GitHub Statistics *                    {(() => {
                      const m = typeof githubInfo.metrics === 'string' ? JSON.parse(githubInfo.metrics) : (githubInfo.metrics || {});
                      const t = m.top_projects || [];
                      return (
                        <div className="mb-5 p-4 bg-[#0d1117] text-white rounded-xl border border-[#30363d]">
                          <h3 className="text-[0.82rem] mb-3 flex items-center gap-2 font-semibold text-gray-200">
                            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.2c3-.3 6-1.5 6-6.5a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 5 3 6.2 6 6.5a4.8 4.8 0 0 0-1 3.2v4"></path></svg>
                            GitHub OSS Activity
                          </h3>
                          <div className="grid grid-cols-3 gap-2 mb-4">
                            <div className="text-center p-2 bg-[#161b22] rounded border border-[#30363d]">
                              <div className="text-lg font-bold text-white leading-tight">{m.public_repos || 0}</div>
                              <div className="text-[0.6rem] uppercase tracking-wider text-gray-400 mt-1">Repos</div>
                            </div>
                            <div className="text-center p-2 bg-[#161b22] rounded border border-[#30363d]">
                              <div className="text-lg font-bold text-white leading-tight">{m.followers || 0}</div>
                              <div className="text-[0.6rem] uppercase tracking-wider text-gray-400 mt-1">Followers</div>
                            </div>
                            <div className="text-center p-2 bg-[#161b22] rounded border border-[#30363d]">
                              <div className="text-lg font-bold text-white leading-tight">{m.total_stars || 0}</div>
                              <div className="text-[0.6rem] uppercase tracking-wider text-gray-400 mt-1">Stars</div>
                            </div>
                          </div>
                          {t.length > 0 && (
                            <div className="space-y-2 mt-4 pt-4 border-t border-[#30363d]">
                              <p className="text-[0.7rem] text-gray-400 font-semibold uppercase tracking-widest">Top Repositories</p>
                              <div className="grid gap-2">
                                {t.map((p: any) => (
                                  <div key={p.name} className="flex justify-between items-center text-[0.78rem]">
                                    <a href={p.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline truncate max-w-[170px] font-medium">{p.name}</a>
                                    <span className="text-gray-500 font-mono text-[0.7rem] flex items-center gap-1">⭐ {p.stars}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })()}
  )}

                  {/* AI Narrative Explanation */}
                  {selected.explanation && (
                    <div className="mb-5 p-4 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)]">
                      <h3 className="text-[0.82rem] mb-2 flex items-center gap-1.5 font-semibold text-[var(--brand)]">
                        <Zap size={14} /> Recruiter Summary
                      </h3>
                      <p className="text-[0.82rem] leading-relaxed text-[var(--text-secondary)] italic">
                        &quot;{selected.explanation}&quot;
                      </p>
                    </div>
                  )}

                  {/* Fraud Flags */}
                  {selected.fraud_flags && selected.fraud_flags.length > 0 && (
                    <div className="mb-4 p-3 bg-[var(--danger)]/5 border border-[var(--danger)]/20 rounded-md">
                      <h3 className="text-[0.85rem] text-[var(--danger)] mb-1.5 flex items-center gap-1.5 font-bold">
                        <AlertTriangle size={16} /> Fraud Risk Detected
                      </h3>
                      <div className="flex flex-col gap-1.5">
                        {selected.fraud_flags.map((flag: any, i: number) => (
                          <div key={i} className="text-[0.75rem] text-[var(--text-primary)] flex gap-1.5 items-start">
                            <span className="text-[var(--danger)] shrink-0">•</span>
                            <span>{flag.reason}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Breakdown */}
                  {selected.breakdown && (
                    <div className="mb-4">
                      <h3 className="text-[0.82rem] mb-3 font-semibold">Score Breakdown</h3>
                      {Object.entries(BREAKDOWN_LABELS)
                        .filter(([key]) => selected.breakdown[key] !== undefined)
                        .map(([key, meta]) => (
                          <div key={key} className="mb-2.5">
                            <div className="flex justify-between text-[0.78rem] mb-1">
                              <span className="text-[var(--text-secondary)]">{meta.label}</span>
                              <span className={`${getProgressColor(selected.breakdown[key])} font-semibold`}>
                                {selected.breakdown[key].toFixed(0)} <span className="font-normal text-[var(--text-muted)] text-[0.68rem]">({meta.weight})</span>
                              </span>
                            </div>
                            <div className="progress-track">
                              <div className="progress-fill" style={{ width: `${selected.breakdown[key]}%`, background: getProgressColor(selected.breakdown[key]) }} />
                            </div>
                          </div>
                        ))}
                    </div>
                  )}

                  {/* Skills */}
                  {(selected.matched_skills?.length > 0 || selected.missing_skills?.length > 0) && (
                    <div className="mb-5">
                      <h3 className="text-[0.82rem] mb-2 font-semibold">Skills</h3>
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
                      <h3 className="text-[0.82rem] mb-3 flex items-center gap-1.5 font-semibold">
                        <span className="text-[var(--brand)]">✨</span> AI Project Analysis
                      </h3>
                      <div className="grid gap-3">
                        {selected.project_evaluations.map((proj: any, idx: number) => (
                          <div key={idx} className="bg-[var(--bg-secondary)] p-3 rounded-lg border-l-4" style={{ 
                            borderLeftColor: proj.complexity_level === 'High' ? 'var(--purple)' : proj.complexity_level === 'Medium' ? 'var(--brand)' : 'var(--border)'
                          }}>
                            <div className="font-semibold text-[0.85rem] mb-1.5 flex justify-between items-start">
                              <span className="truncate max-w-[70%]">{proj.project_name}</span>
                              <span className="text-[0.75rem] text-[var(--text-muted)] shrink-0 ml-2">Score: {proj.innovation_impact_score}</span>
                            </div>
                            
                            <div className="flex gap-2 mb-2">
                              <span className="badge badge-neutral text-[0.65rem] px-1.5 py-0.5">{proj.complexity_level} Complexity</span>
                              <span className="badge badge-neutral text-[0.65rem] px-1.5 py-0.5">{proj.relevance_to_job}% Match</span>
                            </div>

                            {proj.core_technologies?.length > 0 && (
                              <div className="text-[0.75rem] text-[var(--text-secondary)] mb-2">
                                <strong>Tech:</strong> {proj.core_technologies.slice(0, 4).join(', ')}
                                {proj.core_technologies.length > 4 ? '...' : ''}
                              </div>
                            )}

                            {proj.description_snippet && (
                              <p className="text-[0.72rem] text-[var(--text-muted)] italic mb-2 line-clamp-2">
                                &quot;{proj.description_snippet}&quot;
                              </p>
                            )}

                            {proj.suggestions?.length > 0 && (
                              <div className="text-[0.72rem] text-[var(--text-muted)] bg-[var(--bg-primary)] p-1.5 rounded mt-2">
                                💡 {proj.suggestions[0]}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2 flex-wrap border-t border-[var(--border)] pt-4 mt-2">
                    <button onClick={() => updateStatus(selected.id, 'shortlisted')}
                      className={`btn btn-sm ${selected.status === 'shortlisted' ? 'btn-primary' : 'btn-secondary'}`}>
                      Shortlist
                    </button>
                    <button onClick={() => setShowInterviewModal(true)}
                      className={`btn btn-sm flex items-center gap-1 ${selected.status === 'interviewed' ? 'btn-primary' : 'btn-secondary'}`}>
                      <Calendar size={14} /> Interview
                    </button>
                    <button onClick={() => updateStatus(selected.id, 'rejected')}
                      className={`btn btn-sm ${selected.status === 'rejected' ? 'btn-danger' : 'btn-secondary'}`}>
                      Reject
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {results.length === 0 && !loading && (
          <div className="card text-center p-12 mt-6">
            <div className="flex justify-center mb-3">
              <FileText size={32} color="var(--text-muted)" />
            </div>
            <h3 className="mb-2">No results yet</h3>
            <p className="text-[var(--text-secondary)]">Upload resumes above, then click &quot;Run Screening&quot; to get AI-powered results.</p>
          </div>
        )}

        {showInterviewModal && selected && (
          <InterviewModal
            resultId={selected.id}
            candidateName={selected.candidate_name || selected.filename}
            onClose={() => setShowInterviewModal(false)}
            onScheduled={() => {
              loadData()
              setSelected({ ...selected, status: 'interviewed' })
            }}
          />
        )}
      </div>
    </AppLayout>
  )
}
