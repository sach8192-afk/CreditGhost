"use client";
import { useState, useEffect } from "react";
import { Cpu } from "lucide-react";

const MSGS = [
  "Parsing Bank Statement with pdfplumber...",
  "Extracting 14 Behavioral Risk Signals...",
  "Analyzing Inflow Variance & Essential Spend...",
  "Running XGBoost Inference Model...",
  "Detecting Income Manipulation Patterns...",
  "Finalizing Risk Intelligence Report...",
];

export default function LoadingScreen() {
  const [msgIdx, setMsgIdx]     = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const m = setInterval(() => setMsgIdx(i => Math.min(i + 1, MSGS.length - 1)), 800);
    const p = setInterval(() => setProgress(v => Math.min(v + 1.8, 100)), 80);
    return () => { clearInterval(m); clearInterval(p); };
  }, []);

  const r = 80, circ = 2 * Math.PI * r;

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0a0f1e,#0f172a,#0a0f1e)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 36, padding: 24, fontFamily: "Inter, sans-serif" }}>
      {/* Ring */}
      <div style={{ position: "relative" }}>
        <svg width="200" height="200" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
          <circle cx="100" cy="100" r={r} fill="none" stroke="#10B981" strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circ} strokeDashoffset={circ * (1 - progress / 100)}
            transform="rotate(-90 100 100)"
            style={{ filter: "drop-shadow(0 0 14px #10B981)", transition: "stroke-dashoffset 0.15s" }} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <Cpu size={28} color="#10B981" style={{ marginBottom: 6 }} />
          <span style={{ color: "#fff", fontSize: 20, fontWeight: 700 }}>{Math.round(progress)}%</span>
        </div>
        <div className="animate-pulse-glow" style={{ position: "absolute", inset: -24, borderRadius: "50%", background: "radial-gradient(circle,#10b98120 0%,transparent 70%)", pointerEvents: "none" }} />
      </div>

      {/* Log feed */}
      <div style={{ textAlign: "center" }}>
        <h2 style={{ color: "#fff", fontSize: 22, fontWeight: 700, marginBottom: 16 }}>Intelligence Engine Running</h2>
        <div style={{ background: "#0a0f1e", border: "1px solid #1e293b", borderRadius: 10, padding: "16px 20px", minWidth: 320, maxWidth: 480, fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>
          {MSGS.slice(0, msgIdx + 1).map((msg, i) => (
            <div key={i} style={{ color: i === msgIdx ? "#10B981" : "#2d3f55", marginBottom: 5, display: "flex", gap: 8 }}>
              <span>{i === msgIdx ? "▶" : "✓"}</span>{msg}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}