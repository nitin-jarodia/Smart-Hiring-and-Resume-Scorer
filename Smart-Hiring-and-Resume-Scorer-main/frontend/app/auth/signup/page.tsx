'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { FileText, Eye, EyeOff, AlertCircle, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SignupPage() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'recruiter' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPw, setShowPw] = useState(false)
  const router = useRouter()
  const { setAuth } = useAuthStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await authApi.signup(form.email, form.password, form.full_name, form.role)
      setAuth(res.data.user, res.data.access_token)
      toast.success('Account created!')
      router.push(res.data.user.role === 'candidate' ? '/candidate/dashboard' : '/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg)] p-8">
      <div className="w-full max-w-[400px]">
        <Link href="/" className="inline-flex items-center gap-2 text-[0.85rem] text-[var(--text-muted)] no-underline mb-8 transition-colors duration-200 hover:text-[var(--text-primary)]">
          <ArrowLeft size={16} /> Back to Home
        </Link>

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-10 h-10 bg-[var(--brand)] rounded-[10px] inline-flex items-center justify-center mb-3">
            <FileText size={20} color="#fff" />
          </div>
          <h1 className="text-[1.4rem] mb-1.5">Create an account</h1>
          <p>Get started with ScreenerAI</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="flex gap-2 items-center p-3 bg-[rgba(201,75,75,0.08)] rounded-lg mb-5 text-[0.82rem] text-[var(--danger)]">
                <AlertCircle size={14} /> {error}
              </div>
            )}

            <div className="mb-4">
              <label>Full name</label>
              <input type="text" className="input" placeholder="Jane Smith"
                value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})} required />
            </div>

            <div className="mb-4">
              <label>Email</label>
              <input type="email" className="input" placeholder="you@company.com"
                value={form.email} onChange={e => setForm({...form, email: e.target.value})} required />
            </div>

            <div className="mb-4">
              <label>Password</label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'}
                  placeholder="At least 6 characters" value={form.password}
                  onChange={e => setForm({...form, password: e.target.value})} required minLength={6}
                  className="input pr-10" />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-2.5 top-1/2 -translate-y-1/2 bg-transparent border-none cursor-pointer text-[var(--text-muted)] p-1">
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="mb-6">
              <label>I am...</label>
              <div className="grid grid-cols-2 gap-3 mt-1.5">
                <button type="button" onClick={() => setForm({...form, role: 'recruiter'})}
                  className={`card p-4 text-center cursor-pointer ${form.role === 'recruiter' ? 'border-2 border-[var(--brand)] bg-[var(--brand-soft)]' : 'border-2 border-[var(--border)] bg-transparent'}`}>
                  <div className="text-[1.5rem] mb-1">👔</div>
                  <div className="text-[0.82rem] font-semibold">Hiring</div>
                  <div className="text-[0.68rem] text-[var(--text-muted)]">I&apos;m a recruiter</div>
                </button>
                <button type="button" onClick={() => setForm({...form, role: 'candidate'})}
                  className={`card p-4 text-center cursor-pointer ${form.role === 'candidate' ? 'border-2 border-[var(--brand)] bg-[var(--brand-soft)]' : 'border-2 border-[var(--border)] bg-transparent'}`}>
                  <div className="text-[1.5rem] mb-1">🎓</div>
                  <div className="text-[0.82rem] font-semibold">Looking for work</div>
                  <div className="text-[0.68rem] text-[var(--text-muted)]">I&apos;m a candidate</div>
                </button>
              </div>
            </div>

            <button type="submit" className="btn btn-primary w-full p-3" disabled={loading}>
              {loading ? <div className="spinner" /> : 'Create account'}
            </button>
          </form>
        </div>

        <p className="text-center mt-5 text-[0.82rem] text-[var(--text-muted)]">
          Already have an account?{' '}
          <Link href="/auth/login" className="text-[var(--brand)] font-medium no-underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
