import React from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const LANG_CONFIG = {
  hindi:  { label: 'Hindi',  primary: '#E85D04', light: 'rgba(232,93,4,0.1)'   },
  telugu: { label: 'Telugu', primary: '#0077B6', light: 'rgba(0,119,182,0.1)'  },
}

const SENTIMENT_COLORS = ['#4ade80', '#f87171', '#9ca3af']

function ScoreGauge({ score }) {
  // score is -1 to +1; map to 0-100
  const pct = ((score + 1) / 2) * 100
  const color = score > 0.2 ? '#4ade80' : score < -0.2 ? '#f87171' : '#9ca3af'
  const radius = 34
  const circumference = 2 * Math.PI * radius
  const strokeDash = (pct / 100) * circumference

  return (
    <div style={{ position: 'relative', width: 88, height: 88 }}>
      <svg width="88" height="88" viewBox="0 0 88 88">
        <circle cx="44" cy="44" r={radius}
          fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
        <circle cx="44" cy="44" r={radius}
          fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={`${strokeDash} ${circumference}`}
          strokeLinecap="round"
          transform="rotate(-90 44 44)"
          style={{ transition: 'stroke-dasharray 0.8s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: '15px', fontWeight: '700', color, fontFamily: "'Syne', sans-serif" }}>
          {score > 0 ? '+' : ''}{score.toFixed(2)}
        </span>
        <span style={{ fontSize: '9px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          score
        </span>
      </div>
    </div>
  )
}

function SentimentDonut({ pos, neg, neu }) {
  const data = [
    { name: 'Positive', value: pos },
    { name: 'Negative', value: neg },
    { name: 'Neutral',  value: neu },
  ]
  return (
    <ResponsiveContainer width={100} height={100}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" innerRadius={28} outerRadius={44}
          dataKey="value" startAngle={90} endAngle={-270} paddingAngle={2}>
          {data.map((_, i) => (
            <Cell key={i} fill={SENTIMENT_COLORS[i]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(v) => `${v.toFixed(1)}%`}
          contentStyle={{ background: '#1C1C26', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

function SentimentBar({ label, value, color }) {
  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
        <span style={{ fontSize: '12px', color: '#888899' }}>{label}</span>
        <span style={{ fontSize: '12px', fontWeight: '600', color }}>{value.toFixed(1)}%</span>
      </div>
      <div style={{ height: '5px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${value}%`, background: color,
          borderRadius: '3px', transition: 'width 0.8s ease',
        }} />
      </div>
    </div>
  )
}

function LanguageCard({ lang, data }) {
  const cfg = LANG_CONFIG[lang] ?? { label: lang, primary: '#aaa', light: '#222' }
  const overall = data?.overall ?? {}
  const pos = overall.positive_pct ?? 0
  const neg = overall.negative_pct ?? 0
  const neu = overall.neutral_pct ?? 0
  const score = overall.weighted_sentiment_score ?? 0
  const total = data?.total_comments ?? 0

  const Icon = score > 0.1 ? TrendingUp : score < -0.1 ? TrendingDown : Minus
  const iconColor = score > 0.1 ? '#4ade80' : score < -0.1 ? '#f87171' : '#9ca3af'
  const verdict = score > 0.3 ? 'Strong Positive' : score > 0.1 ? 'Mildly Positive'
    : score < -0.3 ? 'Strong Negative' : score < -0.1 ? 'Mildly Negative' : 'Neutral'

  return (
    <div style={{
      ...cardStyle,
      borderTop: `3px solid ${cfg.primary}`,
      flex: 1,
      minWidth: '280px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{
              width: '10px', height: '10px', borderRadius: '50%',
              background: cfg.primary, display: 'inline-block',
            }} />
            <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: '700', fontSize: '18px' }}>
              {cfg.label}
            </span>
          </div>
          <div style={{ fontSize: '12px', color: '#888899' }}>
            {total.toLocaleString()} comments analysed
          </div>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '5px 10px', borderRadius: '20px',
          background: score > 0 ? 'rgba(74,222,128,0.1)' : score < 0 ? 'rgba(248,113,113,0.1)' : 'rgba(156,163,175,0.1)',
          border: `1px solid ${iconColor}33`,
        }}>
          <Icon size={13} color={iconColor} />
          <span style={{ fontSize: '11px', color: iconColor, fontWeight: '600' }}>{verdict}</span>
        </div>
      </div>

      {/* Visuals */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px' }}>
        <ScoreGauge score={score} />
        <SentimentDonut pos={pos} neg={neg} neu={neu} />
        <div style={{ flex: 1 }}>
          <SentimentBar label="Positive" value={pos} color="#4ade80" />
          <SentimentBar label="Negative" value={neg} color="#f87171" />
          <SentimentBar label="Neutral"  value={neu} color="#9ca3af" />
        </div>
      </div>

      {/* Source breakdown */}
      {data?.source_breakdown && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {Object.entries(data.source_breakdown).map(([src, cnt]) => (
            <div key={src} style={{
              padding: '3px 10px', borderRadius: '12px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              fontSize: '11px', color: '#666677',
            }}>
              {src}: {cnt}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function SentimentCards({ overview }) {
  const languages = overview?.languages ?? {}

  if (!Object.keys(languages).length) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#555' }}>
        No data available — run the pipeline first.
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
      {Object.entries(languages).map(([lang, data]) => (
        <LanguageCard key={lang} lang={lang} data={data} />
      ))}
    </div>
  )
}

const cardStyle = {
  background   : '#13131A',
  border       : '1px solid rgba(255,255,255,0.08)',
  borderRadius : '20px',
  padding      : '24px',
}
