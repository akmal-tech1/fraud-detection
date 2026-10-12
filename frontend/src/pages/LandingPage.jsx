import { Link } from "react-router-dom";

const appPages = [
  "Live dashboard",
  "Transaction analysis",
  "Batch CSV analysis",
  "Transaction history",
  "Model performance",
  "About & documentation",
  "Sign in",
];

export default function LandingPage() {
  return (
    <main className="landing-page">
      <div className="landing-orb landing-orb-one" aria-hidden="true" />
      <div className="landing-orb landing-orb-two" aria-hidden="true" />

      <header className="landing-header">
        <Link
          className="landing-brand"
          to="/"
          aria-label="Fraud Risk Detection home"
        >
          <span className="landing-brand-mark" aria-hidden="true">
            FR
          </span>
          <span>Fraud Risk Detection</span>
        </Link>
        <span className="landing-demo-label">EDUCATIONAL DEMO</span>
      </header>

      <div className="landing-main">
        <section className="landing-hero" aria-labelledby="landing-title">
          <p className="landing-eyebrow">
            <span className="landing-status-dot" aria-hidden="true" />
            FINANCIAL FRAUD RISK DETECTION
          </p>
          <h1 id="landing-title">
            See risk
            <span> more clearly.</span>
          </h1>
          <p className="landing-description">
            Explore a demonstration risk analysis workspace powered by a
            machine learning ensemble and synthetic transaction data.
          </p>
          <Link className="landing-enter-button" to="/dashboard">
            Enter the application
            <span className="landing-enter-arrow" aria-hidden="true">→</span>
          </Link>
          <p className="landing-enter-hint">
            Your analysis workspace is one click away.
          </p>
        </section>

        <aside className="landing-visual" aria-label="Risk score band guide">
          <div className="landing-visual-glow" aria-hidden="true" />
          <div className="landing-orbit landing-orbit-outer" aria-hidden="true" />
          <div className="landing-orbit landing-orbit-inner" aria-hidden="true" />
          <div className="risk-guide-card">
            <div className="risk-guide-heading">
              <div>
                <span className="risk-guide-kicker">QUICK REFERENCE</span>
                <h2>Risk score bands</h2>
              </div>
              <span className="risk-guide-scale">0—100</span>
            </div>
            <div className="risk-guide-bar" aria-hidden="true">
              <span className="risk-guide-segment risk-guide-low" />
              <span className="risk-guide-segment risk-guide-medium" />
              <span className="risk-guide-segment risk-guide-high" />
              <span className="risk-guide-segment risk-guide-critical" />
            </div>
            <ul className="risk-guide-list">
              <li>
                <span><i className="risk-guide-dot risk-guide-low" />Low</span>
                <strong>0–39</strong>
              </li>
              <li>
                <span><i className="risk-guide-dot risk-guide-medium" />Medium</span>
                <strong>40–59</strong>
              </li>
              <li>
                <span><i className="risk-guide-dot risk-guide-high" />High</span>
                <strong>60–79</strong>
              </li>
              <li>
                <span><i className="risk-guide-dot risk-guide-critical" />Critical</span>
                <strong>80–100</strong>
              </li>
            </ul>
            <p className="risk-guide-note">
              A guide to the demo’s score categories—not a live prediction.
            </p>
          </div>
        </aside>
      </div>

      <nav className="landing-pages" aria-label="Pages available after entering">
        {appPages.map((page, index) => (
          <span className="landing-page-chip" key={page}>
            <span className="landing-chip-number">0{index + 1}</span>
            {page}
          </span>
        ))}
      </nav>

      <footer className="landing-footer">
        <span>Built for learning and demonstration</span>
        <span className="landing-safety-note">
          Not connected to real banking or payment systems.
        </span>
      </footer>
    </main>
  );
}
