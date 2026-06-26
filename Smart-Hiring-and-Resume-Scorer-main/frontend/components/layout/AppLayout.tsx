'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import Sidebar from './Sidebar'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const loadFromStorage = useAuthStore(state => state.loadFromStorage)
  const router = useRouter()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    loadFromStorage()
  }, [loadFromStorage])

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      router.push('/auth/login')
    } else {
      // Restore theme
      const theme = localStorage.getItem('theme')
      if (theme === 'dark') document.documentElement.classList.add('dark')
      setReady(true)
    }
  }, [router])

  if (!ready) return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg)]">
      <div className="spinner" />
    </div>
  )

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="main-content flex-1 ml-[240px] min-h-screen bg-[var(--bg)]">
        {children}
      </main>
    </div>
  )
}
