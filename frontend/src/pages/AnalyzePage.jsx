import { useState } from "react";
import { predictTransaction } from "../services/api";
import RiskBar from "../components/RiskBar";

// Merchant categories mirror the backend dataset schema
// (backend/ml/generate_synthetic_data.py -> CATEGORIES).
const CATEGORIES = [
  "groceries",
  "electronics",
  "dining",
  "travel",
  "entertainment",
  "healthcare",
  "utilities",
  "other",
];

const DAYS_OF_WEEK = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
];

const DAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

// Human-readable labels for the feature echo in the result.
const FEATURE_LABELS = {
  amount: "Amount",
  category: "Category",
  transaction_hour: "Hour of day",
  day_of_week: "Day of week",
  merchant_risk_score: "Merchant risk score",
  distance_from_home: "Distance from home (km)",
  is_foreign: "Foreign transaction",
  is_card_present: "Card present",
  previous_transactions_today: "Transactions earlier today",
  account_age_days: "Account age (days)",
  failed_attempts_24h: "Failed attempts (24 h)",
};

// Fills the form with a deliberately high-risk example so a
// demo can show a CRITICAL result immediately.
const HIGH_RISK_EXAMPLE = {
  transaction_reference: "",
  amount: "250",
  category: "electronics",
  transaction_hour: "2",
  day_of_week: "1",
  merchant_risk_score: "80",
  distance_from_home: "45.5",
  is_foreign: true,
  is_card_present: false,
  previous_transactions_today: "3",
  account_age_days: "30",
  failed_attempts_24h: "2",
};

const initialForm = {
  transaction_reference: "",
  amount: "",
  category: "groceries",
  transaction_hour: "",
  day_of_week: "0",
  merchant_risk_score: "",
  distance_from_home: "",
  is_foreign: false,
  is_card_present: true,
  previous_transactions_today: "",
  account_age_days: "",
  failed_attempts_24h: "",
};

function formatFeatureValue(key, value) {
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (key === "transaction_hour") {
    return `${String(value).padStart(2, "0")}:00`;
  }
  if (key === "day_of_week") {
    return DAY_NAMES[value] ?? String(value);
  }
  return String(value);
}

export default function AnalyzePage() {
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function handleCheckbox(event) {
    const { name, checked } = event.target;
    setForm((previous) => ({ ...previous, [name]: checked }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setResult(null);

    // Empty optional reference becomes null (backend generates one).
    const payload = {
      transaction_reference: form.transaction_reference.trim() || null,
      amount: Number(form.amount),
      category: form.category,
      transaction_hour: Number(form.transaction_hour),
      day_of_week: Number(form.day_of_week),
      merchant_risk_score: Number(form.merchant_risk_score),
      distance_from_home: Number(form.distance_from_home),
      is_foreign: form.is_foreign,
      is_card_present: form.is_card_present,
      previous_transactions_today: Number(
        form.previous_transactions_today
      ),
      account_age_days: Number(form.account_age_days),
      failed_attempts_24h: Number(form.failed_attempts_24h),
    };

    try {
      const data = await predictTransaction(payload);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h2>Analyze a Transaction</h2>
      <p className="muted">
        Enter the transaction details. The backend applies the same
        preprocessing used during model training, runs the XGBoost +
        Random Forest ensemble, and returns an estimated risk score.
        Fields marked * are required.
      </p>

      <div className="analyze-grid">
        <div className="card form-card">
          <h3>Transaction details</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label htmlFor="transaction_reference">
                Reference (optional)
              </label>
              <input
                id="transaction_reference"
                name="transaction_reference"
                type="text"
                maxLength={64}
                placeholder="Generated if empty"
                value={form.transaction_reference}
                onChange={handleChange}
              />
            </div>

            <div className="form-row">
              <label htmlFor="amount">Amount *</label>
              <input
                id="amount"
                name="amount"
                type="number"
                min="0.01"
                max="1000000"
                step="0.01"
                required
                placeholder="e.g. 149.99"
                value={form.amount}
                onChange={handleChange}
              />
            </div>

            <div className="form-row">
              <label htmlFor="category">Merchant category *</label>
              <select
                id="category"
                name="category"
                required
                value={form.category}
                onChange={handleChange}
              >
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <label htmlFor="transaction_hour">
                Hour of day (0-23) *
              </label>
              <input
                id="transaction_hour"
                name="transaction_hour"
                type="number"
                min="0"
                max="23"
                required
                value={form.transaction_hour}
                onChange={handleChange}
              />
            </div>

            <div className="form-row">
              <label htmlFor="day_of_week">Day of week *</label>
              <select
                id="day_of_week"
                name="day_of_week"
                required
                value={form.day_of_week}
                onChange={handleChange}
              >
                {DAYS_OF_WEEK.map((day) => (
                  <option key={day.value} value={day.value}>
                    {day.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <label htmlFor="merchant_risk_score">
                Merchant risk score (0-100) *
              </label>
              <input
                id="merchant_risk_score"
                name="merchant_risk_score"
                type="number"
                min="0"
                max="100"
                step="0.1"
                required
                value={form.merchant_risk_score}
                onChange={handleChange}
              />
            </div>

            <div className="form-row">
              <label htmlFor="distance_from_home">
                Distance from home (km) *
              </label>
              <input
                id="distance_from_home"
                name="distance_from_home"
                type="number"
                min="0"
                step="0.1"
                required
                value={form.distance_from_home}
                onChange={handleChange}
              />
            </div>

            <div className="form-row checkbox-row">
              <input
                id="is_foreign"
                name="is_foreign"
                type="checkbox"
                checked={form.is_foreign}
                onChange={handleCheckbox}
              />
              <label htmlFor="is_foreign">Foreign transaction</label>
            </div>

            <div className="form-row checkbox-row">
              <input
                id="is_card_present"
                name="is_card_present"
                type="checkbox"
                checked={form.is_card_present}
                onChange={handleCheckbox}
              />
              <label htmlFor="is_card_present">
                Card present (chip/swipe)
              </label>
            </div>

            <div className="form-row">
              <label htmlFor="previous_transactions_today">
                Transactions earlier today *
              </label>
              <input
                id="previous_transactions_today"
                name="previous_transactions_today"
                type="number"
                min="0"
                required
                value={form.previous_transactions_today}
                onChange={handleChange}
              />
            </div>

            <div className="form-row">
              <label htmlFor="account_age_days">Account age (days) *</label>
              <input
                id="account_age_days"
                name="account_age_days"
                type="number"
                min="0"
                required
                value={form.account_age_days}
                onChange={handleChange}
              />
            </div>

            <div className="form-row">
              <label htmlFor="failed_attempts_24h">
                Failed attempts in last 24 h *
              </label>
              <input
                id="failed_attempts_24h"
                name="failed_attempts_24h"
                type="number"
                min="0"
                required
                value={form.failed_attempts_24h}
                onChange={handleChange}
              />
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="button-primary"
                disabled={submitting}
              >
                {submitting ? "Analyzing…" : "Analyze transaction"}
              </button>
              <button
                type="button"
                className="button-secondary"
                onClick={() => setForm(HIGH_RISK_EXAMPLE)}
              >
                Load high-risk example
              </button>
            </div>
          </form>
        </div>

        <div>
          {error && (
            <div className="card">
              <h3>Analysis failed</h3>
              <p className="error-text">{error}</p>
            </div>
          )}

          {result && (
            <div className="card result-card">
              <h3>Analysis result</h3>
              <div className="result-summary">
                <div>
                  <div className="score-label">Risk score</div>
                  <div className="score-display">{result.risk_score}</div>
                  <div className="score-max">out of 100</div>
                </div>
                <span
                  className={`risk-badge risk-badge-${result.risk_category}`}
                >
                  {result.risk_category}
                </span>
              </div>

              <RiskBar
                score={result.risk_score}
                category={result.risk_category}
              />

              <dl className="result-stats">
                <div>
                  <dt>Fraud probability</dt>
                  <dd>{(result.fraud_probability * 100).toFixed(2)}%</dd>
                </div>
                <div>
                  <dt>Predicted class</dt>
                  <dd>{result.predicted_class}</dd>
                </div>
                <div>
                  <dt>Model version</dt>
                  <dd>{result.model_version}</dd>
                </div>
              </dl>

              <h4>Transaction details</h4>
              <table className="details-table">
                <tbody>
                  <tr>
                    <th>Reference</th>
                    <td>{result.transaction_reference}</td>
                  </tr>
                  <tr>
                    <th>Analyzed at</th>
                    <td>
                      {new Date(
                        result.transaction_timestamp
                      ).toLocaleString()}
                    </td>
                  </tr>
                  {Object.entries(result.features).map(([key, value]) => (
                    <tr key={key}>
                      <th>{FEATURE_LABELS[key] || key}</th>
                      <td>{formatFeatureValue(key, value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <p className="disclaimer">{result.disclaimer}</p>
            </div>
          )}

          {!result && !error && (
            <div className="card">
              <h3>Result</h3>
              <p className="muted">
                Submit the form to see the estimated fraud risk for
                this transaction. Tip: use "Load high-risk example"
                to see a CRITICAL result.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
