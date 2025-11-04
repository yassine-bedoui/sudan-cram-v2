export function RiskLegend() {
  const categories = [
    { label: 'VERY HIGH', color: '#dc2626', range: '9-10' },
    { label: 'HIGH', color: '#ea580c', range: '7-8' },
    { label: 'MODERATE', color: '#ca8a04', range: '5-6' },
    { label: 'LOW', color: '#16a34a', range: '3-4' },
    { label: 'VERY LOW', color: '#64748b', range: '0-2' }
  ]

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Risk Level Legend</h3>
      <div className="space-y-2">
        {categories.map((cat) => (
          <div key={cat.label} className="flex items-center gap-3">
            <div
              className="w-6 h-6 rounded-full border-2 border-white shadow"
              style={{ backgroundColor: cat.color }}
            />
            <div className="flex-1">
              <p className="text-white text-sm font-medium">{cat.label}</p>
              <p className="text-slate-400 text-xs">Score: {cat.range}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
