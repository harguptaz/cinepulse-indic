import React from 'react'
import { Film, MessageSquare, Calendar, Zap } from 'lucide-react'

const LANG_META = {
  hindi:  { label: 'Hindi',  color: '#E85D04', bg: 'rgba(232,93,4,0.12)'   },
  telugu: { label: 'Telugu', color: '#0077B6', bg: 'rgba(0,119,182,0.12)'  },
}

export default function MovieHeader({ overview, status }) {
  const languages = overview?.languages ?? {}
  const totalComments = Object.values(languages).reduce(
    (acc, l) => acc + (l.total_comments ?? 0), 0
  )

  const isPipelineRunning = status?.status === 'running'

  return (
    <header style={styles.wrapper}>
      {/* Left — title block */}
      <div style={styles.titleBlock}>
        <div style={styles.iconWrap}>
          <Film size={22} color="#FFB703" />
        </div>
        <div>
          <div style={styles.eyebrow}>CinePulse-Indic Analysis</div>
          <h1 style={styles.title}>
            {overview?.movie ?? 'Dhurandhar'}
          </h1>
          <div style={styles.tagline}>
            Cross-Linguistic Sentiment Mapping
          </div>
        </div>
      </div>

      {/* Right — stats */}
      <div style={styles.statsRow}>
        {/* Release date */}
        {overview?.release_date && (
          <div style={styles.statChip}>
            <Calendar size={13} color="#888899" />
            <span>{overview.release_date}</span>
          </div>
        )}

        {/* Total comments */}
        <div style={styles.statChip}>
          <MessageSquare size={13} color="#888899" />
          <span>{totalComments.toLocaleString()} comments</span>
        </div>

        {/* Language badges */}
        {Object.entries(languages).map(([lang, data]) => {
          const meta = LANG_META[lang] ?? { label: lang, color: '#aaa', bg: '#222' }
          return (
            <div key={lang} style={{
              ...styles.langBadge,
              color: meta.color,
              background: meta.bg,
              border: `1px solid ${meta.color}33`,
            }}>
              <span style={{ ...styles.langDot, background: meta.color }} />
              {meta.label}
              <span style={styles.langCount}>
                {data.total_comments?.toLocaleString()}
              </span>
            </div>
          )
        })}

        {/* Pipeline status indicator */}
        {isPipelineRunning && (
          <div style={styles.pipelineChip}>
            <Zap size={12} color="#FFB703" />
            <span>Pipeline running: {status.step_name}</span>
          </div>
        )}
      </div>
    </header>
  )
}

const styles = {
  wrapper: {
    display        : 'flex',
    alignItems     : 'center',
    justifyContent : 'space-between',
    flexWrap       : 'wrap',
    gap            : '16px',
    padding        : '28px 32px',
    background     : 'linear-gradient(135deg, #13131A 0%, #1C1C26 100%)',
    borderBottom   : '1px solid rgba(255,255,255,0.06)',
    position       : 'sticky',
    top            : 0,
    zIndex         : 100,
  },
  titleBlock: {
    display    : 'flex',
    alignItems : 'center',
    gap        : '16px',
  },
  iconWrap: {
    width          : '48px',
    height         : '48px',
    background     : 'rgba(255,183,3,0.12)',
    border         : '1px solid rgba(255,183,3,0.3)',
    borderRadius   : '12px',
    display        : 'flex',
    alignItems     : 'center',
    justifyContent : 'center',
    flexShrink     : 0,
  },
  eyebrow: {
    fontSize     : '11px',
    fontWeight   : '600',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color        : '#888899',
    marginBottom : '4px',
  },
  title: {
    fontSize  : '26px',
    fontFamily: "'Syne', sans-serif",
    fontWeight: '800',
    color     : '#F0F0F0',
    lineHeight: 1.1,
  },
  tagline: {
    fontSize : '13px',
    color    : '#555566',
    marginTop: '3px',
  },
  statsRow: {
    display   : 'flex',
    alignItems: 'center',
    flexWrap  : 'wrap',
    gap       : '10px',
  },
  statChip: {
    display       : 'flex',
    alignItems    : 'center',
    gap           : '6px',
    padding       : '6px 12px',
    background    : 'rgba(255,255,255,0.05)',
    border        : '1px solid rgba(255,255,255,0.08)',
    borderRadius  : '20px',
    fontSize      : '12px',
    color         : '#888899',
  },
  langBadge: {
    display      : 'flex',
    alignItems   : 'center',
    gap          : '6px',
    padding      : '6px 14px',
    borderRadius : '20px',
    fontSize     : '12px',
    fontWeight   : '600',
  },
  langDot: {
    width       : '7px',
    height      : '7px',
    borderRadius: '50%',
    flexShrink  : 0,
  },
  langCount: {
    opacity    : 0.7,
    marginLeft : '2px',
    fontWeight : '400',
  },
  pipelineChip: {
    display    : 'flex',
    alignItems : 'center',
    gap        : '6px',
    padding    : '6px 12px',
    background : 'rgba(255,183,3,0.1)',
    border     : '1px solid rgba(255,183,3,0.3)',
    borderRadius: '20px',
    fontSize   : '12px',
    color      : '#FFB703',
    animation  : 'pulse 2s ease infinite',
  },
}
