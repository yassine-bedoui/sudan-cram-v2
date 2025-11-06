'use client'

export default function Sidebar({ selectedIndicator, onSelectIndicator }: { selectedIndicator: string; onSelectIndicator: (id: string) => void }) {
  const indicators = [
    { id: 'climate-risk', label: 'Climate Risk', icon: '☁️' },
    { id: 'conflict-risk', label: 'Conflict Risk', icon: '⚡' },
    { id: 'combined-risk', label: 'Compound Risk', icon: '⚠️' },
  ]

  return (
    <aside className="w-64 border-r border-gray-200 overflow-y-auto bg-white">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xs uppercase tracking-widest text-gray-600 mb-4 font-bold">
          Indicator Layers
        </h2>
        <div className="space-y-3">
          {indicators.map(indicator => (
            <button
              key={indicator.id}
              onClick={() => onSelectIndicator(indicator.id)}
              className="w-full border border-gray-300 p-3 text-left text-xs uppercase tracking-wide hover:border-gray-400 transition-colors bg-white text-gray-900 font-medium"
            >
              <i className="mr-2">{indicator.icon}</i>
              {indicator.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 space-y-2 border-b border-gray-200">
        <button className="w-full text-left text-xs uppercase tracking-wide text-orange-600 hover:text-orange-700 py-2 font-medium transition">
          <i className="mr-2">📥</i>Download Data
        </button>
        <button className="w-full text-left text-xs uppercase tracking-wide text-orange-600 hover:text-orange-700 py-2 font-medium transition">
          <i className="mr-2">📄</i>Generate Report
        </button>
      </div>

      <div className="p-6 space-y-2">
        <button className="w-full border border-gray-300 bg-white text-gray-900 p-3 text-xs uppercase tracking-wide hover:bg-gray-100 transition-colors font-medium">
          <i className="mr-2">🔄</i>Reset All Filters
        </button>
        <button className="w-full border border-gray-300 bg-white text-gray-900 p-3 text-xs uppercase tracking-wide hover:bg-gray-100 transition-colors font-medium">
          <i className="mr-2">🗺️</i>Change Map Style
        </button>
      </div>
    </aside>
  )
}
