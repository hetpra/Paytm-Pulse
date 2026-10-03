import { useT } from '../localization'

export default function PlanSheet({ proposal, onClose, onApprove, onReject, approving }) {
  const t = useT()
  if (!proposal) return null

  const { line_items, subtotal, platform_fee, total, cash_available, cash_gap, loan_offer } = proposal
  const eligibilityReason = reason => {
    const monthlyRevenue = reason.match(/^₹([\d,]+) average monthly revenue$/)
    if (monthlyRevenue) return t('₹{amount} average monthly revenue', { amount: monthlyRevenue[1] })
    const consistency = reason.match(/^Revenue consistency multiplier ([\d.]+)$/)
    if (consistency) return t('Revenue consistency multiplier {multiplier}', { multiplier: consistency[1] })
    return t(reason)
  }

  // Group line items by supplier
  const grouped = {}
  for (const li of (line_items || [])) {
    const key = li.supplier_id
    if (!grouped[key]) grouped[key] = { name: li.supplier_name, items: [] }
    grouped[key].items.push(li)
  }

  return (
    <div data-testid="plan-sheet" className="fixed inset-0 z-50 flex items-end justify-center" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" />

      {/* Sheet */}
      <div
        className="relative bg-white rounded-t-2xl w-full max-w-md max-h-[85vh] overflow-y-auto animate-slideUp"
        onClick={e => e.stopPropagation()}
      >
        {/* Handle */}
        <div className="flex justify-center pt-2 pb-1">
          <div className="w-8 h-1 bg-gray-300 rounded-full" />
        </div>

        <div className="px-4 pb-4">
          <h2 className="text-base font-bold text-[#002E6E] mb-3">{t('Order Details')}</h2>

          {/* Line items grouped by supplier */}
          {Object.entries(grouped).map(([suppId, group]) => (
            <div key={suppId} className="mb-3">
              <h4 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                📦 {group.name}
              </h4>
              {group.items.map(li => (
                <div key={li.sku_id} className="flex items-center justify-between py-1.5 border-b border-gray-50">
                  <div className="flex items-center gap-2">
                    <span>{li.emoji}</span>
                    <div>
                      <p className="text-xs font-medium text-gray-800">{li.name}</p>
                      <p className="text-[10px] text-gray-400">
                        {li.qty} × ₹{li.unit_cost} ·{' '}
                        <span className={li.status === 'critical' ? 'text-red-500' : 'text-amber-500'}>
                          {li.days_left <= 1 ? t('Out tomorrow!') : t('≈{days} days', { days: li.days_left.toFixed(1) })}
                        </span>
                      </p>
                    </div>
                  </div>
                  <p className="text-xs font-semibold text-gray-700">₹{li.line_total.toLocaleString('en-IN')}</p>
                </div>
              ))}
            </div>
          ))}

          {/* Totals */}
          <div className="border-t border-gray-200 pt-2 mt-2 space-y-1">
            <div className="flex justify-between text-xs text-gray-500">
              <span>{t('Subtotal')}</span>
              <span>₹{subtotal?.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between text-xs text-gray-500">
              <span>{t('Platform fee (1%)')}</span>
              <span>₹{platform_fee?.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between text-sm font-bold text-[#002E6E]">
              <span>{t('Total')}</span>
              <span>₹{total?.toLocaleString('en-IN')}</span>
            </div>
          </div>

          {/* Cash section */}
          <div className="border-t border-gray-200 pt-2 mt-2 space-y-1">
            <div className="flex justify-between text-xs text-gray-500">
              <span>{t('Cash available')}</span>
              <span>₹{cash_available?.toLocaleString('en-IN')}</span>
            </div>
            {cash_gap > 0 && (
              <div className="flex justify-between text-xs text-red-500 font-medium">
                <span>{t('Cash gap')}</span>
                <span>₹{cash_gap?.toLocaleString('en-IN')}</span>
              </div>
            )}
          </div>

          {/* Loan terms */}
          {loan_offer && loan_offer.principal > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 mt-3">
              <h4 className="text-xs font-bold text-[#002E6E] mb-1.5">💰 {t('Pre-approved Paytm Business Loan')}</h4>
              <div className="space-y-1 text-[11px] text-gray-600">
                <div className="flex justify-between">
                  <span>{t('Principal')}</span>
                  <span className="font-semibold">₹{loan_offer.principal.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t('Interest ({rate}% flat)', { rate: loan_offer.interest_rate_pct })}</span>
                  <span>₹{loan_offer.interest.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t('Processing fee')}</span>
                  <span>₹{loan_offer.processing_fee.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between font-bold text-[#002E6E] pt-1 border-t border-blue-200">
                  <span>{t('Repay in {days} days', { days: loan_offer.tenure_days })}</span>
                  <span>₹{loan_offer.total_repayment.toLocaleString('en-IN')}</span>
                </div>
                {loan_offer.daily_deduction && <div className="flex justify-between"><span>{t('Daily settlement deduction')}</span><span>₹{loan_offer.daily_deduction.toLocaleString('en-IN')}</span></div>}
                {loan_offer.apr_pct && <div className="flex justify-between"><span>{t('Effective APR (illustrative)')}</span><span>≈ {loan_offer.apr_pct}%</span></div>}
              </div>
              {loan_offer.eligibility?.reasons?.map((reason, index) => <p key={index} className="text-[10px] text-blue-800 mt-1">✓ {eligibilityReason(reason)}</p>)}
              {!loan_offer.fully_covered && (
                <p className="text-[10px] text-amber-600 mt-1">⚠️ {t("Loan doesn't fully cover the gap")}</p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={onReject}
              className="flex-1 py-2.5 text-sm font-medium text-gray-500 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
            >
              {t('Dismiss')}
            </button>
            <button
              onClick={onApprove}
              disabled={approving}
              className="flex-[2] py-2.5 text-sm font-bold text-[#002E6E] bg-[#00BAF2] rounded-xl hover:bg-[#00A8DC] transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {approving ? t('Placing orders…') : `✓ ${t('Approve & Fund')}`}
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        .animate-slideUp { animation: slideUp 0.3s ease-out; }
      `}</style>
    </div>
  )
}
