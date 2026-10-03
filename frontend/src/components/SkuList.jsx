import { useState } from 'react'
import ForecastChart from './ForecastChart'
import { useT } from '../localization'

const STATUS_COLORS = {
  critical: { bg: 'bg-red-500', text: 'text-red-600', bar: 'bg-red-400' },
  warning: { bg: 'bg-amber-500', text: 'text-amber-600', bar: 'bg-amber-400' },
  ok: { bg: 'bg-green-500', text: 'text-green-600', bar: 'bg-green-400' },
  incoming: { bg: 'bg-blue-500', text: 'text-blue-600', bar: 'bg-blue-400' },
}

export default function SkuList({ skus, plan }) {
  const t = useT()
  const [selectedSku, setSelectedSku] = useState(null)

  if (!skus || skus.length === 0) return null

  return (
    <>
      <div className="mx-4 mt-5">
        <div className="flex items-end justify-between mb-2.5">
          <div>
            <h3 className="text-sm font-bold text-slate-800">{t('Inventory')}</h3>
            <p className="text-[10px] text-slate-400 mt-0.5">{t('Tap an item to view its forecast')}</p>
          </div>
          <span className="text-[10px] font-semibold text-slate-500 bg-white border border-slate-200 rounded-full px-2 py-1">{t('{count} items', { count: skus.length })}</span>
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden divide-y divide-slate-100">
          {skus.map(sku => {
            const colors = STATUS_COLORS[sku.status] || STATUS_COLORS.ok
            const barWidth = Math.max(3, Math.min(100, sku.stock_pct * 100))

            return (
              <div data-testid="sku-row"
                key={sku.id}
                className="flex items-center gap-3 px-3.5 py-3 hover:bg-slate-50/80 cursor-pointer transition-colors"
                onClick={() => setSelectedSku(sku.id === selectedSku ? null : sku.id)}
              >
                <span className="text-lg w-9 h-9 rounded-xl bg-slate-50 flex items-center justify-center shrink-0">{sku.emoji}</span>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-gray-800 truncate">{sku.name}</p>
                    <span className={`text-[10px] font-medium ${colors.text}`}>
                      {sku.status === 'incoming'
                        ? t('Incoming')
                        : sku.days_left <= 1
                          ? t('Out tomorrow!')
                          : t('≈{days} days', { days: sku.days_left.toFixed(1) })
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
                      📦 +{sku.incoming_qty} {t('arriving {date}', { date: sku.incoming_eta })}
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
