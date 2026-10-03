import { useEffect, useState } from 'react'
import { ext } from '../../api'
import { useMerchantId } from '../framework'

const money = n => `₹${Math.round(n || 0).toLocaleString('en-IN')}`
function ImpactCard({ merchant }) {
  const merchantId = useMerchantId(); const [data, setData] = useState(null); const [open, setOpen] = useState(false)
  useEffect(() => { ext('impact', '', {}, merchantId).then(setData).catch(() => {}) }, [merchantId])
  if (!data) return null
  return <section className="mx-4 mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-3"><button className="w-full text-left" onClick={() => setOpen(!open)}><p className="font-bold text-emerald-950">🛡️ Pulse would have protected {money(data.revenue_protected)} revenue</p><p className="text-sm text-emerald-800">{money(data.net_gain)} net profit in {data.window.days} days</p><p className="text-[10px] text-emerald-700 mt-1">Simulation on synthetic history · tap for assumptions</p></button>
    {open && <div className="mt-3 pt-3 border-t border-emerald-200 text-xs text-emerald-950 space-y-1"><p>Without Pulse lost revenue: {money(data.without.lost_revenue)}</p><p>With Pulse lost revenue: {money(data.with.lost_revenue)}</p><p>Costs: {money(data.costs.platform_fees + data.costs.loan_costs)}</p><p>Orders arrive in {data.assumptions.pulse_arrival}; reactive orders in {data.assumptions.reactive_arrival}.</p></div>}
  </section>
}
function Impact() { const merchantId = useMerchantId(); const [data, setData] = useState(null); useEffect(() => { ext('impact', '', {}, merchantId).then(setData).catch(() => {}) }, [merchantId]); return <section className="p-4"><h2 className="font-bold text-[#002E6E] text-lg">Impact simulator</h2>{data ? <ImpactCard merchant={{ id: merchantId }} /> : <p className="text-sm text-gray-500 mt-3">Running simulation…</p>}</section> }
export default { id: 'impact', flag: 'impact', label: 'Impact', icon: '🛡', order: 3, Tab: Impact, slots: { 'dashboard.top': ImpactCard } }
