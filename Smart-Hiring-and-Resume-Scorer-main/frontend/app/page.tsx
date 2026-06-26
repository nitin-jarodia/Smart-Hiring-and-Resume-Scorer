'use client'
import Link from 'next/link'
import { useState, useEffect } from 'react'
import { FileText, ArrowRight, Upload, Brain, Briefcase } from 'lucide-react'

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  return (
    <div style={{
      minHeight: '100vh',
      background: '#040c1f',
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
      overflowX: 'hidden',
    }}>

      {/* ── Subtle background glow ─────────────────────── */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }}>
        <div style={{
          position: 'absolute', top: '-30%', left: '-20%',
          width: '80vw', height: '80vw', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.13) 0%, transparent 60%)',
          filter: 'blur(60px)',
        }} />
        <div style={{
          position: 'absolute', bottom: '-10%', right: '-10%',
          width: '60vw', height: '60vw', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(14,165,233,0.09) 0%, transparent 60%)',
          filter: 'blur(60px)',
        }} />
        {/* Stars */}
        {[...Array(40)].map((_, i) => (
          <div key={i} style={{
            position: 'absolute',
            left: `${(i * 137.5) % 100}%`,
            top: `${(i * 97.3) % 100}%`,
            width: i % 7 === 0 ? 2.5 : 1.5,
            height: i % 7 === 0 ? 2.5 : 1.5,
            borderRadius: '50%',
            background: '#fff',
            opacity: 0.12 + (i % 4) * 0.07,
          }} />
        ))}
      </div>

      {/* ── NAVBAR ────────────────────────────────────── */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 2.5rem', height: 60,
        background: scrolled ? 'rgba(4,12,31,0.88)' : 'transparent',
        backdropFilter: scrolled ? 'blur(16px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(255,255,255,0.06)' : '1px solid transparent',
        transition: 'all 0.3s',
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <FileText size={15} color="#fff" />
          </div>
          <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.01em' }}>
            ScreenerAI
          </span>
        </div>

        {/* Auth buttons */}
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <Link href="/auth/login" style={{
            fontSize: '0.875rem', color: 'rgba(241,245,249,0.75)',
            textDecoration: 'none', padding: '0.4rem 1rem',
            borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)',
            transition: 'all 0.2s',
          }}>Login</Link>
          <Link href="/auth/signup" style={{
            fontSize: '0.875rem', fontWeight: 600, color: '#fff',
            textDecoration: 'none', padding: '0.4rem 1.1rem',
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            borderRadius: 8, boxShadow: '0 0 16px rgba(99,102,241,0.4)',
            transition: 'all 0.2s',
          }}>Sign Up</Link>
        </div>
      </nav>

      {/* ── HERO ──────────────────────────────────────── */}
      <section style={{
        position: 'relative', zIndex: 1,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexDirection: 'column', textAlign: 'center',
        padding: '9rem 2rem 5rem',
      }}>
        {/* Pill badge */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
          padding: '0.3rem 0.9rem', borderRadius: 100,
          background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.28)',
          fontSize: '0.72rem', fontWeight: 600, color: '#a5b4fc',
          marginBottom: '1.5rem', letterSpacing: '0.04em',
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#818cf8', boxShadow: '0 0 6px #818cf8' }} />
          AI-Powered · Bias-Free · Instant Results
        </div>

        {/* Headline */}
        <h1 style={{
          fontSize: 'clamp(2rem, 5.5vw, 3.6rem)',
          fontWeight: 800, lineHeight: 1.12, letterSpacing: '-0.03em',
          color: '#f1f5f9', maxWidth: 700, marginBottom: '1.25rem',
        }}>
          Resume Screening &{' '}
          <span style={{
            background: 'linear-gradient(135deg, #818cf8 0%, #06b6d4 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>Smart Hiring</span>
        </h1>

        {/* Sub */}
        <p style={{
          fontSize: 'clamp(0.95rem, 1.8vw, 1.1rem)',
          color: 'rgba(241,245,249,0.5)', maxWidth: 520, lineHeight: 1.75,
          marginBottom: '2.25rem',
        }}>
          Streamline your hiring with AI-powered screening that finds the best candidates quickly — with built-in fairness guardrails.
        </p>

        {/* CTAs */}
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link href="/auth/signup" style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.45rem',
            padding: '0.75rem 2rem', borderRadius: 10, textDecoration: 'none',
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            color: '#fff', fontWeight: 700, fontSize: '0.95rem',
            boxShadow: '0 0 30px rgba(99,102,241,0.45)',
          }}>
            Get Started <ArrowRight size={16} />
          </Link>
          <Link href="/auth/login" style={{
            display: 'inline-flex', alignItems: 'center',
            padding: '0.75rem 2rem', borderRadius: 10, textDecoration: 'none',
            background: 'rgba(255,255,255,0.06)', backdropFilter: 'blur(10px)',
            color: '#f1f5f9', fontWeight: 600, fontSize: '0.95rem',
            border: '1px solid rgba(255,255,255,0.1)',
          }}>
            Log In
          </Link>
        </div>

        {/* ── 3 STEP CARDS ──────────────────────────────── */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1.25rem', maxWidth: 860, width: '100%', marginTop: '4.5rem',
        }}>
          {[
            {
              icon: Upload, emoji: '📄',
              gradient: 'linear-gradient(135deg, #6366f1 0%, #818cf8 100%)',
              title: 'Upload Resumes',
              desc: 'Easily upload and manage candidate resumes for screening. PDF, DOCX, or TXT.',
            },
            {
              icon: Brain, emoji: '🤖',
              gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
              title: 'AI Screening',
              desc: 'Our AI analyses each resume against your job description and highlights top candidates.',
            },
            {
              icon: Briefcase, emoji: '🎯',
              gradient: 'linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%)',
              title: 'Smart Hiring',
              desc: 'Hire with confidence using data-driven insights, ranked results, and skill breakdowns.',
            },
          ].map((card, i) => (
            <div key={i} style={{
              background: 'rgba(12,18,45,0.7)', backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.07)', borderRadius: 18,
              padding: '1.75rem 1.5rem', textAlign: 'center',
              transition: 'all 0.25s ease',
            }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'translateY(-4px)'
                e.currentTarget.style.border = '1px solid rgba(99,102,241,0.3)'
                e.currentTarget.style.boxShadow = '0 16px 40px rgba(0,0,0,0.3)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.border = '1px solid rgba(255,255,255,0.07)'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              {/* Icon */}
              <div style={{
                width: 52, height: 52, borderRadius: 14, margin: '0 auto 1.1rem',
                background: card.gradient,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.5rem',
                boxShadow: '0 8px 20px rgba(0,0,0,0.25)',
              }}>
                {card.emoji}
              </div>
              <h3 style={{
                fontSize: '0.95rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '0.6rem',
              }}>{card.title}</h3>
              <p style={{
                fontSize: '0.8rem', color: 'rgba(241,245,249,0.5)', lineHeight: 1.7,
              }}>{card.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── FOOTER ────────────────────────────────────── */}
      <footer style={{
        position: 'relative', zIndex: 1,
        padding: '1.75rem 2.5rem',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: '1rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{
            width: 22, height: 22, borderRadius: 6,
            background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <FileText size={11} color="#fff" />
          </div>
          <span style={{ fontSize: '0.8rem', color: 'rgba(241,245,249,0.4)', fontWeight: 600 }}>ScreenerAI</span>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'rgba(241,245,249,0.25)' }}>
          © {new Date().getFullYear()} ScreenerAI — AI-powered resume screening
        </p>
      </footer>
    </div>
  )
}
