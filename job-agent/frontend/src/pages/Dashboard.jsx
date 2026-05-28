import { useState, useEffect } from 'react'
import { Bot, Zap, RefreshCw, User, Briefcase, Star, TrendingUp } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function Dashboard() {
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [profile, setProfile] = useState(null)
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      api.get('/api/profile/'),
      api.get('/api/jobs/'),
      api.get('/api/agents/status'),
    ]).then(([profileRes, jobsRes]) => {
      setProfile(profileRes.data)
      setJobs(jobsRes.data || [])
    }).catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const runAgent = async () => {
    setRunning(true)
    setError('')
    setResult(null)
    try {
      const { data } = await api.post('/api/agents/run', {}, { timeout: 180000 })
      setResult(data)
      const jobsRes = await api.get('/api/jobs/')
      setJobs(jobsRes.data || [])
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Agent run failed'
      setError(msg)
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  const skillList = profile?.all_skills?.length
    ? profile.all_skills
    : profile?.skills || []
  const hasProfile = skillList.length > 0
  const topJobs = jobs.slice(0, 3)

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Dashboard</h1>
        <p className="text-gray-400 text-sm">
          Your AI-powered job search command center
        </p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <User size={16} className="text-sky-400" />
            <h2 className="text-white font-medium">Profile Status</h2>
          </div>
          <button onClick={() => navigate('/profile')}
            className="text-sky-400 text-sm hover:underline">
            Edit Profile
          </button>
        </div>
        {hasProfile ? (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Star size={14} className="text-yellow-400" />
                <span className="text-gray-400 text-xs">Skills</span>
              </div>
              <p className="text-2xl font-bold text-white">{skillList.length}</p>
              <p className="text-gray-500 text-xs mt-1 truncate">
                {skillList.slice(0, 3).join(', ')}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Briefcase size={14} className="text-sky-400" />
                <span className="text-gray-400 text-xs">Target Roles</span>
              </div>
              <p className="text-2xl font-bold text-white">{profile.target_roles?.length || 0}</p>
              <p className="text-gray-500 text-xs mt-1 truncate">
                {profile.target_roles?.slice(0, 2).join(', ')}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={14} className="text-green-400" />
                <span className="text-gray-400 text-xs">Experience</span>
              </div>
              <p className="text-2xl font-bold text-white">{profile.experience_years || 0}</p>
              <p className="text-gray-500 text-xs mt-1">years</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-gray-400 text-sm mb-3">
              No profile found. Add your skills to get started.
            </p>
            <button onClick={() => navigate('/profile')}
              className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg text-sm transition-colors">
              Set Up Profile →
            </button>
          </div>
        )}
      </div>

      {jobs.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Jobs Found', value: jobs.length, color: 'text-white' },
            {
              label: 'Avg Match',
              value: Math.round(jobs.reduce((a, j) => a + (j.match_score || 0), 0) / jobs.length) + '%',
              color: 'text-green-400'
            },
            {
              label: 'Top Match',
              value: (jobs[0]?.match_score || 0) + '%',
              color: 'text-sky-400'
            },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <p className="text-gray-400 text-xs mb-2">{label}</p>
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-white font-medium">Run Job Agent</h2>
            <p className="text-gray-500 text-xs mt-1">
              Searches 15+ sites and scores jobs against your profile
            </p>
          </div>
          <button onClick={runAgent} disabled={running || !hasProfile}
            className="flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white px-6 py-2.5 rounded-xl font-medium transition-colors disabled:opacity-50">
            {running
              ? <><RefreshCw size={16} className="animate-spin" /> Running...</>
              : <><Zap size={16} /> Run Agent</>
            }
          </button>
        </div>

        {!hasProfile && (
          <p className="text-yellow-400 text-xs">
            Save your profile first before running the agent.
          </p>
        )}

        {error && (
          <div className="mt-3 bg-red-900/20 border border-red-800 rounded-lg p-3">
            <p className="text-red-400 text-sm">{error}</p>
            {error.toLowerCase().includes('profile') && (
              <button onClick={() => navigate('/profile')}
                className="text-sky-400 text-xs mt-1 hover:underline">
                Go to Profile →
              </button>
            )}
          </div>
        )}

        {result && (
          <div className="mt-4 bg-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Bot size={16} className="text-sky-400" />
              <span className="text-white text-sm font-medium">Agent Complete</span>
            </div>
            <p className="text-gray-300 text-sm mb-4">{result.summary}</p>
            <div className="grid grid-cols-3 gap-3 mb-4">
              {[
                { label: 'Jobs Found', value: result.total_jobs },
                { label: 'Avg Match', value: result.avg_score + '%' },
                { label: 'Sites', value: result.sites_scraped },
              ].map(({ label, value }) => (
                <div key={label} className="bg-gray-700 rounded-lg p-3 text-center">
                  <p className="text-lg font-bold text-white">{value}</p>
                  <p className="text-gray-400 text-xs">{label}</p>
                </div>
              ))}
            </div>
            <button onClick={() => navigate('/jobs')}
              className="w-full bg-sky-600 hover:bg-sky-500 text-white rounded-lg py-2 text-sm transition-colors">
              View Jobs →
            </button>
          </div>
        )}
      </div>

      {topJobs.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-medium">Top Matches</h2>
            <button onClick={() => navigate('/jobs')}
              className="text-sky-400 text-sm hover:underline">
              View all →
            </button>
          </div>
          <div className="space-y-3">
            {topJobs.map((job, i) => (
              <div key={i} className="flex items-center justify-between bg-gray-800 rounded-lg p-4">
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium truncate">{job.title}</p>
                  <p className="text-gray-400 text-xs mt-0.5">
                    {job.company} · {job.source}
                  </p>
                </div>
                <div className="ml-4 flex items-center gap-3">
                  <span className={`text-sm font-bold ${
                    job.match_score >= 80 ? 'text-green-400' :
                      job.match_score >= 60 ? 'text-yellow-400' :
                        'text-gray-400'
                  }`}>
                    {job.match_score}%
                  </span>
                  {job.url && (
                    <a href={job.url} target="_blank"
                      rel="noopener noreferrer"
                      className="text-sky-400 text-xs hover:underline">
                      Apply
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
