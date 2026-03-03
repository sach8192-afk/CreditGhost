import { CheckCircle2, AlertTriangle, ArrowRight, Zap } from "lucide-react";
import GlowCard from "./GlowCard";
import ScoreGauge from "./ScoreGauge";
import ConfidenceRing from "./ConfidenceRing";
import Navbar from "./Navbar";
import { getScoreColor, getRiskLabel, getMetrics, type Reason } from "@/lib/utils";

// ── Props ─────────────────────────────────────────────────────
interface Props {
  result: {
    score:       number;
    confidence:  number;
    reasons:     Reason[];
    bucket?:     string;
    bucketEmoji?: string;
    bucketColor?: string;
    topHelping?: string[];
    topHurting?: string[];
  };
  onReset: () => void;
}

export default function ResultsDashboard({ result, onReset }: Props) {
  const { score, confidence, reasons, bucketEmoji, bucket } = result;
  const scoreColor = getScoreColor(score);
  const metrics    = getMetrics(score);

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0a0f1e,#0f172a,#060d1a)", fontFamily: "Inter, sans-serif", color: "#f1f5f9" }}>
      <Navbar />
      <div style={{ maxWidth: 920, margin: "0 auto", padding: "40px 20px" }}>

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "#10b98115", border: "1px solid #10b98130", borderRadius: 20, padding: "5px 14px", marginBottom: 12, fontSize: 12, color: "#10B981" }}>
            <CheckCircle2 size={12} /> Analysis Complete
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.02em", marginBottom: 4 }}>
            Risk Intelligence Report{" "}
            {bucketEmoji && (
              <span style={{ fontSize: 24 }}>{bucketEmoji}</span>
            )}
          </h1>
          {bucket && (
            <div style={{ display: "inline-block", marginBottom: 6, padding: "3px 12px", borderRadius: 12, background: `${scoreColor}20`, color: scoreColor, fontSize: 12, fontWeight: 700, border: `1px solid ${scoreColor}40` }}>
              {bucket}
            </div>
          )}
          <p style={{ color: "#64748b", fontSize: 13 }}>Generated {new Date().toLocaleString()}</p>
        </div>

        {/* Top 3 cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 20, marginBottom: 20 }}>
          <GlowCard style={{ padding: 28, textAlign: "center" }}>
            <ScoreGauge score={score} />
          </GlowCard>

          <GlowCard style={{ padding: 28, textAlign: "center" }}>
            <ConfidenceRing value={confidence} />
            <div style={{ marginTop: 18 }}>
              <div style={{ color: "#64748b", fontSize: 11, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>Risk Classification</div>
              <div style={{ display: "inline-block", padding: "5px 16px", borderRadius: 20, background: `${scoreColor}20`, color: scoreColor, fontSize: 13, fontWeight: 700, border: `1px solid ${scoreColor}40` }}>
                {getRiskLabel(score)}
              </div>
            </div>
          </GlowCard>

          <GlowCard style={{ padding: 24 }}>
            <div style={{ color: "#94a3b8", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 16 }}>Key Metrics</div>
            {metrics.map((m, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: i < 2 ? "1px solid #1e293b" : "none" }}>
                <span style={{ color: "#64748b", fontSize: 13 }}>{m.label}</span>
                <span style={{ color: scoreColor, fontWeight: 700, fontSize: 13 }}>{m.value}</span>
              </div>
            ))}
          </GlowCard>
        </div>

        {/* Reasoning feed */}
        <GlowCard style={{ padding: 28, marginBottom: 28 }}>
          <h3 style={{ fontWeight: 700, fontSize: 16, marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
            <Zap size={16} color="#10B981" /> AI Reasoning Feed
          </h3>

          {reasons.length === 0 ? (
            <p style={{ color: "#475569", fontSize: 13 }}>No reasoning signals returned from backend.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {reasons.map((r, i) => {
                const pos = r.type === "positive";
                return (
                  <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 14, background: pos ? "#10b98108" : "#ef444408", border: `1px solid ${pos ? "#10b98125" : "#ef444425"}`, borderRadius: 10, padding: "14px 16px" }}>
                    <div style={{ width: 32, height: 32, borderRadius: 8, flexShrink: 0, background: pos ? "#10b98120" : "#ef444420", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      {pos
                        ? <CheckCircle2 size={16} color="#10B981" />
                        : <AlertTriangle size={16} color="#EF4444" />
                      }
                    </div>
                    <div style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 500, paddingTop: 6 }}>{r.text}</div>
                  </div>
                );
              })}
            </div>
          )}
        </GlowCard>

        {/* CTA */}
        <div style={{ textAlign: "center" }}>
          <button onClick={onReset} style={{ background: "linear-gradient(135deg,#10B981,#059669)", color: "#fff", border: "none", borderRadius: 10, padding: "14px 32px", fontWeight: 700, fontSize: 15, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 8, boxShadow: "0 4px 24px #10b98140" }}>
            Run New Analysis <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}