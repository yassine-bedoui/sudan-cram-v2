export default function AIAlertFeed() {
  const alerts = [
    {
      id: 1,
      title: 'High Conflict Risk Alert',
      description: 'Escalating tensions reported in North Darfur region. Risk index increased by 23% over the past week. Humanitarian access remains severely restricted.',
      timestamp: '2 hours ago',
      borderColor: 'border-orange-600',
    },
    {
      id: 2,
      title: 'Moderate Climate Risk Update',
      description: 'Flooding conditions persist in White Nile state. Rainfall patterns suggest continued risk through mid-October. Agricultural impact assessment ongoing.',
      timestamp: '4 hours ago',
      borderColor: 'border-orange-500',
    },
    {
      id: 3,
      title: 'Compound Risk Warning',
      description: 'Khartoum experiencing simultaneous climate stress and security concerns. Displacement pressure increasing. Early action recommended.',
      timestamp: '6 hours ago',
      borderColor: 'border-orange-400',
    }
  ]

  return (
    <div className="border border-gray-300 p-4 bg-white">
      <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-4 flex justify-between items-center font-bold">
        <span><i className="mr-2">🔔</i>AI Alert Feed</span>
        <button className="text-orange-600 hover:text-orange-700 transition">↻</button>
      </h3>
      <div className="space-y-3">
        {alerts.map(alert => (
          <div key={alert.id} className={`border-l-4 ${alert.borderColor} pl-3 py-2`}>
            <p className="text-xs font-bold text-gray-900">{alert.title}</p>
            <p className="text-xs text-gray-600 mt-1">{alert.description}</p>
            <p className="text-xs text-gray-500 mt-2">{alert.timestamp}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
