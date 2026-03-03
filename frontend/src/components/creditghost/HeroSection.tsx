import { Zap, Cpu, ShieldCheck, BarChart3 } from "lucide-react";
import GlowCard from "./GlowCard";

const features = [
  { icon: <Cpu size={20} color="#10B981" />,    title: "XGBoost Model",    desc: "14 behavioral risk signals" },
  { icon: <ShieldCheck size={20} color="#3b82f6" />, title: "Fraud Detection", desc: "Income manipulation scanner" },
  { icon: <BarChart3 size={20} color="#f59e0b" />,   title: "360° Profiling",  desc: "Inflow, savings & spend analysis" },
];

export default function HeroSection() {
  return (
    <>
      {/* Hero text */}
      <div className="animate-fadeUp" style={{ textAlign: "center", marginBottom: 52 }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "#10b98115", border: "1px solid #10b98130", borderRadius: 20, padding: "6px 14px", marginBottom: 20, fontSize: 12, color: "#10B981" }}>
          <Zap size={12} /> Behavioral Credit Scoring · 14 Risk Signals
        </div>
        <h1 style={{ fontSize: "clamp(30px,5vw,52px)", fontWeight: 800, letterSpacing: "-0.035em", lineHeight: 1.12, marginBottom: 16, color: "#f1f5f9" }}>
          Know Your True<br />
          <span style={{ background: "linear-gradient(90deg,#10B981,#3b82f6,#8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Credit Potential
          </span>
        </h1>
        <p style={{ color: "#64748b", fontSize: 15, maxWidth: 460, margin: "0 auto" }}>
          AI-powered risk assessment using behavioral signals from your financial data. No traditional credit history needed.
        </p>
      </div>

      {/* Feature cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: 16, marginBottom: 52 }}>
        {features.map((c, i) => (
          <GlowCard key={i} style={{ padding: "22px 20px 20px" }}>
            <div style={{ marginBottom: 10 }}>{c.icon}</div>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4, color: "#f1f5f9" }}>{c.title}</div>
            <div style={{ color: "#64748b", fontSize: 12 }}>{c.desc}</div>
          </GlowCard>
        ))}
      </div>
    </>
  );
}