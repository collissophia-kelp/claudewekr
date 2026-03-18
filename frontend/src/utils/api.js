const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => request('/dashboard/summary'),
  getMarketShare: () => request('/dashboard/market-share'),

  // Companies
  getCompanies: (params = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v != null && v !== '') qs.set(k, v); });
    const q = qs.toString();
    return request(`/companies${q ? '?' + q : ''}`);
  },
  getCompany: (name) => request(`/companies/${encodeURIComponent(name)}`),
  updateScores: (name, scores) =>
    request(`/companies/${encodeURIComponent(name)}/scores`, {
      method: 'PATCH', body: JSON.stringify(scores),
    }),
  createCompany: (data) =>
    request('/companies', { method: 'POST', body: JSON.stringify(data) }),

  // Config
  getScoringConfig: () => request('/config/scoring'),
  updateScoringConfig: (data) =>
    request('/config/scoring', { method: 'PUT', body: JSON.stringify(data) }),
  whatIf: (weights) =>
    request('/config/what-if', { method: 'POST', body: JSON.stringify(weights) }),
  getCropBaselines: () => request('/config/crop-baselines'),
  getMarketData: () => request('/config/market-data'),
  getCurrencyRate: (from, to) => request(`/config/currency/${from}/${to}`),

  // Analysis
  analyseCompany: (url) =>
    request('/analysis/analyse', { method: 'POST', body: JSON.stringify({ url }) }),
  getFarmerROI: (crop, country, areaHa = 100) =>
    request(`/analysis/farmer-roi?crop=${encodeURIComponent(crop)}&country=${encodeURIComponent(country)}&area_ha=${areaHa}`),
  getProjections: (name, hectares, rampYears = 3) => {
    const qs = new URLSearchParams();
    if (hectares) qs.set('hectares', hectares);
    qs.set('ramp_years', rampYears);
    return request(`/analysis/projections/${encodeURIComponent(name)}?${qs}`);
  },
};
