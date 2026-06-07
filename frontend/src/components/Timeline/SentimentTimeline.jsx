import React, { useState } from 'react'
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1C1C26', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '10px', padding: '12px 16px', fontSize: '12px', minWidth: '200px',
    }}>
      <div style={{ fontWeight: '700', marginBottom: '8px', color: '#888899' }}>
        📅 {label}
      </div>
      {payload.map((p, i) => (
        <div key={i} style={{
          display: 'flex', justifyContent: 'space-between',
          gap: '16px', marginBottom: '4px',
        }}>
          <span style={{ color: p.color }}>{p.name}</span>
          <span style={{ fontWeight: '600', color: '#F0F0F0' }}>
            {p.dataKey.includes('volume')
              ? `${p.value} comments`
              : p.value > 0 ? `+${p.value.toFixed(3)}` : p.value.toFixed(3)
            }
          </span>
        </div>
      ))}
    </div>
  )
}

export default function SentimentTimeline({ timeline }) {
  const [showVolume, setShowVolume] = useState(true)
  const data = timeline?.timeline ?? []

  if (!data.length) {
    return (
      <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#555' }}>
        No timeline data available
      </div>
    )
  }

  // Format dates for display
  const chartData = data.map(d => ({
    ...d,
    date: d.date?.slice(5) ?? d.date,   // show MM-DD
  }))

  return (
    <div>
      {/* Toggle volume */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
        <button
          onClick={() => setShowVolume(v => !v)}
          style={{
            padding    : '5px 12px',
            borderRadius: '16px',
            border     : '1px solid',
            borderColor: showVolume ? 'rgba(255,183,3,0.4)' : 'rgba(255,255,255,0.1)',
            background : showVolume ? 'rgba(255,183,3,0.1)' : 'transparent',
            color      : showVolume ? '#FFB703' : '#888899',
            fontSize   : '11px', cursor: 'pointer',
          }}
        >
          {showVolume ? '● Volume On' : '○ Volume Off'}
        </button>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
          <defs>
            <linearGradient id="hindiVol" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#E85D04" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#E85D04" stopOpacity={0}    />
            </linearGradient>
            <linearGradient id="teluguVol" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#0077B6" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#0077B6" stopOpacity={0}    />
            </linearGradient>
          </defs>

          <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#555566', fontSize: 11 }}
            axisLine={false} tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            yAxisId="score"
            domain={[-1, 1]}
            tick={{ fill: '#555566', fontSize: 10 }}
            axisLine={false} tickLine={false}
            tickFormatter={v => v.toFixed(1)}
          />
          {showVolume && (
            <YAxis
              yAxisId="vol"
              orientation="right"
              tick={{ fill: '#333344', fontSize: 10 }}
              axisLine={false} tickLine={false}
            />
          )}
          <ReferenceLine
            yAxisId="score" y={0}
            stroke="rgba(255,255,255,0.12)" strokeDasharray="4 4"
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend formatter={(val) => (
            <span style={{ color: '#888899', fontSize: 12 }}>{val}</span>
          )} />

          {showVolume && (
            <>
              <Area
                yAxisId="vol" type="monotone"
                dataKey="hindi_volume" name="Hindi Vol"
                fill="url(#hindiVol)" stroke="none"
              />
              <Area
                yAxisId="vol" type="monotone"
                dataKey="telugu_volume" name="Telugu Vol"
                fill="url(#teluguVol)" stroke="none"
              />
            </>
          )}

          <Line
            yAxisId="score" type="monotone"
            dataKey="hindi_score" name="Hindi Score"
            stroke="#E85D04" strokeWidth={2.5}
            dot={false} activeDot={{ r: 5, strokeWidth: 0 }}
          />
          <Line
            yAxisId="score" type="monotone"
            dataKey="telugu_score" name="Telugu Score"
            stroke="#0077B6" strokeWidth={2.5}
            dot={false} activeDot={{ r: 5, strokeWidth: 0 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
