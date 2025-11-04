'use client'

export type IndicatorMode = 'conflict_proneness' | 'climate_risk' | 'combined_risk' | 'bivariate'

interface IndicatorSelectorProps {
  selected: IndicatorMode
  onChange: (mode: IndicatorMode) => void
}

export function IndicatorSelector({ selected, onChange }: IndicatorSelectorProps) {
  const options: { value: IndicatorMode; label: string; icon: string }[] = [
    { value: 'conflict_proneness', label: 'Conflict Proneness', icon: '⚡' },
    { value: 'climate_risk', label: 'Climate Risk', icon: '🌡️' },
    { value: 'combined_risk', label: 'Combined Risk', icon: '🎯' },
    { value: 'bivariate', label: 'Bivariate', icon: '🗺️' },
  ]

  return (
    <div className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-lg p-2">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            selected === option.value
              ? 'bg-teal-500 text-white shadow-lg'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <span className="mr-2">{option.icon}</span>
          {option.label}
        </button>
      ))}
    </div>
  )
}
