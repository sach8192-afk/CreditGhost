import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CreditGhost — Behavioral Credit Scoring",
  description: "AI-powered credit scoring for thin-file borrowers using 14 behavioral risk signals.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}