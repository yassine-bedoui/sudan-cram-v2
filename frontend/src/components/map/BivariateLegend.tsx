'use client'

import { BIVARIATE_COLORS } from '@/lib/bivariate-colors'

export function BivariateLegend() {
  // 3x3 grid layout
  const grid = [
    ['3-3', '3-2', '3-1'],
    ['2-3', '2-2', '2-1'],
    ['1-3', '1-2', '1-1'],
  ]

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Bivariate Legend</h3>
      
      {/* 3x3 Color Grid */}
      <div className="mb-4">
        <div className="grid grid-cols-3 gap-1">
          {grid.map((row, rowIdx) => (
            <React.Fragment key={rowIdx}>
              {row.map((key) => {
                const bvClass = BIVARIATE_COLORS[key]
                return (
                  <div
                    key={key}
                    className="w-16 h-16 flex items-center justify-center text-xs font-bold border border-slate-600"
                    style={{ backgroundColor: bvClass.color }}
                    title={bvClass.label}
                  >
                    {key}
                  </div>
                )
              })}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Axis Labels */}
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">↑ Conflict Proneness</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Climate Risk →</span>
        </div>
      </div>
    </div>
  )
}
