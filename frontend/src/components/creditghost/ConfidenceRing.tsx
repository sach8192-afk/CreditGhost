export default function ConfidenceRing({ value }: { value: number }) {
  const r = 36, circ = 2 * Math.PI * r;
  const color = value >= 75 ? "#10B981" : "#F59E0B";
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
      <svg width="96" height="96" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle cx="48" cy="48" r={r} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={circ * (1 - value / 100)}
          transform="rotate(-90 48 48)"
          style={{ filter: `drop-shadow(0 0 6px ${color})`, transition: "stroke-dashoffset 1.2s ease" }} />
        <text x="48" y="53" textAnchor="middle" fill="#fff" fontSize="16" fontWeight="700" fontFamily="Inter, sans-serif">{value}%</text>
      </svg>
      <p style={{ color: "#94a3b8", fontSize: 11, textAlign: "center" }}>Verification Confidence</p>
    </div>
  );
}