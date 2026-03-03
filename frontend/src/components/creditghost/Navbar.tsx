import { ShieldCheck } from "lucide-react";

export default function Navbar() {
  return (
    <nav style={{ borderBottom: "1px solid #1e293b", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: 8, background: "linear-gradient(135deg,#10B981,#3b82f6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <ShieldCheck size={18} color="#fff" />
        </div>
        <span style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em", color: "#f1f5f9" }}>CreditGhost</span>
      </div>
      <span style={{ fontSize: 12, color: "#10B981", background: "#10b98115", border: "1px solid #10b98130", padding: "4px 12px", borderRadius: 20 }}>
        Beta
      </span>
    </nav>
  );
}