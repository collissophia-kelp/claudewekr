import { tierColor, tierBgColor } from '../../utils/formatters';

export default function TierBadge({ tier, label }) {
  return (
    <span
      className="tier-badge"
      style={{ background: tierBgColor(tier), color: tierColor(tier), border: `1px solid ${tierColor(tier)}` }}
    >
      {label || `Tier ${tier}`}
    </span>
  );
}
