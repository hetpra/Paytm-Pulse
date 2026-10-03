import { useState } from 'react'
import ForecastChart from './ForecastChart'

const STATUS_COLORS = {
  critical: { bg: 'bg-red-500', text: 'text-red-600', bar: 'bg-red-400' },
  warning: { bg: 'bg-amber-500', text: 'text-amber-600', bar: 'bg-amber-400' },
  ok: { bg: 'bg-green-500', text: 'text-green-600', bar: 'bg-green-400' },
  incoming: { bg: 'bg-blue-500', text: 'text-blue-600', bar: 'bg-blue-400' },
}

export default function SkuList({ skus, plan }) {
  const [selectedSku, setSelectedSku] = useState(null)

  if (!skus || skus.length === 0) return null

  return (
    <>
      <div className="mx-4 mt-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Inventory</h3>

        <div className="bg-white rounded-xl shadow-sm overflow-hidden divide-y divide-gray-50">
          {skus.map(sku => {
            const colors = STATUS_COLORS[sku.status] || STATUS_COLORS.ok
            const barWidth = Math.max(3, Math.min(100, sku.stock_pct * 100))

            return (
              <div
                key={sku.id}
                className="flex items-center gap-2.5 px-3 py-2.5 hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => setSelectedSku(sku.id === selectedSku ? null : sku.id)}
              >
                <span className="text-lg w-7 text-center">{sku.emoji}</span>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-gray-800 truncate">{sku.name}</p>
                    <span className={`text-[10px] font-medium ${colors.text}`}>
                      {sku.status === 'incoming'
                        ? 'Incoming'
                        : sku.days_left <= 1
                          ? 'Out tomorrow!'
                          : `≈${sku.days_left.toFixed(1)} days`
                      }
                    </span>
                  </div>

                  {/* Stock bar */}
                  <div className="mt-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${colors.bar}`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>

                  {/* Incoming chip */}
                  {sku.incoming_qty > 0 && (
                    <p className="text-[10px] text-blue-500 font-medium mt-1">
                      📦 +{sku.incoming_qty} arriving {sku.incoming_eta}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Forecast chart overlay */}
      {selectedSku && (
        <ForecastChart
          skuId={selectedSku}
          isPremium={plan === 'premium'}
          onClose={() => setSelectedSku(null)}
        />
      )}
    </>
  )
}
