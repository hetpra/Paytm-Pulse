import { useEffect, useState } from 'react'
import { ext } from '../../api'
import { useMerchantId } from '../framework'
import { useT } from '../../localization'

const pct = value => `${Math.round((value || 0) * 100)}%`

function AccuracyChip({ merchant }) {
  const t = useT()
  const [result, setResult] = useState(null)
  useEffect(() => { ext('backtest', '', {}, merchant.id).then(setResult).catch(() => {}) }, [merchant.id])
  if (!result?.ready) return null
  const uplift = Math.round((result.overall.accuracy - result.overall.naive_accuracy) * 100)
  return <div className="mx-4 mt-3 rounded-xl bg-white border border-cyan-200 p-3 text-sm text-[#002E6E]"><b>{t('Forecast accuracy')} {pct(result.overall.accuracy)}</b> · {uplift >= 0 ? '+' : ''}{uplift} {t('pts vs baseline')}<br/><span className="text-[10px] text-slate-500">{t('14-day historical check')} · {result.engine} {t('forecast')}</span></div>
}

function Backtest() {
  const t = useT()
  const merchantId = useMerchantId(); const [data, setData] = useState(null)
  useEffect(() => { ext('backtest', '', {}, merchantId).then(setData).catch(() => {}) }, [merchantId])
  if (!data) return <div className="p-4 text-sm text-gray-500">{t('Calculating forecast accuracy…')}</div>
  return <section className="p-4 space-y-3"><h2 className="font-bold text-[#002E6E] text-lg">{t('Forecast performance')}</h2>
    <div className="bg-white rounded-xl border border-slate-200 p-4"><p className="text-3xl font-bold text-[#002E6E]">{pct(data.overall.accuracy)}</p><p className="text-xs text-gray-500">{t('Accuracy over the last {days} days', { days: data.holdout_days })}</p><p className="mt-2 text-sm text-slate-700">{t('Baseline')}: {pct(data.overall.naive_accuracy)}</p></div>
    {data.festival && <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-sm">🪔 {data.festival.name} · {data.festival.days_away} {t('days away')} — {t('forecast uplift')} {Math.round((data.festival.uplift - 1) * 100)}% <span className="text-xs">({t('business assumption')})</span></div>}
    <div className="space-y-2">{data.skus.map(s => <div key={s.sku_id} className="bg-white rounded-lg border p-3 text-sm flex justify-between"><span>{s.sku_id}</span><span>{pct(s.accuracy)} · {s.lift_pct >= 0 ? '+' : ''}{s.lift_pct}% {t('vs baseline')}</span></div>)}</div>
  </section>
}
export default { id: 'backtest', flag: 'backtest', label: 'Accuracy', icon: '🎯', order: 2, Tab: Backtest, slots: { 'dashboard.top': AccuracyChip } }
