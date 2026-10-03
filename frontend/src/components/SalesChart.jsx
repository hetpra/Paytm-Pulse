import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { useT } from '../localization'

export default function SalesChart({ data }) {
  const t = useT()
  if (!data || data.length === 0) return null

  const formatted = data.map(d => ({
    ...d,
    label: new Date(d.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
  }))

  return (
    <div className="mx-4 mt-4 bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-800">{t('Daily revenue')}</h3>
          <p className="text-[10px] text-slate-500 mt-0.5">{t('A two-week view of your sales')}</p>
        </div>
        <span className="rounded-lg bg-[#E6F9FF] text-[#005E8A] px-2.5 py-1.5 text-[9px] font-semibold">{t('14 days')}</span>
      </div>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={formatted} barSize={14} margin={{ top: 4, right: 2, bottom: 0, left: 2 }}>
          <CartesianGrid vertical={false} stroke="#EDF2F7" strokeDasharray="3 4" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 9, fill: '#94A3B8' }}
            axisLine={false}
            tickLine={false}
            interval={2}
          />
          <YAxis hide />
          <Tooltip
            formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, t('Revenue')]}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.12)' }}
          />
          <Bar dataKey="revenue" fill="#00BAF2" radius={[5, 5, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
