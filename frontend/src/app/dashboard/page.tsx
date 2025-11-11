'use client'

import React, { useState, useEffect } from 'react'
import Header from '@/components/dashboard/Header'
import Sidebar from '@/components/dashboard/Sidebar'
import MainMap from '@/components/dashboard/MainMap'
import RightPanel from '@/components/dashboard/RightPanel'

export default function DashboardPage() {
  const [selectedRegion, setSelectedRegion] = useState('All Regions')
  const [selectedDistrict, setSelectedDistrict] = useState('All Districts')
  const [selectedDate, setSelectedDate] = useState('2025-10-01')
  const [selectedIndicator, setSelectedIndicator] = useState('conflict-risk')

  return (
    <div className="flex h-screen bg-white text-gray-900" style={{ fontFamily: "'Inter', 'Roboto', sans-serif" }}>
      {/* Sidebar */}
      <Sidebar 
        selectedIndicator={selectedIndicator}
        onSelectIndicator={setSelectedIndicator}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Filter Bar */}
        <div className="border-b border-gray-200 bg-white px-6 py-4">
          <p className="text-xs text-gray-600 mb-4">
            Filter the map to visualize climate and conflict risks in Sudan by region and district.
          </p>
          <div className="flex gap-4">
            <select 
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="bg-white border border-gray-300 px-3 py-2 text-xs text-gray-900 rounded"
            >
              <option>All Regions</option>
              <option>Khartoum</option>
              <option>White Nile</option>
              <option>Blue Nile</option>
              <option>Gezira</option>
              <option>Kassala</option>
              <option>Red Sea</option>
              <option>North Darfur</option>
              <option>South Darfur</option>
              <option>West Darfur</option>
              <option>North Kordofan</option>
              <option>South Kordofan</option>
              <option>Sennar</option>
            </select>

            <select 
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="bg-white border border-gray-300 px-3 py-2 text-xs text-gray-900 rounded"
            >
              <option>All Districts</option>
              <option>Khartoum District</option>
              <option>Omdurman</option>
              <option>Bahri</option>
            </select>

            <input 
              type="date" 
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-white border border-gray-300 px-3 py-2 text-xs text-gray-900 rounded"
            />
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto flex gap-6 p-6">
          {/* Map Section */}
          <MainMap indicator={selectedIndicator} />

          {/* Right Panel - Now includes Goldstein */}
          <RightPanel />
        </div>
      </div>
    </div>
  )
}
