"use client";
import { useState } from "react";
import { TrendingUp, AlertTriangle } from "lucide-react";
import Navbar from "@/components/creditghost/Navbar";
import HeroSection from "@/components/creditghost/HeroSection";
import OnboardingForm from "@/components/creditghost/OnboardingForm";
import LoadingScreen from "@/components/creditghost/LoadingScreen";
import ResultsDashboard from "@/components/creditghost/ResultsDashboard";
import type { Reason } from "@/lib/utils";

// ── Types ────────────────────────────────────────────────────
interface ScoreResult {
  score: number;
  confidence: number;
  reasons: Reason[];
  bucket: string;
  bucketEmoji: string;
  bucketColor: string;
  topHelping: string[];
  topHurting: string[];
}

// ── API base URL from env (falls back to localhost for dev) ──
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Page() {
  const [step, setStep]     = useState(0);         // 0=home, 1=loading, 2=results
  const [result, setResult] = useState<ScoreResult | null>(null);

  async function handleAnalyze() {
    setStep(1); // show loading screen

    try {
      const persona = "priya"; // rotate to priya / arjun as needed

      const response = await fetch(`${API_URL}/demo/${persona}`);

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();
      console.log("Backend response:", data);

      // ── Map backend signal objects → Reason[] ───────────────
      // top_helping / top_hurting are objects with shape:
      // { signal, name, score, max, pct, level, direction, impact, message, tip }
      // We display `name` as the label and `message` as the detail text.
      const reasons: Reason[] = [
        ...(data.top_helping ?? []).map((r: { name: string; message: string }) => ({
          type: "positive" as const,
          text: r.message ? `${r.name}: ${r.message}` : r.name,
          icon: TrendingUp,
        })),
        ...(data.top_hurting ?? []).map((r: { name: string; message: string; tip?: string }) => ({
          type: "negative" as const,
          text: r.message
            ? `${r.name}: ${r.message}${r.tip ? ` 💡 ${r.tip}` : ""}`
            : r.name,
          icon: AlertTriangle,
        })),
      ];

      setResult({
        score:       data.final_score,
        confidence:  data.percentile,
        reasons,
        bucket:      data.bucket       ?? "",
        bucketEmoji: data.bucket_emoji ?? "",
        bucketColor: data.bucket_color ?? "#10B981",
        topHelping:  data.top_helping  ?? [],
        topHurting:  data.top_hurting  ?? [],
      });

      setStep(2);
    } catch (error) {
      console.error("API error:", error);
      alert(
        "Could not reach backend.\n" +
        "Make sure FastAPI is running:\n\n" +
        "  cd CreditGhost/backend\n" +
        "  uvicorn backend.app.main:app --reload --port 8000"
      );
      setStep(0);
    }
  }

  function handleReset() {
    setStep(0);
    setResult(null);
  }

  if (step === 1) return <LoadingScreen />;
  if (step === 2 && result) return <ResultsDashboard result={result} onReset={handleReset} />;

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0a0f1e,#0f172a,#060d1a)" }}>
      <Navbar />
      <div style={{ maxWidth: 920, margin: "0 auto", padding: "52px 20px 60px" }}>
        <HeroSection />
        <OnboardingForm onAnalyze={handleAnalyze} />
      </div>
    </div>
  );
}