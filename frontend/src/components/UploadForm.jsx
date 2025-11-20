import React, { useState, useRef } from "react";

export default function UploadForm({ onSubmit, loading }) {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [style, setStyle] = useState("brief");
  const [maxTokens, setMaxTokens] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef();

  const accepted = [
    ".txt", ".md", ".markdown", ".pdf", ".docx", ".doc", ".html", ".htm", ".rtf",
  ].join(",");

  function handleFileChange(e) {
    const f = e.target.files?.[0] || null;
    setFile(f);
    if (f) setText("");
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0] || null;
    setFile(f);
    if (f) setText("");
  }

  function openFileDialog() {
    inputRef.current?.click();
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!text && !file) {
      alert("Please paste text or upload a file.");
      return;
    }
    onSubmit({
      text: text || null,
      file,
      style,
      max_tokens: maxTokens ? Number(maxTokens) : undefined,
    });
  }

  function handleClear() {
    setText("");
    setFile(null);
    setMaxTokens("");
  }

  return (
    <form className="card glass" onSubmit={handleSubmit}>
      <div className="upload-grid">
        {/* LEFT SIDE — TEXT */}
        <div>
          <label className="label">Paste text</label>
          <textarea
            placeholder="Paste long text here (or drop/upload a file on the right)..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
          />

          <div className="helper-row">
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              Max tokens
              <input
                type="number"
                placeholder="optional"
                value={maxTokens}
                onChange={(e) => setMaxTokens(e.target.value)}
                style={{ width: 120 }}
                min={10}
                disabled={loading}
              />
            </label>

            <div className="tip">Upload PDFs, DOCX, HTML & more</div>
          </div>
        </div>

        {/* RIGHT SIDE — FILE + STYLE */}
        <div className="controls">
          <label className="label">Upload / Drop file</label>

          <div
            className={`dropzone ${dragOver ? "dragover" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={openFileDialog}
            role="button"
            tabIndex={0}
          >
            <input
              ref={inputRef}
              type="file"
              accept={accepted}
              onChange={handleFileChange}
              style={{ display: "none" }}
            />

            <div className="dz-title">{file ? "File ready" : "Drop file or click to upload"}</div>
            <div className="file-info">
              {file ? `${file.name} · ${Math.round(file.size / 1024)} KB` : "Supported: PDF, DOCX, HTML, RTF, TXT"}
            </div>
          </div>

          <label className="label">Style</label>
          <select value={style} onChange={(e) => setStyle(e.target.value)} disabled={loading}>
            <option value="brief">Brief (2–4 sentences)</option>
            <option value="detailed">Detailed</option>
            <option value="bullets">Bullet points</option>
          </select>
        </div>
      </div>

      {/* NEW BOTTOM BUTTON BAR */}
      <div className="bottom-actions">
        <button className="big-btn" type="submit" disabled={loading}>
          {loading ? "Summarizing…" : "Summarize"}
        </button>

        <button type="button" className="big-btn clear-btn" onClick={handleClear} disabled={loading}>
          Clear
        </button>
      </div>
    </form>
  );
}
