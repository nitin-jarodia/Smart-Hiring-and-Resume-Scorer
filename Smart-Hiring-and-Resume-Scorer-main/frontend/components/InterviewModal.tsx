'use client'
import { useState } from 'react'
import { X, Calendar, Clock, Video, FileText } from 'lucide-react'
import { interviewsApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface InterviewModalProps {
  resultId: string;
  candidateName: string;
  onClose: () => void;
  onScheduled: () => void;
}

export default function InterviewModal({ resultId, candidateName, onClose, onScheduled }: InterviewModalProps) {
  const [date, setDate] = useState('')
  const [time, setTime] = useState('')
  const [duration, setDuration] = useState(60)
  const [link, setLink] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!date || !time) {
      toast.error('Please select both date and time')
      return
    }

    setLoading(true)
    try {
      // Combine date and time locally into ISO string
      const dateTimeString = `${date}T${time}:00`
      const scheduledAt = new Date(dateTimeString).toISOString()

      await interviewsApi.schedule({
        result_id: resultId,
        scheduled_at: scheduledAt,
        duration_minutes: duration,
        meeting_link: link,
        notes: notes
      })
      toast.success('Interview scheduled successfully')
      onScheduled()
      onClose()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to schedule interview')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="card w-full max-w-[500px] p-0 overflow-hidden animate-[fadeInUp_0.3s_ease]">
        <div className="px-6 py-5 border-b border-[var(--border)] flex justify-between items-center">
          <h3 className="m-0 text-lg font-semibold">Schedule Interview</h3>
          <button onClick={onClose} className="btn btn-ghost btn-sm p-1" title="Close" aria-label="Close">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="mb-6 p-3 bg-[var(--hover-row)] rounded-lg">
            <span className="text-[0.8rem] text-[var(--text-muted)]">Candidate</span>
            <div className="font-medium mt-0.5">{candidateName}</div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="int-date" className="flex items-center gap-1.5 mb-1.5 text-[0.85rem]">
                <Calendar size={14} /> Date
              </label>
              <input id="int-date" type="date" className="input" value={date} onChange={e => setDate(e.target.value)} required />
            </div>
            <div>
              <label htmlFor="int-time" className="flex items-center gap-1.5 mb-1.5 text-[0.85rem]">
                <Clock size={14} /> Time
              </label>
              <input id="int-time" type="time" className="input" value={time} onChange={e => setTime(e.target.value)} required />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="col-span-2">
              <label htmlFor="int-duration" className="flex items-center gap-1.5 mb-1.5 text-[0.85rem]">
                Duration (minutes)
              </label>
              <select id="int-duration" className="input" value={duration} aria-label="Duration" onChange={e => setDuration(Number(e.target.value))}>
                <option value={15}>15 mins</option>
                <option value={30}>30 mins</option>
                <option value={45}>45 mins</option>
                <option value={60}>60 mins (1 hr)</option>
                <option value={90}>90 mins (1.5 hrs)</option>
                <option value={120}>120 mins (2 hrs)</option>
              </select>
            </div>
          </div>

          <div className="mb-4">
            <label htmlFor="int-link" className="flex items-center gap-1.5 mb-1.5 text-[0.85rem]">
              <Video size={14} /> Meeting Link (Optional)
            </label>
            <input id="int-link" type="url" className="input" placeholder="https://zoom.us/j/..." value={link} onChange={e => setLink(e.target.value)} />
          </div>

          <div className="mb-8">
            <label htmlFor="int-notes" className="flex items-center gap-1.5 mb-1.5 text-[0.85rem]">
              <FileText size={14} /> Notes for Candidate (Optional)
            </label>
            <textarea id="int-notes" className="input" placeholder="Format: Technical screen, covering system design..." rows={3} value={notes} onChange={e => setNotes(e.target.value)} />
          </div>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <div className="spinner" /> : 'Confirm Interview'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
