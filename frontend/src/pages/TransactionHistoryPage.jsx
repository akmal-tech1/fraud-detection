import { useEffect, useState } from "react";
import { fetchTransaction, fetchTransactions } from "../services/api";

const PAGE_SIZE = 20;
const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const FEATURE_LABELS = {
  amount: "Amount",
  category: "Merchant category",
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

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function formatFeature(key, value) {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (key === "day_of_week" && Number.isInteger(value)) {
    return DAY_NAMES[value] || String(value);
  }
  if (key === "amount" && Number.isFinite(Number(value))) {
    return Number(value).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  return String(value ?? "—");
}

export default function TransactionHistoryPage() {
  const [page, setPage] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadPage() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchTransactions({
          skip: page * PAGE_SIZE,
          limit: PAGE_SIZE,
        });
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadPage();
    return () => {
      cancelled = true;
    };
  }, [page, refreshKey]);

  useEffect(() => {
    if (selectedId === null) return undefined;
    let cancelled = false;

    async function loadDetail() {
      setDetail(null);
      setDetailError("");
      setDetailLoading(true);
      try {
        const data = await fetchTransaction(selectedId);
        if (!cancelled) setDetail(data);
      } catch (err) {
        if (!cancelled) setDetailError(err.message);
      } finally {
        if (!cancelled) setDetailLoading(false);
      }
    }

    loadDetail();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const firstItem = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const lastItem = Math.min((page + 1) * PAGE_SIZE, total);

  return (
    <div className="page">
      <div className="history-heading">
        <div>
          <h2>Transaction History</h2>
          <p className="muted">
            Browse saved transaction analyses and inspect their recorded features.
          </p>
        </div>
        <button
          className="button-secondary"
          type="button"
          onClick={() => setRefreshKey((value) => value + 1)}
          disabled={loading}
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="card history-message">
          <p className="error-text">{error}</p>
          <button
            className="button-primary"
            type="button"
            onClick={() => setRefreshKey((value) => value + 1)}
          >
            Try again
          </button>
        </div>
      )}

      <section className="card history-card" aria-label="Transaction history">
        <div className="history-table-header">
          <h3>Saved transactions</h3>
          <span className="muted">
            {loading ? "Loading…" : `${total.toLocaleString()} total`}
          </span>
        </div>

        {loading && items.length === 0 ? (
          <p className="muted" role="status">Loading transaction history…</p>
        ) : !loading && !error && items.length === 0 ? (
          <div className="history-empty">
            <h4>No transactions yet</h4>
            <p className="muted">
              Transactions appear here after you analyze one or run a batch.
            </p>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="history-table">
              <thead>
                <tr>
                  <th scope="col">Reference</th>
                  <th scope="col">Transaction date</th>
                  <th scope="col">Amount</th>
                  <th scope="col">Category</th>
                  <th scope="col">Risk score</th>
                  <th scope="col">Prediction</th>
                  <th scope="col"><span className="sr-only">Details</span></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const preview = item.features_preview || {};
                  const prediction = item.prediction;
                  return (
                    <tr key={item.id}>
                      <td className="history-reference">{item.transaction_reference}</td>
                      <td>{formatDate(item.transaction_timestamp)}</td>
                      <td>
                        {preview.amount === undefined
                          ? "—"
                          : formatFeature("amount", preview.amount)}
                      </td>
                      <td>{preview.category ?? "—"}</td>
                      <td>
                        {prediction ? (
                          <span className={`risk-badge risk-badge-${prediction.risk_category}`}>
                            {prediction.risk_score} · {prediction.risk_category}
                          </span>
                        ) : "—"}
                      </td>
                      <td>{prediction?.predicted_class ?? "Not analyzed"}</td>
                      <td>
                        <button
                          className="history-detail-button"
                          type="button"
                          onClick={() => setSelectedId(item.id)}
                          aria-label={`View details for ${item.transaction_reference}`}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <div className="history-pagination">
          <span className="muted">
            Showing {firstItem}–{lastItem} of {total.toLocaleString()}
          </span>
          <div className="history-page-controls">
            <button
              className="button-secondary"
              type="button"
              disabled={page === 0 || loading}
              onClick={() => setPage((value) => Math.max(0, value - 1))}
            >
              Previous
            </button>
            <span className="muted">Page {page + 1} of {pageCount}</span>
            <button
              className="button-secondary"
              type="button"
              disabled={page + 1 >= pageCount || loading}
              onClick={() => setPage((value) => value + 1)}
            >
              Next
            </button>
          </div>
        </div>
      </section>

      {selectedId !== null && (
        <section className="card history-detail-card" aria-label="Transaction details">
          <div className="history-table-header">
            <h3>Transaction details</h3>
            <button
              className="button-secondary"
              type="button"
              onClick={() => setSelectedId(null)}
            >
              Close
            </button>
          </div>
          {detailLoading && <p className="muted" role="status">Loading details…</p>}
          {detailError && <p className="error-text">{detailError}</p>}
          {detail && (
            <>
              <dl className="history-detail-meta">
                <div>
                  <dt>Reference</dt>
                  <dd>{detail.transaction_reference}</dd>
                </div>
                <div>
                  <dt>Transaction date</dt>
                  <dd>{formatDate(detail.transaction_timestamp)}</dd>
                </div>
              </dl>
              <h4>Recorded features</h4>
              <table className="details-table">
                <tbody>
                  {Object.entries(detail.features || {}).map(([key, value]) => (
                    <tr key={key}>
                      <th scope="row">{FEATURE_LABELS[key] || key}</th>
                      <td>{formatFeature(key, value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <h4>Latest prediction</h4>
              {detail.prediction ? (
                <dl className="history-detail-meta">
                  <div>
                    <dt>Risk</dt>
                    <dd>
                      <span className={`risk-badge risk-badge-${detail.prediction.risk_category}`}>
                        {detail.prediction.risk_score} · {detail.prediction.risk_category}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>Predicted class</dt>
                    <dd>{detail.prediction.predicted_class}</dd>
                  </div>
                  <div>
                    <dt>Fraud probability</dt>
                    <dd>{(detail.prediction.fraud_probability * 100).toFixed(2)}%</dd>
                  </div>
                  <div>
                    <dt>Model version</dt>
                    <dd>{detail.prediction.model_version}</dd>
                  </div>
                  <div>
                    <dt>Analyzed</dt>
                    <dd>{formatDate(detail.prediction.created_at)}</dd>
                  </div>
                </dl>
              ) : (
                <p className="muted">No prediction is recorded for this transaction.</p>
              )}
            </>
          )}
        </section>
      )}
    </div>
  );
}
