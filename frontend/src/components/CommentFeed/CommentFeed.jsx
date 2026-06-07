import React, { useState, useEffect, useCallback } from 'react'
import { fetchComments } from '../../services/api.js'
import { MessageSquare, ChevronLeft, ChevronRight, Filter } from 'lucide-react'

const ASPECTS = ['all','acting','audio','technical','plot','dub_quality','direction','general']
const SENTIMENTS = ['all','POSITIVE','NEGATIVE','NEUTRAL']
const LANGS = ['all','hindi','telugu']
const SOURCES = ['all','youtube','reddit']

const SENTIMENT_STYLE = {
  POSITIVE: { label: '▲ Pos', bg: 'rgba(74,222,128,0.12)',  color: '#4ade80', border: 'rgba(74,222,128,0.25)'  },
  NEGATIVE: { label: '▼ Neg', bg: 'rgba(248,113,113,0.12)', color: '#f87171', border: 'rgba(248,113,113,0.25)' },
  NEUTRAL : { label: '~ Neu', bg: 'rgba(156,163,175,0.12)', color: '#9ca3af', border: 'rgba(156,163,175,0.25)' },
}
const LANG_STYLE = {
  hindi : { color: '#E85D04', bg: 'rgba(232,93,4,0.1)'  },
  telugu: { color: '#0077B6', bg: 'rgba(0,119,182,0.1)' },
}

function FilterPill({ value, options, onChange, label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
      <span style={{ fontSize: '11px', color: '#555566', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </span>
      {options.map(opt => (
        <button key={opt}
          onClick={() => onChange(opt)}
          style={{
            padding     : '4px 10px',
            borderRadius: '14px',
            border      : '1px solid',
            borderColor : value === opt ? '#FFB703' : 'rgba(255,255,255,0.08)',
            background  : value === opt ? 'rgba(255,183,3,0.1)' : 'transparent',
            color       : value === opt ? '#FFB703' : '#666677',
            fontSize    : '11px',
            cursor      : 'pointer',
            transition  : 'all 0.15s',
            whiteSpace  : 'nowrap',
          }}
        >
          {opt === 'all' ? 'All' : opt.replace('_', ' ')}
        </button>
      ))}
    </div>
  )
}

function CommentRow({ comment }) {
  const sentStyle = SENTIMENT_STYLE[comment.sentiment_label] ?? SENTIMENT_STYLE.NEUTRAL
  const langStyle = LANG_STYLE[comment.language]  ?? { color: '#aaa', bg: '#222' }
  const confidence = comment.sentiment_confidence
    ? ` (${(comment.sentiment_confidence * 100).toFixed(0)}%)`
    : ''

  return (
    <div style={rowStyle}>
      {/* Comment text */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{
          fontSize: '13px', lineHeight: '1.5', color: '#D0D0D0',
          overflow: 'hidden', display: '-webkit-box',
          WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        }}>
          {comment.text || '—'}
        </p>
        <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
          {/* Language badge */}
          <span style={{
            ...badgeBase, background: langStyle.bg,
            color: langStyle.color, border: `1px solid ${langStyle.color}33`,
          }}>
            {comment.language}
          </span>
          {/* Source badge */}
          <span style={{ ...badgeBase, background: 'rgba(255,255,255,0.05)', color: '#888899', border: '1px solid rgba(255,255,255,0.08)' }}>
            {comment.source}
          </span>
          {/* Aspect badge */}
          {comment.primary_aspect && (
            <span style={{ ...badgeBase, background: 'rgba(255,183,3,0.08)', color: '#FFB703', border: '1px solid rgba(255,183,3,0.2)' }}>
              {comment.primary_aspect.replace('_', ' ')}
            </span>
          )}
        </div>
      </div>

      {/* Right — sentiment + weight */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px', flexShrink: 0 }}>
        <span style={{
          ...badgeBase, background: sentStyle.bg,
          color: sentStyle.color, border: `1px solid ${sentStyle.border}`,
          fontWeight: '700',
        }}>
          {sentStyle.label}{confidence}
        </span>
        <span style={{ fontSize: '11px', color: '#444455' }}>
          w: {(+comment.weight || 0).toFixed(3)}
        </span>
      </div>
    </div>
  )
}

export default function CommentFeed() {
  const [filters, setFilters] = useState({
    lang: 'all', aspect: 'all', sentiment: 'all', source: 'all',
  })
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: 15 }
      if (filters.lang      !== 'all') params.lang      = filters.lang
      if (filters.aspect    !== 'all') params.aspect    = filters.aspect
      if (filters.sentiment !== 'all') params.sentiment = filters.sentiment
      if (filters.source    !== 'all') params.source    = filters.source
      const result = await fetchComments(params)
      setData(result)
    } catch (e) {
      console.error('Failed to load comments:', e)
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => { load() }, [load])

  const setFilter = (key) => (val) => {
    setFilters(f => ({ ...f, [key]: val }))
    setPage(1)
  }

  const comments     = data?.comments ?? []
  const total        = data?.total ?? 0
  const totalPages   = data?.total_pages ?? 1

  return (
    <div>
      {/* Filter toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', color: '#888899' }}>
          {total.toLocaleString()} comments
          {total !== 0 && (
            <span style={{ marginLeft: '8px', color: '#555' }}>
              • page {page}/{totalPages}
            </span>
          )}
        </span>
        <button
          onClick={() => setShowFilters(v => !v)}
          style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '6px 12px', borderRadius: '20px',
            border: '1px solid rgba(255,255,255,0.1)',
            background: showFilters ? 'rgba(255,183,3,0.1)' : 'transparent',
            color: showFilters ? '#FFB703' : '#888899',
            fontSize: '12px', cursor: 'pointer',
          }}
        >
          <Filter size={13} />
          Filters
        </button>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div style={{
          padding: '16px', background: '#1C1C26',
          borderRadius: '12px', marginBottom: '16px',
          border: '1px solid rgba(255,255,255,0.06)',
          display: 'flex', flexDirection: 'column', gap: '12px',
        }}>
          <FilterPill value={filters.lang}      options={LANGS}      onChange={setFilter('lang')}      label="Language" />
          <FilterPill value={filters.aspect}    options={ASPECTS}    onChange={setFilter('aspect')}    label="Aspect" />
          <FilterPill value={filters.sentiment} options={SENTIMENTS} onChange={setFilter('sentiment')} label="Sentiment" />
          <FilterPill value={filters.source}    options={SOURCES}    onChange={setFilter('source')}    label="Source" />
        </div>
      )}

      {/* Comment list */}
      <div style={{ position: 'relative', minHeight: '200px' }}>
        {loading && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            background: 'rgba(10,10,15,0.7)', borderRadius: '12px', zIndex: 2,
          }}>
            <div className="spinner" />
          </div>
        )}

        {!loading && !comments.length && (
          <div style={{ padding: '40px', textAlign: 'center', color: '#444' }}>
            <MessageSquare size={32} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }} />
            No comments match the current filters.
          </div>
        )}

        {comments.map((c, i) => (
          <CommentRow key={c.comment_id ?? i} comment={c} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', marginTop: '20px' }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
            style={paginBtnStyle(page === 1)}>
            <ChevronLeft size={16} />
          </button>
          <span style={{ fontSize: '13px', color: '#888899' }}>
            {page} / {totalPages}
          </span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
            style={paginBtnStyle(page === totalPages)}>
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}

const rowStyle = {
  display      : 'flex',
  alignItems   : 'flex-start',
  gap          : '16px',
  padding      : '14px 0',
  borderBottom : '1px solid rgba(255,255,255,0.05)',
}

const badgeBase = {
  display       : 'inline-flex',
  alignItems    : 'center',
  padding       : '2px 8px',
  borderRadius  : '12px',
  fontSize      : '11px',
  fontWeight    : '500',
  whiteSpace    : 'nowrap',
}

const paginBtnStyle = (disabled) => ({
  width         : '32px',
  height        : '32px',
  display       : 'flex',
  alignItems    : 'center',
  justifyContent: 'center',
  borderRadius  : '8px',
  border        : '1px solid rgba(255,255,255,0.1)',
  background    : 'transparent',
  color         : disabled ? '#333344' : '#888899',
  cursor        : disabled ? 'not-allowed' : 'pointer',
})
