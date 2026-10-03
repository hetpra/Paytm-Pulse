import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import SalesChart from './components/SalesChart'
import RestockAlert from './components/RestockAlert'
import SkuList from './components/SkuList'
import Toast from './components/Toast'
import { fetchDashboard, fetchFeatures, postAnalyze, approveProposal, rejectProposal, resetDemo, updatePlan } from './api'
import { MerchantContext, Slot, TabBar } from './features/framework'
import { enabledFeatures } from './features/registry'
import { LanguageContext, translate } from './localization'

function App() {
  const [language, setLanguage] = useState(() => localStorage.getItem('pulse-language') || 'en')
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)
  const [approving, setApproving] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
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
  useEffect(() => {
    const changeLanguage = event => setLanguage(event.detail || localStorage.getItem('pulse-language') || 'en')
    window.addEventListener('pulse-language', changeLanguage)
    return () => window.removeEventListener('pulse-language', changeLanguage)
  }, [])
  useEffect(() => {
    document.documentElement.lang = language === 'hi' ? 'hi' : language === 'hinglish' ? 'hi-Latn' : 'en'
  }, [language])

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      const data = await postAnalyze(merchantId)
      if (data.proposal) {
        await loadDashboard()
        setToast({ type: 'info', message: translate(language, 'Restock plan ready — review the suggested order below') })
      } else {
        setToast({ type: 'info', message: translate(language, 'All items are well-stocked!') })
      }
    } catch (e) {
      setToast({ type: 'error', message: translate(language, 'Analysis failed') })
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
      let msg = translate(language, 'Orders placed with {count} distributor(s) ✓', { count: pos.length })
      if (loan) msg += translate(language, ' · Loan ₹{amount} disbursed ✓', { amount: loan.principal.toLocaleString('en-IN') })
      if (result.merchant) msg += translate(language, ' · Cash ₹{amount}', { amount: result.merchant.cash_balance.toLocaleString('en-IN') })
      setToast({ type: 'success', message: msg })
      await loadDashboard()
    } catch (e) {
      setToast({ type: 'error', message: translate(language, 'Approval failed') })
    } finally {
      setApproving(false)
    }
  }

  const handleReject = async (proposalId) => {
    try {
      await rejectProposal(proposalId)
      setToast({ type: 'info', message: translate(language, 'Proposal dismissed') })
      await loadDashboard()
    } catch (e) {
      setToast({ type: 'error', message: translate(language, 'Rejection failed') })
    }
  }

  const handleReset = async () => {
    try {
      await resetDemo(merchantId)
      setToast({ type: 'info', message: translate(language, 'Demo reset ✓') })
      await loadDashboard()
    } catch (e) {
      setToast({ type: 'error', message: translate(language, 'Reset failed') })
    }
  }

  const handlePlanToggle = async () => {
    if (!dashboard) return
    const newPlan = dashboard.merchant.plan === 'premium' ? 'free' : 'premium'
    try {
      await updatePlan(newPlan, merchantId)
      await loadDashboard()
      setToast({ type: 'success', message: translate(language, newPlan === 'premium' ? 'Premium activated! ₹499/mo' : 'Switched to Free plan') })
    } catch (e) {
      setToast({ type: 'error', message: translate(language, 'Plan update failed') })
    }
  }

  // Loading skeleton
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center p-3">
        <div className="app-shell max-w-md w-full mx-auto p-4 space-y-4">
          <div className="h-24 bg-slate-200 rounded-2xl animate-pulse" />
          <div className="h-8 bg-slate-200 rounded-lg animate-pulse w-3/4" />
          <div className="h-40 bg-slate-200 rounded-2xl animate-pulse" />
          <div className="h-24 bg-slate-200 rounded-2xl animate-pulse" />
          <div className="h-24 bg-slate-200 rounded-2xl animate-pulse" />
        </div>
      </div>
    )
  }

  if (error && !dashboard) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
        <div className="app-shell text-center p-8 w-full max-w-md">
          <p className="text-red-600 text-lg font-semibold mb-4">{translate(language, error)}</p>
          <button onClick={loadDashboard} className="px-5 py-2.5 bg-[#00BAF2] text-white font-semibold rounded-xl shadow-sm">{translate(language, 'Retry')}</button>
        </div>
      </div>
    )
  }

  const { merchant, kpis, sales_last_14d, skus, pending_proposal } = dashboard
  const hasAtRisk = kpis.skus_at_risk > 0

  const activeFeature = enabledFeatures(features).find(feature => feature.id === tab)
  const ActiveTab = activeFeature?.Tab
  return (
    <LanguageContext.Provider value={language}>
    <MerchantContext.Provider value={merchant.id}>
    <div className="min-h-screen bg-slate-100 px-0 sm:px-4 sm:py-5">
      <div className="app-shell max-w-md mx-auto min-h-screen sm:min-h-[calc(100vh-2.5rem)] pb-24 overflow-hidden">
        <Header
          merchant={merchant}
          onPlanToggle={handlePlanToggle}
          onStoreToggle={merchantId === 'm_user' || localStorage.getItem('pulse-user-store') ? () => setMerchantId(merchantId === 'm_user' ? 'm1' : 'm_user') : null}
          headerRight={<Slot name="header.right" enabled={features} ctx={{ merchant, dashboard }} />}
        />

        {!activeFeature && (
          <div className="mx-4 mt-5 mb-1 flex items-end justify-between gap-3">
            <div>
              <p className="text-[9px] font-bold tracking-[0.16em] text-slate-400 uppercase">{translate(language, 'Store overview')}</p>
              <h2 className="mt-1 text-base font-bold tracking-tight text-[#002E6E]">{translate(language, 'Your business at a glance')}</h2>
            </div>
            <span className={`mb-0.5 inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[9px] font-semibold ${hasAtRisk ? 'bg-amber-50 text-amber-800' : 'bg-cyan-50 text-[#005E8A]'}`}>
              <span className={`h-1.5 w-1.5 rounded-full ${hasAtRisk ? 'bg-amber-500' : 'bg-[#00BAF2]'}`} />
              {translate(language, hasAtRisk ? 'Needs attention' : 'On track')}
            </span>
          </div>
        )}

        {!activeFeature && <Slot name="dashboard.top" enabled={features} ctx={{ merchant, dashboard }} />}
        {!activeFeature && <>{/* KPI row */}
            <div className="grid grid-cols-2 gap-3 mx-4 mt-4">
              {kpis.revenue_at_risk_7d > 0 && (
                <div className="metric-card metric-card-risk">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[9px] text-rose-700 uppercase font-bold tracking-[0.1em]">{translate(language, 'Revenue at risk')}</p>
                    <span className="metric-icon text-rose-700" aria-hidden="true">₹</span>
                  </div>
                  <p className="text-xl font-bold text-slate-900 mt-2 tabular-nums">₹{kpis.revenue_at_risk_7d.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{translate(language, 'Potential sales · next 7 days')}</p>
                </div>
              )}
              <div className={`metric-card ${kpis.skus_at_risk > 0 ? 'metric-card-stock-risk' : 'metric-card-good'} ${kpis.revenue_at_risk_7d > 0 ? '' : 'col-span-2'}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className={`text-[9px] uppercase font-bold tracking-[0.1em] ${kpis.skus_at_risk > 0 ? 'text-amber-800' : 'text-[#005E8A]'}`}>{translate(language, 'Items at risk')}</p>
                  <span className="metric-icon text-[#002E6E]" aria-hidden="true">▦</span>
                </div>
                <p className="text-xl font-bold text-slate-900 mt-2 tabular-nums">{kpis.skus_at_risk}<span className="text-xs font-medium text-slate-400"> / {kpis.items_total}</span></p>
                <p className="text-[10px] text-slate-500 mt-1">{translate(language, kpis.skus_at_risk > 0 ? 'Stock may run low soon' : 'All listed items look covered')}</p>
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
              <div className="mx-4 mt-4">
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  className="w-full py-3 bg-[#00BAF2] text-[#002E6E] font-semibold rounded-xl hover:bg-[#00a8dc] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {analyzing ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                      {translate(language, 'Preparing your restock plan…')}
                    </>
                  ) : (
                    translate(language, 'Create restock plan')
                  )}
                </button>
              </div>
            )}

            {/* SKU list */}
            <SkuList skus={skus} plan={merchant.plan} />
            <Slot name="dashboard.bottom" enabled={features} ctx={{ merchant, dashboard }} /></>}
        {ActiveTab && <div className="feature-panel"><ActiveTab merchant={merchant} dashboard={dashboard} /></div>}

        {tab === 'impact' && (
          <div className="text-center mt-5 mb-4">
            <button
              onClick={handleReset}
              className="text-xs text-slate-400 hover:text-slate-600 underline underline-offset-4"
            >
              {translate(language, 'Reset demo')}
            </button>
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <Slot name="app.overlay" enabled={features} ctx={{ merchant, dashboard }} />
      <TabBar enabled={features} active={tab} onChange={setTab} />
    </div>
    </MerchantContext.Provider>
    </LanguageContext.Provider>
  )
}

export default App
