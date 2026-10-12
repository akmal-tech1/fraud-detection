import { useEffect, useState } from "react";
import {
  API_BASE_URL,
  fetchDashboardSummary,
  fetchHealth,
  fetchRoot,
} from "../services/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Link } from "react-router-dom";

const categories = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

const colorByRisk = {
  LOW: "#00C851",
  MEDIUM: "#7ED321",
  HIGH: "#FFC833",
  CRITICAL: "#FF5B5B",
};

export default function Dashboard() {
  const [apiStatus, setApiStatus] = useState("checking");
  const [apiInfo, setApiInfo] = useState(null);
  const [error, setError] = useState("");

  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [health, info] = await Promise.all([fetchHealth(), fetchRoot()]);
        if (cancelled) return;
        setApiStatus(health.status === "ok" ? "connected" : "degraded");
        setApiInfo(info);
        setError("");

        try {
          setSummary(await fetchDashboardSummary());
        } catch (e) {
          if (!cancelled) {
            setError(`Dashboard data could not be loaded: ${e.message}`);
          }
        }

        setLoadingSummary(false);
      } catch (err) {
        if (cancelled) return;
        setApiStatus("error");
        setError(
          `${err.message} — is the FastAPI server running? ` +
            `Start it with: cd backend && uvicorn main:app --reload`
        );
        setLoadingSummary(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loadingSummary && !apiStatus) {
    return (
      <div className="page">
        <h2>Dashboard</h2>
        <p className="muted">Loading dashboard data…</p>
      </div>
    );
  }

  // If we have no summary data yet, render a graceful placeholder.
  if (!summary) {
    return (
      <div className="page">
        <h2>Dashboard</h2>
        <div className="card">
          <h3>Backend connection</h3>
          <p>
            Status:{" "}
            <span className={`badge badge-${apiStatus}`}>
              {apiStatus.toUpperCase()}
            </span>
          </p>
          {apiInfo && (
            <p className="muted">
              {apiInfo.name} v{apiInfo.version} — interactive API docs at{" "}
              <a href={`${API_BASE_URL}${apiInfo.docs}`} target="_blank" rel="noreferrer">
                {apiInfo.docs}
              </a>
            </p>
          )}
          {error && <p className="error-text">{error}</p>}
          <div className="mt-4">
            <p className="muted">
              Transaction statistics will appear here once predictions are
              stored in the database. No placeholder numbers are shown by
              design — all values are queried in real time from SQLite.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const {
    total_transactions,
    total_predictions,
    fraud_count,
    legitimate_count,
    risk_distribution,
    score_min,
    score_max,
  } = summary;

  // Build a default-ordered array for the 4 risk categories.
  const data = categories.map((cat) => ({
    name: cat,
    count: risk_distribution[cat] || 0,
    color: colorByRisk[cat],
  }));

  return (
    <div className="page">
      <h2>Dashboard</h2>

      <div className="card">
        <h3>Backend connection</h3>
        <p>
          Status:{" "}
          <span className={`badge badge-${apiStatus}`}>
            {apiStatus.toUpperCase()}
          </span>
        </p>
        {apiInfo && (
          <p className="muted">
            {apiInfo.name} v{apiInfo.version} — interactive API docs at{" "}
            <a href={`${API_BASE_URL}${apiInfo.docs}`} target="_blank" rel="noreferrer">
              {apiInfo.docs}
            </a>
          </p>
        )}
        {error && <p className="error-text">{error}</p>}
      </div>

      {/* Summary metrics row */}
      <div className="mt-4">
        <dl className="result-stats">
          <div>
            <dt>Total transactions</dt>
            <dd>{total_transactions}</dd>
          </div>
          <div>
            <dt>Total predictions</dt>
            <dd>{total_predictions}</dd>
          </div>
          <div>
            <dt>Fraud detected</dt>
            <dd>{fraud_count}</dd>
          </div>
          <div>
            <dt>Legitimate</dt>
            <dd>{legitimate_count}</dd>
          </div>
        </dl>
      </div>

      {/* Risk distribution chart */}
      <div className="mt-6">
        <h3>Risk category distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {data.map((item, index) => (
              <Bar
                key={item.name}
                dataKey="count"
                name={item.name}
                fill={item.color}
                barSize={12}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
        <p className="muted">
          {total_predictions} predictions analyzed • {" "}
          {fraud_count} potentially fraudulent
        </p>
      </div>

      {/* Score range banner */}
      <div className="mt-4">
        <p className="muted">
          Risk score range:{" "}
          <strong>{score_min}</strong>{" — "}{" "}
          <strong>{score_max}</strong>{" out of 100"}
        </p>
      </div>
    </div>
  );
}