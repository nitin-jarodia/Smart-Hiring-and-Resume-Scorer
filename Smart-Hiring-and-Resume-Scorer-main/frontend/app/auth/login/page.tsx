'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { FileText, Eye, EyeOff, AlertCircle, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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
      const res = await authApi.login(email, password)
      setAuth(res.data.user, res.data.access_token)
      toast.success('Welcome back!')
      router.push(res.data.user.role === 'candidate' ? '/candidate/dashboard' : '/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials')
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
          <h1 className="text-[1.4rem] mb-1.5">Welcome back</h1>
          <p>Sign in to your ScreenerAI account</p>
        </div>

        {/* Form */}
        <div className="card">
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="flex gap-2 items-center p-3 bg-[rgba(201,75,75,0.08)] rounded-lg mb-5 text-[0.82rem] text-[var(--danger)]">
                <AlertCircle size={14} /> {error}
              </div>
            )}

            <div className="mb-4">
              <label>Email</label>
              <input type="email" className="input" placeholder="you@company.com"
                value={email} onChange={e => setEmail(e.target.value)} required />
            </div>

            <div className="mb-6">
              <label>Password</label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'}
                  placeholder="••••••••" value={password}
                  onChange={e => setPassword(e.target.value)} required
                  className="input pr-10" />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-2.5 top-1/2 -translate-y-1/2 bg-transparent border-none cursor-pointer text-[var(--text-muted)] p-1">
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button type="submit" className="btn btn-primary w-full p-3" disabled={loading}>
              {loading ? <div className="spinner" /> : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center mt-5 text-[0.82rem] text-[var(--text-muted)]">
          Don&apos;t have an account?{' '}
          <Link href="/auth/signup" className="text-[var(--brand)] font-medium no-underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}
