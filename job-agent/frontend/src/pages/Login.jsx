import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bot } from 'lucide-react'
import api from '../api/client'
import { formatApiError } from '../api/errors'

export default function Login({ onAuth }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const submit = async () => {
    setLoading(true)
    setError('')
    setSuccess('')

    const username = form.username.trim()
    const password = form.password

    if (!username || !password) {
      setError('Username and password are required')
      setLoading(false)
      return
    }

    if (mode === 'register' && password.length < 8) {
      setError('Password must be at least 8 characters')
      setLoading(false)
      return
    }

    try {
      if (mode === 'register') {
        await api.post('/api/auth/register', { username, password })
        setSuccess('Account created. Sign in with your credentials.')
        setMode('login')
        setForm((f) => ({ ...f, password: '' }))
        return
      }

      const body = new URLSearchParams()
      body.append('username', username)
      body.append('password', password)

      const { data } = await api.post('/api/auth/token', body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })

      localStorage.setItem('token', data.access_token)
      onAuth?.()
      navigate('/', { replace: true })
    } catch (e) {
      setError(formatApiError(e))
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (next) => {
    setMode(next)
    setError('')
    setSuccess('')
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="w-full max-w-sm bg-gray-900 rounded-2xl p-8 border border-gray-800">
        <div className="flex items-center gap-3 mb-8">
          <Bot className="text-sky-400" size={32} />
          <h1 className="text-2xl font-bold text-white">Job Agent</h1>
        </div>
        <h2 className="text-gray-300 text-sm mb-6">
          {mode === 'login' ? 'Sign in to your account' : 'Create an account'}
        </h2>
        {success && <p className="text-green-400 text-sm mb-4">{success}</p>}
        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
        <div className="space-y-4">
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500"
            placeholder="Username (min 3 characters)"
            value={form.username}
            autoComplete="username"
            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
          />
          <input
            type="password"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500"
            placeholder={mode === 'register' ? 'Password (min 8 characters)' : 'Password'}
            value={form.password}
            autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
          <button
            type="button"
            onClick={submit}
            disabled={loading}
            className="w-full bg-sky-600 hover:bg-sky-500 text-white rounded-lg py-2.5 text-sm font-medium transition-colors disabled:opacity-50"
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Register'}
          </button>
        </div>
        <p className="text-center text-gray-500 text-sm mt-6">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
            className="text-sky-400 hover:underline"
          >
            {mode === 'login' ? 'Register' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  )
}
