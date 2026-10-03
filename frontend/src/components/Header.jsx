export default function Header({ merchant, onPlanToggle, onStoreToggle }) {
  return (
    <div className="bg-[#002E6E] text-white px-4 pt-10 pb-4 rounded-b-2xl relative">
      {/* Simulated demo tag */}
      <span className="absolute top-2 right-2 px-1.5 py-0.5 bg-amber-400/20 text-amber-300 text-[9px] rounded-full font-medium">
        Simulated demo
      </span>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-tight">📊 Inventory</h1>
          <p className="text-blue-200 text-xs mt-0.5">{merchant.name}</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Cash chip */}
          <div className="bg-white/10 backdrop-blur px-2.5 py-1 rounded-lg">
            <p className="text-[9px] text-blue-200">Cash</p>
            <p className="text-sm font-bold">₹{merchant.cash_balance.toLocaleString('en-IN')}</p>
          </div>
        </div>
      </div>

      {/* Plan badge */}
      <div className="mt-2 flex items-center gap-2">
        {onStoreToggle && <button onClick={onStoreToggle} className="px-2 py-0.5 rounded-full text-[10px] bg-white/15 text-white">{merchant.id === 'm_user' ? 'My store' : 'Demo store'}</button>}
        <button
          onClick={onPlanToggle}
          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all
            ${merchant.plan === 'premium'
              ? 'bg-amber-400 text-[#002E6E]'
              : 'bg-white/15 text-white/70 hover:bg-white/25'
            }`}
        >
          {merchant.plan === 'premium' ? '⭐ Premium' : 'Free'}
        </button>
        {merchant.plan === 'free' && (
          <span className="text-[9px] text-blue-300">Tap to upgrade → ₹499/mo</span>
        )}
      </div>
    </div>
  )
}
