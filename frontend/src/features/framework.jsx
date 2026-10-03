import { Component, createContext, useContext } from 'react'
import { enabledFeatures } from './registry'
import { useT } from '../localization'

export const MerchantContext = createContext('m1')
export const useMerchantId = () => useContext(MerchantContext)

export class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { failed: false } }
  static getDerivedStateFromError() { return { failed: true } }
  render() { return this.state.failed ? null : this.props.children }
}

export function Slot({ name, enabled, ctx = {} }) {
  return enabledFeatures(enabled).flatMap((feature) => {
    const Extension = feature.slots?.[name]
    return Extension ? [<ErrorBoundary key={feature.id}><Extension {...ctx} /></ErrorBoundary>] : []
  })
}

export function TabBar({ enabled, active, onChange }) {
  const t = useT()
  const tabs = enabledFeatures(enabled).filter((feature) => feature.Tab)
  const labels = { insights: 'Insights', backtest: 'Accuracy', impact: 'Impact', lending: 'Loan', trace: 'Trace', ask: 'Ask', byod: 'My data', distributor: 'Supplier', autopilot: 'Autopilot' }
  if (!tabs.length) return null
  return (
    <nav data-testid="tab-bar" className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-md bg-white/95 border-t border-slate-200 overflow-x-auto pb-[env(safe-area-inset-bottom)]">
      <div className="min-w-max flex px-2 py-1">
        <button data-testid="tab-home" onClick={() => onChange('home')} className={'shrink-0 mx-0.5 min-h-11 px-3 py-3 rounded-lg text-xs font-semibold transition-colors ' + (active === 'home' ? 'bg-[#E6F9FF] text-[#002E6E]' : 'text-slate-500')}>⌂ <span className="ml-0.5">{t('Home')}</span></button>
        {tabs.map((feature) => (
          <button key={feature.id} data-testid={'tab-' + feature.id} onClick={() => onChange(feature.id)}
            className={'shrink-0 mx-0.5 min-h-11 px-3 py-3 rounded-lg text-xs transition-colors ' + (active === feature.id ? 'bg-[#E6F9FF] text-[#002E6E] font-bold' : 'text-slate-500')}>
            {feature.icon} {t(labels[feature.id] || feature.label)}
          </button>
        ))}
      </div>
    </nav>
  )
}
