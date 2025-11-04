'use client'

import React from 'react'

export function TopBar() {
  return (
    <header className="h-16 bg-slate-950 border-b border-slate-700 flex items-center justify-between px-6">
      {/* Breadcrumb / Page Title */}
      <div>
        <h2 className="text-lg font-semibold text-white">Dashboard Overview</h2>
        <p className="text-xs text-slate-400">Real-time conflict risk monitoring</p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        {/* Last Updated */}
        <div className="text-sm text-slate-400">
          Updated: <span className="text-slate-200 font-medium">Now</span>
        </div>

        {/* User Menu */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center">
            <span className="text-white text-sm font-bold">U</span>
          </div>
        </div>
      </div>
    </header>
  )
}
