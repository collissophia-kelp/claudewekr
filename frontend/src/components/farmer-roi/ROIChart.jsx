import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { fmtPct, fmtCurrency } from '../../utils/formatters';

export default function ROIChart({ scenarios }) {
  if (!scenarios?.length) return null;

  const data = scenarios.map(s => ({
    name: `${s.uplift_pct}% Uplift`,
    roi: s.roi_pct,
    netBenefit: s.net_benefit,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ left: 10, right: 20, top: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="name" tick={{ fill: '#8BA4C4', fontSize: 12 }} />
        <YAxis tick={{ fill: '#8BA4C4', fontSize: 11 }} tickFormatter={v => `${v}%`} />
        <Tooltip
          contentStyle={{ background: '#162A48', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#E8EDF3' }}
          formatter={(v, name) => [
            name === 'roi' ? fmtPct(v) : fmtCurrency(v),
            name === 'roi' ? 'ROI' : 'Net Benefit',
          ]}
        />
        <Bar dataKey="roi" radius={[4, 4, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.roi >= 100 ? '#4CAF50' : d.roi >= 50 ? '#2E6FC2' : '#FFA726'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
