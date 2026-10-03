const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const fetchDashboard = () => fetch(`${API}/api/dashboard`).then(r => r.json());
export const fetchForecast = (skuId) => fetch(`${API}/api/skus/${skuId}/forecast`).then(r => r.json());
export const postAnalyze = (merchantId = 'm1') => fetch(`${API}/api/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ merchant_id: merchantId }) }).then(r => r.json());
export const getProposal = (id) => fetch(`${API}/api/proposals/${id}`).then(r => r.json());
export const approveProposal = (id) => fetch(`${API}/api/proposals/${id}/approve`, { method: 'POST' }).then(r => r.json());
export const rejectProposal = (id) => fetch(`${API}/api/proposals/${id}/reject`, { method: 'POST' }).then(r => r.json());
export const fetchRevenue = () => fetch(`${API}/api/revenue`).then(r => r.json());
export const updatePlan = (plan) => fetch(`${API}/api/merchant/plan`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan }) }).then(r => r.json());
export const resetDemo = () => fetch(`${API}/api/demo/reset`, { method: 'POST' }).then(r => r.json());
export const fetchHealth = () => fetch(`${API}/health`).then(r => r.json());
