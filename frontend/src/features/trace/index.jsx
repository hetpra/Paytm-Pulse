import { useEffect, useState } from 'react'
import { ext } from '../../api'
import { useMerchantId } from '../framework'

function Trace() { const merchantId=useMerchantId(); const [data,setData]=useState(null); useEffect(()=>{ext('trace','',{},merchantId).then(setData).catch(()=>setData({events:[]}))},[merchantId]); return <section className="p-4"><h2 className="font-bold text-[#002E6E] text-lg">Pulse execution trace</h2><p className="text-xs text-gray-500 mt-1">A transparent record of the workflow.</p><div className="mt-4 space-y-3">{data?.events?.map(event=><div key={event.id} className="flex gap-3 text-sm"><span className="text-green-600">✓</span><div><p className="font-medium">{event.summary}</p><p className="text-[10px] text-gray-500">{event.node} · {event.ms} ms</p></div></div>)}{data && !data.events.length && <p className="text-sm text-gray-500">Run an analysis to see its trace.</p>}</div></section> }
export default { id:'trace', flag:'trace', label:'Trace', icon:'◷', order:5, Tab:Trace }
