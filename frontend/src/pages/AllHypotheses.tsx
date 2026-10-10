import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Lightbulb } from 'lucide-react'
import {
  listProjects, listHypotheses,
  type Project, type Hypothesis,
} from '../api'
import { CardSkeleton } from '../components/Skeleton'
import EmptyState from '../components/EmptyState'

export default function AllHypotheses() {
  const [items, setItems] = useState<{ project: Project; hypotheses: Hypothesis[] }[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listProjects()
      .then(async projects => {
        const grouped = await Promise.all(
          projects.map(async p => ({
            project: p,
            hypotheses: await listHypotheses(p.id),
          }))
        )
        setItems(grouped.filter(g => g.hypotheses.length > 0))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-3xl font-bold text-slate-900">All Hypotheses</h2>
        <p className="text-slate-500 mt-1">
          Groq-generated research hypotheses.
        </p>
      </header>

      {loading ? (
        <div className="space-y-3">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={Lightbulb}
          title="No hypotheses yet"
          description="Upload papers and run analysis to generate testable research hypotheses."
          action={{ label: 'Go to Projects', to: '/projects' }}
        />
      ) : (
        items.map(({ project, hypotheses }) => (
          <div key={project.id}>
            <Link
              to={`/projects/${project.id}`}
              className="text-sm font-medium text-brand-600 hover:underline mb-2 inline-block"
            >
              {project.name} →
            </Link>
            <div className="space-y-3">
              {hypotheses.map(h => (
                <div
                  key={h.id}
                  className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-sm transition"
                >
                  <div className="flex items-start justify-between gap-4">
                    <p className="text-sm font-medium leading-relaxed text-slate-900">
                      {h.text}
                    </p>
                    <div className="text-xl font-bold text-brand-600 shrink-0">
                      {h.overall_score.toFixed(0)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}