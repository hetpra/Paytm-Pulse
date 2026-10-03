import { useState } from 'react'
import { ext } from '../../api'
import { useT } from '../../localization'
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
function validationMessage(message, t) {
  let match = message.match(/^Invalid (sales|catalog) row for (.+)$/)
  if (match) return t(`Invalid ${match[1]} row for {item}`, { item: match[2] })
  match = message.match(/^Sales item (.+) is not in catalog$/)
  if (match) return t('Sales item {item} is not in catalog', { item: match[1] })
  match = message.match(/^(.+) has fewer than 28 sales days; fallback forecast may be used$/)
  if (match) return t('{item} has fewer than 28 sales days; fallback forecast may be used', { item: match[1] })
  return t(message)
}

function Byod() {
  const t = useT()
  const [result, setResult] = useState(null)
  const [sales, setSales] = useState(null)
  const [catalog, setCatalog] = useState(null)
  const upload = () => {
    if (!sales || !catalog) return
    const form = new FormData()
    form.append('sales', sales)
    form.append('catalog', catalog)
    form.append('store_name', 'My Store')
    form.append('cash_balance', '5000')
    ext('byod', 'upload', { method: 'POST', body: form }).then(data => {
      setResult(data)
      if (data.ok) {
        localStorage.setItem('pulse-user-store', '1')
        window.dispatchEvent(new CustomEvent('pulse-store', { detail: 'm_user' }))
      }
    })
  }

  return <section className="p-4 space-y-3">
    <h2 className="font-bold text-[#002E6E] text-lg">{t('My data')}</h2>
    <p className="text-xs text-gray-500">{t('Upload the documented catalog + sales pair. Demo data stays unchanged.')}</p>
    <div className="flex gap-3">
      <a className="text-xs text-[#002E6E] underline" href={`${API}/api/ext/byod/template/sales`}>{t('Sales template')}</a>
      <a className="text-xs text-[#002E6E] underline" href={`${API}/api/ext/byod/template/catalog`}>{t('Catalog template')}</a>
    </div>
    <input type="file" accept=".csv" aria-label={t('Sales template')} onChange={event => setSales(event.target.files[0])} />
    <input type="file" accept=".csv" aria-label={t('Catalog template')} onChange={event => setCatalog(event.target.files[0])} />
    <button disabled={!sales || !catalog} onClick={upload} className="w-full py-2 bg-[#00BAF2] disabled:opacity-40 text-white rounded-lg">{t('Validate & upload')}</button>
    {result && <div className="text-xs bg-gray-50 p-3 rounded space-y-1">
      <p className="font-semibold">{t(result.ok ? 'Upload successful' : 'Upload needs attention')}</p>
      <p>{t('Items')}: {result.skus} · {t('Sales rows')}: {result.rows}</p>
      {result.date_range && <p>{t('Date range')}: {result.date_range.join(' – ')}</p>}
      {result.errors.map((message, index) => <p key={`error-${index}`} className="text-red-700">{validationMessage(message, t)}</p>)}
      {result.warnings.map((message, index) => <p key={`warning-${index}`} className="text-amber-700">{validationMessage(message, t)}</p>)}
    </div>}
  </section>
}

export default { id: 'byod', flag: 'byod', label: 'My data', icon: '↑', order: 8, Tab: Byod }
