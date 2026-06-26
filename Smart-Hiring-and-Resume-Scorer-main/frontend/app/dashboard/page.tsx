'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import AppLayout from '@/components/layout/AppLayout'
import { jobsApi, interviewsApi, searchApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Briefcase, FileText, BarChart3, Plus, ArrowRight, Calendar, Video, Search, User as UserIcon } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [jobs, setJobs] = useState<any[]>([])
  const [interviews, setInterviews] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Semantic Search State
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  
  const handleSemanticSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const { data } = await searchApi.semanticSearch(searchQuery)
      setSearchResults(data.results || [])
    } catch (err) {
      console.error("Semantic search failed:", err)
    } finally {
      setSearching(false)
    }
  }

  useEffect(() => {
    Promise.all([
      jobsApi.list().catch(() => ({ data: [] })),
      interviewsApi.getMyInterviews().catch(() => ({ data: [] }))
    ]).then(([jobsRes, interviewsRes]) => {
      setJobs(jobsRes.data)
      setInterviews(interviewsRes.data.filter((i: any) => i.status !== 'cancelled'))
      setLoading(false)
    })
  }, [])

  const stats = [
    { icon: Briefcase, label: 'Active Jobs', value: jobs.length, color: 'var(--brand)' },
    { icon: FileText, label: 'Total Resumes', value: jobs.reduce((s, j) => s + (j.resume_count || 0), 0), color: 'var(--success)' },
    { icon: BarChart3, label: 'Screenings', value: jobs.reduce((s, j) => s + (j.result_count || 0), 0), color: 'var(--warning)' },
  ]

  return (
    <AppLayout>
      <div className="p-8 md:px-10 max-w-[960px] mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="mb-1">Welcome back{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}</h1>
          <p className="mt-1.5 text-[var(--text-secondary)]">Here&apos;s an overview of your screening pipeline.</p>
        </div>

        {/* Stats */}
        <div className="stat-grid grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {loading ? (
            [1,2,3].map(i => <div key={i} className="skeleton h-[100px]" />)
          ) : (
            stats.map(stat => (
              <div key={stat.label} className="stat-card">
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon size={16} color={stat.color} />
                  <span className="stat-label mt-0 text-[var(--text-secondary)]">{stat.label}</span>
                </div>
                <div className="stat-value text-3xl font-bold" style={{ color: stat.color }}>{stat.value}</div>
              </div>
            ))
          )}
        </div>

        {/* Semantic Candidate Search */}
        <div className="card mb-8 border-l-4 border-l-[var(--brand)]">
          <h3 className="flex items-center gap-2 mb-2">
            <Search size={16} color="var(--brand)" /> AI Semantic Candidate Search
          </h3>
          <p className="text-[0.85rem] text-[var(--text-muted)] mb-4">
            Search naturally across all uploaded resumes (e.g., &quot;Looking for a senior frontend dev fluent in React and animations&quot;)
          </p>
          <form onSubmit={handleSemanticSearch} className="flex gap-2 mb-4">
            <input 
              className="input flex-1" 
              placeholder="Describe the candidate you need..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="btn btn-primary px-6" disabled={searching || !searchQuery.trim()}>
              {searching ? <div className="spinner" /> : 'Search'}
            </button>
          </form>

          {searchResults.length > 0 && (
            <div className="grid gap-3 mt-4">
              <h4 className="text-sm font-semibold mb-2 text-[var(--text-secondary)]">Top Matches</h4>
              {searchResults.map((cand, idx) => (
                <div key={cand.id} className="flex flex-wrap justify-between items-center p-3 sm:px-4 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center text-[var(--text-muted)]">
                      <UserIcon size={14} />
                    </div>
                    <div>
                      <div className="font-semibold text-[0.9rem] flex items-center gap-2">
                        {cand.filename || 'Candidate Profile'}
                        <span className="text-[0.7rem] bg-[var(--success)]/10 text-[var(--success)] px-1.5 py-0.5 rounded">
                          {(cand.similarity * 100).toFixed(1)}% Match
                        </span>
                      </div>
                      <div className="text-[0.75rem] text-[var(--text-muted)] mt-1 max-w-[400px] truncate">
                        {cand.extracted_skills?.slice(0, 6).join(' • ') || 'No specific skills extracted'}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upcoming Interviews */}
        {interviews.length > 0 && (
          <div className="card mb-8 border-l-4 border-l-[var(--purple)]">
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
                        <span className="font-semibold block text-[var(--text-primary)]">Notes:</span>
                        {inv.notes}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Jobs */}
        <div className="card p-0 overflow-hidden">
          <div className="py-4 px-5 flex justify-between items-center border-b border-[var(--border)]">
            <h3 className="m-0 text-lg">Recent Jobs</h3>
            <Link href="/jobs/new" className="btn btn-primary btn-sm inline-flex items-center">
              <Plus size={14} className="mr-1" /> New Job
            </Link>
          </div>

          {loading ? (
            <div className="p-5">
              {[1,2,3].map(i => <div key={i} className="skeleton h-12 mb-1" />)}
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-[var(--text-muted)] mb-4">No jobs created yet.</p>
              <Link href="/jobs/new" className="btn btn-primary btn-sm">Create your first job</Link>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>Company</th>
                  <th>Resumes</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {jobs.slice(0, 5).map(job => (
                  <tr key={job.id} className="transition-colors hover:bg-[var(--hover-row)] duration-150">
                    <td className="font-medium">{job.title}</td>
                    <td className="text-[var(--text-muted)]">{job.company || '—'}</td>
                    <td><span className="badge badge-neutral">{job.resume_count || 0}</span></td>
                    <td className="text-[var(--text-muted)] text-[0.8rem]">{formatDate(job.created_at)}</td>
                    <td className="text-right">
                      <Link href={`/jobs/${job.id}`} className="btn btn-ghost btn-sm inline-flex items-center hover:bg-[var(--bg-primary)]">
                        View <ArrowRight size={14} className="ml-1.5" />
                      </Link>
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
