import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Loader2, ArrowLeft, Download, RefreshCw, FlaskConical,
  Users, ClipboardList, BarChart3, Clock, AlertTriangle,
  ShieldCheck, Wrench,
} from 'lucide-react'
import {
  getExperimentPlan, generateExperimentPlan, deleteExperimentPlan,
  type ExperimentPlanResponse, type ExperimentPlan,
} from '../api'
import { notify } from '../toast'

export default function ExperimentPlanPage() {
  const { id } = useParams()  // hypothesis id
  const hypothesisId = Number(id)

  const [plan, setPlan] = useState<ExperimentPlanResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const loadExistingPlan = async () => {
    try {
      const existing = await getExperimentPlan(hypothesisId)
      setPlan(existing)
    } catch {
      setPlan(null)
    }
  }

  useEffect(() => {
    if (isNaN(hypothesisId)) return
    setLoading(true)
    loadExistingPlan().finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hypothesisId])

  const handleGenerate = async () => {
    setGenerating(true)
    const loadingId = notify.loading('Designing experiment with Groq…')
    try {
      const result = await generateExperimentPlan(hypothesisId)
      setPlan(result)
      notify.dismiss(loadingId)
      notify.success(result.cached ? 'Plan loaded' : 'Experiment plan generated')
    } catch (err: any) {
      notify.dismiss(loadingId)
      notify.error(err?.response?.data?.detail || err.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleRegenerate = async () => {
    setGenerating(true)
    const loadingId = notify.loading('Regenerating plan…')
    try {
      await deleteExperimentPlan(hypothesisId)
      const result = await generateExperimentPlan(hypothesisId)
      setPlan(result)
      notify.dismiss(loadingId)
      notify.success('Experiment plan regenerated')
    } catch (err: any) {
      notify.dismiss(loadingId)
      notify.error(err?.response?.data?.detail || err.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleDownload = () => {
    if (!plan?.markdown) return
    const blob = new Blob([plan.markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `experiment-plan-${hypothesisId}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    notify.success('Downloaded as Markdown')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-500">
        <Loader2 className="animate-spin mr-2" /> Loading…
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header>
        <Link
          to={`/hypotheses`}
          className="text-sm text-brand-600 hover:underline inline-flex items-center gap-1 mb-2"
        >
          <ArrowLeft size={14} /> Back to hypotheses
        </Link>
        <h2 className="text-3xl font-bold text-slate-900">Experiment Planner</h2>
        <p className="text-slate-500 mt-1 text-sm">
          Groq-designed experimental protocol for hypothesis #{hypothesisId}
        </p>
      </header>

      {!plan ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <FlaskConical className="mx-auto text-brand-600 mb-4" size={40} />
          <h3 className="text-lg font-semibold text-slate-900">
            No experiment plan yet
          </h3>
          <p className="text-slate-500 mt-2 max-w-md mx-auto">
            Let Groq design a complete experimental protocol: participants,
            variables, procedure, statistical tests, and timeline.
          </p>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="mt-6 inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition"
          >
            {generating ? <Loader2 className="animate-spin" size={16} /> : <FlaskConical size={16} />}
            {generating ? 'Designing…' : 'Generate Experiment Plan'}
          </button>
        </div>
      ) : (
        <>
          {/* Action bar */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              <Download size={16} /> Download Markdown
            </button>
            <button
              onClick={handleRegenerate}
              disabled={generating}
              className="flex items-center gap-2 bg-white border border-slate-300 hover:border-brand-500 px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50"
            >
              {generating ? <Loader2 className="animate-spin" size={16} /> : <RefreshCw size={16} />}
              {generating ? 'Regenerating…' : 'Regenerate'}
            </button>
          </div>

          <PlanView plan={plan.plan} />
        </>
      )}
    </div>
  )
}

// ---------- Presentational Components ----------

function PlanView({ plan }: { plan: ExperimentPlan }) {
  return (
    <div className="space-y-6">
      {/* Overview */}
      <Card icon={FlaskConical} title="Design Overview">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-100 text-brand-700 text-sm font-medium">
          {plan.design_type}
        </div>
      </Card>

      {/* Participants */}
      {plan.participants && (
        <Card icon={Users} title="Participants">
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Population" value={plan.participants.population} />
            <Field label="Sample size" value={plan.participants.sample_size} />
            {plan.participants.recruitment && (
              <Field label="Recruitment" value={plan.participants.recruitment} full />
            )}
            {plan.participants.inclusion_criteria?.length ? (
              <Field
                label="Inclusion criteria"
                value={plan.participants.inclusion_criteria}
                isList
              />
            ) : null}
            {plan.participants.exclusion_criteria?.length ? (
              <Field
                label="Exclusion criteria"
                value={plan.participants.exclusion_criteria}
                isList
              />
            ) : null}
          </dl>
        </Card>
      )}

      {/* Design */}
      {plan.design && (
        <Card icon={ClipboardList} title="Study Design">
          {plan.design.conditions?.length ? (
            <div className="mb-3">
              <div className="text-xs uppercase text-slate-500 mb-1">Conditions</div>
              <ul className="list-disc list-inside text-sm text-slate-700">
                {plan.design.conditions.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
          ) : null}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Field label="Randomization" value={plan.design.randomization} />
            <Field label="Blinding" value={plan.design.blinding} />
            <Field label="Duration" value={plan.design.duration} />
          </div>
        </Card>
      )}

      {/* Procedure */}
      {plan.procedure?.length ? (
        <Card icon={ClipboardList} title="Procedure">
          <ol className="space-y-2 text-sm text-slate-700 list-decimal list-inside">
            {plan.procedure.map((step, i) => <li key={i}>{step}</li>)}
          </ol>
        </Card>
      ) : null}

      {/* Variables */}
      {plan.variables && (
        <Card icon={BarChart3} title="Variables">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Field label="Independent" value={plan.variables.independent} isList />
            <Field label="Dependent" value={plan.variables.dependent} isList />
            <Field label="Controls" value={plan.variables.controls} isList />
            <Field
              label="Confounds to watch"
              value={plan.variables.confounds_to_watch}
              isList
            />
          </div>
        </Card>
      )}

      {/* Instruments */}
      {plan.instruments?.length ? (
        <Card icon={Wrench} title="Instruments & Measures">
          <ul className="space-y-2 text-sm text-slate-700">
            {plan.instruments.map((inst, i) => (
              <li key={i}>
                <span className="font-medium">{inst.name}</span>
                {inst.purpose ? <span> — {inst.purpose}</span> : null}
                {inst.source ? (
                  <span className="text-slate-500"> ({inst.source})</span>
                ) : null}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {/* Stats */}
      {plan.statistical_analysis &&
        Object.keys(plan.statistical_analysis).length > 0 && (
          <Card icon={BarChart3} title="Statistical Analysis">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(plan.statistical_analysis).map(([k, v]) => (
                <Field key={k} label={k.replace(/_/g, ' ')} value={String(v)} />
              ))}
            </dl>
          </Card>
        )}

      {/* Expected outcomes */}
      {plan.expected_outcome && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5">
            <div className="text-xs uppercase text-emerald-700 font-semibold mb-2">
              If H₁ is true
            </div>
            <p className="text-sm text-emerald-900">{plan.expected_outcome}</p>
          </div>
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-5">
            <div className="text-xs uppercase text-rose-700 font-semibold mb-2">
              If H₀ is true
            </div>
            <p className="text-sm text-rose-900">{plan.null_outcome}</p>
          </div>
        </div>
      )}

      {/* Threats & Ethics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plan.threats_to_validity?.length ? (
          <Card icon={AlertTriangle} title="Threats to Validity">
            <ul className="list-disc list-inside text-sm text-slate-700 space-y-1">
              {plan.threats_to_validity.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          </Card>
        ) : null}
        {plan.ethical_considerations?.length ? (
          <Card icon={ShieldCheck} title="Ethical Considerations">
            <ul className="list-disc list-inside text-sm text-slate-700 space-y-1">
              {plan.ethical_considerations.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </Card>
        ) : null}
      </div>

      {/* Timeline */}
      {plan.timeline?.length ? (
        <Card icon={Clock} title="Timeline">
          <div className="space-y-2">
            {plan.timeline.map((t, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
              >
                <span className="text-sm text-slate-700">{t.phase}</span>
                <span className="text-sm font-medium text-slate-900">
                  {t.duration}
                </span>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  )
}

function Card({
  icon: Icon,
  title,
  children,
}: {
  icon: any
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="bg-white rounded-xl border border-slate-200 p-5">
      <h3 className="flex items-center gap-2 text-base font-semibold text-slate-900 mb-3">
        <Icon size={16} className="text-brand-600" /> {title}
      </h3>
      {children}
    </section>
  )
}

function Field({
  label,
  value,
  isList,
  full,
}: {
  label: string
  value?: any
  isList?: boolean
  full?: boolean
}) {
  if (!value) return null
  return (
    <div className={full ? 'md:col-span-2' : ''}>
      <dt className="text-xs uppercase text-slate-500 mb-1">{label}</dt>
      <dd className="text-sm text-slate-700">
        {isList && Array.isArray(value) ? (
          <ul className="list-disc list-inside space-y-1">
            {value.map((v: string, i: number) => <li key={i}>{v}</li>)}
          </ul>
        ) : (
          String(value)
        )}
      </dd>
    </div>
  )
}