import React, { useState } from 'react'
import { Download, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { downloadReport } from '../../services/api.js'

export default function ExportButton() {
  const [state, setState] = useState('idle')  // idle | loading | success | error

  const handleDownload = async () => {
    setState('loading')
    try {
      await downloadReport()
      setState('success')
      setTimeout(() => setState('idle'), 3000)
    } catch {
      setState('error')
      setTimeout(() => setState('idle'), 3000)
    }
  }

  const config = {
    idle   : { icon: Download,      label: 'Download PDF Report', color: '#FFB703', bg: 'rgba(255,183,3,0.12)', border: 'rgba(255,183,3,0.3)'  },
    loading: { icon: FileText,      label: 'Generating PDF…',     color: '#888899', bg: 'rgba(255,255,255,0.06)', border: 'rgba(255,255,255,0.1)' },
    success: { icon: CheckCircle,   label: 'Report Downloaded!',  color: '#4ade80', bg: 'rgba(74,222,128,0.1)', border: 'rgba(74,222,128,0.3)'  },
    error  : { icon: AlertCircle,   label: 'Generation Failed',   color: '#f87171', bg: 'rgba(248,113,113,0.1)', border: 'rgba(248,113,113,0.3)' },
  }

  const { icon: Icon, label, color, bg, border } = config[state]

  return (
    <button
      onClick={handleDownload}
      disabled={state === 'loading'}
      style={{
        display       : 'flex',
        alignItems    : 'center',
        gap           : '8px',
        padding       : '10px 20px',
        borderRadius  : '12px',
        border        : `1px solid ${border}`,
        background    : bg,
        color,
        fontSize      : '13px',
        fontWeight    : '600',
        cursor        : state === 'loading' ? 'wait' : 'pointer',
        transition    : 'all 0.2s',
        fontFamily    : "'DM Sans', sans-serif",
        whiteSpace    : 'nowrap',
      }}
    >
      {state === 'loading'
        ? <div style={{ width: 16, height: 16, border: `2px solid ${color}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
        : <Icon size={16} />
      }
      {label}
    </button>
  )
}
