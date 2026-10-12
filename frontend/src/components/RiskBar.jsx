// Visual risk indicator: a 0-100 bar split into the four
// category segments with a marker at the score.
// Risk is never communicated by color alone - every segment
// and the marker position have text labels (accessibility rule).
export default function RiskBar({ score, category }) {
  const clamped = Math.min(Math.max(score, 0), 100);
  return (
    <div className="risk-bar">
      <div
        className="risk-bar-track"
        role="img"
        aria-label={`Risk score ${score} out of 100, category ${category}`}
      >
        <div className="risk-bar-segments">
          <div className="segment segment-low" style={{ width: "40%" }} />
          <div className="segment segment-medium" style={{ width: "20%" }} />
          <div className="segment segment-high" style={{ width: "20%" }} />
          <div
            className="segment segment-critical"
            style={{ width: "20%" }}
          />
        </div>
        <div className="risk-bar-marker" style={{ left: `${clamped}%` }} />
      </div>
      <div className="risk-bar-labels" aria-hidden="true">
        <span>0 LOW</span>
        <span>40 MEDIUM</span>
        <span>60 HIGH</span>
        <span>80 CRITICAL 100</span>
      </div>
    </div>
  );
}
