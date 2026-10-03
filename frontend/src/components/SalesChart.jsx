import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function SalesChart({ data }) {
  if (!data || data.length === 0) return null

  const formatted = data.map(d => ({
    ...d,
    label: new Date(d.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
  }))

  return (
    <div className="mx-4 mt-3 bg-white rounded-xl p-3 shadow-sm">
      <h3 className="text-xs font-semibold text-gray-500 mb-2">Daily Revenue (14 days)</h3>
      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={formatted} barSize={12}>
          <XAxis
            dataKey="label"
            tick={{ fontSize: 8, fill: '#9CA3AF' }}
            axisLine={false}
            tickLine={false}
            interval={2}
          />
          <YAxis hide />
          <Tooltip
            formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, 'Revenue']}
            contentStyle={{ fontSize: 11, borderRadius: 8, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.12)' }}
          />
          <Bar dataKey="revenue" fill="#00BAF2" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
