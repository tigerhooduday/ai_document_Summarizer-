import React, { useState } from "react";
import UploadForm from "./components/UploadForm";
import SummaryResult from "./components/SummaryResult";
import { summarize } from "./services/api";

// Decorative hero image (local uploaded screenshot)
// const heroImageUrl = "/src/assests/img.jpg";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [summaryData, setSummaryData] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit({ text, file, max_tokens, style }) {
    setLoading(true);
    setSummaryData(null);
    setError(null);

    try {
      const res = await summarize({ text, file, style, max_tokens });
      setSummaryData({
        summary: res.summary,
        style: res.style,
        provider: res.provider || "unknown",
      });
    } catch (err) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="hero light">
        <div className="hero-inner">
          <div className="hero-text">
            <h1>Document Summarizer</h1>
            <p className="lead">
              Paste text or upload PDFs, DOCX, HTML, RTF, Markdown or plain text. Choose a style and receive a clean summary.
            </p>
          </div>

          <div className="hero-image" aria-hidden>
            {/* <img src={heroImageUrl} alt="Decorative" /> */}
          </div>
        </div>
      </header>

      <main className="container">
        <UploadForm onSubmit={handleSubmit} loading={loading} />

        <div className="result-wrapper">
          {loading && (
            <div className="loading-card card glass">
              <div className="spinner" />
              <div>Generating summary…</div>
            </div>
          )}

          {error && (
            <div className="error-card card glass">
              <strong>Error:</strong> {error}
            </div>
          )}

          {summaryData && (
            <SummaryResult
              summary={summaryData.summary}
              style={summaryData.style}
              provider={summaryData.provider}
            />
          )}
        </div>
      </main>

      <footer className="footer subtle">
        <div />
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Light, glassy & interactive — modern UI</div>
      </footer>
    </div>
  );
}
