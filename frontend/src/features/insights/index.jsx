import { useEffect, useState } from 'react'
import { ext } from '../../api'
import { useMerchantId } from '../framework'

const icon = { mover_up: '↗', mover_down: '↘', overstock: '▣', dead_stock: '◌', best_weekday: '★', worst_weekday: '◔', profit_leader: '₹', hidden_gem: '✦', cash_tied_up: '⌁' }

function Insights() {
  const merchantId = useMerchantId()
  const [data, setData] = useState(null)
  useEffect(() => { ext('insights', '', {}, merchantId).then(setData).catch(() => setData({ insights: [] })) }, [merchantId])
  if (!data) return <div className="p-4 text-sm text-gray-500">Finding growth opportunities…</div>
  return <section className="p-4 space-y-3">
    <div><h2 className="font-bold text-[#002E6E] text-lg">Growth insights</h2><p className="text-xs text-gray-500 mt-1">Computed from your sales history</p></div>
    {data.summary_text && <p className="rounded-xl bg-blue-50 border border-blue-100 p-3 text-sm text-blue-950 leading-relaxed">{data.summary_text}</p>}
    {data.insights.map((item, index) => <article key={index} className="rounded-xl bg-white border border-gray-100 shadow-sm p-3">
      <div className="flex gap-3"><span className="text-xl text-[#00BAF2]">{icon[item.type] || '•'}</span><div className="min-w-0 flex-1"><div className="flex justify-between gap-2"><h3 className="font-semibold text-sm">{item.title}</h3><span className="shrink-0 text-xs font-bold text-[#002E6E]">{item.metric}</span></div><p className="mt-2 text-xs font-semibold text-gray-700">Do this: {item.action}</p></div></div>
    </article>)}
    {!data.insights.length && <p className="text-sm text-gray-500">No notable changes yet.</p>}
  </section>
}

export default { id: 'insights', flag: 'insights', label: 'Insights', icon: '✦', order: 1, Tab: Insights }
