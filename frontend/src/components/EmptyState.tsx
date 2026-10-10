import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    to?: string
    onClick?: () => void
  }
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-brand-50 text-brand-600 mb-4">
        <Icon size={28} />
      </div>
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      <p className="text-slate-500 mt-1 max-w-md mx-auto">{description}</p>
      {action && (
        <div className="mt-6">
          {action.to ? (
            <Link
              to={action.to}
              className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              {action.label}
            </Link>
          ) : (
            <button
              onClick={action.onClick}
              className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              {action.label}
            </button>
          )}
        </div>
      )}
    </div>
  )
}