'use client'

import dynamic from 'next/dynamic'

const SudanMap = dynamic(
  () => import('@/components/map/SudanMap'),
  { 
    ssr: false,
    loading: () => (
      <div className="bg-gray-100 border border-gray-300 h-full flex items-center justify-center rounded">
        <div className="text-center">
          <p className="text-xs text-gray-600">Loading map...</p>
        </div>
      </div>
    )
  }
)

export default function MainMap({ indicator }) {
  return (
    <section className="flex-1">
      <div className="bg-gray-100 border border-gray-300 h-full rounded overflow-hidden">
        <SudanMap 
          backendAvailable={true}
          indicator={indicator}
        />
      </div>
    </section>
  )
}
