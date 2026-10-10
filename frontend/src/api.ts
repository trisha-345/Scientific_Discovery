import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
})

// ---------- Types ----------
export interface Project {
  id: number
  name: string
  topic: string
  research_area: string
  created_at: string
}

export interface Paper {
  id: number
  title: string | null
  abstract: string | null
}

export interface Gap {
  id: number
  gap_type: string
  title: string
  description: string
  evidence: any[] | null
  opportunity_score: number
}

export interface Hypothesis {
  id: number
  text: string
  null_hypothesis: string | null
  independent_var: string | null
  dependent_var: string | null
  control_vars: string[] | null
  novelty_score: number
  evidence_score: number
  testability_score: number
  feasibility_score: number
  overall_score: number
  evidence_chain: any[] | null
}

export interface DashboardStats {
  projects: number
  papers: number
  gaps: number
  hypotheses: number
}

export interface GraphNode {
  id: string
  type?: string
  data: {
    label: string
    kind: 'project' | 'paper' | 'claim' | 'gap' | 'hypothesis'
    detail?: string
    score?: number
    gap_type?: string
    claim_type?: string
    paper_id?: number
    gap_id?: number
    hyp_id?: number
  }
  position: { x: number; y: number }
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type?: string
  animated?: boolean
  style?: Record<string, any>
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ---------- Projects ----------
export const listProjects = () =>
  api.get<Project[]>('/api/projects').then(r => r.data)

export const createProject = (data: {
  name: string
  topic: string
  research_area?: string
}) => api.post<Project>('/api/projects', data).then(r => r.data)

export const getProject = (id: number) =>
  api.get<Project>(`/api/projects/${id}`).then(r => r.data)

// ---------- Papers ----------
export const listPapers = (projectId: number) =>
  api.get<Paper[]>(`/api/papers/${projectId}`).then(r => r.data)

export const uploadPaper = (projectId: number, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api
    .post(`/api/papers/upload?project_id=${projectId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then(r => r.data)
}

export const uploadTextPaper = (
  projectId: number,
  data: { title: string; text: string }
) =>
  api
    .post(`/api/papers/text?project_id=${projectId}`, data)
    .then(r => r.data)

// ---------- Analysis ----------
export const runAnalysis = (projectId: number) =>
  api.post(`/api/analyze/${projectId}`).then(r => r.data)

export const listGaps = (projectId: number) =>
  api.get<Gap[]>(`/api/analyze/${projectId}/gaps`).then(r => r.data)

export const listHypotheses = (projectId: number) =>
  api.get<Hypothesis[]>(`/api/analyze/${projectId}/hypotheses`).then(r => r.data)

export const getGraph = (projectId: number) =>
  api.get<GraphData>(`/api/analyze/${projectId}/graph`).then(r => r.data)

// ---------- Dashboard ----------
export const getStats = () =>
  api.get<DashboardStats>('/api/dashboard').then(r => r.data)
// ---------- Experiment Plans ----------
export interface ExperimentPlan {
  design_type: string
  participants: {
    population?: string
    sample_size?: string
    inclusion_criteria?: string[]
    exclusion_criteria?: string[]
    recruitment?: string
  }
  design: {
    conditions?: string[]
    randomization?: string
    blinding?: string
    duration?: string
  }
  procedure: string[]
  variables: {
    independent?: string[]
    dependent?: string[]
    controls?: string[]
    confounds_to_watch?: string[]
  }
  instruments: { name: string; purpose: string; source: string }[]
  statistical_analysis: Record<string, string>
  expected_outcome: string
  null_outcome: string
  threats_to_validity: string[]
  ethical_considerations: string[]
  timeline: { phase: string; duration: string }[]
}

export interface ExperimentPlanResponse {
  plan_id: number
  hypothesis_id: number
  plan: ExperimentPlan
  markdown: string
  cached: boolean
}

export const generateExperimentPlan = (hypothesisId: number) =>
  api
    .post<ExperimentPlanResponse>(`/api/hypotheses/${hypothesisId}/plan`)
    .then(r => r.data)

export const getExperimentPlan = (hypothesisId: number) =>
  api
    .get<ExperimentPlanResponse>(`/api/hypotheses/${hypothesisId}/plan`)
    .then(r => r.data)

export const deleteExperimentPlan = (hypothesisId: number) =>
  api
    .delete(`/api/hypotheses/${hypothesisId}/plan`)
    .then(r => r.data)