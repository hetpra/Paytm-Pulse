import { useState } from 'react'

const choices = [['en','EN'],['hi','हिंदी'],['hinglish','Hinglish']]
function LanguageToggle() { const [language,setLanguage]=useState(localStorage.getItem('pulse-language') || 'en'); const select=value=>{localStorage.setItem('pulse-language',value); setLanguage(value); window.dispatchEvent(new CustomEvent('pulse-language',{detail:value}))}; return <div className="flex items-center justify-end gap-1">{choices.map(([value,label])=><button key={value} onClick={()=>select(value)} className={'whitespace-nowrap text-[9px] px-2 py-1.5 rounded-md transition-colors '+(language===value?'bg-white text-[#002E6E] font-semibold':'bg-white/10 text-blue-100 hover:bg-white/20')} aria-label={'Use '+label}>{label}</button>)}</div> }
export default { id:'i18n', flag:'i18n', order:6, slots:{'header.right':LanguageToggle} }
