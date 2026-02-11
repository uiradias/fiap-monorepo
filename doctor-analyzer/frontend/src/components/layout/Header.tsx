import { Activity } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Doctor Analyzer</h1>
            <p className="text-sm text-gray-500">Patient Emotional Analysis System</p>
          </div>
        </div>
      </div>
    </header>
  )
}
