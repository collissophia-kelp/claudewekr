import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { tierColor, fmtCurrency } from '../../utils/formatters';

const COLORS = [tierColor(1), tierColor(2), tierColor(3), tierColor(4)];

export default function TierDistribution({ tiers }) {
  const data = tiers.map(t => ({
    name: t.label,
    value: t.count,
    revenue: t.revenue,
    tier: t.tier,
  }));

  return (
    <div className="flex items-center gap-4">
      <ResponsiveContainer width="50%" height={200}>
        <PieChart>
          <Pie data={data} dataKey="value" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2}>
            {data.map((d, i) => <Cell key={i} fill={COLORS[i]} />)}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#162A48', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#E8EDF3' }}
            formatter={(v, name, entry) => [`${v} companies`, entry.payload.name]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex-1 space-y-2">
        {tiers.map(t => (
          <div key={t.tier} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div style={{ width: 10, height: 10, borderRadius: 2, background: tierColor(t.tier) }} />
              <span style={{ fontSize: '0.85rem' }}>{t.label}</span>
            </div>
            <div className="text-right">
              <span style={{ fontWeight: 600 }}>{t.count}</span>
              <span style={{ color: 'var(--text-muted)', marginLeft: 8, fontSize: '0.8rem' }}>{fmtCurrency(t.revenue)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
