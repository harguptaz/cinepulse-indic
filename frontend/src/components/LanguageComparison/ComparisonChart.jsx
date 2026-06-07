import React from 'react'

const ASPECT_LABELS = {
  acting     : 'Acting & Performance',
  audio      : 'Music & Audio',
  technical  : 'VFX & Visuals',
  plot       : 'Story & Plot',
  dub_quality: 'Dubbing Quality',
  direction  : 'Direction',
}

function GapBar({ hindiScore, teluguScore, aspect }) {
  const label = ASPECT_LABELS[aspect] ?? aspect
  const hi = ((hindiScore  + 1) / 2) * 100
  const te = ((teluguScore + 1) / 2) * 100
  const gap = Math.abs(hi - te)

  const gapColor = gap > 25 ? '#FFB703' : gap > 15 ? '#888899' : '#333344'
  const hiColor  = hindiScore  > 0 ? '#4ade80' : '#f87171'
  const teColor  = teluguScore > 0 ? '#4ade80' : '#f87171'

  return (
    <div style={{ marginBottom: '20px' }}>
      {/* Label row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '13px', color: '#C0C0C0', fontWeight: '500' }}>{label}</span>
        {gap > 15 && (
          <span style={{
            fontSize: '11px', color: gapColor,
            padding: '2px 8px', borderRadius: '10px',
            background: `${gapColor}15`, border: `1px solid ${gapColor}33`,
          }}>
            Δ {gap.toFixed(0)}pt gap
          </span>
        )}
      </div>

      {/* Hindi bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
        <span style={{ fontSize: '11px', color: '#E85D04', width: '48px', textAlign: 'right', flexShrink: 0 }}>
          Hindi
        </span>
        <div style={{ flex: 1, height: '8px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${hi}%`,
            background: `linear-gradient(90deg, #E85D04, ${hiColor})`,
            borderRadius: '4px', transition: 'width 0.8s ease',
          }} />
        </div>
        <span style={{ fontSize: '11px', color: hiColor, width: '36px', flexShrink: 0 }}>
          {hindiScore > 0 ? '+' : ''}{hindiScore.toFixed(2)}
        </span>
      </div>

      {/* Telugu bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '11px', color: '#0077B6', width: '48px', textAlign: 'right', flexShrink: 0 }}>
          Telugu
        </span>
        <div style={{ flex: 1, height: '8px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${te}%`,
            background: `linear-gradient(90deg, #0077B6, ${teColor})`,
            borderRadius: '4px', transition: 'width 0.8s ease',
          }} />
        </div>
        <span style={{ fontSize: '11px', color: teColor, width: '36px', flexShrink: 0 }}>
          {teluguScore > 0 ? '+' : ''}{teluguScore.toFixed(2)}
        </span>
      </div>
    </div>
  )
}

export default function LanguageComparison({ reportData }) {
  const gaps = reportData?.gap_analysis ?? []

  if (!gaps.length) {
    return (
      <div style={{ color: '#555', textAlign: 'center', padding: '40px' }}>
        No gap analysis available
      </div>
    )
  }

  const biggestGap = gaps[0]

  return (
    <div>
      {/* Biggest gap callout */}
      {biggestGap && biggestGap.gap > 0.1 && (
        <div style={{
          padding: '12px 16px', marginBottom: '24px',
          background: 'rgba(255,183,3,0.06)',
          border: '1px solid rgba(255,183,3,0.2)',
          borderRadius: '12px', fontSize: '13px', color: '#D0D0D0',
        }}>
          <span style={{ color: '#FFB703', fontWeight: '600' }}>⚡ Biggest gap: </span>
          {ASPECT_LABELS[biggestGap.aspect] ?? biggestGap.aspect} — Hindi{' '}
          {biggestGap.hindi_score > 0 ? 'positive' : 'negative'} vs Telugu{' '}
          {biggestGap.telugu_score > 0 ? 'positive' : 'negative'}
          {' '}(Δ {(biggestGap.gap * 50).toFixed(0)}pt)
        </div>
      )}

      {/* All aspects */}
      {gaps.map(item => (
        <GapBar
          key={item.aspect}
          aspect={item.aspect}
          hindiScore={item.hindi_score ?? 0}
          teluguScore={item.telugu_score ?? 0}
        />
      ))}
    </div>
  )
}
