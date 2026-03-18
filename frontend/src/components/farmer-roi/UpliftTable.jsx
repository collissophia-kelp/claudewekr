import { fmtCurrency, fmtNumber, fmtPct } from '../../utils/formatters';

export default function UpliftTable({ scenarios }) {
  if (!scenarios?.length) return null;

  const currency = scenarios[0].currency || 'USD';

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data-table" style={{ fontSize: '0.8rem' }}>
        <thead>
          <tr>
            <th>Uplift</th>
            <th className="text-right">Baseline Yield</th>
            <th className="text-right">New Yield</th>
            <th className="text-right">Uplift Revenue</th>
            <th className="text-right">Stimblue+ Cost</th>
            <th className="text-right">Net Benefit</th>
            <th className="text-right">ROI</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map(s => (
            <tr key={s.uplift_pct}>
              <td style={{ fontWeight: 600 }}>{fmtPct(s.uplift_pct, 0)}</td>
              <td className="text-right">{fmtNumber(s.baseline_yield, 1)} t</td>
              <td className="text-right">{fmtNumber(s.new_yield, 1)} t</td>
              <td className="text-right">{fmtCurrency(s.uplift_revenue, currency)}</td>
              <td className="text-right" style={{ color: 'var(--danger)' }}>{fmtCurrency(s.stimblue_cost, currency)}</td>
              <td className="text-right" style={{ color: s.net_benefit >= 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>
                {fmtCurrency(s.net_benefit, currency)}
              </td>
              <td className="text-right" style={{ fontWeight: 700, color: s.roi_pct >= 100 ? 'var(--success)' : 'var(--warning)' }}>
                {fmtPct(s.roi_pct)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
