import React from "react";

export default function SummaryResult({ summary, style, provider }) {
  // color-code provider badge: stub = orange, others = green
  const isStub = (provider || "").toLowerCase().includes("stub");
  const pillStyle = {
    background: isStub ? "linear-gradient(90deg,#fbbf24,#fb923c)" : "linear-gradient(90deg,#bbf7d0,#86efac)",
    color: isStub ? "#7c2d12" : "#064e3b",
    padding: "6px 10px",
    borderRadius: 999,
    fontSize: 13,
  };

  return (
    <div className="summary-card card">
      <div className="summary-head">
        <h3>Summary ({style})</h3>
        <div style={pillStyle}>{provider}</div>
      </div>
      <div className="summary-body">{summary}</div>
    </div>
  );
}
