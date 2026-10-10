import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FlaskConical } from 'lucide-react'
import { listProjects, listGaps, type Project, type Gap } from '../api'
import { CardSkeleton } from '../components/Skeleton'
import EmptyState from '../components/EmptyState'

export default function AllGaps() {
  const [items, setItems] = useState<{ project: Project; gaps: Gap[] }[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listProjects()
      .then(async projects => {
        const grouped = await Promise.all(
          projects.map(async p => ({ project: p, gaps: await listGaps(p.id) }))
        )
        setItems(grouped.filter(g => g.gaps.length > 0))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-3xl font-bold text-slate-900">All Research Gaps</h2>
        <p className="text-slate-500 mt-1">
          Opportunities across all your projects.
        </p>
      </header>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="No gaps detected yet"
          description="Upload papers to a project and run analysis to detect research opportunities."
          action={{ label: 'Go to Projects', to: '/projects' }}
        />
      ) : (
        items.map(({ project, gaps }) => (
          <div key={project.id}>
            <Link
              to={`/projects/${project.id}`}
              className="text-sm font-medium text-brand-600 hover:underline mb-2 inline-block"
            >
              {project.name} →
            </Link>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {gaps.map(g => (
                <div
                  key={g.id}
                  className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-sm transition"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 uppercase">
                      {g.gap_type}
                    </span>
                    <span className="text-sm font-bold">
                      {g.opportunity_score.toFixed(0)}%
                    </span>
                  </div>
                  <div className="font-medium text-sm text-slate-900">{g.title}</div>
                  <p className="text-sm text-slate-500 mt-1 line-clamp-2">
                    {g.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}