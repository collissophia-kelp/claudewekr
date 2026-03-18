export const fmtCurrency = (v, currency = 'EUR') => {
  if (v == null) return '—';
  const sym = currency === 'EUR' ? '€' : currency === 'USD' ? '$' : currency + ' ';
  if (Math.abs(v) >= 1e9) return `${sym}${(v / 1e9).toFixed(1)}B`;
  if (Math.abs(v) >= 1e6) return `${sym}${(v / 1e6).toFixed(1)}M`;
  if (Math.abs(v) >= 1e3) return `${sym}${(v / 1e3).toFixed(0)}K`;
  return `${sym}${v.toLocaleString('en', { maximumFractionDigits: 0 })}`;
};

export const fmtNumber = (v, decimals = 0) => {
  if (v == null) return '—';
  return v.toLocaleString('en', { maximumFractionDigits: decimals });
};

export const fmtPct = (v, decimals = 1) => {
  if (v == null) return '—';
  return `${v.toFixed(decimals)}%`;
};

export const fmtScore = (v) => {
  if (v == null) return '—';
  return v.toFixed(2);
};

export const tierColor = (tier) => {
  const colors = { 1: '#2E7D32', 2: '#4CAF50', 3: '#FFA726', 4: '#9E9E9E' };
  return colors[tier] || '#9E9E9E';
};

export const tierBgColor = (tier) => {
  const colors = {
    1: 'rgba(46,125,50,0.15)', 2: 'rgba(76,175,80,0.15)',
    3: 'rgba(255,167,38,0.15)', 4: 'rgba(158,158,158,0.1)',
  };
  return colors[tier] || 'rgba(158,158,158,0.1)';
};

export const stageColor = (stage) => {
  const colors = { L5: '#2E7D32', L4: '#43A047', L3: '#66BB6A', L2: '#2E6FC2', L1: '#90CAF9', L0: '#546E7A' };
  return colors[stage] || '#546E7A';
};
