import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './Layout'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import Workspace from './pages/Workspace'
import KnowledgeGraph from './pages/KnowledgeGraph'
import ExperimentPlan from './pages/ExperimentPlan'
import AllGaps from './pages/AllGaps'
import AllHypotheses from './pages/AllHypotheses'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:id" element={<Workspace />} />
          <Route path="/projects/:id/graph" element={<KnowledgeGraph />} />
          <Route path="/hypotheses" element={<AllHypotheses />} />
          <Route path="/hypotheses/:id/plan" element={<ExperimentPlan />} />
          <Route path="/gaps" element={<AllGaps />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}