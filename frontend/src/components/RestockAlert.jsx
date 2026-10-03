import { useState } from 'react'
import PlanSheet from './PlanSheet'
import { useLanguage, useT } from '../localization'

export default function RestockAlert({ proposal, onApprove, onReject, approving }) {
  const language = useLanguage()
  const t = useT()
  const [showSheet, setShowSheet] = useState(false)
  const [preview, setPreview] = useState(false)

  if (!proposal) return null

  const { alert_text, line_items, total, loan_offer, alert_i18n } = proposal
  const earliestItem = line_items?.reduce((earliest, item) => item.days_left < earliest.days_left ? item : earliest, line_items[0])
  const alertFallback = earliestItem
    ? t('⚠️ {name} may run out in about {days} days. Restock {count} items for ₹{total}.', {
      name: earliestItem.name,
      days: Number.isFinite(earliestItem.days_left) ? Math.ceil(earliestItem.days_left) : 1,
      count: line_items.length,
      total: total?.toLocaleString('en-IN', { maximumFractionDigits: 0 }),
    }) + (loan_offer?.principal ? ` ${t('Loan option: ₹{amount}', { amount: loan_offer.principal.toLocaleString('en-IN', { maximumFractionDigits: 0 }) })}` : '')
    : alert_text
  const displayedAlert = language === 'en' ? alert_text : alert_i18n?.[language] || alertFallback
  const hasLocalizedAlert = Boolean(alert_i18n) || language !== 'en'

  return (
    <>
      <div className="mx-4 mt-3">
        <div data-testid="alert-card"
          className="bg-white border border-rose-200 rounded-2xl overflow-hidden shadow-sm shadow-rose-900/5 cursor-pointer"
          onClick={() => setShowSheet(true)}
        >
          {/* Header */}
          <div className="bg-[#FFF8EE] border-b border-amber-100 px-4 py-3 flex items-center gap-2.5">
            <span className="w-8 h-8 rounded-xl bg-white border border-amber-100 flex items-center justify-center">!</span>
            <div>
              <h3 className="text-sm font-bold text-rose-800">{t('Restock alert')}</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">{t('Review your suggested order')}</p>
            </div>
          </div>

          {/* Alert text */}
          <div className="px-4 py-3">
            <p className="text-xs text-slate-700 leading-relaxed">{displayedAlert}</p>
          </div>
          {hasLocalizedAlert && <button onClick={(e) => { e.stopPropagation(); setPreview(true) }} className="mx-3 mb-2 text-[10px] text-[#002E6E] underline">{t('Preview notification')}</button>}
          {hasLocalizedAlert && typeof speechSynthesis !== 'undefined' && <button onClick={(e) => { e.stopPropagation(); const utterance = new SpeechSynthesisUtterance(displayedAlert); utterance.lang = language === 'hi' || language === 'hinglish' ? 'hi-IN' : 'en-IN'; speechSynthesis.speak(utterance) }} className="mb-2 ml-3 text-[10px] text-[#002E6E] underline">🔊 {t('Listen')}</button>}

          {/* Summary strip */}
          <div className="px-4 py-2.5 bg-slate-50 flex items-center gap-1.5 text-[10px] text-slate-500 flex-wrap">
            <span className="font-medium">{t('{count} items', { count: line_items?.length || 0 })}</span>
            <span>·</span>
            <span>{t('Order ₹{amount}', { amount: total?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) })}</span>
            {loan_offer && (
              <>
                <span>·</span>
                <span>{t('Loan')} ₹{loan_offer.principal?.toLocaleString('en-IN')} @{loan_offer.interest_rate_pct}%</span>
              </>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex border-t border-gray-100">
            <button data-testid="reject-button"
              onClick={(e) => { e.stopPropagation(); onReject() }}
              className="flex-1 py-3 text-xs font-semibold text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors border-r border-slate-100"
            >
              {t('Dismiss')}
            </button>
            <button data-testid="approve-button"
              onClick={(e) => { e.stopPropagation(); onApprove() }}
              disabled={approving}
              className="flex-[2] py-3 text-sm font-bold text-[#002E6E] bg-[#00BAF2] hover:bg-[#00A8DC] transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {approving ? (
                <>
                  <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                  {t('Placing orders…')}
                </>
              ) : (
                `✓ ${t('Approve & Fund')}`
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Plan Sheet (bottom sheet) */}
      {showSheet && (
        <PlanSheet
          proposal={proposal}
          onClose={() => setShowSheet(false)}
          onApprove={() => { setShowSheet(false); onApprove() }}
          onReject={() => { setShowSheet(false); onReject() }}
          approving={approving}
        />
      )}
      {preview && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-5" onClick={() => setPreview(false)}><div className="bg-[#e8f5e9] rounded-2xl p-4 max-w-sm shadow-xl" onClick={event => event.stopPropagation()}><p className="text-[10px] text-green-700 mb-2">{t('Paytm Business · Simulated notification')}</p><p className="bg-white rounded-lg p-3 text-sm">{displayedAlert}</p><button onClick={() => { setPreview(false); onApprove() }} className="mt-3 w-full py-2 rounded-lg bg-[#00BAF2] text-[#002E6E] text-sm font-bold">✓ {t('Approve & Fund')}</button></div></div>}
    </>
  )
}
