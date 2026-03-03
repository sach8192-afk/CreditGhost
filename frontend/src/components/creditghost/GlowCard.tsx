"use client";
import { GlowingEffect } from "@/components/ui/glowing-effect";

interface GlowCardProps {
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
}

export default function GlowCard({ children, style = {}, className = "" }: GlowCardProps) {
  return (
    <div
      className={className}
      style={{
        position: "relative",
        borderRadius: 16,
        background: "#0f172a",
        overflow: "visible",
        ...style,
      }}
    >
      <GlowingEffect
        borderWidth={1}
        spread={90}
        proximity={80}
        inactiveZone={0.3}
        movementDuration={0.15}
        disabled={false}
      />
      <div style={{
        position: "relative",
        zIndex: 1,
        borderRadius: 16,
        overflow: "hidden",
        height: "100%",
      }}>
        {children}
      </div>
    </div>
  );
}