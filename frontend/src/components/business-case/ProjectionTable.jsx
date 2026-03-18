import { fmtCurrency, fmtNumber, fmtPct } from '../../utils/formatters';

export default function ProjectionTable({ projections }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data-table" style={{ fontSize: '0.8rem' }}>
        <thead>
          <tr>
            <th>Year</th>
            <th className="text-right">Hectares</th>
            <th className="text-right">Coverage</th>
            <th className="text-right">Treated Ha</th>
            <th className="text-right">Litres</th>
            <th className="text-right">Revenue (EUR)</th>
          </tr>
        </thead>
        <tbody>
          {projections.map(p => (
            <tr key={p.year}>
              <td style={{ fontWeight: 600 }}>Year {p.year}</td>
              <td className="text-right">{fmtNumber(p.hectares)}</td>
              <td className="text-right">{fmtPct(p.coverage_pct * 100, 0)}</td>
              <td className="text-right">{fmtNumber(p.treated_hectares)}</td>
              <td className="text-right">{fmtNumber(p.litres_required)}</td>
              <td className="text-right" style={{ fontWeight: 600, color: 'var(--success)' }}>{fmtCurrency(p.revenue_eur)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr style={{ fontWeight: 700, borderTop: '2px solid var(--border)' }}>
            <td>Total</td>
            <td></td>
            <td></td>
            <td></td>
            <td className="text-right">{fmtNumber(projections.reduce((s, p) => s + p.litres_required, 0))}</td>
            <td className="text-right" style={{ color: 'var(--success)' }}>
              {fmtCurrency(projections.reduce((s, p) => s + p.revenue_eur, 0))}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
