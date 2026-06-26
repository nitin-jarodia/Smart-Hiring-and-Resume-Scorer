'use client'
import { useEffect, useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import { candidateApi } from '@/lib/api'
import { getScoreColor } from '@/lib/utils'
import { Briefcase, Search, MapPin, Clock, Send, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function CandidateJobsPage() {
  const [jobs, setJobs] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState<string | null>(null)

  useEffect(() => { loadJobs() }, [])

  const loadJobs = async () => {
    try {
      const [jobsRes, recsRes] = await Promise.all([
        candidateApi.getPublicJobs(),
        candidateApi.getRecommendations().catch(() => ({ data: [] })),
      ])
      // Merge match data from recommendations
      const recsMap = new Map<string, any>(recsRes.data.map((r: any) => [r.job_id, r]))
      const merged = jobsRes.data.map((j: any) => ({
        ...j,
        match_percent: recsMap.get(j.id)?.match_percent ?? null,
        matched_skills: recsMap.get(j.id)?.matched_skills ?? [],
        missing_skills: recsMap.get(j.id)?.missing_skills ?? [],
        already_applied: recsMap.get(j.id)?.already_applied ?? false,
      }))
      // Sort: matched jobs first
      merged.sort((a: any, b: any) => (b.match_percent ?? -1) - (a.match_percent ?? -1))
      setJobs(merged)
    } catch {} finally { setLoading(false) }
  }

  const applyToJob = async (jobId: string) => {
    setApplying(jobId)
    try {
      const res = await candidateApi.apply(jobId)
      toast.success(res.data.message)
      loadJobs()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to apply')
    } finally { setApplying(null) }
  }

  const filtered = jobs.filter(j =>
    !search || j.title.toLowerCase().includes(search.toLowerCase()) ||
    j.company.toLowerCase().includes(search.toLowerCase()) ||
    (j.required_skills || []).some((s: string) => s.toLowerCase().includes(search.toLowerCase()))
  )

  if (loading) return (
    <AppLayout>
      <div className="p-8 md:px-10">
        {[1,2,3].map(i => <div key={i} className="skeleton h-[120px] mb-3" />)}
      </div>
    </AppLayout>
  )

  return (
    <AppLayout>
      <div className="p-8 md:px-10 max-w-[900px] mx-auto">
        <h1 className="mb-1">Browse Jobs</h1>
        <p className="mb-6 text-[var(--text-secondary)]">Find jobs that match your skills</p>

        {/* Search */}
        <div className="relative mb-6">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input className="input pl-9 w-full" placeholder="Search by title, company, or skills..."
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        {/* Job Cards */}
        <div className="flex flex-col gap-3">
          {filtered.map(job => (
            <div key={job.id} className="card p-5">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1.5">
                    <h3 className="text-base m-0">{job.title}</h3>
                    {job.match_percent !== null && (
                      <span className={`badge ${job.match_percent >= 70 ? 'badge-success' : job.match_percent >= 40 ? 'badge-warning' : 'badge-danger'}`}>
                        {job.match_percent.toFixed(0)}% match
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-4 text-[0.78rem] text-[var(--text-muted)] mb-2.5">
                    {job.company && <span className="flex items-center gap-1.5"><Briefcase size={12} />{job.company}</span>}
                    <span className="flex items-center gap-1.5"><Clock size={12} />{job.min_years_exp}+ years</span>
                    <span>{job.application_count} applied</span>
                  </div>

                  {/* Skills */}
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {(job.matched_skills || []).map((s: string) => (
                      <span key={s} className="badge badge-success">{s}</span>
                    ))}
                    {(job.missing_skills || []).map((s: string) => (
                      <span key={s} className="badge badge-neutral">{s}</span>
                    ))}
                    {job.match_percent === null && (job.required_skills || []).map((s: string) => (
                      <span key={s} className="badge badge-neutral">{s}</span>
                    ))}
                  </div>
                </div>

                {/* Apply Button */}
                <div className="shrink-0 ml-4">
                  {job.already_applied ? (
                    <button className="btn btn-sm btn-secondary flex items-center gap-1" disabled>
                      <CheckCircle size={14} /> Applied
                    </button>
                  ) : (
                    <button className="btn btn-sm btn-primary flex items-center gap-1" disabled={applying === job.id}
                      onClick={() => applyToJob(job.id)}>
                      {applying === job.id ? <div className="spinner" /> : <><Send size={14} /> Apply</>}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}

          {filtered.length === 0 && (
            <div className="card text-center p-12 text-[var(--text-muted)]">
              No jobs found matching your search.
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
