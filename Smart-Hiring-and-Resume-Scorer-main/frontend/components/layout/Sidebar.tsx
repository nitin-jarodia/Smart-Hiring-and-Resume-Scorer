'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import {
  LayoutDashboard, Briefcase, PlusCircle, Shield, BarChart3, LogOut,
  Sun, Moon, FileText, Search, ClipboardList, Upload
} from 'lucide-react'
import { useState, useEffect } from 'react'

const recruiterItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/jobs', icon: Briefcase, label: 'Jobs' },
  { href: '/jobs/new', icon: PlusCircle, label: 'New Job' },
]

const adminItems = [
  { href: '/admin', icon: Shield, label: 'Admin' },
  { href: '/admin/analytics', icon: BarChart3, label: 'Analytics' },
]

const candidateItems = [
  { href: '/candidate/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/candidate/jobs', icon: Search, label: 'Browse Jobs' },
  { href: '/candidate/applications', icon: ClipboardList, label: 'My Applications' },
  { href: '/candidate/resume', icon: Upload, label: 'My Resume' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout } = useAuthStore()
  const [dark, setDark] = useState(false)

  const isCandidate = user?.role === 'candidate'

  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark') {
      setDark(true)
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleTheme = () => {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('theme', next ? 'dark' : 'light')
  }

  const handleLogout = () => {
    logout()
    router.push('/auth/login')
  }

  const isActive = (href: string) => {
    if (href === '/dashboard') return pathname === '/dashboard'
    return pathname === href || pathname.startsWith(href + '/')
  }

  const navItems = isCandidate ? candidateItems : recruiterItems

  return (
    <aside className="sidebar" style={{
      width: 240,
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      position: 'fixed',
      left: 0,
      top: 0,
      zIndex: 100,
    }}>
      {/* Logo */}
      <div style={{ padding: '1.25rem 1rem', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: 32, height: 32,
            background: 'var(--brand)',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <FileText size={16} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              ScreenerAI
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
              {isCandidate ? 'Job Seeker' : 'Resume Screening'}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '0.75rem 0', overflowY: 'auto' }}>
        <div style={{ padding: '0 0.75rem', marginBottom: '0.5rem' }}>
          <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0.5rem 0.85rem' }}>
            {isCandidate ? 'My Portal' : 'Workspace'}
          </div>
          {navItems.map(item => (
            <Link key={item.href} href={item.href}
              className={`nav-link ${isActive(item.href) ? 'active' : ''}`}>
              <item.icon size={16} />
              {item.label}
            </Link>
          ))}
        </div>

        {user?.role === 'admin' && (
          <div style={{ padding: '0 0.75rem', marginTop: '0.5rem' }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0.5rem 0.85rem' }}>
              Admin
            </div>
            {adminItems.map(item => (
              <Link key={item.href} href={item.href}
                className={`nav-link ${isActive(item.href) ? 'active' : ''}`}>
                <item.icon size={16} />
                {item.label}
              </Link>
            ))}
          </div>
        )}
      </nav>

      {/* Bottom */}
      <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--border)' }}>
        {/* Theme toggle */}
        <button onClick={toggleTheme} className="btn btn-ghost btn-sm"
          style={{ width: '100%', justifyContent: 'flex-start', marginBottom: '0.5rem' }}>
          {dark ? <Sun size={14} /> : <Moon size={14} />}
          {dark ? 'Light mode' : 'Dark mode'}
        </button>

        {/* User */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.5rem 0' }}>
            <div style={{
              width: 32, height: 32,
              background: 'var(--brand-soft)',
              borderRadius: 8,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--brand)',
            }}>
              {(user.full_name || user.email)[0].toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.full_name || user.email}
              </div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                {user.role}
              </div>
            </div>
            <button onClick={handleLogout} title="Logout"
              className="btn btn-ghost btn-sm" style={{ padding: '0.3rem' }}>
              <LogOut size={14} />
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}
