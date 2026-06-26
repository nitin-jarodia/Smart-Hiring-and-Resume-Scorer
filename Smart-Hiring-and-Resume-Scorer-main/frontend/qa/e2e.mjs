import { chromium } from 'playwright'
import { spawn } from 'node:child_process'
import { setTimeout as delay } from 'node:timers/promises'

const BACKEND_URL = process.env.QA_BACKEND_URL || 'http://127.0.0.1:8000'
const FRONTEND_URL = process.env.QA_FRONTEND_URL || 'http://127.0.0.1:3000'
const PYTHON_BIN = process.env.QA_PYTHON || 'python'
const ROOT = new URL('..', import.meta.url).pathname

function log(...args) {
  process.stdout.write(args.join(' ') + '\n')
}

async function waitForHttpOk(url, { timeoutMs = 60000, intervalMs = 500 } = {}) {
  const start = Date.now()
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const res = await fetch(url, { redirect: 'manual' })
      if (res.ok) return
    } catch {}
    if (Date.now() - start > timeoutMs) throw new Error(`Timeout waiting for ${url}`)
    await delay(intervalMs)
  }
}

function spawnProc(label, cmd, args, cwd) {
  // Use shell so Windows can resolve executables like `python`/`npm` reliably.
  const proc = spawn(cmd, args, { cwd, stdio: 'pipe', shell: true })
  proc.stdout.on('data', (d) => process.stdout.write(`[${label}] ${d}`))
  proc.stderr.on('data', (d) => process.stderr.write(`[${label}] ${d}`))
  proc.on('exit', (code) => log(`[${label}] exited with code ${code}`))
  return proc
}

async function apiJson(method, path, token, body) {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body && !(body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? (body instanceof FormData ? body : JSON.stringify(body)) : undefined,
  })
  const text = await res.text()
  let json
  try { json = text ? JSON.parse(text) : null } catch { json = { _raw: text } }
  if (!res.ok) {
    const msg = typeof json === 'object' ? JSON.stringify(json) : String(json)
    throw new Error(`${method} ${path} failed: ${res.status} ${msg}`)
  }
  return json
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg)
}

async function run() {
  // Start backend and frontend for this test run
  const backend = spawnProc('backend', PYTHON_BIN, ['-m', 'uvicorn', 'app.main:app', '--port', '8000'], new URL('../backend', import.meta.url).pathname)
  const frontend = spawnProc('frontend', 'npm', ['run', 'dev', '--', '--port', '3000'], ROOT)

  const killAll = async () => {
    for (const p of [frontend, backend]) {
      if (p && !p.killed) {
        try { p.kill('SIGTERM') } catch {}
      }
    }
  }

  try {
    log('Waiting for backend and frontend...')
    await waitForHttpOk(`${BACKEND_URL}/health`)
    await waitForHttpOk(`${FRONTEND_URL}/`)

    // Seed minimal data via API (no reliance on seed_data.py)
    const uniq = Date.now()
    const recruiterEmail = `recruiter_${uniq}@qa.dev`
    const candidateEmail = `candidate_${uniq}@qa.dev`
    const recruiterPass = 'recruiter123'
    const candidatePass = 'candidate123'

    const recruiterTok = await apiJson('POST', '/auth/signup', null, { email: recruiterEmail, password: recruiterPass, full_name: 'QA Recruiter', role: 'recruiter' })
    const candidateTok = await apiJson('POST', '/auth/signup', null, { email: candidateEmail, password: candidatePass, full_name: 'QA Candidate', role: 'candidate' })
    assert(recruiterTok?.access_token, 'Recruiter signup did not return access_token')
    assert(candidateTok?.access_token, 'Candidate signup did not return access_token')

    // Create a job as recruiter
    const job = await apiJson('POST', '/jobs', recruiterTok.access_token, {
      title: 'QA Backend Engineer',
      company: 'QA Inc',
      jd_text: 'Looking for a backend engineer with Python, FastAPI, SQL, Docker. 3+ years experience.',
      required_skills: ['python', 'fastapi', 'sql', 'docker'],
      min_years_exp: 3,
    })
    assert(job?.id, 'Job create did not return id')

    // Candidate job browsing + fit/chance should work
    const publicJobs = await apiJson('GET', '/jobs/public', null)
    assert(Array.isArray(publicJobs) && publicJobs.length >= 1, 'Public jobs list is empty')

    // Candidate must upload resume before recommendations/apply
    // Use an existing sample resume file if present; otherwise a minimal text resume.
    const resumeText = `QA Candidate\nEmail: ${candidateEmail}\n\nSkills: Python, FastAPI, SQL, Docker\nExperience: 4 years building APIs in Python and FastAPI.\n`
    const fd = new FormData()
    fd.append('file', new Blob([resumeText], { type: 'text/plain' }), 'resume.txt')
    await apiJson('POST', '/candidate/profile', candidateTok.access_token, fd)

    const profile = await apiJson('GET', '/candidate/profile', candidateTok.access_token)
    assert(profile?.has_profile === true, 'Candidate profile missing after upload')
    assert(typeof profile.overall_score === 'number', 'Candidate overall_score not numeric')
    assert(profile.seniority !== undefined, 'Candidate seniority missing')
    assert(Array.isArray(profile.extracted_skills), 'Candidate extracted_skills missing/invalid')

    const recs = await apiJson('GET', '/candidate/recommendations', candidateTok.access_token)
    assert(Array.isArray(recs), 'Recommendations not an array')

    // Candidate apply
    const applyRes = await apiJson('POST', `/candidate/apply/${job.id}`, candidateTok.access_token)
    assert(applyRes?.application_id, 'Apply did not return application_id')

    const apps = await apiJson('GET', '/candidate/applications', candidateTok.access_token)
    assert(Array.isArray(apps) && apps.length === 1, 'Candidate applications should contain exactly one entry')
    assert(apps[0].status === 'pending', 'New application status should be pending')

    // Recruiter sees results for the job (should include candidate application mapped into ResultOut)
    const results = await apiJson('GET', `/jobs/${job.id}/results`, recruiterTok.access_token)
    assert(Array.isArray(results) && results.length >= 1, 'Recruiter results list is empty')
    const candRow = results.find(r => r.candidate_email === candidateEmail) || results[0]
    assert(candRow?.id, 'Could not locate candidate row in results')

    // Recruiter updates status and it reflects for candidate
    await apiJson('PATCH', `/results/${candRow.id}`, recruiterTok.access_token, { status: 'shortlisted' })
    const apps2 = await apiJson('GET', '/candidate/applications', candidateTok.access_token)
    assert(apps2[0].status === 'shortlisted', 'Recruiter-updated status did not reflect on candidate applications')

    // Recruiter schedules interview and candidate can see it with meeting link
    const scheduledAt = new Date(Date.now() + 3600_000).toISOString()
    await apiJson('POST', '/interviews', recruiterTok.access_token, {
      result_id: candRow.id,
      scheduled_at: scheduledAt,
      duration_minutes: 30,
      meeting_link: 'https://example.com/meet/qa',
      notes: 'QA interview',
    })
    const candInterviews = await apiJson('GET', '/interviews/my-interviews', candidateTok.access_token)
    assert(Array.isArray(candInterviews) && candInterviews.length >= 1, 'Candidate interviews list is empty after scheduling')
    assert(candInterviews[0].meeting_link === 'https://example.com/meet/qa', 'Candidate meeting link mismatch')

    // Guards: candidate should be blocked from recruiter-only routes
    let blocked = false
    try { await apiJson('GET', '/jobs', candidateTok.access_token) } catch { blocked = true }
    assert(blocked, 'Candidate unexpectedly accessed recruiter-only GET /jobs')

    // Guards: recruiter should be blocked from candidate-only routes
    blocked = false
    try { await apiJson('GET', '/candidate/profile', recruiterTok.access_token) } catch { blocked = true }
    assert(blocked, 'Recruiter unexpectedly accessed candidate-only GET /candidate/profile')

    // Browser checks (smoke): landing + auth pages load
    const browser = await chromium.launch()
    const page = await browser.newPage()
    await page.goto(`${FRONTEND_URL}/`, { waitUntil: 'networkidle' })
    await page.goto(`${FRONTEND_URL}/auth/login`, { waitUntil: 'domcontentloaded' })
    await page.goto(`${FRONTEND_URL}/auth/signup`, { waitUntil: 'domcontentloaded' })
    await browser.close()

    log('E2E QA PASS')
  } finally {
    await killAll()
  }
}

run().catch((e) => {
  process.stderr.write(`E2E QA FAIL: ${e?.stack || e}\n`)
  process.exit(1)
})

