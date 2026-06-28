import { useAuthStore } from './store/authStore'
import AuthPage from './pages/AuthPage'
import ChatPage from './pages/ChatPage'

export default function App() {
  const token = useAuthStore((s) => s.token)
  return token ? <ChatPage /> : <AuthPage />
}