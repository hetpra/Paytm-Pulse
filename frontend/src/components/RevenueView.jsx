import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { fetchRevenue } from '../api'

const COLORS = ['#002E6E', '#00BAF2', '#F5A623']

export default function RevenueView() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRevenue()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="mx-4 mt-3 bg-white rounded-xl p-4 shadow-sm">
        <div className="h-40 bg-gray-100 rounded-lg animate-pulse" />
      </div>
    )
  }

  if (!data) return null

  const pieData = [
    { name: 'Loan (Interest + Fees)', value: (data.loan_interest || 0) + (data.loan_fees || 0) },
    { name: 'B2B Platform Fees', value: data.b2b_fees || 0 },
    { name: 'Subscriptions', value: data.subscriptions || 0 },
  ].filter(d => d.value > 0)

  const hasRevenue = data.total > 0

  return (
    <div className="mx-4 mt-3 space-y-3">
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">💼</span>
          <h3 className="text-sm font-bold text-[#002E6E]">Paytm Revenue — This Demo Run</h3>
        </div>

        {!hasRevenue ? (
          <div className="text-center py-6">
            <p className="text-gray-400 text-sm">No revenue yet</p>
            <p className="text-gray-300 text-xs mt-1">Approve a restock order to generate revenue</p>
          </div>
        ) : (
          <>
            {/* Total */}
            <div className="text-center mb-4">
              <p className="text-2xl font-bold text-[#002E6E]">₹{data.total.toLocaleString('en-IN')}</p>
              <p className="text-[10px] text-gray-400 uppercase">Total Revenue</p>
            </div>

            {/* Pie chart */}
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={65}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v) => `₹${v.toLocaleString('en-IN')}`}
                  contentStyle={{ fontSize: 11, borderRadius: 8, border: 'none' }}
                />
              </PieChart>
            </ResponsiveContainer>

            {/* Breakdown */}
            <div className="space-y-1.5 mt-2">
              <Row color={COLORS[0]} label="Loan interest" value={data.loan_interest} pct={data.mix_pct?.loan} />
              <Row color={COLORS[0]} label="Loan processing fees" value={data.loan_fees} sub />
              <Row color={COLORS[1]} label="B2B platform fees (1%)" value={data.b2b_fees} pct={data.mix_pct?.b2b} />
              <Row color={COLORS[2]} label="Subscriptions (₹499/mo)" value={data.subscriptions} pct={data.mix_pct?.subscription} />
            </div>
          </>
        )}
      </div>

      {/* Projected mix caption */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-3">
        <p className="text-[10px] text-blue-700 leading-relaxed">
          <span className="font-semibold">Projected mix at scale:</span> 60% loan interest & fees · 30% B2B platform fees · 10% subscriptions.
          This ledger shows <em>this demo run's</em> actuals.
        </p>
      </div>
    </div>
  )
}

function Row({ color, label, value, pct, sub }) {
  return (
    <div className={`flex items-center justify-between ${sub ? 'pl-4' : ''}`}>
      <div className="flex items-center gap-1.5">
        {!sub && <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />}
        <span className={`text-xs text-gray-600 ${sub ? 'text-[10px] text-gray-400' : ''}`}>{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-xs font-medium ${sub ? 'text-[10px] text-gray-400' : 'text-gray-800'}`}>
          ₹{(value || 0).toLocaleString('en-IN')}
        </span>
        {pct != null && !sub && (
          <span className="text-[9px] text-gray-400 w-8 text-right">{pct}%</span>
        )}
      </div>
    </div>
  )
}
