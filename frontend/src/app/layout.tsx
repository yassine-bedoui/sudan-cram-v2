import type { Metadata } from 'next'
import './globals.css'
import 'leaflet/dist/leaflet.css'  // ADD THIS LINE

export const metadata: Metadata = {
  title: 'Sudan CRAM - Climate & Conflict Risk',
  description: 'Sudan Climate & Conflict Risk Assessment Monitor',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}