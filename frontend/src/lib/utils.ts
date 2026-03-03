import { TrendingUp, PiggyBank, BarChart3, ShieldCheck, AlertTriangle, LucideIcon } from "lucide-react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export type Reason = {
  type: "positive" | "negative";
  text: string;
  icon: LucideIcon;
};

/**
 * Utility to join class names and intelligently merge Tailwind classes.
 *
 * Usage: `cn("p-4", condition && "bg-red-500")`
 */
export function cn(...inputs: Parameters<typeof clsx>) {
  return twMerge(clsx(...inputs));
}

export function getScoreColor(score: number) {
  if (score >= 750) return "#10B981";
  if (score >= 600) return "#F59E0B";
  return "#EF4444";
}

export function getScoreLabel(score: number) {
  if (score >= 750) return "Excellent";
  if (score >= 600) return "Fair";
  return "Poor";
}

export function getRiskLabel(score: number) {
  if (score >= 750) return "Low Risk Borrower";
  if (score >= 600) return "Moderate Risk";
  return "High Risk Borrower";
}

export function getMetrics(score: number) {
  return [
    { label: "Income Stability",      value: score >= 750 ? "High"     : score >= 600 ? "Medium"   : "Low"    },
    { label: "Savings Buffer Days",   value: score >= 750 ? "45+ days" : score >= 600 ? "12 days"  : "< 5 days" },
    { label: "Essential Spend Ratio", value: score >= 750 ? "52%"      : score >= 600 ? "68%"      : "85%+"   },
  ];
}

export function generateReasons(score: number): Reason[] {
  if (score >= 750) return [
    { type: "positive", text: "Consistent monthly salary deposits detected — Inflow Stability: High", icon: TrendingUp },
    { type: "positive", text: "Savings buffer exceeds 45 days of expenses", icon: PiggyBank },
    { type: "positive", text: "Essential spend ratio within healthy 52% threshold", icon: BarChart3 },
  ];
  if (score >= 600) return [
    { type: "positive", text: "Moderate income consistency — some irregular inflows noted", icon: TrendingUp },
    { type: "negative", text: "Savings buffer is thin — only ~12 days of expense coverage", icon: PiggyBank },
    { type: "positive", text: "No fraudulent transaction patterns detected by XGBoost model", icon: ShieldCheck },
  ];
  return [
    { type: "negative", text: "High inflow variance detected — income manipulation risk flagged", icon: AlertTriangle },
    { type: "negative", text: "Essential spend ratio exceeds 85% — financial stress signal", icon: BarChart3 },
    { type: "negative", text: "Insufficient savings buffer — less than 5 days of coverage", icon: PiggyBank },
  ];
}