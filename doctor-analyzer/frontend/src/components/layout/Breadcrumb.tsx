import { ArrowLeft, ChevronRight } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  const navigate = useNavigate()

  return (
    <nav className="flex items-center gap-2 text-sm mb-4">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center text-gray-600 hover:text-gray-900 transition"
      >
        <ArrowLeft className="w-4 h-4" />
      </button>
      {items.map((item, index) => {
        const isLast = index === items.length - 1

        return (
          <span key={index} className="flex items-center gap-1">
            {index > 0 && <ChevronRight className="w-4 h-4 text-gray-400" />}
            {isLast || !item.href ? (
              <span className="text-gray-500">{item.label}</span>
            ) : (
              <Link
                to={item.href}
                className="text-blue-600 hover:underline"
              >
                {item.label}
              </Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
