"use client";

import { memo, useCallback, useEffect, useRef } from "react";

interface GlowingEffectProps {
  spread?: number;
  proximity?: number;
  inactiveZone?: number;
  borderWidth?: number;
  movementDuration?: number;
  disabled?: boolean;
}

const GlowingEffect = memo(
  ({
    spread = 90,
    proximity = 80,
    inactiveZone = 0.01,
    borderWidth = 0.5,
    movementDuration = 1.5,
    disabled = false,
  }: GlowingEffectProps) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const angleRef = useRef(0);
  const rafRef = useRef<number>(0);
  const activeRef = useRef(false);

  useEffect(() => {
    if (disabled) return;
    const card = cardRef.current?.parentElement;
    if (!card) return;

    const onMove = (e: PointerEvent) => {
      const rect = card.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;

      const dist = Math.hypot(e.clientX - cx, e.clientY - cy);
      const inactiveR = Math.min(rect.width, rect.height) * inactiveZone * 0.5;
      if (dist < inactiveR) { activeRef.current = false; return; }

      const inBounds =
        e.clientX > rect.left - proximity &&
        e.clientX < rect.right + proximity &&
        e.clientY > rect.top - proximity &&
        e.clientY < rect.bottom + proximity;

      activeRef.current = inBounds;
      if (!inBounds) return;

      const targetAngle =
        (Math.atan2(e.clientY - cy, e.clientX - cx) * 180) / Math.PI + 90;

      const diff = ((targetAngle - angleRef.current + 180) % 360) - 180;
      const target = angleRef.current + diff;

      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      const start = performance.now();
      const from = angleRef.current;
      const duration = movementDuration * 1000;

      const animate = (now: number) => {
        const t = Math.min((now - start) / duration, 1);
        const eased = t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2;
        angleRef.current = from + diff * eased;
        updateGradient();
        if (t < 1) rafRef.current = requestAnimationFrame(animate);
      };
      rafRef.current = requestAnimationFrame(animate);
    };

    const onLeave = () => { activeRef.current = false; updateGradient(); };

    document.addEventListener("pointermove", onMove, { passive: true });
    card.addEventListener("mouseleave", onLeave);
    return () => {
      document.removeEventListener("pointermove", onMove);
      card.removeEventListener("mouseleave", onLeave);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [disabled, proximity, inactiveZone, movementDuration]);

  const updateGradient = useCallback(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    if (!rect.width) return;

    const w = rect.width;
    const h = rect.height;
    const perimeter = 2 * (w + h);
    const halfSpread = (spread / 360) * perimeter;

    // Convert angle to a point on the border
    const angle = ((angleRef.current % 360) + 360) % 360;
    const pos = (angle / 360) * perimeter;

    // Build gradient stops along the perimeter
    const pct = (p: number) => `${(((p % perimeter) + perimeter) % perimeter / perimeter) * 100}%`;

    const active = activeRef.current;

    svg.style.opacity = "1";

    // Update the feGaussianBlur and gradient
    const grad = svg.querySelector("#glow-grad") as SVGLinearGradientElement | null;
    if (!grad) return;

    // Use a conic approach via SVG stroke-dashoffset
    const circle = svg.querySelector("#glow-path") as SVGPathElement | null;
    if (!circle) return;

    const total = circle.getTotalLength();
    const spotPos = (angle / 360) * total;
    const spotSize = (spread / 360) * total;

    if (active) {
      circle.style.strokeDasharray = `${spotSize} ${total - spotSize}`;
      circle.style.strokeDashoffset = `${total - spotPos + spotSize / 2}`;
      circle.style.opacity = "1";
    } else {
      circle.style.opacity = "0";
    }
  }, [spread]);

  if (disabled) return null;

  return (
    <div
      ref={cardRef}
      style={{
        position: "absolute",
        inset: `-${borderWidth}px`,
        borderRadius: "inherit",
        pointerEvents: "none",
        zIndex: 0,
        overflow: "hidden",
      }}
    >
      {/* Dim border background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "inherit",
          border: `${borderWidth}px solid`,
          borderColor: "rgba(0,0,0,0)",
        }}
      />

      {/* SVG glow that travels along border */}
      <svg
        ref={svgRef}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          overflow: "visible",
          borderRadius: "inherit",
        }}
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <defs>
          
          <linearGradient id="glow-grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%"   stopColor="#10b981" />
            <stop offset="33%"  stopColor="#3b82f6" />
            <stop offset="66%"  stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#f59e0b" />
          </linearGradient>
        </defs>
        <rect
          id="glow-path"
          x={borderWidth}
          y={borderWidth}
          width={100 - borderWidth * 2}
          height={100 - borderWidth * 2}
          rx="4"
          fill="none"
          stroke="url(#glow-grad)"
          strokeWidth={borderWidth}
          style={{
            opacity: 0,
            transition: "opacity 0.3s ease",
            strokeLinecap: "round",
          }}
        />
      </svg>
    </div>
  );
});

GlowingEffect.displayName = "GlowingEffect";

export { GlowingEffect };