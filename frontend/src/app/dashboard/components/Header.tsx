import React from 'react'
import Image from 'next/image'

export function DashboardHeader() {
  return (
    <header className="bg-gradient-to-r from-slate-900 to-slate-800 border-b border-slate-700 sticky top-0 z-50">
      <div className="px-4 py-6 max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
            <span className="text-white font-bold text-xl">🇸🇩</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Sudan CRAM v2.0</h1>
            <p className="text-sm text-slate-400">Conflict Risk Assessment & Monitoring</p>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-3 px-4 py-2 bg-green-900/20 rounded-lg border border-green-700/30">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
          <span className="text-sm text-green-300 font-medium">Live Data • Last updated: Now</span>
        </div>
      </div>
    </header>
  )
}
