'use client'

import React, { useState } from 'react'
import LeftSidebar from '@/components/dashboard/LeftSidebar'
import InteractiveMap from '@/components/dashboard/InteractiveMap'
import RightPanel from '@/components/dashboard/RightPanel'
import Header from '@/components/dashboard/Header'

export default function DashboardPage() {
  const [darkMode, setDarkMode] = useState(true)
  const [selectedIndicator, setSelectedIndicator] = useState('conflict-risk')

  return (
    <div className={`${darkMode ? 'dark' : ''}`}>
      <div className="bg-gray-900 text-white min-h-screen flex flex-col">
        {/* Header */}
        <Header 
          darkMode={darkMode} 
          onToggleDarkMode={() => setDarkMode(!darkMode)} 
        />

        {/* Main Content: 3-Column Layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar */}
          <LeftSidebar 
            selectedIndicator={selectedIndicator}
            onSelectIndicator={setSelectedIndicator}
          />

          {/* Main Map (Center - 70%) */}
          <div className="flex-1 bg-gray-800">
            <InteractiveMap indicator={selectedIndicator} />
          </div>

          {/* Right Panel (30%) */}
          <RightPanel />
        </div>
      </div>
    </div>
  )
}
