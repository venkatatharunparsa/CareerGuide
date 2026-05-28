import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink, MapPin, Building2, Clock } from 'lucide-react'
import api from '../api/client'

export default function Jobs() {
  const [tailoringJob, setTailoringJob] = useState(null)
  const [tailorResult, setTailorResult] = useState(null)
  const [selectedJob, setSelectedJob] = useState(null)
  const [minScore, setMinScore] = useState(0)
  const [sourceFilter, setSourceFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => api.get('/api/jobs/').then(r => r.data),
  })

  const filteredJobs = (data || []).filter(
    j =>
      Number(j.match_score || 0) >= minScore &&
      (sourceFilter === '' || j.source === sourceFilter)
  )

  const tailorResume = async (jobIndex) => {
    setTailoringJob(jobIndex)
    setTailorResult(null)
    try {
      const res = await api.post(
        `/api/jobs/tailor-resume/${jobIndex}`,
        {},
        { timeout: 180000 }
      )
      setTailorResult({ ...res.data, jobIndex })
    } catch (e) {
      alert(
        'Resume tailoring failed: ' +
          (e.response?.data?.detail || e.message || 'Unknown error')
      )
    } finally {
      setTailoringJob(null)
    }
  }

  const downloadPDF = (result) => {
    const bytes = atob(result.pdf_base64)
    const arr = new Uint8Array(bytes.length)
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
    const blob = new Blob([arr], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `resume_${result.job_company}_${result.ats_score}pct_ATS.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const viewLatex = (result) => {
    const escaped = (result.latex_code || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    const win = window.open('', '_blank')
    if (!win) return
    win.document.write(`<!doctype html><html><head><title>LaTeX Resume</title></head><body style="margin:0;background:#0b1020;color:#e5e7eb;font-family:Inter,system-ui"><div style="padding:16px"><h3 style="margin:0 0 12px 0">LaTeX Resume (editable)</h3><textarea style="width:100%;height:85vh;background:#111827;color:#e5e7eb;border:1px solid #374151;border-radius:8px;padding:12px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace">${escaped}</textarea></div></body></html>`)
    win.document.close()
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Job Matches</h1>
      <p className="text-gray-400 text-sm mb-8">
        AI-ranked opportunities based on your profile
      </p>

      {isLoading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="bg-gray-900 border border-gray-800 rounded-xl p-6 animate-pulse h-32"
            />
          ))}
        </div>
      )}

      {!isLoading && data?.length === 0 && (
        <div className="text-center py-20 text-gray-500">
          <p>No jobs yet. Run the agent from the Dashboard first.</p>
        </div>
      )}

      {data?.length > 0 && (
        <div className="flex gap-3 mb-6 flex-wrap">
          <select
            value={minScore}
            onChange={e => setMinScore(Number(e.target.value))}
            className="bg-gray-900 border border-gray-800 text-gray-300 text-sm rounded-lg px-3 py-2"
          >
            <option value={0}>All scores</option>
            <option value={60}>60%+ match</option>
            <option value={75}>75%+ match</option>
            <option value={85}>85%+ match</option>
          </select>
          <select
            value={sourceFilter}
            onChange={e => setSourceFilter(e.target.value)}
            className="bg-gray-900 border border-gray-800 text-gray-300 text-sm rounded-lg px-3 py-2"
          >
            <option value="">All sources</option>
            {[...new Set((data || []).map(j => j.source).filter(Boolean))].map(
              s => (
                <option key={s} value={s}>
                  {s}
                </option>
              )
            )}
          </select>
          <span className="text-gray-500 text-sm self-center">
            {filteredJobs.length} jobs shown
          </span>
        </div>
      )}

      <div className="space-y-4">
        {filteredJobs.map(job => {
          const apiIndex = data.findIndex(d => d.id === job.id)
          const cardKey = job.id ?? apiIndex
          const isSelected = selectedJob === cardKey

          return (
            <div
              key={cardKey}
              className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors cursor-pointer"
              onClick={() => setSelectedJob(isSelected ? null : cardKey)}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-white font-semibold">{job.title}</h2>
                    {job.match_score != null && (
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          job.match_score >= 80
                            ? 'bg-green-900/40 text-green-400'
                            : job.match_score >= 60
                              ? 'bg-yellow-900/40 text-yellow-400'
                              : 'bg-gray-800 text-gray-400'
                        }`}
                      >
                        {job.match_score}% match
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-gray-400 text-sm">
                    <span className="flex items-center gap-1.5">
                      <Building2 size={13} />
                      {job.company}
                    </span>
                    {job.location && (
                      <span className="flex items-center gap-1.5">
                        <MapPin size={13} />
                        {job.location}
                      </span>
                    )}
                    {job.posted_date && (
                      <span className="flex items-center gap-1.5">
                        <Clock size={13} />
                        {job.posted_date}
                      </span>
                    )}
                  </div>
                  {job.description && (
                    <p className="text-gray-500 text-sm mt-3 line-clamp-2">
                      {job.description}
                    </p>
                  )}
                </div>
                {job.url && (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={e => e.stopPropagation()}
                    className="text-sky-400 hover:text-sky-300 transition-colors mt-1"
                  >
                    <ExternalLink size={18} />
                  </a>
                )}
              </div>

              {isSelected && (
                <div
                  className="mt-4 pt-4 border-t border-gray-700 space-y-3"
                  onClick={e => e.stopPropagation()}
                >
                  {job.match_reason && (
                    <p className="text-gray-400 text-xs">{job.match_reason}</p>
                  )}
                  {job.matched_skills?.length > 0 && (
                    <div>
                      <p className="text-gray-500 text-xs mb-1">Matched skills</p>
                      <div className="flex flex-wrap gap-1">
                        {job.matched_skills.slice(0, 8).map((s, j) => (
                          <span
                            key={j}
                            className="bg-green-900/30 text-green-400 text-xs px-2 py-0.5 rounded"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {job.missing_skills?.length > 0 && (
                    <div>
                      <p className="text-gray-500 text-xs mb-1">Missing skills</p>
                      <div className="flex flex-wrap gap-1">
                        {job.missing_skills.slice(0, 6).map((s, j) => (
                          <span
                            key={j}
                            className="bg-red-900/20 text-red-400 text-xs px-2 py-0.5 rounded"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {job.skill_gaps?.length > 0 && (
                    <div>
                      <p className="text-gray-500 text-xs mb-1">
                        To learn for this role
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {job.skill_gaps.slice(0, 4).map((s, j) => (
                          <span
                            key={j}
                            className="bg-yellow-900/20 text-yellow-400 text-xs px-2 py-0.5 rounded"
                          >
                            + {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {job.learning_suggestions?.length > 0 && (
                    <div>
                      <p className="text-gray-500 text-xs mb-1">How to get there</p>
                      {job.learning_suggestions.slice(0, 2).map((s, j) => (
                        <p key={j} className="text-gray-400 text-xs">
                          • {s}
                        </p>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => tailorResume(apiIndex)}
                      disabled={tailoringJob === apiIndex}
                      className="flex-1 bg-sky-600 hover:bg-sky-500 text-white text-xs py-2 rounded-lg disabled:opacity-50"
                    >
                      {tailoringJob === apiIndex
                        ? 'Generating ATS Resume...'
                        : 'Tailor Resume PDF'}
                    </button>
                    {job.url && (
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 text-center bg-green-700 hover:bg-green-600 text-white text-xs py-2 rounded-lg"
                      >
                        Apply Now
                      </a>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-3 text-xs text-gray-600">Source: {job.source}</div>
            </div>
          )
        })}
      </div>

      {tailorResult && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-md w-full">
            <h3 className="text-white font-semibold mb-4">Resume Ready</h3>
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`text-3xl font-bold ${
                  tailorResult.ats_score >= 80
                    ? 'text-green-400'
                    : tailorResult.ats_score >= 65
                      ? 'text-yellow-400'
                      : 'text-red-400'
                }`}
              >
                {tailorResult.ats_score}%
              </div>
              <div>
                <p className="text-white text-sm font-medium">ATS Score</p>
                <p className="text-gray-400 text-xs">
                  Template: {tailorResult.template_used}
                </p>
              </div>
            </div>
            {tailorResult.improvements?.length > 0 && (
              <div className="mb-4">
                <p className="text-gray-400 text-xs mb-2">Improvements made:</p>
                {tailorResult.improvements.slice(0, 3).map((imp, i) => (
                  <p key={i} className="text-gray-300 text-xs">
                    • {imp}
                  </p>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={() => downloadPDF(tailorResult)}
                className="flex-1 bg-sky-600 hover:bg-sky-500 text-white text-sm py-2.5 rounded-lg font-medium"
              >
                Download PDF
              </button>
              <button
                onClick={() => viewLatex(tailorResult)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white text-sm py-2.5 rounded-lg font-medium"
              >
                View LaTeX
              </button>
              {tailorResult.apply_url && (
                <a
                  href={tailorResult.apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 text-center bg-green-700 hover:bg-green-600 text-white text-sm py-2.5 rounded-lg font-medium"
                >
                  Apply
                </a>
              )}
            </div>
            <button
              onClick={() => setTailorResult(null)}
              className="w-full mt-2 text-gray-500 text-xs hover:text-gray-300"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
