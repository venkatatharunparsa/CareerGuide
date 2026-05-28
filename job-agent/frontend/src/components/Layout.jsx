import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, User, Briefcase, LogOut, Bot } from 'lucide-react'

export default function Layout({ onLogout }) {
  const navigate = useNavigate()
  const logout = () => {
    localStorage.removeItem('token')
    onLogout?.()
    navigate('/login')
  }

  const nav = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/profile', icon: User, label: 'Profile' },
    { to: '/jobs', icon: Briefcase, label: 'Jobs' }
  ]

  return (
    <div className="flex h-screen bg-gray-950">
      <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <Bot className="text-sky-400" size={28} />
          <span className="text-lg font-semibold text-white">Job Agent</span>
        </div>
        <nav className="flex-1 px-3 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-sky-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <button onClick={logout}
          className="m-4 flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-red-400 transition-colors">
          <LogOut size={16} /> Logout
        </button>
      </aside>
      <main className="flex-1 overflow-auto p-8">
        <Outlet />
      </main>
    </div>
  )
}
