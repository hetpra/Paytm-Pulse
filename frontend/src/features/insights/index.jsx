import { useEffect, useState } from 'react'
import { ext } from '../../api'
import { useMerchantId } from '../framework'
import { useT } from '../../localization'

const icon = { mover_up: '↗', mover_down: '↘', overstock: '▣', dead_stock: '◌', best_weekday: '★', worst_weekday: '◔', profit_leader: '₹', hidden_gem: '✦', cash_tied_up: '⌁' }
const numberIn = value => value?.match(/[\d,]+(?:\.\d+)?/)?.[0]?.replaceAll(',', '') || '0'
const amount = value => Math.round(Number(value) || 0).toLocaleString('en-IN')

function localizeInsight(item, t) {
  const { type, title, metric, action, evidence = {} } = item
  if (type === 'best_weekday' || type === 'worst_weekday') {
    const day = t(evidence.weekday)
    return {
      title: t(type === 'best_weekday' ? '{day} is your strongest day' : '{day} needs attention', { day }),
      metric: t('₹{amount} average revenue', { amount: amount(numberIn(metric)) }),
      action: t(type === 'best_weekday' ? 'Stock up before {day}.' : 'Run a promo on {day}.', { day }),
    }
  }
  if (type === 'dead_stock') return { title, metric: t(metric), action: t(action) }
  if (type === 'overstock') return {
    title,
    metric: t('~{days} days of stock', { days: numberIn(metric) }),
    action: t('Pause reordering {name}.', { name: title }),
  }
  if (type === 'mover_up' || type === 'mover_down') {
    const magnitude = numberIn(metric).replace(/^[+-]/, '')
    const change = type === 'mover_down' ? `-${magnitude}` : magnitude
    const key = type === 'mover_up' ? '+{change}% revenue vs last week' : '{change}% revenue vs last week'
    return { title, metric: t(key, { change }), action: t(action) }
  }
  if (type === 'profit_leader') {
    const [profit, share = '0'] = metric.match(/[\d,]+(?:\.\d+)?/g) || []
    return {
      title,
      metric: t('₹{amount} gross profit ({share}%)', { amount: amount(profit), share }),
      action: t(action),
    }
  }
  if (type === 'hidden_gem') return {
    title,
    metric: t('₹{amount}/unit margin', { amount: amount(numberIn(metric)) }),
    action: t('Promote {name}.', { name: title }),
  }
  if (type === 'cash_tied_up') return {
    title: t(title),
    metric: `₹${amount(numberIn(metric))}`,
    action: t(action),
  }
  return { title: t(title), metric: t(metric), action: t(action) }
}

function Insights() {
  const t = useT()
  const merchantId = useMerchantId()
  const [data, setData] = useState(null)
  useEffect(() => { ext('insights', '', {}, merchantId).then(setData).catch(() => setData({ insights: [] })) }, [merchantId])
  if (!data) return <div className="p-4 text-sm text-gray-500">{t('Finding growth opportunities…')}</div>

  const insights = data.insights.map(item => ({ ...item, localized: localizeInsight(item, t) }))
  const summary = insights.slice(0, 3).map(({ localized }) => `${localized.title}: ${localized.metric}. ${localized.action}`).join(' ')

  return <section className="p-4 space-y-3">
    <div><h2 className="font-bold text-[#002E6E] text-lg">{t('Growth insights')}</h2><p className="text-xs text-gray-500 mt-1">{t('Computed from your sales history')}</p></div>
    {summary && <p className="rounded-xl bg-[#E6F9FF] border border-cyan-100 p-3 text-sm text-[#002E6E] leading-relaxed">{summary}</p>}
    {insights.map((item, index) => <article key={index} className="rounded-xl bg-white border border-gray-100 shadow-sm p-3">
      <div className="flex gap-3"><span className="text-xl text-[#00BAF2]">{icon[item.type] || '•'}</span><div className="min-w-0 flex-1"><div className="flex justify-between gap-2"><h3 className="font-semibold text-sm">{item.localized.title}</h3><span className="shrink-0 text-xs font-bold text-[#002E6E]">{item.localized.metric}</span></div><p className="mt-2 text-xs font-semibold text-gray-700">{t('Do this:')} {item.localized.action}</p></div></div>
    </article>)}
    {!insights.length && <p className="text-sm text-gray-500">{t('No notable changes yet.')}</p>}
  </section>
}

export default { id: 'insights', flag: 'insights', label: 'Insights', icon: '✦', order: 1, Tab: Insights }
