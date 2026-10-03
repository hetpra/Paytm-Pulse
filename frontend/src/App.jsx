import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import SalesChart from './components/SalesChart'
import RestockAlert from './components/RestockAlert'
import SkuList from './components/SkuList'
import RevenueView from './components/RevenueView'
import Toast from './components/Toast'
import { fetchDashboard, fetchFeatures, postAnalyze, approveProposal, rejectProposal, resetDemo, updatePlan } from './api'
import { MerchantContext, Slot, TabBar } from './features/framework'
import { enabledFeatures } from './features/registry'

function App() {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)
  const [approving, setApproving] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [view, setView] = useState('merchant') // merchant | paytm
  const [features, setFeatures] = useState([])
  const [tab, setTab] = useState('home')
  const [merchantId, setMerchantId] = useState(() => localStorage.getItem('pulse-merchant') || 'm1')

  const loadDashboard = useCallback(async () => {
    try {
      const data = await fetchDashboard(merchantId)
      setDashboard(data)
      setError(null)
    } catch (e) {
      if (merchantId === 'm_user') {
        localStorage.removeItem('pulse-user-store')
        setMerchantId('m1')
        return
      }
      setError('Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [merchantId])

  useEffect(() => {
    loadDashboard()
    fetchFeatures().then(data => setFeatures(data.enabled || [])).catch(() => setFeatures([]))
  }, [loadDashboard])

  useEffect(() => {
    const switchStore = event => setMerchantId(event.detail || 'm1')
    window.addEventListener('pulse-store', switchStore)
    return () => window.removeEventListener('pulse-store', switchStore)
  }, [])

  useEffect(() => { localStorage.setItem('pulse-merchant', merchantId) }, [merchantId])

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      const data = await postAnalyze(merchantId)
      if (data.proposal) {
        await loadDashboard()
        setToast({ type: 'info', message: 'Analysis complete — review the restock alert below' })
      } else {
        setToast({ type: 'info', message: 'All items are well-stocked!' })
      }
    } catch (e) {
      setToast({ type: 'error', message: 'Analysis failed' })
    } finally {
      setAnalyzing(false)
    }
  }

  const handleApprove = async (proposalId) => {
    setApproving(true)
    try {
      const result = await approveProposal(proposalId)
      const pos = result.purchase_orders || []
      const loan = result.loan
      let msg = `Orders placed with ${pos.length} distributor(s) ✓`
      if (loan) msg += ` · Loan ₹${loan.principal.toLocaleString('en-IN')} disbursed ✓`
      if (result.merchant) msg += ` · Cash ₹${result.merchant.cash_balance.toLocaleString('en-IN')}`
      setToast({ type: 'success', message: msg })
      await loadDashboard()
    } catch (e) {
      setToast({ type: 'error', message: 'Approval failed' })
    } finally {
      setApproving(false)
    }
  }

  const handleReject = async (proposalId) => {
    try {
      await rejectProposal(proposalId)
      setToast({ type: 'info', message: 'Proposal dismissed' })
      await loadDashboard()
    } catch (e) {
      setToast({ type: 'error', message: 'Rejection failed' })
    }
  }

  const handleReset = async () => {
    try {
      await resetDemo(merchantId)
      setToast({ type: 'info', message: 'Demo reset ✓' })
      await loadDashboard()
    } catch (e) {
      setToast({ type: 'error', message: 'Reset failed' })
    }
  }

  const handlePlanToggle = async () => {
    if (!dashboard) return
    const newPlan = dashboard.merchant.plan === 'premium' ? 'free' : 'premium'
    try {
      await updatePlan(newPlan, merchantId)
      await loadDashboard()
      setToast({ type: 'success', message: newPlan === 'premium' ? 'Premium activated! ₹499/mo' : 'Switched to Free plan' })
    } catch (e) {
      setToast({ type: 'error', message: 'Plan update failed' })
    }
  }

  // Loading skeleton
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full mx-auto p-4 space-y-4">
          <div className="h-14 bg-gray-200 rounded-xl animate-pulse" />
          <div className="h-8 bg-gray-200 rounded-lg animate-pulse w-3/4" />
          <div className="h-40 bg-gray-200 rounded-xl animate-pulse" />
          <div className="h-24 bg-gray-200 rounded-xl animate-pulse" />
          <div className="h-24 bg-gray-200 rounded-xl animate-pulse" />
        </div>
      </div>
    )
  }

  if (error && !dashboard) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-8">
          <p className="text-red-500 text-lg mb-4">{error}</p>
          <button onClick={loadDashboard} className="px-4 py-2 bg-[#00BAF2] text-white rounded-lg">Retry</button>
        </div>
      </div>
    )
  }

  const { merchant, kpis, sales_last_14d, skus, pending_proposal } = dashboard
  const hasAtRisk = kpis.skus_at_risk > 0

  const activeFeature = enabledFeatures(features).find(feature => feature.id === tab)
  const ActiveTab = activeFeature?.Tab
  return (
    <MerchantContext.Provider value={merchant.id}>
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-md mx-auto pb-20">
        <Header
          merchant={merchant}
          onPlanToggle={handlePlanToggle}
          onStoreToggle={merchantId === 'm_user' || localStorage.getItem('pulse-user-store') ? () => setMerchantId(merchantId === 'm_user' ? 'm1' : 'm_user') : null}
        />
        <Slot name="header.right" enabled={features} ctx={{ merchant, dashboard }} />

        {/* View toggle */}
        <div className="flex mx-4 mt-3 bg-gray-200 rounded-lg p-0.5">
          <button
            onClick={() => setView('merchant')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${view === 'merchant' ? 'bg-white text-[#002E6E] shadow-sm' : 'text-gray-500'}`}
          >
            Merchant View
          </button>
          <button
            onClick={() => setView('paytm')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${view === 'paytm' ? 'bg-white text-[#002E6E] shadow-sm' : 'text-gray-500'}`}
          >
            Paytm View
          </button>
        </div>

        {view === 'merchant' ? (
          <>
            {!activeFeature && <Slot name="dashboard.top" enabled={features} ctx={{ merchant, dashboard }} />}
            {!activeFeature && <>{/* KPI row */}
            <div className="flex gap-2 mx-4 mt-3">
              {kpis.revenue_at_risk_7d > 0 && (
                <div className="flex-1 bg-red-50 border border-red-200 rounded-xl p-3">
                  <p className="text-[10px] text-red-500 uppercase font-medium">Revenue at risk</p>
                  <p className="text-lg font-bold text-red-600">₹{kpis.revenue_at_risk_7d.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                  <p className="text-[10px] text-red-400">this week</p>
                </div>
              )}
              <div className={`flex-1 rounded-xl p-3 ${kpis.skus_at_risk > 0 ? 'bg-amber-50 border border-amber-200' : 'bg-green-50 border border-green-200'}`}>
                <p className={`text-[10px] uppercase font-medium ${kpis.skus_at_risk > 0 ? 'text-amber-500' : 'text-green-500'}`}>Items at risk</p>
                <p className={`text-lg font-bold ${kpis.skus_at_risk > 0 ? 'text-amber-600' : 'text-green-600'}`}>{kpis.skus_at_risk}</p>
                <p className={`text-[10px] ${kpis.skus_at_risk > 0 ? 'text-amber-400' : 'text-green-400'}`}>of {kpis.items_total} total</p>
              </div>
            </div>

            {/* Sales chart */}
            <SalesChart data={sales_last_14d} />

            {/* Restock alert */}
            {pending_proposal && (
              <RestockAlert
                proposal={pending_proposal}
                onApprove={() => handleApprove(pending_proposal.id)}
                onReject={() => handleReject(pending_proposal.id)}
                approving={approving}
              />
            )}

            {/* Analyze button */}
            {!pending_proposal && hasAtRisk && (
              <div className="mx-4 mt-3">
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  className="w-full py-3 bg-[#00BAF2] text-white font-semibold rounded-xl hover:bg-[#009dd4] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {analyzing ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                      Analyzing...
                    </>
                  ) : (
                    '🤖 Run AI Analysis'
                  )}
                </button>
              </div>
            )}

            {/* SKU list */}
            <SkuList skus={skus} plan={merchant.plan} />
            <Slot name="dashboard.bottom" enabled={features} ctx={{ merchant, dashboard }} /></>}
            {ActiveTab && <ActiveTab merchant={merchant} dashboard={dashboard} />}
          </>
        ) : (
          <RevenueView />
        )}

        {/* Footer */}
        <div className="text-center mt-8 mb-4">
          <button
            onClick={handleReset}
            className="text-xs text-gray-400 hover:text-gray-600 underline"
          >
            Reset demo
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <Slot name="app.overlay" enabled={features} ctx={{ merchant, dashboard }} />
      <TabBar enabled={features} active={tab} onChange={setTab} />
    </div>
    </MerchantContext.Provider>
  )
}

export default App
