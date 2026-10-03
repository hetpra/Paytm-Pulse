import { useEffect, useState } from 'react'

const choices = [['en','EN'],['hi','हिंदी'],['hinglish','Hinglish']]
function LanguageToggle() { const [language,setLanguage]=useState(localStorage.getItem('pulse-language') || 'en'); const select=value=>{localStorage.setItem('pulse-language',value); setLanguage(value); window.dispatchEvent(new CustomEvent('pulse-language',{detail:value}))}; return <div className="absolute right-2 top-8 flex gap-1">{choices.map(([value,label])=><button key={value} onClick={()=>select(value)} className={'text-[9px] px-1.5 py-1 rounded '+(language===value?'bg-white text-[#002E6E]':'bg-white/15 text-white')} aria-label={'Use '+label}>{label}</button>)}</div> }
export default { id:'i18n', flag:'i18n', order:6, slots:{'header.right':LanguageToggle} }
