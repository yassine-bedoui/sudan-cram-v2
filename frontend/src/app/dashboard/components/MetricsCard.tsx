interface MetricsCardProps {
  title: string
  value: number | string
  change: string
  color: 'red' | 'orange' | 'yellow' | 'green'
  icon: string
}

export function MetricsCard({ title, value, change, color, icon }: MetricsCardProps) {
  const colorClasses = {
    red: 'from-red-900/20 to-red-800/10 border-red-700/30',
    orange: 'from-orange-900/20 to-orange-800/10 border-orange-700/30',
    yellow: 'from-yellow-900/20 to-yellow-800/10 border-yellow-700/30',
    green: 'from-green-900/20 to-green-800/10 border-green-700/30'
  }

  const textColors = {
    red: 'text-red-300',
    orange: 'text-orange-300',
    yellow: 'text-yellow-300',
    green: 'text-green-300'
  }

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-lg border p-6`}>
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-sm font-medium text-slate-300">{title}</h3>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="mb-2">
        <p className="text-3xl font-bold text-white">{value}</p>
      </div>
      <p className={`text-sm font-medium ${textColors[color]}`}>{change} this month</p>
    </div>
  )
}
