import { useRef, useState } from "react";
import {
  downloadSampleDataset,
  runBatchAnalysis,
  uploadDataset,
} from "../services/api";

const CATEGORY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export default function BatchPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  // null = idle, otherwise which action is in progress.
  const [busy, setBusy] = useState(null);
  const fileInputRef = useRef(null);

  function handleFileChange(event) {
    const selected = event.target.files?.[0] || null;
    setFile(selected);
    setPreview(null);
    setResults(null);
    setError("");
  }

  async function handleUpload(event) {
    event.preventDefault();
    if (!file) {
      return;
    }
    setBusy("uploading");
    setError("");
    try {
      const data = await uploadDataset(file);
      setPreview(data);
    } catch (err) {
      setError(err.message);
      setPreview(null);
    } finally {
      setBusy(null);
    }
  }

  async function handleRunBatch(event) {
    if (event) {
      event.preventDefault();
    }
    if (!file) {
      return;
    }
    setBusy("analyzing");
    setError("");
    try {
      const data = await runBatchAnalysis(file);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  }

  function handleReset() {
    setFile(null);
    setPreview(null);
    setResults(null);
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  // Build a CSV from the batch results and trigger a
  // client-side download (no server-side temp files).
  function downloadResults() {
    if (!results) {
      return;
    }
    const header =
      "transaction_reference,fraud_probability,risk_score,risk_category,predicted_class";
    const lines = results.predictions.map((item) =>
      [
        item.transaction_reference,
        item.fraud_probability,
        item.risk_score,
        item.risk_category,
        item.predicted_class,
      ].join(",")
    );
    const blob = new Blob([[header].concat(lines).join("\n")], {
      type: "text/csv",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "batch_predictions.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function handleDownloadSample() {
    setError("");
    try {
      const blob = await downloadSampleDataset();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "synthetic_transactions.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  }

  const highRiskCount = results
    ? (results.category_counts.HIGH || 0) +
      (results.category_counts.CRITICAL || 0)
    : 0;

  return (
    <div className="page">
      <h2>Batch Analysis</h2>
      <p className="muted">
        Upload a CSV of transactions (same columns as the
        dataset schema). Valid rows are analyzed with the
        ensemble; invalid rows are reported with reasons.
        Maximum 10 MB and 10,000 rows.
      </p>

      <div className="card">
        <h3>Upload a CSV dataset</h3>
        <form onSubmit={handleUpload}>
          <div className="form-row">
            <label htmlFor="csv-file">CSV file</label>
            <input
              id="csv-file"
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
            />
          </div>
          <div className="form-actions">
            <button
              type="submit"
              className="button-primary"
              disabled={!file || busy === "uploading"}
            >
              {busy === "uploading" ? "Validating…" : "Validate & preview"}
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={handleDownloadSample}
            >
              Download sample dataset (synthetic)
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="card">
          <h3>Batch analysis failed</h3>
          <p className="error-text">{error}</p>
        </div>
      )}

      {preview && !results && (
        <div className="card">
          <h3>Dataset preview: {preview.filename}</h3>
          <dl className="result-stats">
            <div>
              <dt>Size</dt>
              <dd>
                {(preview.size_bytes / 1024).toFixed(1)} KB
              </dd>
            </div>
            <div>
              <dt>Rows</dt>
              <dd>{preview.row_count}</dd>
            </div>
            <div>
              <dt>Columns</dt>
              <dd>{preview.column_count}</dd>
            </div>
            <div>
              <dt>Valid rows</dt>
              <dd>{preview.valid_rows}</dd>
            </div>
            <div>
              <dt>Invalid rows</dt>
              <dd>{preview.invalid_rows}</dd>
            </div>
          </dl>

          <h4>Columns</h4>
          <p className="muted">{preview.columns.join(", ")}</p>

          <h4>First 5 rows</h4>
          <div className="table-scroll">
            <table className="details-table">
              <thead>
                <tr>
                  {preview.columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.sample_rows.map((row, index) => (
                  <tr key={index}>
                    {preview.columns.map((column) => (
                      <td key={column}>
                        {row[column] === null ||
                        row[column] === undefined
                          ? ""
                          : String(row[column])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="button-primary"
              onClick={handleRunBatch}
              disabled={busy === "analyzing"}
            >
              {busy === "analyzing"
                ? `Analyzing ${preview.valid_rows} transactions…`
                : "Run batch analysis"}
            </button>
          </div>
        </div>
      )}

      {results && (
        <>
          <div className="card">
            <h3>Batch analysis complete</h3>
            <dl className="result-stats">
              <div>
                <dt>Analyzed</dt>
                <dd>{results.valid_rows}</dd>
              </div>
              <div>
                <dt>Invalid (skipped)</dt>
                <dd>{results.invalid_rows}</dd>
              </div>
              <div>
                <dt>References regenerated</dt>
                <dd>{results.references_regenerated}</dd>
              </div>
            </dl>
            <p>
              Potentially fraudulent (HIGH + CRITICAL):{" "}
              <strong>{highRiskCount}</strong>
            </p>
            <div className="form-actions">
              <button
                type="button"
                className="button-primary"
                onClick={downloadResults}
              >
                Download predictions CSV
              </button>
              <button
                type="button"
                className="button-secondary"
                onClick={handleReset}
              >
                Analyze another file
              </button>
            </div>
            <p className="disclaimer">{results.disclaimer}</p>
          </div>

          <div className="card">
            <h3>Risk category distribution</h3>
            {CATEGORY_ORDER.map((category) => {
              const count = results.category_counts[category] || 0;
              const percent = results.valid_rows
                ? (count / results.valid_rows) * 100
                : 0;
              return (
                <div key={category} className="dist-row">
                  <span className="dist-label">{category}</span>
                  <div className="dist-bar-track">
                    <div
                      className={`dist-bar-fill dist-${category.toLowerCase()}`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                  <span className="dist-count">{count}</span>
                </div>
              );
            })}
            <p className="muted">
              {results.valid_rows} transactions analyzed.
            </p>
          </div>

          <div className="card">
            <h3>Analyzed transactions</h3>
            <div className="table-scroll">
              <table className="details-table">
                <thead>
                  <tr>
                    <th>Reference</th>
                    <th>Risk score</th>
                    <th>Category</th>
                    <th>Predicted class</th>
                    <th>Fraud probability</th>
                  </tr>
                </thead>
                <tbody>
                  {results.predictions.slice(0, 100).map((item) => (
                    <tr key={item.transaction_reference}>
                      <td>{item.transaction_reference}</td>
                      <td>{item.risk_score}</td>
                      <td>
                        <span
                          className={`risk-badge risk-badge-${item.risk_category}`}
                        >
                          {item.risk_category}
                        </span>
                      </td>
                      <td>{item.predicted_class}</td>
                      <td>
                        {(item.fraud_probability * 100).toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {results.predictions.length > 100 && (
              <p className="muted">
                Showing 100 of {results.predictions.length} results.
                Download the CSV for the full list.
              </p>
            )}
          </div>

          {results.invalid_rows > 0 && (
            <div className="card">
              <h3>Invalid rows ({results.invalid_rows})</h3>
              <p className="muted">
                These rows were skipped (not analyzed). Showing
                the first 10:
              </p>
              <ul className="invalid-list">
                {results.invalid.slice(0, 10).map((row) => (
                  <li key={row.row_number}>
                    <strong>Row {row.row_number}:</strong>{" "}
                    {row.errors.join("; ")}
                  </li>
                ))}
              </ul>
              {results.invalid.length > 10 && (
                <p className="muted">
                  …and {results.invalid.length - 10} more invalid
                  rows.
                </p>
              )}
            </div>
          )}
        </>
      )}

      {!preview && !results && !error && (
        <div className="card">
          <h3>How it works</h3>
          <p className="muted">
            1. Upload a CSV and review the preview. 2. Run the
            batch analysis. 3. Download the predictions as CSV.
            Tip: use "Download sample dataset" to get a
            synthetic CSV for testing.
          </p>
        </div>
      )}
    </div>
  );
}
