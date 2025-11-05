'use client'

import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
      <div className="text-center px-4">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-2xl">
            <span className="text-white font-bold text-5xl">🇸🇩</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-5xl font-bold text-white mb-4">Sudan CRAM v2.0</h1>
        <p className="text-xl text-slate-300 mb-12 max-w-2xl mx-auto">
          Comprehensive conflict risk assessment and monitoring platform for Sudan
        </p>

        {/* CTA Button */}
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-3 px-8 py-4 bg-teal-500 hover:bg-teal-600 text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl"
        >
          <span>Enter Dashboard</span>
          <span>→</span>
        </Link>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
            <div className="text-4xl mb-3">📊</div>
            <h3 className="text-white font-semibold mb-2">Real-time Data</h3>
            <p className="text-sm text-slate-400">Live conflict monitoring across 19 Sudanese states</p>
          </div>

          <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
            <div className="text-4xl mb-3">🗺️</div>
            <h3 className="text-white font-semibold mb-2">Interactive Maps</h3>
            <p className="text-sm text-slate-400">Geospatial risk visualization and analysis</p>
          </div>

          <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
            <div className="text-4xl mb-3">📈</div>
            <h3 className="text-white font-semibold mb-2">Forecasting</h3>
            <p className="text-sm text-slate-400">Predictive analytics for conflict trends</p>
          </div>
        </div>
      </div>
    </div>
  )
}
