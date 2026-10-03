import { useEffect, useState } from 'react'
import { ext } from '../../api'
import { useMerchantId } from '../framework'

const pct = value => `${Math.round((value || 0) * 100)}%`

function AccuracyChip({ merchant }) {
  const [result, setResult] = useState(null)
  useEffect(() => { ext('backtest', '', {}, merchant.id).then(setResult).catch(() => {}) }, [merchant.id])
  if (!result?.ready) return null
  const uplift = Math.round((result.overall.accuracy - result.overall.naive_accuracy) * 100)
  return <div className="mx-4 mt-3 rounded-xl bg-indigo-50 border border-indigo-100 p-3 text-sm text-indigo-950"><b>🎯 Forecast accuracy {pct(result.overall.accuracy)}</b> · {uplift >= 0 ? '+' : ''}{uplift} pts vs naive<br/><span className="text-[10px] text-indigo-700">14-day holdout · {result.engine} engine</span></div>
}

function Backtest() {
  const merchantId = useMerchantId(); const [data, setData] = useState(null)
  useEffect(() => { ext('backtest', '', {}, merchantId).then(setData).catch(() => {}) }, [merchantId])
  if (!data) return <div className="p-4 text-sm text-gray-500">Calculating forecast accuracy…</div>
  return <section className="p-4 space-y-3"><h2 className="font-bold text-[#002E6E] text-lg">Forecast confidence</h2>
    <div className="bg-white rounded-xl border p-4"><p className="text-3xl font-bold">{pct(data.overall.accuracy)}</p><p className="text-xs text-gray-500">Accuracy on the last {data.holdout_days} days</p><p className="mt-2 text-sm">Naive baseline: {pct(data.overall.naive_accuracy)}</p></div>
    {data.festival && <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-sm">🪔 {data.festival.name} in {data.festival.days_away} days — forecast boosted {Math.round((data.festival.uplift - 1) * 100)}% <span className="text-xs">(business assumption)</span></div>}
    <div className="space-y-2">{data.skus.map(s => <div key={s.sku_id} className="bg-white rounded-lg border p-3 text-sm flex justify-between"><span>{s.sku_id}</span><span>{pct(s.accuracy)} · {s.lift_pct >= 0 ? '+' : ''}{s.lift_pct}% vs naive</span></div>)}</div>
  </section>
}
export default { id: 'backtest', flag: 'backtest', label: 'Accuracy', icon: '🎯', order: 2, Tab: Backtest, slots: { 'dashboard.top': AccuracyChip } }
