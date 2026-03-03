import { getScoreColor, getScoreLabel } from "@/lib/utils";

export default function ScoreGauge({ score }: { score: number }) {
  const pct = Math.min(1, Math.max(0, (score - 300) / 620));
  const color = getScoreColor(score);

  // Fixed arc: always draws left to right on a 180deg semicircle
  const cx = 100, cy = 105, r = 75;
  const startX = cx - r;  // leftmost point
  const endX = cx + r;    // rightmost point

  // Target point on arc
  const angle = Math.PI - pct * Math.PI; // goes from PI (left) to 0 (right)
  const fgX = cx + r * Math.cos(angle);
  const fgY = cy - r * Math.sin(angle);  // subtract because SVG y is flipped

  // Needle
  const needleAngle = Math.PI - pct * Math.PI;
  const needleX = cx + 60 * Math.cos(needleAngle);
  const needleY = cy - 60 * Math.sin(needleAngle);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width="210" height="125" viewBox="0 0 210 125">
        {/* Background arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#1e293b"
          strokeWidth="12"
          strokeLinecap="round"
        />

        {/* Foreground arc - always largeArc=0, sweep=1 */}
        {pct > 0 && (
          <path
            d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${fgX} ${fgY}`}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 6px ${color})` }}
          />
        )}

        {/* Needle */}
        <line
          x1={cx} y1={cy}
          x2={needleX} y2={needleY}
          stroke="#fff"
          strokeWidth="2"
          strokeLinecap="round"
          style={{ filter: "drop-shadow(0 0 3px #ffffff88)" }}
        />
        <circle cx={cx} cy={cy} r="5" fill={color} />

        {/* Labels */}
        <text x={cx} y={cy - 10} textAnchor="middle" fill="#fff" fontSize="24" fontWeight="700" fontFamily="Inter, sans-serif">
          {score}
        </text>
        <text x={cx} y={cy + 8} textAnchor="middle" fill={color} fontSize="11" fontWeight="600" fontFamily="Inter, sans-serif">
          {getScoreLabel(score)}
        </text>
        <text x={cx - r} y={cy + 18} textAnchor="middle" fill="#475569" fontSize="9" fontFamily="Inter, sans-serif">300</text>
        <text x={cx + r} y={cy + 18} textAnchor="middle" fill="#475569" fontSize="9" fontFamily="Inter, sans-serif">920</text>
      </svg>
      <p style={{ color: "#64748b", fontSize: 12, marginTop: 2 }}>Credit Score</p>
    </div>
  );
}