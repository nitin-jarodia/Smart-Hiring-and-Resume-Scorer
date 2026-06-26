'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import AppLayout from '@/components/layout/AppLayout'
import { jobsApi } from '@/lib/api'
import { ArrowLeft, Plus, X } from 'lucide-react'
import toast from 'react-hot-toast'
import Link from 'next/link'

const SAMPLE_JD = `Senior Backend Engineer

We are looking for a Senior Backend Engineer to join our platform team. 
You will design and build scalable microservices, optimize databases, and lead technical initiatives.

Requirements:
- 5+ years of backend development experience
- Strong proficiency in Python, PostgreSQL, and Redis
- Experience with AWS, Docker, and Kubernetes
- Familiarity with microservices architecture and REST API design
- BS/MS in Computer Science or equivalent

Nice to have:
- Experience with Go or Rust
- Knowledge of Terraform and infrastructure as code
- GraphQL experience`

export default function NewJobPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    title: '', company: '', min_years_exp: '', jd_text: '', required_skills: [] as string[],
  })
  const [skillInput, setSkillInput] = useState('')

  const addSkill = () => {
    const skill = skillInput.trim().toLowerCase()
    if (skill && !form.required_skills.includes(skill)) {
      setForm({...form, required_skills: [...form.required_skills, skill]})
      setSkillInput('')
    }
  }

  const removeSkill = (s: string) => {
    setForm({...form, required_skills: form.required_skills.filter(x => x !== s)})
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = {
        ...form,
        min_years_exp: form.min_years_exp ? parseInt(form.min_years_exp) : 0,
      }
      const res = await jobsApi.create(data)
      toast.success('Job created!')
      router.push(`/jobs/${res.data.id}`)
    } catch { toast.error('Failed to create job') }
    finally { setLoading(false) }
  }

  return (
    <AppLayout>
      <div className="p-8 md:px-10 max-w-[700px] mx-auto">
        <Link href="/jobs" className="btn btn-ghost btn-sm mb-4 inline-flex items-center">
          <ArrowLeft size={14} className="mr-1.5" /> Back to Jobs
        </Link>

        <h1 className="mb-1.5">Create a new job</h1>
        <p className="mb-8 text-[var(--text-secondary)]">Set up a job description to screen candidates against.</p>

        <form onSubmit={handleSubmit}>
          <div className="card mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label>Job Title *</label>
                <input className="input" placeholder="e.g. Senior Backend Engineer"
                  value={form.title} onChange={e => setForm({...form, title: e.target.value})} required />
              </div>
              <div>
                <label>Company</label>
                <input className="input" placeholder="e.g. Acme Corp"
                  value={form.company} onChange={e => setForm({...form, company: e.target.value})} />
              </div>
            </div>

            <div className="mb-4">
              <label>Minimum Experience (years)</label>
              <input className="input max-w-[160px]" type="number" min="0" placeholder="e.g. 5"
                value={form.min_years_exp} onChange={e => setForm({...form, min_years_exp: e.target.value})} />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="mb-0">Job Description *</label>
                <button type="button" className="btn btn-ghost btn-sm text-[0.72rem]"
                  onClick={() => setForm({...form, jd_text: SAMPLE_JD, title: form.title || 'Senior Backend Engineer', company: form.company || 'Acme Corp', min_years_exp: form.min_years_exp || '5'})}>
                  Load sample
                </button>
              </div>
              <textarea className="input" rows={8} placeholder="Paste the job description here..."
                value={form.jd_text} onChange={e => setForm({...form, jd_text: e.target.value})} required />
            </div>
          </div>

          <div className="card mb-6">
            <label>Required Skills</label>
            <p className="text-[0.78rem] text-[var(--text-muted)] mb-3">
              Add skills manually, or they&apos;ll be auto-extracted from the job description.
            </p>
            <div className="flex gap-2 mb-3">
              <input className="input" placeholder="e.g. python"
                value={skillInput} onChange={e => setSkillInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addSkill() } }} />
              <button type="button" className="btn btn-secondary" onClick={addSkill} title="Add Skill">
                <Plus size={14} />
              </button>
            </div>
            {form.required_skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {form.required_skills.map(s => (
                  <span key={s} className="badge badge-brand cursor-pointer flex items-center gap-1"
                    onClick={() => removeSkill(s)}>
                    {s} <X size={10} />
                  </span>
                ))}
              </div>
            )}
          </div>

          <button type="submit" className="btn btn-primary px-8 py-2.5" disabled={loading}>
            {loading ? <div className="spinner" /> : 'Create Job'}
          </button>
        </form>
      </div>
    </AppLayout>
  )
}
