import { useState, FormEvent } from 'react'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'

export default function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await authApi.login(email, password)
      setAuth(res.data.access_token, res.data.user)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail
      setError(detail ?? 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-[11px] font-medium text-zinc-500 uppercase tracking-wider mb-1.5">
          Email
        </label>
        <input
          type="email" value={email} onChange={(e) => setEmail(e.target.value)}
          required autoComplete="email" placeholder="you@example.com"
          className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors font-mono"
        />
      </div>
      <div>
        <label className="block text-[11px] font-medium text-zinc-500 uppercase tracking-wider mb-1.5">
          Password
        </label>
        <input
          type="password" value={password} onChange={(e) => setPassword(e.target.value)}
          required autoComplete="current-password" placeholder="••••••••"
          className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
        />
      </div>
      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2 font-mono">
          {error}
        </p>
      )}
      <button
        type="submit" disabled={loading}
        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg py-2.5 text-sm font-medium transition-colors"
      >
        {loading ? 'Authenticating…' : 'Sign in'}
      </button>
    </form>
  )
}