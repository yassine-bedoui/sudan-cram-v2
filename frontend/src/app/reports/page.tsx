'use client'

import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'

interface BriefResponse {
  brief: string
  generated_at: string
  regions_analyzed: number
  total_events: number
  total_fatalities: number
}

export default function ReportsPage() {
  const [brief, setBrief] = useState<BriefResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generateBrief = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/generate-brief`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error('Failed to generate brief')
      }

      const data = await response.json()
      setBrief(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
            📄 AI-Generated Reports
          </h1>
          <p className="text-slate-400">
            Automated conflict analysis briefs powered by Groq AI
          </p>
        </div>

        {/* Generate Button */}
        <div className="mb-6">
          <button
            onClick={generateBrief}
            disabled={loading}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              loading
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-teal-500 text-white hover:bg-teal-600'
            }`}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Generating Brief...
              </span>
            ) : (
              '🤖 Generate New Brief'
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-6">
            <p className="text-red-400">❌ Error: {error}</p>
          </div>
        )}

        {/* Brief Display */}
        {brief && (
          <div className="space-y-6">
            {/* Stats Bar */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">Regions Analyzed</div>
                <div className="text-2xl font-bold text-white">{brief.regions_analyzed}</div>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">Total Events</div>
                <div className="text-2xl font-bold text-teal-400">
                  {brief.total_events.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">Total Fatalities</div>
                <div className="text-2xl font-bold text-red-400">
                  {brief.total_fatalities.toLocaleString()}
                </div>
              </div>
            </div>

            {/* Brief Content */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-8">
              <div className="prose prose-invert prose-slate max-w-none">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => (
                      <h1 className="text-3xl font-bold text-white mb-4">{children}</h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-2xl font-bold text-white mt-8 mb-4">{children}</h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-xl font-bold text-white mt-6 mb-3">{children}</h3>
                    ),
                    p: ({ children }) => (
                      <p className="text-slate-300 mb-4 leading-relaxed">{children}</p>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc list-inside text-slate-300 mb-4 space-y-2">
                        {children}
                      </ul>
                    ),
                    li: ({ children }) => <li className="text-slate-300">{children}</li>,
                    strong: ({ children }) => (
                      <strong className="text-white font-semibold">{children}</strong>
                    ),
                    em: ({ children }) => (
                      <em className="text-slate-400 italic">{children}</em>
                    ),
                    hr: () => <hr className="border-slate-700 my-6" />,
                  }}
                >
                  {brief.brief}
                </ReactMarkdown>
              </div>

              {/* Timestamp */}
              <div className="mt-8 pt-6 border-t border-slate-700">
                <p className="text-slate-500 text-sm">
                  Generated: {new Date(brief.generated_at).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Export Button */}
            <div className="flex gap-4">
              <button
                onClick={() => {
                  const blob = new Blob([brief.brief], { type: 'text/markdown' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `sudan-brief-${new Date().toISOString().split('T')[0]}.md`
                  a.click()
                }}
                className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all"
              >
                📥 Export as Markdown
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!brief && !loading && !error && (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📄</div>
            <div className="text-slate-400 text-lg mb-2">
              No reports generated yet
            </div>
            <div className="text-slate-500 text-sm">
              Click "Generate New Brief" to create your first AI-powered report
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
