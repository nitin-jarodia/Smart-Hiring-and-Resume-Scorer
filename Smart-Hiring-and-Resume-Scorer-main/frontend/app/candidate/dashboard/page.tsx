'use client'
import { useEffect, useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import { candidateApi, interviewsApi } from '@/lib/api'
import { getScoreColor, getProgressColor, formatDate } from '@/lib/utils'
import { Upload, TrendingUp, BookOpen, Briefcase, ChevronRight, AlertCircle, CheckCircle, Lightbulb, Calendar, Video, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

export default function CandidateDashboard() {
  const [profile, setProfile] = useState<any>(null)
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [skills, setSkills] = useState<any[]>([])
  const [tips, setTips] = useState<any[]>([])
  const [interviews, setInterviews] = useState<any[]>([])
  
  // GitHub state
  const [githubInfo, setGithubInfo] = useState<any>(null)
  const [githubInput, setGithubInput] = useState('')
  const [syncingGithub, setSyncingGithub] = useState(false)
  const [githubLinked, setGithubLinked] = useState(false)
  
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAll()
  }, [])

  const loadAll = async () => {
    try {
      const [profileRes, recsRes, skillsRes, tipsRes, interviewsRes] = await Promise.all([
        candidateApi.getProfile().catch(() => ({ data: { has_profile: false } })),
        candidateApi.getRecommendations().catch(() => ({ data: [] })),
        candidateApi.getSkillSuggestions().catch(() => ({ data: [] })),
        candidateApi.getResumeTips().catch(() => ({ data: [] })),
        interviewsApi.getMyInterviews().catch(() => ({ data: [] })),
      ])
      setProfile(profileRes.data)
      setRecommendations(recsRes.data.slice(0, 5))
      setSkills(skillsRes.data.slice(0, 10))
      setTips(tipsRes.data)
      setInterviews(interviewsRes.data.filter((i: any) => i.status !== 'cancelled'))
      
      if (profileRes.data?.id) {
        import('@/lib/api').then(({ githubApi }) => {
           githubApi.getProfile(profileRes.data.id)
             .then(res => setGithubInfo(res.data))
             .catch(() => setGithubInfo(null))
        })
      }
    } catch {} finally { setLoading(false) }
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
        <h1 className="mb-1">Candidate Dashboard</h1>
        <p className="mb-6 text-[var(--text-secondary)]">Your resume insights and job recommendations</p>

        {/* No Resume Prompt */}
        {!profile?.has_profile && (
          <div className="card text-center p-12">
            <div className="flex justify-center mb-4">
              <Upload size={36} color="var(--text-muted)" />
            </div>
            <h3 className="mb-2">Upload Your Resume</h3>
            <p className="mb-6 text-[var(--text-secondary)]">Get AI-powered score, job recommendations, and skill suggestions</p>
            <Link href="/candidate/resume" className="btn btn-primary">Upload Resume</Link>
          </div>
        )}

        {profile?.has_profile && (
          <>
            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="card text-center border-b-4 border-b-[var(--brand)]">
                <div className={`${getScoreColor(profile.overall_score || 0)} text-3xl font-bold leading-none`}>
                  {(profile.overall_score || 0).toFixed(0)}
                </div>
                <p className="text-[0.7rem] uppercase tracking-wider text-[var(--text-muted)] mt-2">Overall Score</p>
              </div>
              <div className="card text-center border-b-4 border-b-[var(--purple)]">
                <div className="text-2xl font-bold text-[var(--purple)]">
                  {profile.seniority || 'Analyzing...'}
                </div>
                <p className="text-[0.7rem] uppercase tracking-wider text-[var(--text-muted)] mt-2">Career Level</p>
              </div>
              <div className="card text-center border-b-4 border-b-[var(--accent)]">
                <div className="text-3xl font-bold text-[var(--accent)]">
                  {(profile.extracted_skills || []).length}
                </div>
                <p className="text-[0.7rem] uppercase tracking-wider text-[var(--text-muted)] mt-2">Skills Found</p>
              </div>
              <div className="card text-center border-b-4 border-b-[var(--teal)]">
                <div className="text-3xl font-bold text-[var(--teal)]">
                  {recommendations.length}
                </div>
                <p className="text-[0.7rem] uppercase tracking-wider text-[var(--text-muted)] mt-2">Job Matches</p>
              </div>
            </div>

            {/* AI Profile Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="card">
                <h3 className="text-[0.82rem] mb-3 font-semibold flex items-center gap-2">
                  <TrendingUp size={16} /> Market Readiness Breakdown
                </h3>
                {profile.breakdown && Object.entries(profile.breakdown).filter(([k]) => k !== 'total').map(([key, value]: [string, any]) => (
                  <div key={key} className="mb-3">
                    <div className="flex justify-between text-[0.78rem] mb-1">
                      <span className="capitalize">{key.replace('_', ' ')}</span>
                      <span className={`${getProgressColor(value)} font-semibold`}>{value.toFixed(0)}%</span>
                    </div>
                    <div className="progress-track">
                      <div className="progress-fill" style={{ width: `${value}%`, background: getProgressColor(value) }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="card">
                <h3 className="text-[0.82rem] mb-2 font-semibold flex items-center gap-2">
                  <Lightbulb size={16} /> Profile Summary
                </h3>
                <p className="text-[0.85rem] leading-relaxed text-[var(--text-secondary)] italic mb-4">
                  &quot;{profile.explanation || "Your resume is currently being analyzed to provide personalized career insights."}&quot;
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {(profile.strength_tags || []).map((tag: string) => (
                    <span key={tag} className="px-2 py-1 rounded-full text-[0.65rem] font-bold tracking-wide uppercase border border-[var(--brand)] text-[var(--brand)] bg-[var(--brand)]/10">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* GitHub Integration */}
            <div className="card mb-6 border-l-4 border-l-[var(--text-primary)]">
              <div className="flex justify-between items-center mb-4">
                 <h3 className="flex items-center gap-2">
                   <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.2c3-.3 6-1.5 6-6.5a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 5 3 6.2 6 6.5a4.8 4.8 0 0 0-1 3.2v4"></path></svg> 
                   GitHub Profile Analyzer
                 </h3>
              </div>
              
              {!githubInfo?.has_github ? (
                <div>
                  <p className="text-[0.85rem] text-[var(--text-muted)] mb-3">
                    Connect your GitHub to showcase your open-source activity, top languages, and total stars to recruiters.
                  </p>
                  <form className="flex gap-2" onSubmit={(e) => {
                    e.preventDefault()
                    if(!githubInput.trim() || !githubInput.includes('github.com')) return toast.error("Enter a valid GitHub URL")
                    setSyncingGithub(true)
                    import('@/lib/api').then(({ githubApi }) => {
                      githubApi.submitProfile(githubInput).then(() => {
                        toast.success("GitHub linked! Analysis running — hit 'Refresh Status' in ~10s.")
                        setGithubInput('')
                        setGithubLinked(true)
                      }).catch(() => {
                        toast.error("Failed to link GitHub. Check the URL and try again.")
                      }).finally(() => setSyncingGithub(false))
                    })
                  }}>
                    <input className="input flex-1" placeholder="https://github.com/username" value={githubInput} onChange={e=>setGithubInput(e.target.value)} />
                    <button type="submit" className="btn btn-primary" disabled={syncingGithub || !githubInput}>
                      {syncingGithub ? "Linking..." : "Link GitHub"}
                    </button>
                  </form>
                  {githubLinked && !githubInfo?.id && (
                    <div className="mt-4 text-center">
                      <button onClick={loadAll} className="btn btn-secondary btn-sm inline-flex items-center">
                        <RefreshCw size={14} className="mr-1.5" /> Refresh Status
                      </button>
                      <p className="text-[0.75rem] text-[var(--text-muted)] mt-2">
                        It might take a few moments for your GitHub profile to be analyzed.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                   <div className="flex gap-4 mb-4">
                     <a href={githubInfo.github_url} target="_blank" rel="noreferrer" className="text-[var(--accent)] font-semibold underline">@{githubInfo.username}</a>
                     <span className="text-[0.8rem] text-[var(--text-muted)]">Last synced: {formatDate(githubInfo.updated_at)}</span>
                   </div>
                   <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 bg-[var(--bg-secondary)] rounded-lg text-center border border-[var(--border)]">
                        <div className="text-xl font-bold">{githubInfo.metrics?.public_repos || 0}</div>
                        <div className="text-[0.7rem] uppercase tracking-wider text-[var(--text-muted)] mt-1">Public Repos</div>
                      </div>
                      <div className="p-3 bg-[var(--bg-secondary)] rounded-lg text-center border border-[var(--border)]">
                        <div className="text-xl font-bold">{githubInfo.metrics?.followers || 0}</div>
                        <div className="text-[0.7rem] uppercase tracking-wider text-[var(--text-muted)] mt-1">Followers</div>
                      </div>
                      <div className="p-3 bg-[var(--bg-secondary)] rounded-lg text-center border border-[var(--border)]">
                        <div className="text-xl font-bold">{githubInfo.metrics?.total_stars || 0}</div>
                        <div className="text-[0.7rem] uppercase tracking-wider text-[var(--text-muted)] mt-1">Total Stars</div>
                      </div>
                   </div>
                   {githubInfo.top_languages && Object.keys(githubInfo.top_languages).length > 0 && (
                     <div className="mt-4">
                       <h4 className="text-[0.8rem] font-semibold mb-2 text-[var(--text-secondary)]">Top Languages</h4>
                       <div className="flex flex-wrap gap-2">
                         {Object.entries(githubInfo.top_languages).map(([lang, count]) => (
                           <span key={lang} className="badge badge-neutral bg-[var(--bg-tertiary)]">{lang}</span>
                         ))}
                       </div>
                     </div>
                   )}
                   {(() => {
                      const m = typeof githubInfo.metrics === 'string' ? JSON.parse(githubInfo.metrics) : (githubInfo.metrics || {});
                      const t = m.top_projects || [];
                      if (t.length === 0) return null;
                      return (
                        <div className="mt-4">
                          <h4 className="text-[0.8rem] font-semibold mb-2 text-[var(--text-secondary)]">Top Projects</h4>
                          <div className="grid gap-2">
                            {t.map((p: any) => (
                              <div key={p.name} className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)]">
                                <div className="flex justify-between items-start mb-1">
                                  <a href={p.url} target="_blank" rel="noreferrer" className="text-[0.85rem] font-semibold hover:underline text-[var(--accent)]">{p.name}</a>
                                  <span className="text-[0.7rem] text-[var(--text-muted)] flex items-center gap-1">⭐ {p.stars}</span>
                                </div>
                                {p.description && <p className="text-[0.75rem] text-[var(--text-muted)] line-clamp-2 mb-2">{p.description}</p>}
                                {p.language && <span className="text-[0.65rem] badge badge-neutral py-0 px-1.5">{p.language}</span>}
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })()}
                </div>
              )}
            </div>

            {/* Upcoming Interviews */}
            {interviews.length > 0 && (
              <div className="card mb-6 border-l-4 border-l-[var(--purple)]">
                <h3 className="flex items-center gap-2 mb-4">
                  <Calendar size={16} color="var(--purple)" /> Upcoming Interviews
                </h3>
                <div className="grid gap-3">
                  {interviews.map(inv => (
                    <div key={inv.id} className="flex flex-wrap justify-between items-center p-4 bg-[var(--bg-secondary)] rounded-lg">
                      <div>
                        <div className="font-semibold text-[0.95rem] mb-1">
                          {new Date(inv.scheduled_at).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })} at {new Date(inv.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                        <div className="text-[0.82rem] text-[var(--text-muted)]">
                          {inv.duration_minutes} minutes
                        </div>
                      </div>
                      <div className="flex gap-3 items-center mt-3 sm:mt-0">
                        {inv.meeting_link && (
                          <a href={inv.meeting_link} target="_blank" rel="noreferrer" className="btn btn-primary btn-sm inline-flex items-center">
                            <Video size={14} className="mr-1.5" /> Join Meeting
                          </a>
                        )}
                        {inv.notes && (
                          <div className="text-[0.75rem] max-w-[220px] text-[var(--text-muted)] border-l-2 border-[var(--border)] pl-2">
                            <span className="font-semibold block">Notes:</span>
                            {inv.notes}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Two Column: Recommendations + Skills */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Job Recommendations */}
              <div className="card">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="flex items-center gap-2">
                    <Briefcase size={16} /> Top Job Matches
                  </h3>
                  <Link href="/candidate/jobs" className="text-[0.72rem] text-[var(--accent)] hover:underline">View all</Link>
                </div>
                {recommendations.length === 0 && <p className="text-[var(--text-muted)] text-[0.82rem]">No jobs available yet</p>}
                {recommendations.map((rec, i) => (
                  <div key={rec.job_id} className={`flex justify-between items-center py-2.5 ${i < recommendations.length - 1 ? 'border-b border-[var(--border)]' : ''}`}>
                    <div>
                      <div className="text-[0.85rem] font-medium">{rec.title}</div>
                      <div className="text-[0.72rem] text-[var(--text-muted)]">{rec.company}</div>
                    </div>
                    <span className={`${getScoreColor(rec.match_percent)} font-bold text-[0.85rem]`}>
                      {rec.match_percent.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>

              {/* Skills to Learn */}
              <div className="card">
                <h3 className="flex items-center gap-2 mb-4">
                  <TrendingUp size={16} /> Skills to Learn
                </h3>
                {skills.length === 0 && <p className="text-[var(--text-muted)] text-[0.82rem]">Upload resume to get suggestions</p>}
                <div className="flex flex-col gap-1.5">
                  {skills.map(s => (
                    <div key={s.skill} className="flex flex-col py-1.5 border-b border-[var(--border)]">
                      <div className="flex justify-between items-center">
                        <span className="text-[0.85rem] font-medium">{s.skill}</span>
                        <span className={`badge ${s.priority === 'high' ? 'badge-danger' : s.priority === 'medium' ? 'badge-warning' : 'badge-neutral'}`}>
                          {s.priority}
                        </span>
                      </div>
                      {s.reason && (
                        <div className="text-[0.72rem] text-[var(--text-muted)] mt-1">
                          {s.reason}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Resume Tips */}
            {tips.length > 0 && (
              <div className="card">
                <h3 className="flex items-center gap-2 mb-4">
                  <Lightbulb size={16} /> Resume Improvement Tips
                </h3>
                <div className="flex flex-col gap-2.5">
                  {tips.map((tip, i) => (
                    <div key={i} className="flex gap-3 items-start p-2.5 bg-[var(--bg-secondary)] rounded">
                      {tip.impact === 'high' ? <AlertCircle size={16} color="var(--ember)" className="shrink-0 mt-0.5" /> :
                       tip.impact === 'medium' ? <Lightbulb size={16} color="var(--warning)" className="shrink-0 mt-0.5" /> :
                       <CheckCircle size={16} color="var(--teal)" className="shrink-0 mt-0.5" />}
                      <div>
                        <span className="badge badge-neutral mb-1 block w-fit">{tip.category}</span>
                        <p className="text-[0.82rem] leading-relaxed">{tip.tip}</p>
                      </div>
                    </div>
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
