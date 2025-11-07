'use client'

import dynamic from 'next/dynamic'

const InteractiveMap = dynamic(
  () => import('./InteractiveMap'),
  { ssr: false }
)

export default function MainMap({ indicator }: { indicator: string }) {
  return <InteractiveMap indicator={indicator} />
}
