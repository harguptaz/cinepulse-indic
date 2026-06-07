import React from 'react'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Legend, ResponsiveContainer, Tooltip,
} from 'recharts'

const ASPECT_LABELS = {
  acting     : 'Acting',
  audio      : 'Music & Audio',
  technical  : 'Visuals',
  plot       : 'Story & Plot',
  dub_quality: 'Dubbing',
  direction  : 'Direction',
}

// Convert -1..+1 score to 0..100 for radar chart
const toRadar = (score) => Math.round(((score ?? 0) + 1) / 2 * 100)

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1C1C26', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '10px', padding: '10px 14px', fontSize: '12px',
    }}>
      <div style={{ fontWeight: '700', marginBottom: '6px', color: '#F0F0F0' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: p.color }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: p.color, display: 'inline-block' }} />
          <span>{p.name}: {p.value}</span>
        </div>
      ))}
    </div>
  )
}

const CustomLegend = () => (
  <div style={{ display: 'flex', justifyContent: 'center', gap: '28px', marginTop: '8px' }}>
    {[
      { color: '#E85D04', label: 'Hindi' },
      { color: '#0077B6', label: 'Telugu' },
    ].map(({ color, label }) => (
      <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ width: '12px', height: '3px', background: color, display: 'inline-block', borderRadius: '2px' }} />
        <span style={{ fontSize: '13px', color: '#888899' }}>{label}</span>
      </div>
    ))}
  </div>
)

export default function AspectRadar({ overview }) {
  const languages = overview?.languages ?? {}
  const hindiAspects  = languages?.hindi?.aspects  ?? {}
  const teluguAspects = languages?.telugu?.aspects ?? {}

  const aspects = Object.keys(ASPECT_LABELS).filter(
    a => a !== 'general'
  )

  const data = aspects.map(aspect => ({
    aspect: ASPECT_LABELS[aspect],
    Hindi : toRadar(hindiAspects[aspect]?.weighted_sentiment_score),
    Telugu: toRadar(teluguAspects[aspect]?.weighted_sentiment_score),
  }))

  return (
    <div style={{ width: '100%', height: '360px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid
            stroke="rgba(255,255,255,0.08)"
            gridType="polygon"
          />
          <PolarAngleAxis
            dataKey="aspect"
            tick={{ fill: '#888899', fontSize: 12, fontFamily: "'DM Sans', sans-serif" }}
          />
          <PolarRadiusAxis
            angle={90} domain={[0, 100]}
            tick={{ fill: '#555566', fontSize: 10 }}
            tickCount={5}
            stroke="rgba(255,255,255,0.05)"
          />
          <Radar
            name="Hindi"
            dataKey="Hindi"
            stroke="#E85D04"
            fill="#E85D04"
            fillOpacity={0.15}
            strokeWidth={2}
          />
          <Radar
            name="Telugu"
            dataKey="Telugu"
            stroke="#0077B6"
            fill="#0077B6"
            fillOpacity={0.15}
            strokeWidth={2}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
