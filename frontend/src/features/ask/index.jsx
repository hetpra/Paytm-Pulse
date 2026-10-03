import { useState } from 'react'
import { ext } from '../../api'
import { useMerchantId } from '../framework'
import { useT } from '../../localization'

const questions = ['What will run out this week?', 'Best sellers on Saturday?', 'Which items make the most profit?']
const amount = value => Math.round(Number(value) || 0).toLocaleString('en-IN')

function localizeAnswer(result, t) {
  const first = result.data?.[0]
  if (result.tool === 'stock_status') {
    if (!result.data?.length) return t('No items are currently at risk.')
    return `${t('Items at risk:')} ${result.data.map(item => `${item.name} (${Number(item.days_left).toFixed(1)} ${t('days')})`).join(', ')}`
  }
  if (!first) return result.answer
  if (result.tool === 'profit_by_item') {
    return t('Top profit item: {name} (₹{amount}).', { name: first.name, amount: amount(first.profit) })
  }
  if (result.tool === 'sales_by_weekday') {
    return t('Best seller on Saturday: {name} ({units} units).', { name: first.name, units: first.saturday_units })
  }
  if (result.tool === 'top_items') {
    return t('Best seller: {name} at ₹{amount} in sales.', { name: first.name, amount: amount(first.revenue) })
  }
  return result.answer
}

function Ask() {
  const merchant = useMerchantId()
  const t = useT()
  const [q, setQ] = useState(questions[0])
  const [result, setResult] = useState(null)
  const ask = () => ext('ask', '/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: q }),
  }, merchant).then(setResult)
  const displayedQuestion = questions.includes(q) ? t(q) : q

  return <section className="p-4 space-y-3">
    <h2 className="font-bold text-[#002E6E] text-lg">{t('Ask Pulse')}</h2>
    <div className="flex gap-2">
      <input value={displayedQuestion} onChange={event => setQ(event.target.value)} className="flex-1 border rounded-lg p-2 text-sm" />
      <button onClick={ask} className="bg-[#00BAF2] text-white px-3 rounded-lg">{t('Ask')}</button>
    </div>
    <div className="flex gap-1 flex-wrap">{questions.map(question => <button key={question} onClick={() => setQ(question)} className="text-xs bg-gray-100 rounded-full px-2 py-1">{t(question)}</button>)}</div>
    {result && <div className="bg-white border rounded-xl p-3 text-sm">
      <p>{localizeAnswer(result, t)}</p>
      <details className="mt-2 text-xs text-gray-500">
        <summary>{t('Computed from your sales data')}</summary>
        <pre className="whitespace-pre-wrap">{JSON.stringify({ tool: result.tool, args: result.args, data: result.data }, null, 2)}</pre>
      </details>
    </div>}
  </section>
}

export default { id: 'ask', flag: 'ask', label: 'Ask', icon: '💬', order: 7, Tab: Ask }
