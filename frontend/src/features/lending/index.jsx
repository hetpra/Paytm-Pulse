import { useState } from 'react'

function LendingTerms({ dashboard }) {
  const offer = dashboard.pending_proposal?.loan_offer
  if (!offer) return null
  return <div className="mx-4 mt-3 rounded-xl bg-blue-50 border border-blue-200 p-3 text-xs text-blue-950"><b>Why you qualify</b><p className="mt-1">Repay ₹{offer.daily_deduction?.toLocaleString('en-IN')}/day · APR ≈ {offer.apr_pct}%</p><p className="text-[10px] mt-1">Illustrative terms based on recent sales.</p></div>
}
function Lending() { return <section className="p-4"><h2 className="font-bold text-[#002E6E] text-lg">Lending eligibility</h2><p className="text-sm text-gray-600 mt-2">Loan offers are calculated from sales consistency, revenue trend, repayment capacity, and a conservative cap. Terms appear with a restock proposal.</p><p className="text-xs text-gray-500 mt-3">Illustrative demo terms — not a lending decision.</p></section> }
export default { id:'lending', flag:'lending', label:'Loan', icon:'₹', order:4, Tab:Lending, slots:{'dashboard.top':LendingTerms} }
