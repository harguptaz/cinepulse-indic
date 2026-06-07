import React, { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, Cell, ResponsiveContainer, ReferenceLine,
} from 'recharts'

const ASPECT_LABELS = {
  acting     : 'Acting',
  audio      : 'Music',
  technical  : 'Visuals',
  plot       : 'Plot',
  dub_quality: 'Dubbing',
  direction  : 'Direction',
}

const VIEW_MODES = [
  { key: 'score',    label: 'Sentiment Score'  },
  { key: 'positive', label: 'Positive %'        },
  { key: 'negative', label: 'Negative %'        },
  { key: 'volume',   label: 'Comment Volume'    },
]

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1C1C26', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '10px', padding: '12px 16px', fontSize: '12px', minWidth: '160px',
    }}>
      <div style={{ fontWeight: '700', marginBottom: '8px', color: '#F0F0F0' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', color: '#ccc', marginBottom: '4px' }}>
          <span style={{ color: p.fill }}>{p.name}</span>
          <span style={{ fontWeight: '600' }}>
            {typeof p.value === 'number'
              ? p.value > 1 ? `${p.value.toFixed(1)}%` : p.value.toFixed(3)
              : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function AspectBarChart({ overview }) {
  const [viewMode, setViewMode] = useState('score')
  const languages    = overview?.languages ?? {}
  const hindiAspects = languages?.hindi?.aspects  ?? {}
  const teluguAspects= languages?.telugu?.aspects ?? {}

  const aspects = Object.keys(ASPECT_LABELS)

  const data = aspects.map(aspect => {
    const hi = hindiAspects[aspect]  ?? {}
    const te = teluguAspects[aspect] ?? {}

    const getValue = (d) => {
      switch (viewMode) {
        case 'score'   : return +(d.weighted_sentiment_score ?? 0).toFixed(3)
        case 'positive': return +(d.positive_pct ?? 0).toFixed(1)
        case 'negative': return +(d.negative_pct ?? 0).toFixed(1)
        case 'volume'  : return d.comment_count ?? 0
      }
    }

    return {
      aspect: ASPECT_LABELS[aspect],
      Hindi : getValue(hi),
      Telugu: getValue(te),
    }
  })

  const isScoreMode = viewMode === 'score'

  return (
    <div>
      {/* View toggle */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
        {VIEW_MODES.map(({ key, label }) => (
          <button key={key}
            onClick={() => setViewMode(key)}
            style={{
              padding       : '6px 14px',
              borderRadius  : '20px',
              border        : '1px solid',
              borderColor   : viewMode === key ? '#FFB703' : 'rgba(255,255,255,0.1)',
              background    : viewMode === key ? 'rgba(255,183,3,0.12)' : 'transparent',
              color         : viewMode === key ? '#FFB703' : '#888899',
              fontSize      : '12px',
              fontWeight    : '600',
              cursor        : 'pointer',
              transition    : 'all 0.2s',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }} barGap={4}>
          <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="aspect"
            tick={{ fill: '#888899', fontSize: 12 }}
            axisLine={false} tickLine={false}
          />
          <YAxis
            domain={isScoreMode ? [-1, 1] : [0, 100]}
            tick={{ fill: '#555566', fontSize: 11 }}
            axisLine={false} tickLine={false}
            tickFormatter={v => isScoreMode ? v.toFixed(1) : `${v}%`}
          />
          {isScoreMode && (
            <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" strokeDasharray="4 4" />
          )}
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(val) => (
              <span style={{ color: '#888899', fontSize: 12 }}>{val}</span>
            )}
          />
          <Bar dataKey="Hindi"  fill="#E85D04" radius={[4,4,0,0]} maxBarSize={32} />
          <Bar dataKey="Telugu" fill="#0077B6" radius={[4,4,0,0]} maxBarSize={32} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
