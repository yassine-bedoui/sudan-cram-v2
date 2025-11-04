'use client'

import { useEffect } from 'react'
import Plot from 'react-plotly.js'

export function ConflictMap() {
  return (
    <div className="w-full h-96">
      <Plot
        data={[
          {
            z: [
              [10.0, 9.75, 9.44, 8.49, 8.41],
              [6.43, 5.62, 5.42, 5.27, 5.00],
              [4.75, 4.52, 4.09, 4.02, 3.67],
              [3.40, 2.75, 3.06, 0.0, 0.0]
            ],
            colorscale: 'Reds',
            type: 'heatmap',
            hovertemplate: '<b>Political Risk: %{z:.2f}</b><extra></extra>'
          }
        ]}
        layout={{
          title: '',
          paper_bgcolor: 'rgba(15, 23, 42, 0)',
          plot_bgcolor: 'rgba(30, 41, 59, 0.5)',
          font: { color: '#e2e8f0' },
          margin: { l: 40, r: 40, t: 20, b: 40 },
          height: 350
        }}
        config={{ responsive: true }}
      />
    </div>
  )
}
