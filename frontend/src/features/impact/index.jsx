import { useEffect, useState } from 'react'
import { ext } from '../../api'
import { useMerchantId } from '../framework'
import { useT } from '../../localization'

const money = n => `₹${Math.round(n || 0).toLocaleString('en-IN')}`
const localizeArrival = (arrival, t) => arrival === 'lead days'
  ? t('Lead time')
  : arrival === 'lead + 1 days'
    ? t('Lead time + 1 day')
    : arrival

function ImpactCard({ merchant }) {
  const t = useT()
  const merchantId = useMerchantId(); const [data, setData] = useState(null); const [open, setOpen] = useState(false)
  useEffect(() => { ext('impact', '', {}, merchantId).then(setData).catch(() => {}) }, [merchantId])
  if (!data) return null
  return <section className="mx-4 mt-3 rounded-xl bg-white border border-cyan-200 p-3"><button className="w-full text-left" onClick={() => setOpen(!open)}><p className="font-bold text-[#002E6E]">{t('Illustrative impact: {amount} revenue protected', { amount: money(data.revenue_protected) })}</p><p className="text-sm text-slate-700">{t('{amount} estimated net gain in {days} days', { amount: money(data.net_gain), days: data.window.days })}</p><p className="text-[10px] text-slate-500 mt-1">{t('Based on simulated sales · view assumptions')}</p></button>
    {open && <div className="mt-3 pt-3 border-t border-slate-200 text-xs text-slate-700 space-y-1"><p>{t('Without Pulse lost revenue:')} {money(data.without.lost_revenue)}</p><p>{t('With Pulse lost revenue:')} {money(data.with.lost_revenue)}</p><p>{t('Costs:')} {money(data.costs.platform_fees + data.costs.loan_costs)}</p><p>{t('Pulse order arrival:')} {localizeArrival(data.assumptions.pulse_arrival, t)}; {t('Reactive order arrival:')} {localizeArrival(data.assumptions.reactive_arrival, t)}.</p></div>}
  </section>
}
function Impact() { const merchantId = useMerchantId(); const t = useT(); const [data, setData] = useState(null); useEffect(() => { ext('impact', '', {}, merchantId).then(setData).catch(() => {}) }, [merchantId]); return <section className="p-4"><h2 className="font-bold text-[#002E6E] text-lg">{t('Impact simulator')}</h2>{data ? <ImpactCard merchant={{ id: merchantId }} /> : <p className="text-sm text-gray-500 mt-3">{t('Running simulation…')}</p>}</section> }
export default { id: 'impact', flag: 'impact', label: 'Impact', icon: '🛡', order: 3, Tab: Impact, slots: { 'dashboard.top': ImpactCard } }
