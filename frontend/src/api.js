const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const json = async response => { const body = await response.json(); if (!response.ok) throw new Error(body?.detail || body?.error?.message || 'Request failed'); return body }
export const fetchDashboard = (merchantId = 'm1') => fetch(`${API}/api/dashboard?merchant_id=${encodeURIComponent(merchantId)}`).then(json);
export const fetchForecast = (skuId) => fetch(`${API}/api/skus/${skuId}/forecast`).then(r => r.json());
export const postAnalyze = (merchantId = 'm1') => fetch(`${API}/api/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ merchant_id: merchantId }) }).then(json);
export const getProposal = (id) => fetch(`${API}/api/proposals/${id}`).then(r => r.json());
export const approveProposal = (id) => fetch(`${API}/api/proposals/${id}/approve`, { method: 'POST' }).then(r => r.json());
export const rejectProposal = (id) => fetch(`${API}/api/proposals/${id}/reject`, { method: 'POST' }).then(r => r.json());
export const fetchRevenue = () => fetch(`${API}/api/revenue`).then(r => r.json());
export const updatePlan = (plan, merchantId = 'm1') => fetch(`${API}/api/merchant/plan`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan, merchant_id: merchantId }) }).then(json);
export const resetDemo = (merchantId = 'm1') => fetch(`${API}/api/demo/reset?merchant_id=${encodeURIComponent(merchantId)}`, { method: 'POST' }).then(json);
export const fetchHealth = () => fetch(`${API}/health`).then(r => r.json());
export const fetchFeatures = () => fetch(`${API}/api/features`).then(r => r.json());
export const ext = (flag, path = '', opts = {}, merchantId = 'm1') => {
  const joiner = path.includes('?') ? '&' : '?'
  return fetch(`${API}/api/ext/${flag}/${path}${joiner}merchant_id=${encodeURIComponent(merchantId)}`, opts)
    .then(r => r.json())
}
