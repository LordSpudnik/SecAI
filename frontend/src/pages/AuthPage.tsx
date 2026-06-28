import { useState } from 'react'
import LoginForm from '../components/auth/LoginForm'
import RegisterForm from '../components/auth/RegisterForm'

type Tab = 'login' | 'register'

export default function AuthPage() {
  const [tab, setTab] = useState<Tab>('login')

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center mb-3">
            <span className="text-white font-bold font-mono text-lg">S</span>
          </div>
          <h1 className="text-lg font-semibold text-zinc-100 tracking-tight">SecAI</h1>
          <p className="text-[11px] text-zinc-600 mt-1 font-mono text-center">// private · local · no external calls</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl">
          <div className="flex border-b border-zinc-800">
            {(['login', 'register'] as Tab[]).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`flex-1 py-3 text-xs font-medium transition-colors ${
                  tab === t ? 'text-zinc-100 border-b-2 border-indigo-500 bg-zinc-800/40' : 'text-zinc-500 hover:text-zinc-300'
                }`}>
                {t === 'login' ? 'Sign in' : 'Register'}
              </button>
            ))}
          </div>
          <div className="p-5">
            {tab === 'login'
              ? <LoginForm />
              : <RegisterForm onSuccess={() => setTab('login')} />}
          </div>
        </div>

        <p className="text-center text-[10px] text-zinc-700 font-mono mt-4">
          Token stored in memory only — refreshing logs you out
        </p>
      </div>
    </div>
  )
}