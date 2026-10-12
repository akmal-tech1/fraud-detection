import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchModelMetrics, fetchModelStatus } from "../services/api";

const MODEL_LABELS = {
  random_forest: "Random Forest",
  xgboost: "XGBoost",
  ensemble: "Ensemble",
};
const COMPARISON_METRICS = [
  { key: "precision", label: "Precision", color: "#0e7c86" },
  { key: "recall", label: "Recall", color: "#2e7d32" },
  { key: "f1", label: "F1 score", color: "#6a1b9a" },
];
const SUMMARY_METRICS = [
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1", label: "F1 score" },
  { key: "roc_auc", label: "ROC-AUC" },
  { key: "average_precision", label: "Average precision" },
];
const ARTIFACT_LABELS = {
  preprocessor: "Fitted preprocessor",
  random_forest: "Random Forest model",
  xgboost: "XGBoost model",
};

function formatPercent(value) {
  return `${(value * 100).toFixed(2)}%`;
}

function formatDate(value) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function metricRows(metrics) {
  return Object.entries(MODEL_LABELS)
    .filter(([key]) => metrics.models?.[key])
    .map(([key, label]) => ({ key, label, ...metrics.models[key] }));
}

export default function ModelPerformancePage() {
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [retryKey, setRetryKey] = useState(0);

  function retryLoad() {
    setLoading(true);
    setError("");
    setRetryKey((value) => value + 1);
  }

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([fetchModelStatus(), fetchModelMetrics()]).then(
      ([statusResult, metricsResult]) => {
        if (cancelled) return;
        const messages = [];
        if (statusResult.status === "fulfilled") {
          setStatus(statusResult.value);
        } else {
          setStatus(null);
          messages.push(`Model status: ${statusResult.reason.message}`);
        }
        if (metricsResult.status === "fulfilled") {
          setMetrics(metricsResult.value);
        } else {
          setMetrics(null);
          messages.push(`Evaluation metrics: ${metricsResult.reason.message}`);
        }
        setError(messages.join(" "));
        setLoading(false);
      }
    );

    return () => {
      cancelled = true;
    };
  }, [retryKey]);

  const models = metrics ? metricRows(metrics) : [];
  const chartData = models.map((model) => ({
    name: model.label,
    precision: model.precision,
    recall: model.recall,
    f1: model.f1,
  }));
  const ensemble = metrics?.models?.ensemble;
  const confusion = ensemble?.confusion_matrix;
  const availableArtifacts = status
    ? Object.entries(ARTIFACT_LABELS).filter(
        ([key]) => status.artifacts?.[key]
      ).length
    : 0;

  return (
    <div className="page">
      <div className="model-page-heading">
        <div>
          <h2>Model Performance</h2>
          <p className="muted">
            Evaluation results from the trained fraud-risk models.
          </p>
        </div>
        <button
          className="button-secondary"
          type="button"
          disabled={loading}
          onClick={retryLoad}
        >
          {loading ? "Loading…" : "Refresh"}
        </button>
      </div>

      <div className="model-demo-warning" role="note">
        <strong>Synthetic demo evaluation.</strong> These results use generated
        demonstration data and are not evidence of real-world effectiveness.
        Do not use this model to make decisions about real transactions.
      </div>

      {error && (
        <div className="card model-error">
          <p className="error-text">{error}</p>
          <button
            className="button-primary"
            type="button"
            onClick={retryLoad}
          >
            Try again
          </button>
        </div>
      )}

      {loading && !metrics ? (
        <div className="card model-message" role="status">
          Loading model evaluation…
        </div>
      ) : !metrics ? (
        <div className="card model-message">
          <h3>Evaluation metrics unavailable</h3>
          <p className="muted">
            No evaluation data is shown until the backend provides its
            measured training metrics.
          </p>
        </div>
      ) : (
        <>
          <div className="model-overview-grid">
            <section className="card model-overview-card">
              <h3>Training run</h3>
              <dl className="model-facts">
                <div>
                  <dt>Model version</dt>
                  <dd>{metrics.model_version || "Not recorded"}</dd>
                </div>
                <div>
                  <dt>Trained</dt>
                  <dd>{formatDate(metrics.training_date)}</dd>
                </div>
                <div>
                  <dt>Dataset</dt>
                  <dd>
                    {metrics.dataset?.synthetic ? "Synthetic demo" : "Dataset"}
                    {metrics.dataset?.rows != null
                      ? ` · ${metrics.dataset.rows.toLocaleString()} rows`
                      : ""}
                  </dd>
                </div>
                <div>
                  <dt>Held-out test rows</dt>
                  <dd>
                    {metrics.dataset?.test_rows == null
                      ? "Not recorded"
                      : metrics.dataset.test_rows.toLocaleString()}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="card model-overview-card">
              <h3>Model availability</h3>
              {status ? (
                <>
                  <p>
                    Status:{" "}
                    <span
                      className={`badge ${
                        status.available ? "badge-connected" : "badge-degraded"
                      }`}
                    >
                      {status.available ? "AVAILABLE" : "INCOMPLETE"}
                    </span>
                  </p>
                  <p className="muted">
                    {availableArtifacts} of {Object.keys(ARTIFACT_LABELS).length}{" "}
                    prediction artifacts found.
                  </p>
                  <ul className="artifact-list">
                    {Object.entries(ARTIFACT_LABELS).map(([key, label]) => (
                      <li key={key}>
                        <span>{label}</span>
                        <strong>
                          {status.artifacts?.[key] ? "Available" : "Missing"}
                        </strong>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="muted">
                  Model availability could not be loaded.
                </p>
              )}
            </section>
          </div>

          <section className="card model-metrics-card">
            <div className="model-section-heading">
              <div>
                <h3>Held-out test metrics</h3>
                <p className="muted">
                  Precision and recall are emphasized because fraud cases are
                  rare and accuracy alone can be misleading.
                </p>
              </div>
            </div>
            <div className="table-scroll">
              <table className="model-metrics-table">
                <thead>
                  <tr>
                    <th scope="col">Model</th>
                    {SUMMARY_METRICS.filter(({ key }) =>
                      models.some((model) => model[key] != null)
                    ).map(({ key, label }) => (
                      <th scope="col" key={key}>{label}</th>
                    ))}
                    <th scope="col">Accuracy</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((model) => (
                    <tr key={model.key}>
                      <th scope="row">{model.label}</th>
                      {SUMMARY_METRICS.filter(({ key }) =>
                        models.some((entry) => entry[key] != null)
                      ).map(({ key }) => (
                        <td key={key}>
                          {model[key] == null ? "—" : formatPercent(model[key])}
                        </td>
                      ))}
                      <td>
                        {model.accuracy == null
                          ? "—"
                          : formatPercent(model.accuracy)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {chartData.length > 0 && (
              <div className="model-chart" aria-label="Model precision, recall, and F1 comparison">
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={chartData} margin={{ top: 12, right: 16, left: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} />
                    <Tooltip formatter={(value) => formatPercent(Number(value))} />
                    <Legend />
                    {COMPARISON_METRICS.map((metric) => (
                      <Bar
                        key={metric.key}
                        dataKey={metric.key}
                        name={metric.label}
                        fill={metric.color}
                        radius={[4, 4, 0, 0]}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </section>

          <div className="model-lower-grid">
            {Array.isArray(confusion) && confusion.length === 2 && (
              <section className="card model-lower-card">
                <h3>Ensemble confusion matrix</h3>
                <p className="muted">
                  Counts on the held-out test set. Fraud is the positive class.
                </p>
                <div className="table-scroll">
                  <table className="confusion-table">
                    <caption>Actual class by predicted class</caption>
                    <thead>
                      <tr>
                        <th scope="col">Actual ↓ / Predicted →</th>
                        <th scope="col">Legitimate</th>
                        <th scope="col">Fraud</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <th scope="row">Legitimate</th>
                        <td>{confusion[0][0]}</td>
                        <td>{confusion[0][1]}</td>
                      </tr>
                      <tr>
                        <th scope="row">Fraud</th>
                        <td>{confusion[1][0]}</td>
                        <td>{confusion[1][1]}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p className="muted">
                  False positives: {confusion[0][1]} · False negatives: {confusion[1][0]}
                </p>
              </section>
            )}

            <section className="card model-lower-card">
              <h3>Evaluation notes</h3>
              {Array.isArray(metrics.notes) && metrics.notes.length > 0 ? (
                <ul className="model-notes">
                  {metrics.notes.map((note) => <li key={note}>{note}</li>)}
                </ul>
              ) : (
                <p className="muted">No evaluation notes were provided.</p>
              )}
              {metrics.ensemble_weights && (
                <p className="muted model-weights">
                  Ensemble weights:{" "}
                  {Object.entries(metrics.ensemble_weights)
                    .map(([name, weight]) => `${MODEL_LABELS[name] || name} ${formatPercent(weight)}`)
                    .join(" · ")}
                  . Initial settings only; not proven optimal.
                </p>
              )}
              {metrics.prediction_threshold != null && (
                <p className="muted">
                  Fraud-class probability threshold:{" "}
                  {formatPercent(metrics.prediction_threshold)}
                </p>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
