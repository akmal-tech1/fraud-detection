// Honest placeholder for pages that are built in a later project phase.
// It says openly that the feature is not implemented yet, instead of
// simulating a finished page with fake data.
export default function PlaceholderPage({ title, phase }) {
  return (
    <div className="page">
      <h2>{title}</h2>
      <div className="card">
        <p>
          This page is built in <strong>Phase {phase}</strong> of the project
          plan. The navigation skeleton is being tested first, so this
          placeholder is intentional.
        </p>
      </div>
    </div>
  );
}
