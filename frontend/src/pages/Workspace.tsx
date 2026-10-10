import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Upload, Play, Loader2, FileText, Type, X,
  FlaskConical, Lightbulb, AlertCircle, Network, Beaker,
} from 'lucide-react'
import {
  getProject, listPapers, uploadPaper, uploadTextPaper, runAnalysis,
  listGaps, listHypotheses,
  type Project, type Paper, type Gap, type Hypothesis,
} from '../api'
import { notify } from '../toast'

type InputMode = 'pdf' | 'text'

export default function Workspace() {
  const { id } = useParams()
  const projectId = Number(id)

  const [project, setProject] = useState<Project | null>(null)
  const [papers, setPapers] = useState<Paper[]>([])
  const [gaps, setGaps] = useState<Gap[]>([])
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])

  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  // Input mode: PDF or paste text
  const [inputMode, setInputMode] = useState<InputMode>('pdf')
  const [pasteTitle, setPasteTitle] = useState('')
  const [pasteText, setPasteText] = useState('')

  const refreshAll = async () => {
    try {
      const [p, pp, gg, hh] = await Promise.all([
        getProject(projectId),
        listPapers(projectId),
        listGaps(projectId),
        listHypotheses(projectId),
      ])
      setProject(p); setPapers(pp); setGaps(gg); setHypotheses(hh)
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err.message
      setError(msg)
      notify.error(msg)
    }
  }

  useEffect(() => {
    if (!isNaN(projectId)) refreshAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const handleUploadPdf = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    setUploading(true)

    const loadingId = notify.loading('Uploading PDF and extracting claims with Groq…')
    try {
      await uploadPaper(projectId, file)
      await refreshAll()
      notify.dismiss(loadingId)
      notify.success('PDF uploaded — claims extracted')
    } catch (err: any) {
      notify.dismiss(loadingId)
      const msg = err?.response?.data?.detail || err.message
      setError(msg)
      notify.error(msg)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const handlePasteSubmit = async () => {
    const title = pasteTitle.trim()
    const text = pasteText.trim()

    if (!title) { notify.error('Please enter a title'); return }
    if (text.length < 100) { notify.error('Text must be at least 100 characters'); return }

    setError(null)
    setUploading(true)

    const loadingId = notify.loading('Extracting claims with Groq…')
    try {
      const result = await uploadTextPaper(projectId, { title, text })
      await refreshAll()
      notify.dismiss(loadingId)
      notify.success(`Text analyzed — ${result.claims_extracted} claims extracted`)
      setPasteTitle('')
      setPasteText('')
    } catch (err: any) {
      notify.dismiss(loadingId)
      const msg = err?.response?.data?.detail || err.message
      setError(msg)
      notify.error(msg)
    } finally {
      setUploading(false)
    }
  }

  const handleAnalyze = async () => {
    setError(null)
    setAnalyzing(true)

    const loadingId = notify.loading('Analyzing papers and generating hypotheses with Groq…')
    try {
      const result = await runAnalysis(projectId)
      await refreshAll()
      notify.dismiss(loadingId)
      const found = result.gaps_found ?? 0
      const hyps = result.hypotheses_generated ?? 0
      notify.success(`Found ${found} gaps · Generated ${hyps} hypotheses`)
    } catch (err: any) {
      notify.dismiss(loadingId)
      const msg = err?.response?.data?.detail || err.message
      setError(msg)
      notify.error(msg)
    } finally {
      setAnalyzing(false)
    }
  }

  if (!project) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-slate-200 rounded animate-pulse" />
        <div className="h-4 w-96 bg-slate-200 rounded animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <header>
        <span className="text-xs px-2 py-0.5 rounded-full bg-brand-100 text-brand-700">
          {project.research_area}
        </span>
        <h2 className="text-3xl font-bold text-slate-900 mt-2">{project.name}</h2>
        <p className="text-slate-500 mt-1">{project.topic}</p>
      </header>

      {error && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ---------- Input Panel ---------- */}
      <section className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => setInputMode('pdf')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition ${
              inputMode === 'pdf'
                ? 'text-brand-700 bg-brand-50 border-b-2 border-brand-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Upload size={16} /> Upload PDF
          </button>
          <button
            onClick={() => setInputMode('text')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition ${
              inputMode === 'text'
                ? 'text-brand-700 bg-brand-50 border-b-2 border-brand-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Type size={16} /> Paste Text
          </button>
        </div>

        {/* Tab body */}
        <div className="p-6">
          {inputMode === 'pdf' ? (
            <div className="text-center py-4">
              <input
                ref={fileRef}
                type="file"
                accept="application/pdf"
                onChange={handleUploadPdf}
                className="hidden"
              />
              <button
                onClick={() => fileRef.current?.click()}
                disabled={uploading || analyzing}
                className="inline-flex items-center gap-2 bg-white border border-slate-300 hover:border-brand-500 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition"
              >
                {uploading ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />}
                {uploading ? 'Uploading…' : 'Choose PDF file'}
              </button>
              <p className="text-xs text-slate-500 mt-3">
                Text-based PDFs work best. Groq extracts claims automatically.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={pasteTitle}
                  onChange={e => setPasteTitle(e.target.value)}
                  placeholder="e.g. Notes on AI tutoring effectiveness"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Text content
                </label>
                <textarea
                  value={pasteText}
                  onChange={e => setPasteText(e.target.value)}
                  rows={10}
                  placeholder="Paste any research text — abstract, notes, section from a paper, dataset description, etc. Minimum 100 characters."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition font-mono text-sm"
                />
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-slate-500">
                    {pasteText.length} characters
                    {pasteText.length < 100 && pasteText.length > 0 && (
                      <span className="text-amber-600"> · need {100 - pasteText.length} more</span>
                    )}
                  </span>
                  {pasteText.length > 0 && (
                    <button
                      onClick={() => { setPasteText(''); setPasteTitle('') }}
                      className="text-xs text-slate-500 hover:text-slate-700 inline-flex items-center gap-1"
                    >
                      <X size={12} /> Clear
                    </button>
                  )}
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  onClick={handlePasteSubmit}
                  disabled={uploading || analyzing || pasteText.length < 100 || !pasteTitle.trim()}
                  className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition"
                >
                  {uploading ? <Loader2 className="animate-spin" size={16} /> : <Type size={16} />}
                  {uploading ? 'Analyzing…' : 'Analyze Text'}
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ---------- Action bar ---------- */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={handleAnalyze}
          disabled={analyzing || uploading || papers.length === 0}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition"
        >
          {analyzing ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
          {analyzing ? 'Analyzing…' : 'Run Analysis'}
        </button>

        <Link
          to={`/projects/${projectId}/graph`}
          className="flex items-center gap-2 bg-white border border-slate-300 hover:border-brand-500 px-4 py-2 rounded-lg text-sm font-medium transition"
        >
          <Network size={16} /> View Knowledge Graph
        </Link>
      </div>

      {/* ---------- Papers ---------- */}
      <section>
        <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-900 mb-3">
          <FileText size={18} /> Papers ({papers.length})
        </h3>
        {papers.length === 0 ? (
          <div className="bg-white rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500 text-sm">
            No papers yet — upload a PDF or paste text to begin.
          </div>
        ) : (
          <div className="space-y-2">
            {papers.map(p => (
              <div
                key={p.id}
                className="bg-white rounded-lg border border-slate-200 p-4 hover:border-brand-300 transition"
              >
                <div className="font-medium text-slate-900">{p.title}</div>
                {p.abstract && (
                  <p className="text-sm text-slate-500 mt-1 line-clamp-2">{p.abstract}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ---------- Gaps ---------- */}
      {gaps.length > 0 && (
        <section>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-900 mb-3">
            <FlaskConical size={18} /> Research Gaps ({gaps.length})
          </h3>
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
                  <span className="text-sm font-bold text-slate-900">
                    {g.opportunity_score.toFixed(0)}%
                  </span>
                </div>
                <div className="font-medium text-slate-900 text-sm">{g.title}</div>
                <p className="text-sm text-slate-500 mt-1 line-clamp-3">{g.description}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ---------- Hypotheses ---------- */}
      {hypotheses.length > 0 && (
        <section>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-900 mb-3">
            <Lightbulb size={18} /> Hypotheses ({hypotheses.length})
          </h3>
          <div className="space-y-4">
            {hypotheses.map(h => (
              <div
                key={h.id}
                className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition"
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <p className="font-medium text-slate-900 leading-relaxed">{h.text}</p>
                  <div className="text-2xl font-bold text-brand-600 shrink-0">
                    {h.overall_score.toFixed(0)}
                  </div>
                </div>

                {h.null_hypothesis && (
                  <p className="text-sm text-slate-500 italic mb-3">
                    H₀: {h.null_hypothesis}
                  </p>
                )}

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                  {([
                    ['Novelty', h.novelty_score],
                    ['Evidence', h.evidence_score],
                    ['Testability', h.testability_score],
                    ['Feasibility', h.feasibility_score],
                  ] as [string, number][]).map(([label, score]) => (
                    <div key={label}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-slate-500">{label}</span>
                        <span className="font-medium text-slate-700">
                          {score.toFixed(0)}
                        </span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full transition-all duration-500"
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap gap-4 text-xs text-slate-500 pt-3 border-t border-slate-100">
                  {h.independent_var && (
                    <div>
                      <span className="font-medium text-slate-700">IV:</span>{' '}
                      {h.independent_var}
                    </div>
                  )}
                  {h.dependent_var && (
                    <div>
                      <span className="font-medium text-slate-700">DV:</span>{' '}
                      {h.dependent_var}
                    </div>
                  )}
                </div>

                {/* Plan Experiment link */}
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <Link
                    to={`/hypotheses/${h.id}/plan`}
                    className="inline-flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 font-medium transition"
                  >
                    <Beaker size={14} /> Plan Experiment →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}