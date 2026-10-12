import { Link } from "react-router-dom";
import { API_BASE_URL } from "../services/api";

const endpoints = [
  { method: "GET", path: "/api/health", purpose: "Check that the API is responding." },
  { method: "POST", path: "/api/predict", purpose: "Analyze one transaction." },
  { method: "POST", path: "/api/dataset/upload", purpose: "Validate and preview a CSV file." },
  { method: "POST", path: "/api/predict/batch", purpose: "Analyze valid rows from a CSV file." },
  { method: "GET", path: "/api/dataset/sample", purpose: "Download the synthetic demonstration CSV." },
  { method: "GET", path: "/api/transactions", purpose: "List saved transactions; supports skip and limit." },
  { method: "GET", path: "/api/transactions/{id}", purpose: "View a saved transaction and its latest prediction." },
  { method: "GET", path: "/api/model/status", purpose: "Check model artifact availability." },
  { method: "GET", path: "/api/model/metrics", purpose: "Read measured model evaluation results." },
  { method: "GET", path: "/api/model/dashboard/summary", purpose: "Read live database summary statistics." },
];

const features = [
  {
    title: "Analyze a transaction",
    description:
      "Enter the demo transaction features to receive an estimated fraud probability, risk score, category, and predicted class.",
    to: "/analyze",
    action: "Open analysis",
  },
  {
    title: "Analyze a CSV batch",
    description:
      "Validate a CSV before analysis. Valid rows are processed; invalid rows and their validation reasons are reported.",
    to: "/batch",
    action: "Open batch analysis",
  },
  {
    title: "Review saved transactions",
    description:
      "Browse persisted analyses, page through results, and inspect the recorded feature values and latest prediction.",
    to: "/history",
    action: "Open transaction history",
  },
  {
    title: "Explore model results",
    description:
      "Compare Random Forest, XGBoost, and ensemble evaluation metrics and inspect the ensemble confusion matrix.",
    to: "/model",
    action: "Open model performance",
  },
];

export default function AboutPage() {
  return (
    <div className="page about-page">
      <header className="about-hero">
        <span className="about-eyebrow">PROJECT GUIDE</span>
        <h2>About &amp; Documentation</h2>
        <p>
          A learning project demonstrating how a machine-learning model can
          estimate transaction fraud risk through a web application.
        </p>
        <div className="about-hero-links">
          <a
            className="button-primary about-primary-link"
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noreferrer"
          >
            Open interactive API docs
          </a>
          <a className="about-text-link" href="#api-reference">
            Browse API endpoints
          </a>
        </div>
      </header>

      <section className="about-safety" aria-labelledby="about-safety-title">
        <span className="about-safety-icon" aria-hidden="true">!</span>
        <div>
          <h3 id="about-safety-title">Educational demo only</h3>
          <p>
            This project uses synthetic demonstration data. It is not connected
            to banks or payment systems, does not process real payment
            credentials, and cannot block transactions. Model performance on
            synthetic data does not demonstrate effectiveness on real-world
            transactions. Do not enter personal, financial, or other sensitive
            information.
          </p>
        </div>
      </section>

      <section className="about-section" aria-labelledby="about-features-title">
        <div className="about-section-heading">
          <span className="about-eyebrow">WHAT YOU CAN DO</span>
          <h3 id="about-features-title">Explore the demo</h3>
        </div>
        <div className="about-feature-grid">
          {features.map((feature, index) => (
            <article className="about-feature-card" key={feature.to}>
              <span className="about-feature-number">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h4>{feature.title}</h4>
              <p>{feature.description}</p>
              <Link to={feature.to} className="about-card-link">
                {feature.action} <span aria-hidden="true">→</span>
              </Link>
            </article>
          ))}
        </div>
      </section>

      <div className="about-two-column">
        <section className="about-section about-info-card" aria-labelledby="about-workflow-title">
          <span className="about-eyebrow">HOW IT WORKS</span>
          <h3 id="about-workflow-title">From input to risk estimate</h3>
          <ol className="about-steps">
            <li>
              <strong>Provide demonstration features.</strong>
              <span>Enter a single example or upload a CSV using the model feature schema.</span>
            </li>
            <li>
              <strong>Validate and preprocess.</strong>
              <span>The API validates fields and applies the fitted preprocessing pipeline used in training.</span>
            </li>
            <li>
              <strong>Combine model probabilities.</strong>
              <span>
                The initial ensemble uses fraud-class probabilities:
                65% XGBoost and 35% Random Forest.
              </span>
            </li>
            <li>
              <strong>Review and learn.</strong>
              <span>
                The estimate and disclaimer are returned, and analyses are
                stored in the local SQLite database for the history page.
              </span>
            </li>
          </ol>
        </section>

        <section className="about-section about-info-card" aria-labelledby="about-risk-title">
          <span className="about-eyebrow">INTERPRETING RESULTS</span>
          <h3 id="about-risk-title">Risk score categories</h3>
          <p className="muted">
            The risk score is the ensemble probability converted to a 0–100
            score. The risk band and predicted class are related but distinct.
          </p>
          <ul className="about-risk-list">
            <li><span className="risk-badge risk-badge-LOW">LOW</span><span>0–39</span></li>
            <li><span className="risk-badge risk-badge-MEDIUM">MEDIUM</span><span>40–59</span></li>
            <li><span className="risk-badge risk-badge-HIGH">HIGH</span><span>60–79</span></li>
            <li><span className="risk-badge risk-badge-CRITICAL">CRITICAL</span><span>80–100</span></li>
          </ul>
          <p className="about-threshold-note">
            Binary predicted class uses a separate fraud probability threshold
            of 0.5. A MEDIUM-risk score can therefore have a “legitimate”
            predicted class.
          </p>
        </section>
      </div>

      <section className="about-section about-data-card" aria-labelledby="about-data-title">
        <span className="about-eyebrow">DATA &amp; EVALUATION</span>
        <h3 id="about-data-title">What the model was trained on</h3>
        <div className="about-data-grid">
          <div>
            <strong>Synthetic dataset</strong>
            <p>
              The bundled dataset is generated for this educational demo. It
              contains 6,000 rows with approximately 4% labeled fraud.
            </p>
          </div>
          <div>
            <strong>Held-out test evaluation</strong>
            <p>
              Reported metrics are calculated on a held-out test split. Class
              imbalance handling is applied only during training.
            </p>
          </div>
          <div>
            <strong>Initial ensemble weights</strong>
            <p>
              The 65/35 XGBoost/Random Forest weights are starting settings,
              not proven optimal. They can be tuned using training-only
              validation data.
            </p>
          </div>
        </div>
        <Link to="/model" className="about-card-link">
          View measured model results <span aria-hidden="true">→</span>
        </Link>
      </section>

      <section
        className="about-section about-api-card"
        id="api-reference"
        aria-labelledby="about-api-title"
      >
        <div className="about-section-heading">
          <div>
            <span className="about-eyebrow">DEVELOPER REFERENCE</span>
            <h3 id="about-api-title">API endpoints</h3>
          </div>
          <a
            className="button-secondary"
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noreferrer"
          >
            Interactive docs ↗
          </a>
        </div>
        <div className="table-scroll">
          <table className="about-endpoints-table">
            <thead>
              <tr>
                <th scope="col">Method</th>
                <th scope="col">Endpoint</th>
                <th scope="col">Purpose</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map((endpoint) => (
                <tr key={`${endpoint.method}-${endpoint.path}`}>
                  <td>
                    <span className={`http-method http-method-${endpoint.method.toLowerCase()}`}>
                      {endpoint.method}
                    </span>
                  </td>
                  <td><code>{endpoint.path}</code></td>
                  <td>{endpoint.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <footer className="about-footer">
        <div>
          <span className="about-eyebrow">BUILT FOR LEARNING</span>
          <p>React · Vite · FastAPI · SQLAlchemy · SQLite · scikit-learn · XGBoost</p>
        </div>
        <a
          className="about-text-link"
          href={`${API_BASE_URL}/docs`}
          target="_blank"
          rel="noreferrer"
        >
          API documentation ↗
        </a>
      </footer>
    </div>
  );
}
