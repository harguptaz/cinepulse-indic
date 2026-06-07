import React, { useState, useEffect, useCallback } from 'react'
import { fetchOverview, fetchTimeline, fetchReportData, fetchPipelineStatus } from '../services/api.js'

import MovieHeader       from '../components/MovieHeader/MovieHeader.jsx'
import SentimentCards    from '../components/SentimentOverview/SentimentCards.jsx'
import AspectRadar       from '../components/AspectAnalysis/AspectRadar.jsx'
import AspectBarChart    from '../components/AspectAnalysis/AspectBarChart.jsx'
import SentimentTimeline from '../components/Timeline/SentimentTimeline.jsx'
import CommentFeed       from '../components/CommentFeed/CommentFeed.jsx'
import ComparisonChart   from '../components/LanguageComparison/ComparisonChart.jsx'
import ExportButton      from '../components/ReportExport/ExportButton.jsx'

// ── Section wrapper ───────────────────────────────────────────
function Section({ title, subtitle, children, action }) {
  return (
    <section style={sectionStyle}>
      <div style={{
        display        : 'flex',
        justifyContent : 'space-between',
        alignItems     : 'flex-start',
        marginBottom   : '20px',
        gap            : '12px',
      }}>
        <div>
          <h2 style={sectionTitleStyle}>{title}</h2>
          {subtitle && (
            <p style={{ fontSize: '13px', color: '#555566', marginTop: '4px' }}>{subtitle}</p>
          )}
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}

// ── Skeleton loader ───────────────────────────────────────────
function Skeleton({ height = 200 }) {
  return (
    <div style={{
      height,
      background    : 'linear-gradient(90deg, #1C1C26 25%, #222230 50%, #1C1C26 75%)',
      backgroundSize: '200% 100%',
      borderRadius  : '12px',
      animation     : 'shimmer 1.5s infinite',
    }} />
  )
}

// ── Error state ───────────────────────────────────────────────
function ErrorState({ message }) {
  return (
    <div style={{
      padding      : '60px 40px',
      textAlign    : 'center',
      background   : '#13131A',
      border       : '1px solid rgba(248,113,113,0.2)',
      borderRadius : '20px',
    }}>
      <div style={{ fontSize: '36px', marginBottom: '16px' }}>⚠️</div>
      <h3 style={{ fontFamily: "'Syne', sans-serif", color: '#f87171', marginBottom: '12px' }}>
        Pipeline Data Not Found
      </h3>
      <p style={{ color: '#888899', fontSize: '14px', lineHeight: 1.6, maxWidth: '480px', margin: '0 auto' }}>
        {message || 'Run the pipeline first to generate analysis data.'}
      </p>
      <div style={{
        marginTop   : '24px',
        padding     : '12px 20px',
        background  : '#1C1C26',
        borderRadius: '10px',
        display     : 'inline-block',
        fontFamily  : "'DM Mono', monospace",
        fontSize    : '13px',
        color       : '#FFB703',
        border      : '1px solid rgba(255,183,3,0.2)',
      }}>
        cd backend &amp;&amp; python run_pipeline.py
      </div>
    </div>
  )
}

// ── Recommendations panel ─────────────────────────────────────
function Recommendations({ reportData }) {
  const recs = reportData?.recommendations ?? []
  if (!recs.length) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {recs.map((rec, i) => (
        <div key={i} style={{
          display     : 'flex',
          gap         : '12px',
          padding     : '14px 16px',
          background  : 'rgba(255,183,3,0.04)',
          border      : '1px solid rgba(255,183,3,0.12)',
          borderRadius: '12px',
          borderLeft  : '3px solid #FFB703',
        }}>
          <span style={{ color: '#FFB703', fontSize: '16px', flexShrink: 0, marginTop: '1px' }}>▸</span>
          <p style={{ fontSize: '13px', color: '#C0C0C0', lineHeight: 1.6 }}>{rec}</p>
        </div>
      ))}
    </div>
  )
}

// ── Main Dashboard ────────────────────────────────────────────
export default function Dashboard() {
  const [overview,   setOverview]   = useState(null)
  const [timeline,   setTimeline]   = useState(null)
  const [reportData, setReportData] = useState(null)
  const [status,     setStatus]     = useState(null)
  const [error,      setError]      = useState(null)
  const [loading,    setLoading]    = useState(true)

  const loadAll = useCallback(async () => {
    try {
      const [ov, tl, rd, st] = await Promise.allSettled([
        fetchOverview(),
        fetchTimeline(),
        fetchReportData(),
        fetchPipelineStatus(),
      ])

      if (ov.status === 'fulfilled') setOverview(ov.value)
      else setError(ov.reason?.response?.data?.detail ?? 'Failed to load analysis data')

      if (tl.status === 'fulfilled') setTimeline(tl.value)
      if (rd.status === 'fulfilled') setReportData(rd.value)
      if (st.status === 'fulfilled') setStatus(st.value)
    } catch (e) {
      setError('Could not connect to backend. Is the API server running?')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAll()
    // Poll status every 10s while pipeline is running
    const interval = setInterval(() => {
      fetchPipelineStatus()
        .then(s => {
          setStatus(s)
          if (s.status === 'done') loadAll()
        })
        .catch(() => {})
    }, 10000)
    return () => clearInterval(interval)
  }, [loadAll])

  return (
    <>
      <style>{`
        @keyframes shimmer {
          0%   { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>

      <div style={{ minHeight: '100vh', background: '#0A0A0F' }}>
        {/* Header */}
        <MovieHeader overview={overview} status={status} />

        {/* Main content */}
        <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '28px 32px' }}>
          {error && <ErrorState message={error} />}

          {!error && (
            <>
              {/* Row 1 — Sentiment overview cards */}
              <Section
                title="Sentiment Overview"
                subtitle="Overall sentiment distribution for each language community"
                action={<ExportButton />}
              >
                {loading
                  ? <div style={{ display: 'flex', gap: '20px' }}><Skeleton height={220} /><Skeleton height={220} /></div>
                  : <SentimentCards overview={overview} />
                }
              </Section>

              {/* Row 2 — Radar + Bar charts */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <Section
                  title="Aspect Radar"
                  subtitle="Hindi vs Telugu across all aspects"
                >
                  {loading ? <Skeleton height={340} /> : <AspectRadar overview={overview} />}
                </Section>

                <Section
                  title="Aspect Breakdown"
                  subtitle="Per-aspect comparison — switch metric above"
                >
                  {loading ? <Skeleton height={340} /> : <AspectBarChart overview={overview} />}
                </Section>
              </div>

              {/* Row 3 — Timeline */}
              <Section
                title="Sentiment Timeline"
                subtitle="Daily weighted sentiment scores since release"
              >
                {loading ? <Skeleton height={280} /> : <SentimentTimeline timeline={timeline} />}
              </Section>

              {/* Row 4 — Gap analysis + Recommendations */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <Section
                  title="Language Gap Analysis"
                  subtitle="Sentiment score delta between Hindi and Telugu communities"
                >
                  {loading
                    ? <Skeleton height={320} />
                    : <ComparisonChart reportData={reportData} />
                  }
                </Section>

                <Section
                  title="Director / Producer Insights"
                  subtitle="Actionable recommendations from sentiment analysis"
                >
                  {loading
                    ? <Skeleton height={320} />
                    : <Recommendations reportData={reportData} />
                  }
                </Section>
              </div>

              {/* Row 5 — Comment feed */}
              <Section
                title="Comment Feed"
                subtitle="Browse individual comments with sentiment and aspect labels"
              >
                <CommentFeed />
              </Section>
            </>
          )}
        </main>
      </div>
    </>
  )
}

const sectionStyle = {
  background   : '#13131A',
  border       : '1px solid rgba(255,255,255,0.06)',
  borderRadius : '20px',
  padding      : '24px',
  marginBottom : '20px',
}

const sectionTitleStyle = {
  fontFamily  : "'Syne', sans-serif",
  fontSize    : '16px',
  fontWeight  : '700',
  color       : '#E0E0E0',
}
