import { useState } from 'react'
import PlanSheet from './PlanSheet'

export default function RestockAlert({ proposal, onApprove, onReject, approving }) {
  const [showSheet, setShowSheet] = useState(false)

  if (!proposal) return null

  const { alert_text, line_items, total, loan_offer } = proposal

  return (
    <>
      <div className="mx-4 mt-3">
        <div
          className="bg-white border-2 border-red-200 rounded-xl overflow-hidden shadow-sm cursor-pointer"
          onClick={() => setShowSheet(true)}
        >
          {/* Header */}
          <div className="bg-red-50 px-3 py-2 flex items-center gap-2">
            <span className="text-lg">⚠️</span>
            <h3 className="text-sm font-bold text-red-700">Restock Alert</h3>
          </div>

          {/* Alert text */}
          <div className="px-3 py-2">
            <p className="text-xs text-gray-700 leading-relaxed">{alert_text}</p>
          </div>

          {/* Summary strip */}
          <div className="px-3 py-2 bg-gray-50 flex items-center gap-1.5 text-[10px] text-gray-500 flex-wrap">
            <span className="font-medium">{line_items?.length || 0} items</span>
            <span>·</span>
            <span>Order ₹{total?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
            {loan_offer && (
              <>
                <span>·</span>
                <span>Loan ₹{loan_offer.principal?.toLocaleString('en-IN')} @{loan_offer.interest_rate_pct}%</span>
              </>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex border-t border-gray-100">
            <button
              onClick={(e) => { e.stopPropagation(); onReject() }}
              className="flex-1 py-2.5 text-sm font-medium text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors border-r border-gray-100"
            >
              ✕
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onApprove() }}
              disabled={approving}
              className="flex-[2] py-2.5 text-sm font-bold text-white bg-[#1FB57A] hover:bg-[#18a06a] transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {approving ? (
                <>
                  <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                  Placing orders…
                </>
              ) : (
                '✓ Approve & Fund'
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
    </>
  )
}
