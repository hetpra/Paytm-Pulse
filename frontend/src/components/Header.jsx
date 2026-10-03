import { useT } from '../localization'

export default function Header({ merchant, onPlanToggle, onStoreToggle, headerRight }) {
  const t = useT()
  return (
    <div className="bg-[#002E6E] text-white px-5 pt-3 pb-5 rounded-b-[1.5rem] relative">
      <div className="flex min-h-8 items-center justify-between gap-2 mb-4">
        <span className="shrink-0 rounded-full bg-white/10 px-2 py-1 text-[9px] font-medium text-blue-100">
          {t('Demo')}
        </span>
        <div className="min-w-0">{headerRight}</div>
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-[#002E6E] shadow-sm" aria-hidden="true">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
                <path d="M4 19.5h16" stroke="#002E6E" strokeWidth="1.7" strokeLinecap="round" />
                <rect x="5" y="11" width="3.5" height="7" rx="1" fill="#00BAF2" />
                <rect x="10.25" y="7" width="3.5" height="11" rx="1" fill="#002E6E" />
                <rect x="15.5" y="4" width="3.5" height="14" rx="1" fill="#00BAF2" />
              </svg>
            </span>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Pulse</h1>
              <p className="text-[10px] font-semibold tracking-[0.12em] text-cyan-200 uppercase">{t('Store desk')}</p>
            </div>
          </div>
          <p className="text-blue-100 text-xs mt-2 truncate">{merchant.name}</p>
        </div>
        <div className="shrink-0 rounded-2xl border border-white/10 bg-white/10 px-3.5 py-2.5">
          <p className="text-[10px] text-blue-100 uppercase tracking-[0.1em]">{t('Available cash')}</p>
          <p className="text-lg font-bold tabular-nums">₹{merchant.cash_balance.toLocaleString('en-IN')}</p>
        </div>
      </div>

      {/* Plan badge */}
      <div className="mt-4 flex min-h-7 flex-wrap items-center gap-2">
        {onStoreToggle && <button onClick={onStoreToggle} className="min-h-9 px-3 py-1.5 rounded-full text-[11px] bg-white/10 text-white">{t(merchant.id === 'm_user' ? 'My store' : 'Demo store')}</button>}
        <button
          onClick={onPlanToggle}
          className={`min-h-9 px-3 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-wider transition-all
            ${merchant.plan === 'premium'
              ? 'bg-[#00BAF2] text-[#002E6E]'
              : 'bg-white text-[#002E6E]'
            }`}
        >
          {merchant.plan === 'premium' ? '⭐ Premium' : t('Free')}
        </button>
        {merchant.plan === 'free' && (
          <span className="text-[11px] text-blue-100">{t('Tap to upgrade · ₹499/mo')}</span>
        )}
      </div>
    </div>
  )
}
