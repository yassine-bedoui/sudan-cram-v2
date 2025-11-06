'use client'

export default function LeftSidebar({ selectedIndicator, onSelectIndicator }) {
  const layers = [
    { id: 'climate-risk', label: 'Climate Risk', icon: '☁️' },
    { id: 'conflict-risk', label: 'Conflict Risk', icon: '⚡' },
    { id: 'conflict-proneness', label: 'Conflict Proneness', icon: '⚠️' },
    { id: 'combined-risk', label: 'Compound Risk', icon: '🟣' },
  ]

  return (
    <aside className="w-48 bg-gray-900 border-r border-gray-800 p-4 flex flex-col">
      <h3 className="text-xs font-bold uppercase text-gray-400 mb-4">Indicator Layers</h3>

      {/* Layer Buttons */}
      <div className="space-y-2 mb-8">
        {layers.map(layer => (
          <button
            key={layer.id}
            onClick={() => onSelectIndicator(layer.id)}
            className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 transition ${
              selectedIndicator === layer.id
                ? 'bg-teal-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            <span>{layer.icon}</span>
            <span className="text-sm font-medium">{layer.label}</span>
          </button>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="space-y-2 mb-8">
        <button className="w-full px-3 py-2 bg-teal-600 hover:bg-teal-700 rounded flex items-center gap-2 text-sm">
          <span>📥</span> Download Data
        </button>
        <button className="w-full px-3 py-2 bg-teal-600 hover:bg-teal-700 rounded flex items-center gap-2 text-sm">
          <span>📄</span> Generate Report
        </button>
      </div>

      {/* Secondary Buttons */}
      <div className="space-y-2 border-t border-gray-800 pt-4">
        <button className="w-full px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm">
          🔄 Reset All Filters
        </button>
        <button className="w-full px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm">
          🗺️ Change Map Style
        </button>
      </div>
    </aside>
  )
}
