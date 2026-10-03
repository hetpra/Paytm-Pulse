import { Component, createContext, useContext } from 'react'
import { enabledFeatures } from './registry'

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
  const tabs = enabledFeatures(enabled).filter((feature) => feature.Tab)
  if (!tabs.length) return null
  return (
    <nav data-testid="tab-bar" className="fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 overflow-x-auto">
      <div className="min-w-max flex px-2">
        <button data-testid="tab-home" onClick={() => onChange('home')} className="shrink-0 px-3 py-3 text-xs">Home</button>
        {tabs.map((feature) => (
          <button key={feature.id} data-testid={'tab-' + feature.id} onClick={() => onChange(feature.id)}
            className={'shrink-0 px-3 py-3 text-xs ' + (active === feature.id ? 'text-[#002E6E] font-bold' : '')}>
            {feature.icon} {feature.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
