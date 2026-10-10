import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, FlaskConical, Lightbulb, FolderOpen } from 'lucide-react'
import { getStats, listProjects, type DashboardStats, type Project } from '../api'
import { StatSkeleton, CardSkeleton } from '../components/Skeleton'
import EmptyState from '../components/EmptyState'

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getStats(), listProjects()])
      .then(([s, p]) => {
        setStats(s)
        setProjects(p)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const cards = [
    { label: 'Projects',   value: stats?.projects,   icon: FolderOpen,   color: 'bg-blue-500' },
    { label: 'Papers',     value: stats?.papers,     icon: FileText,     color: 'bg-emerald-500' },
    { label: 'Gaps Found', value: stats?.gaps,       icon: FlaskConical, color: 'bg-amber-500' },
    { label: 'Hypotheses', value: stats?.hypotheses, icon: Lightbulb,    color: 'bg-purple-500' },
  ]

  return (
    <div className="space-y-8">
      <header>
        <h2 className="text-3xl font-bold text-slate-900">Dashboard</h2>
        <p className="text-slate-500 mt-1">
          Overview of your scientific discovery workspace.
        </p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading
          ? [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
          : cards.map(({ label, value, icon: Icon, color }) => (
              <div
                key={label}
                className="bg-white rounded-xl p-5 shadow-sm border border-slate-200 transition hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">{label}</span>
                  <div className={`${color} p-2 rounded-lg text-white`}>
                    <Icon size={16} />
                  </div>
                </div>
                <div className="text-3xl font-bold text-slate-900 mt-3">
                  {value ?? 0}
                </div>
              </div>
            ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-slate-900">Recent Projects</h3>
          {projects.length > 0 && (
            <Link
              to="/projects"
              className="text-brand-600 hover:text-brand-700 text-sm font-medium"
            >
              View all →
            </Link>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        ) : projects.length === 0 ? (
          <EmptyState
            icon={FolderOpen}
            title="No projects yet"
            description="Create your first research workspace to start discovering opportunities and generating hypotheses."
            action={{ label: 'Create your first project', to: '/projects' }}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.slice(0, 4).map(p => (
              <Link
                key={p.id}
                to={`/projects/${p.id}`}
                className="block bg-white rounded-xl border border-slate-200 p-5 hover:border-brand-500 hover:shadow-md transition"
              >
                <span className="text-xs px-2 py-0.5 rounded-full bg-brand-100 text-brand-700">
                  {p.research_area}
                </span>
                <h4 className="font-semibold text-slate-900 mt-2">{p.name}</h4>
                <p className="text-sm text-slate-500 mt-1 line-clamp-2">{p.topic}</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}