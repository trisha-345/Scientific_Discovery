import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, FolderOpen, FlaskConical, Lightbulb, Menu, X,
} from 'lucide-react'

const nav = [
  { to: '/',           label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/projects',   label: 'Projects',    icon: FolderOpen },
  { to: '/gaps',       label: 'Gaps',        icon: FlaskConical },
  { to: '/hypotheses', label: 'Hypotheses',  icon: Lightbulb },
]

export default function Layout() {
  const [open, setOpen] = useState(false)

  return (
    <div className="flex h-screen bg-slate-50">
      <div className="lg:hidden fixed top-0 left-0 right-0 z-30 bg-slate-900 text-white flex items-center justify-between px-4 py-3">
        <span className="font-bold">🔬 SciDiscovery</span>
        <button
          onClick={() => setOpen(o => !o)}
          className="p-1 rounded hover:bg-slate-800"
          aria-label="Toggle menu"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div
          onClick={() => setOpen(false)}
          className="lg:hidden fixed inset-0 bg-black/40 z-30"
        />
      )}

      <aside
        className={`fixed lg:static top-0 left-0 h-full w-64 bg-slate-900 text-slate-100 flex flex-col shrink-0 z-40 transform transition-transform duration-200 ${
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-6 border-b border-slate-800">
          <h1 className="text-lg font-bold text-white">🔬 SciDiscovery</h1>
          <p className="text-xs text-slate-400 mt-1">AI Research Assistant</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 text-xs text-slate-500 border-t border-slate-800">
          Backend: localhost:8000
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto pt-16 lg:pt-0">
        <div className="max-w-6xl mx-auto p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}