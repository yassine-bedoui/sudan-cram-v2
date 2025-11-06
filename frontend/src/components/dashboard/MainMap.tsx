'use client'

export default function MainMap({ indicator }) {
  return (
    <section className="flex-1">
      <div className="bg-white border border-gray-300 h-full rounded overflow-hidden flex items-center justify-center">
        <div className="text-center">
          <p className="text-4xl mb-2">🗺️</p>
          <p className="text-sm text-gray-600">Interactive Map View</p>
          <p className="text-xs text-gray-400 mt-2">({indicator})</p>
        </div>
      </div>
    </section>
  )
}
