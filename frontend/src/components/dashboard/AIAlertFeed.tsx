'use client'

export default function AIAlertFeed() {
  const alerts = [
    {
      id: 1,
      level: 'HIGH',
      title: 'High Conflict Risk Alert',
      description: 'Escalating tensions reported in North Darfur region. Risk index increased by 23% over the past week. Humanitarian access remains severely restricted.',
      timestamp: '2 hours ago',
      color: 'bg-red-900 border-l-4 border-red-500'
    },
    {
      id: 2,
      level: 'MODERATE',
      title: 'Moderate Climate Risk Update',
      description: 'Flooding conditions persist in White Nile state. Rainfall patterns suggest continued risk through mid-October. Agricultural impact assessment ongoing.',
      timestamp: '4 hours ago',
      color: 'bg-orange-900 border-l-4 border-orange-500'
    },
    {
      id: 3,
      level: 'ALERT',
      title: 'Compound Risk Warning',
      description: 'Khartoum experiencing simultaneous climate stress and security concerns. Displacement pressure increasing. Early action recommended.',
      timestamp: '6 hours ago',
      color: 'bg-yellow-900 border-l-4 border-yellow-500'
    }
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold flex items-center gap-2">
          <span>🔔</span> AI Alert Feed
        </h3>
        <button className="text-gray-400 hover:text-white">↻</button>
      </div>

      <div className="space-y-3">
        {alerts.map(alert => (
          <div key={alert.id} className={`${alert.color} p-3 rounded text-sm`}>
            <h4 className="font-semibold text-white mb-1">{alert.title}</h4>
            <p className="text-gray-200 text-xs mb-2">{alert.description}</p>
            <p className="text-gray-400 text-xs">{alert.timestamp}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
