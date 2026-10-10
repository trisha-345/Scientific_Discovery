import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Loader2, FolderOpen } from 'lucide-react'
import { listProjects, createProject, type Project } from '../api'
import { notify } from '../toast'
import { CardSkeleton } from '../components/Skeleton'
import EmptyState from '../components/EmptyState'

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showForm, setShowForm] = useState(false)

  const [name, setName] = useState('')
  const [topic, setTopic] = useState('')
  const [area, setArea] = useState('Education')

  const refresh = () => {
    setLoading(true)
    listProjects()
      .then(setProjects)
      .catch(err => notify.error(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(refresh, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !topic.trim()) return

    setCreating(true)
    try {
      await createProject({ name, topic, research_area: area })
      notify.success('Project created')
      setName(''); setTopic(''); setArea('Education')
      setShowForm(false)
      refresh()
    } catch (err: any) {
      notify.error(err?.response?.data?.detail || err.message)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">Projects</h2>
          <p className="text-slate-500 mt-1">Your research workspaces.</p>
        </div>
        <button
          onClick={() => setShowForm(s => !s)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
        >
          <Plus size={16} /> New Project
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={submit}
          className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 shadow-sm"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Project name
            </label>
            <input
              required
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="AI Tutoring Study"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Research topic
            </label>
            <textarea
              required
              value={topic}
              onChange={e => setTopic(e.target.value)}
              rows={3}
              placeholder="Effect of AI-assisted learning on engineering students"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Research area
            </label>
            <select
              value={area}
              onChange={e => setArea(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
            >
              {['Education', 'Computer Science', 'Medicine', 'Physics', 'Biology', 'Chemistry', 'Other'].map(o => (
                <option key={o}>{o}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={creating}
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              {creating && <Loader2 className="animate-spin" size={16} />}
              Create
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : projects.length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title="No projects yet"
          description="Create your first research workspace to start uploading papers and generating hypotheses."
          action={{
            label: 'Create a project',
            onClick: () => setShowForm(true),
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map(p => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              className="block bg-white rounded-xl border border-slate-200 p-5 hover:border-brand-500 hover:shadow-md transition"
            >
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-100 text-brand-700">
                {p.research_area}
              </span>
              <h3 className="font-semibold text-slate-900 mt-2">{p.name}</h3>
              <p className="text-sm text-slate-500 mt-1 line-clamp-2">{p.topic}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}