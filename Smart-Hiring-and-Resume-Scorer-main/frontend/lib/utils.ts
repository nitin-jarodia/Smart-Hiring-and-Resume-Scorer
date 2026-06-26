export function getScoreColor(score: number): string {
  if (score >= 75) return 'score-excellent'
  if (score >= 60) return 'score-good'
  if (score >= 40) return 'score-moderate'
  return 'score-poor'
}

export function getScoreLabel(score: number): string {
  if (score >= 80) return 'Excellent Match'
  if (score >= 65) return 'Strong Match'
  if (score >= 50) return 'Moderate Match'
  if (score >= 35) return 'Weak Match'
  return 'Poor Match'
}

export function getProgressColor(score: number): string {
  if (score >= 75) return 'var(--success)'
  if (score >= 60) return 'var(--brand)'
  if (score >= 40) return 'var(--warning)'
  return 'var(--danger)'
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  })
}
