import { useEffect } from 'react'

export default function Toast({ type = 'info', message, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 5000)
    return () => clearTimeout(t)
  }, [onClose])

  const colors = {
    success: 'bg-[#1FB57A] text-white',
    error: 'bg-[#E5322D] text-white',
    info: 'bg-[#002E6E] text-white',
  }

  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
  }

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 max-w-sm w-[90%] animate-fadeIn">
      <div className={`${colors[type] || colors.info} px-4 py-3 rounded-xl shadow-lg flex items-start gap-2`}>
        <span className="text-sm mt-0.5">{icons[type]}</span>
        <p className="text-xs leading-relaxed flex-1">{message}</p>
        <button onClick={onClose} className="text-white/60 hover:text-white text-sm ml-1">✕</button>
      </div>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translate(-50%, 10px); }
          to { opacity: 1; transform: translate(-50%, 0); }
        }
        .animate-fadeIn { animation: fadeIn 0.3s ease-out; }
      `}</style>
    </div>
  )
}
