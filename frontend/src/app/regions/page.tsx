'use client'

import { Layout } from '@/components/layout/Layout'

export default function RegionsPage() {
  return (
    <Layout>
      <div>
        <h1 className="text-3xl font-bold text-white mb-4">Regional Comparison</h1>
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 h-[600px] flex items-center justify-center">
          <p className="text-slate-400">State-by-State Comparison - Coming soon</p>
        </div>
      </div>
    </Layout>
  )
}
