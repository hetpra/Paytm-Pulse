import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, ReferenceLine, ComposedChart } from 'recharts'
import { fetchForecast } from '../api'

export default function ForecastChart({ skuId, isPremium, onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchForecast(skuId)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [skuId])

  if (loading) {
    return (
      <div className="mx-4 mt-3 bg-white rounded-xl p-4 shadow-sm">
        <div className="h-40 bg-gray-100 rounded-lg animate-pulse" />
      </div>
    )
  }

  if (!data) return null

  // Build chart data
  const history = (data.history || []).map(h => ({
    date: h.date,
    label: new Date(h.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
    actual: h.units,
  }))

  const forecast = (data.forecast || []).map(f => ({
    date: f.date,
    label: new Date(f.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
    predicted: Math.round(f.yhat),
    lower: Math.round(f.lower),
    upper: Math.round(f.upper),
  }))

  // Bridge: last history point + first forecast point
  const bridgePoint = history.length > 0 ? {
    ...history[history.length - 1],
    predicted: history[history.length - 1].actual,
    lower: history[history.length - 1].actual,
    upper: history[history.length - 1].actual,
  } : null

  const chartData = [
    ...history,
    ...(bridgePoint ? [bridgePoint] : []),
    ...forecast,
  ]

  // Deduplicate by date (bridge point may duplicate last history)
  const seen = new Set()
  const uniqueData = chartData.filter(d => {
    if (seen.has(d.date)) return false
    seen.add(d.date)
    return true
  })

  return (
    <div className="mx-4 mt-3 bg-white rounded-xl shadow-sm overflow-hidden">
      <div className="px-3 pt-3 pb-1 flex items-center justify-between">
        <div>
          <h3 className="text-xs font-bold text-[#002E6E]">{data.name} — Forecast</h3>
          {data.stockout_date && (
            <p className="text-[10px] text-red-500 font-medium">
              Stockout: {new Date(data.stockout_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
              {data.days_left != null && ` (${data.days_left.toFixed(1)} days)`}
            </p>
          )}
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-sm">✕</button>
      </div>

      <div className={`relative ${!isPremium ? 'select-none' : ''}`}>
        {/* Blur gate for free plan */}
        {!isPremium && (
          <div className="absolute inset-0 z-10 backdrop-blur-sm bg-white/60 flex flex-col items-center justify-center rounded-b-xl">
            <p className="text-sm font-bold text-[#002E6E]">🔒 Unlock with Premium</p>
            <p className="text-[10px] text-gray-500 mt-0.5">₹499/mo — Tap the plan badge above</p>
          </div>
        )}

        <div className="px-1 pb-3">
          <ResponsiveContainer width="100%" height={180}>
            <ComposedChart data={uniqueData} margin={{ top: 5, right: 10, bottom: 5, left: -15 }}>
              <XAxis
                dataKey="label"
                tick={{ fontSize: 7, fill: '#9CA3AF' }}
                axisLine={false}
                tickLine={false}
                interval={6}
              />
              <YAxis
                tick={{ fontSize: 8, fill: '#9CA3AF' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ fontSize: 10, borderRadius: 8, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.12)' }}
              />
              {/* Confidence band */}
              <Area dataKey="upper" stroke="none" fill="#00BAF2" fillOpacity={0.08} />
              <Area dataKey="lower" stroke="none" fill="#ffffff" fillOpacity={0.8} />
              {/* Actual */}
              <Line dataKey="actual" stroke="#002E6E" strokeWidth={1.5} dot={false} connectNulls />
              {/* Predicted */}
              <Line dataKey="predicted" stroke="#00BAF2" strokeWidth={1.5} strokeDasharray="4 2" dot={false} connectNulls />
              {/* Stockout line */}
              {data.stockout_date && (
                <ReferenceLine
                  x={new Date(data.stockout_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                  stroke="#E5322D"
                  strokeWidth={1.5}
                  strokeDasharray="3 3"
                  label={{ value: '⚠', position: 'top', fontSize: 12 }}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-4 pb-2 text-[9px] text-gray-400">
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#002E6E] inline-block" /> Actual</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#00BAF2] inline-block border-dashed" /> Forecast</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 bg-[#00BAF2]/10 inline-block rounded" /> Confidence</span>
        </div>
      </div>
    </div>
  )
}
