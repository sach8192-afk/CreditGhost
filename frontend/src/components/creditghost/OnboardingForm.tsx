"use client";
import { useState } from "react";
import { ChevronRight, Lock, Zap } from "lucide-react";
import GlowCard from "./GlowCard";

interface Props {
  onAnalyze: (result: any) => void;
}

function Input({ label, placeholder = "", type = "text", value, onChange, error }: {
  label: string; placeholder?: string; type?: string;
  value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: "block", color: "#94a3b8", fontSize: 11, fontWeight: 600, marginBottom: 6, letterSpacing: "0.08em", textTransform: "uppercase" }}>
        {label}
      </label>
      <input
        type={type} placeholder={placeholder} value={value} onChange={onChange}
        style={{
          width: "100%", background: "#1e293b",
          border: `1px solid ${error ? "#ef4444" : "#334155"}`,
          borderRadius: 8, padding: "11px 14px", color: "#f1f5f9", fontSize: 14,
          outline: "none", fontFamily: "Inter, sans-serif",
        }}
        onFocus={e => (e.target.style.borderColor = error ? "#ef4444" : "#10B981")}
        onBlur={e  => (e.target.style.borderColor = error ? "#ef4444" : "#334155")}
      />
      {error && (
        <p style={{ color: "#ef4444", fontSize: 11, marginTop: 4 }}>⚠ {error}</p>
      )}
    </div>
  );
}

export default function OnboardingForm({ onAnalyze }: Props) {
  const [formStep, setFormStep] = useState(1);
  const [form, setForm] = useState({ name: "", dob: "", pan: "", aadhaar: "", phone: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const update = (k: string, v: string) => {
    setForm(f => ({ ...f, [k]: v }));
    setErrors(e => ({ ...e, [k]: "" })); // clear error on type
  };

  function validateStep1() {
    const e: Record<string, string> = {};
    if (!form.name.trim())       e.name = "Full name is required";
    if (!form.dob.trim())        e.dob  = "Date of birth is required";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function validateStep2() {
    const e: Record<string, string> = {};
    if (!form.pan.trim())                            e.pan    = "PAN number is required";
    else if (!/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(form.pan.toUpperCase())) e.pan = "Invalid PAN format (e.g. ABCDE1234F)";
    if (!form.aadhaar.trim())                        e.aadhaar = "Aadhaar number is required";
    else if (form.aadhaar.replace(/\s/g, "").length !== 12) e.aadhaar = "Aadhaar must be 12 digits";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function validateStep3() {
    const e: Record<string, string> = {};
    if (!form.phone.trim())                             e.phone = "Phone number is required";
    else if (!/^[6-9]\d{9}$/.test(form.phone.replace(/\s|\+91/g, ""))) e.phone = "Enter a valid 10-digit Indian mobile number";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  const btnPrimary: React.CSSProperties = {
    background: "#10B981", color: "#fff", border: "none", borderRadius: 8,
    padding: "12px", fontWeight: 700, fontSize: 14, cursor: "pointer",
    display: "flex", alignItems: "center", justifyContent: "center", gap: 8, width: "100%",
  };
  const btnBack: React.CSSProperties = {
    flex: 1, background: "#1e293b", color: "#94a3b8", border: "1px solid #334155",
    borderRadius: 8, padding: "12px", fontWeight: 600, fontSize: 14, cursor: "pointer",
  };

  return (
    <GlowCard style={{ maxWidth: 480, margin: "0 auto", padding: 32 }}>
      {/* Step indicator */}
      <div style={{ display: "flex", alignItems: "center", marginBottom: 28 }}>
        {[1, 2, 3].map(s => (
          <div key={s} style={{ display: "flex", alignItems: "center", flex: s < 3 ? 1 : 0 }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: 11, fontWeight: 700, flexShrink: 0,
              background: formStep === s ? "#10B981" : formStep > s ? "#10b98130" : "#1e293b",
              color: formStep >= s ? "#fff" : "#475569",
              border: formStep === s ? "2px solid #10B981" : "2px solid transparent",
              transition: "all 0.3s",
            }}>
              {formStep > s ? "✓" : s}
            </div>
            {s < 3 && <div style={{ flex: 1, height: 2, background: formStep > s ? "#10b98140" : "#1e293b", margin: "0 8px", transition: "background 0.3s" }} />}
          </div>
        ))}
      </div>

      {formStep === 1 && (
        <>
          <h2 style={{ fontWeight: 700, fontSize: 18, marginBottom: 4, color: "#f1f5f9" }}>Identity Verification</h2>
          <p style={{ color: "#64748b", fontSize: 13, marginBottom: 24 }}>Step 1 of 3 — Personal details</p>
          <Input label="Full Name" placeholder="Arjun Sharma" value={form.name} onChange={e => update("name", e.target.value)} error={errors.name} />
          <Input label="Date of Birth" type="date" value={form.dob} onChange={e => update("dob", e.target.value)} error={errors.dob} />
          <button style={btnPrimary} onClick={() => { if (validateStep1()) setFormStep(2); }}>
            Continue <ChevronRight size={16} />
          </button>
        </>
      )}

      {formStep === 2 && (
        <>
          <h2 style={{ fontWeight: 700, fontSize: 18, marginBottom: 4, color: "#f1f5f9" }}>Financial Identifiers</h2>
          <p style={{ color: "#64748b", fontSize: 13, marginBottom: 24 }}>Step 2 of 3 — KYC documents</p>
          <Input label="PAN Number" placeholder="ABCDE1234F" value={form.pan} onChange={e => update("pan", e.target.value.toUpperCase())} error={errors.pan} />
          <Input label="Aadhaar Number" placeholder="XXXX XXXX XXXX" value={form.aadhaar} onChange={e => update("aadhaar", e.target.value)} error={errors.aadhaar} />
          <div style={{ display: "flex", gap: 10 }}>
            <button style={btnBack} onClick={() => setFormStep(1)}>Back</button>
            <button style={{ ...btnPrimary, flex: 2, width: "auto" }} onClick={() => { if (validateStep2()) setFormStep(3); }}>
              Continue <ChevronRight size={16} />
            </button>
          </div>
        </>
      )}

      {formStep === 3 && (
        <>
          <h2 style={{ fontWeight: 700, fontSize: 18, marginBottom: 4, color: "#f1f5f9" }}>Financial Link</h2>
          <p style={{ color: "#64748b", fontSize: 13, marginBottom: 24 }}>Step 3 of 3 — Connect your accounts</p>
          <Input label="Phone Number" placeholder="9876543210" type="tel" value={form.phone} onChange={e => update("phone", e.target.value)} error={errors.phone} />
          <button style={{ width: "100%", background: "#0f172a", border: "1px dashed #334155", borderRadius: 8, padding: "12px", color: "#64748b", cursor: "pointer", fontSize: 13, fontWeight: 600, marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
            <Lock size={14} /> Link Bank Account via Account Aggregator
          </button>
          <div style={{ display: "flex", gap: 10 }}>
            <button style={btnBack} onClick={() => setFormStep(2)}>Back</button>
            <button
              style={{ flex: 2, background: "linear-gradient(135deg,#10B981,#059669)", color: "#fff", border: "none", borderRadius: 8, padding: "12px", fontWeight: 700, fontSize: 14, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, boxShadow: "0 4px 20px #10b98150" }}
              onClick={() => { if (validateStep3()) onAnalyze(); }}
            >
              <Zap size={15} /> Analyze Now
            </button>
          </div>
        </>
      )}
    </GlowCard>
  );
}