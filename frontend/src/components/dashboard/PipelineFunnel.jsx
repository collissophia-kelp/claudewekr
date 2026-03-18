import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { fmtCurrency, fmtNumber, stageColor } from '../../utils/formatters';

export default function PipelineFunnel({ funnel }) {
  const data = funnel.map(f => ({
    name: `${f.stage} — ${f.stage_name}`,
    stage: f.stage,
    count: f.count,
    hectares: f.hectares,
    revenue: f.revenue,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="name" width={180} tick={{ fill: '#8BA4C4', fontSize: 12 }} />
          <Tooltip
            contentStyle={{ background: '#162A48', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#E8EDF3' }}
            formatter={(v, name) => [name === 'count' ? v : fmtCurrency(v), name === 'count' ? 'Companies' : 'Revenue']}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {data.map((d, i) => <Cell key={i} fill={stageColor(d.stage)} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-3 grid grid-cols-3 gap-3 text-center" style={{ fontSize: '0.8rem' }}>
        {funnel.filter(f => f.count > 0).slice(0, 3).map(f => (
          <div key={f.stage}>
            <div style={{ color: stageColor(f.stage), fontWeight: 700 }}>{f.stage}</div>
            <div style={{ color: 'var(--text-secondary)' }}>{f.count} companies</div>
            <div style={{ color: 'var(--text-muted)' }}>{fmtCurrency(f.revenue)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
