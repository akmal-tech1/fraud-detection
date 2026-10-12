import { useEffect, useState } from "react";
import {
  clearAuthToken,
  fetchCurrentUser,
  getAuthToken,
  loginUser,
  registerUser,
  setAuthToken,
} from "../services/api";

export default function LoginPage() {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [user, setUser] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const token = getAuthToken();
    if (!token) return undefined;
    let cancelled = false;

    fetchCurrentUser(token)
      .then((profile) => {
        if (!cancelled) setUser(profile);
      })
      .catch(() => {
        if (!cancelled) clearAuthToken();
      });

    return () => {
      cancelled = true;
    };
  }, []);

  function selectMode(nextMode) {
    setMode(nextMode);
    setError("");
    setNotice("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");

    try {
      if (mode === "register") {
        await registerUser({
          username: username.trim(),
          email: email.trim(),
          password,
        });
        setNotice("Account created. Signing you in…");
      }

      const tokenResponse = await loginUser({
        email: email.trim(),
        password,
      });
      setAuthToken(tokenResponse.access_token);
      const profile = await fetchCurrentUser(tokenResponse.access_token);
      setUser(profile);
      setPassword("");
      setNotice(
        mode === "register"
          ? "Your demo account is ready."
          : "You are signed in."
      );
    } catch (err) {
      clearAuthToken();
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function handleSignOut() {
    clearAuthToken();
    setUser(null);
    setPassword("");
    setError("");
    setNotice("You have been signed out.");
  }

  if (user) {
    return (
      <div className="page auth-page">
        <section className="auth-card" aria-labelledby="account-title">
          <div className="auth-brand-mark" aria-hidden="true">FR</div>
          <span className="about-eyebrow">DEMO ACCOUNT</span>
          <h2 id="account-title">You’re signed in</h2>
          <p className="muted">
            Authentication is active for this browser session.
          </p>
          <dl className="auth-profile">
            <div>
              <dt>Username</dt>
              <dd>{user.username}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user.email}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{user.role}</dd>
            </div>
          </dl>
          {notice && <p className="auth-notice" role="status">{notice}</p>}
          <button
            className="button-secondary auth-submit"
            type="button"
            onClick={handleSignOut}
          >
            Sign out
          </button>
          <p className="auth-footnote">
            Signing in does not connect this educational demo to a bank or
            authorize real transactions.
          </p>
        </section>
      </div>
    );
  }

  const isRegistering = mode === "register";

  return (
    <div className="page auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-brand-mark" aria-hidden="true">FR</div>
        <span className="about-eyebrow">FINANCIAL FRAUD RISK DETECTION</span>
        <h2 id="auth-title">
          {isRegistering ? "Create your demo account" : "Welcome back"}
        </h2>
        <p className="muted">
          {isRegistering
            ? "Create an account to sign in to this educational demo."
            : "Sign in with your email and password."}
        </p>

        <div className="auth-tabs" role="tablist" aria-label="Account access">
          <button
            id="login-tab"
            className={`auth-tab${!isRegistering ? " auth-tab-active" : ""}`}
            type="button"
            role="tab"
            aria-selected={!isRegistering}
            aria-controls="auth-form"
            onClick={() => selectMode("login")}
          >
            Sign in
          </button>
          <button
            id="register-tab"
            className={`auth-tab${isRegistering ? " auth-tab-active" : ""}`}
            type="button"
            role="tab"
            aria-selected={isRegistering}
            aria-controls="auth-form"
            onClick={() => selectMode("register")}
          >
            Create account
          </button>
        </div>

        <form id="auth-form" onSubmit={handleSubmit}>
          {isRegistering && (
            <div className="form-row">
              <label htmlFor="auth-username">Username</label>
              <input
                id="auth-username"
                name="username"
                type="text"
                autoComplete="username"
                minLength={3}
                maxLength={50}
                pattern="[A-Za-z0-9_.-]+"
                title="Use 3–50 letters, numbers, dots, underscores, or hyphens."
                required
                value={username}
                onChange={(event) => setUsername(event.target.value)}
              />
              <span className="auth-field-hint">
                3–50 letters, numbers, dots, underscores, or hyphens.
              </span>
            </div>
          )}

          <div className="form-row">
            <label htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              name="email"
              type="email"
              autoComplete="email"
              maxLength={254}
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          <div className="form-row">
            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              name="password"
              type="password"
              autoComplete={isRegistering ? "new-password" : "current-password"}
              minLength={isRegistering ? 8 : undefined}
              maxLength={72}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            {isRegistering && (
              <span className="auth-field-hint">
                At least 8 characters, no more than 72 bytes.
              </span>
            )}
          </div>

          {error && <p className="error-text" role="alert">{error}</p>}
          {notice && <p className="auth-notice" role="status">{notice}</p>}

          <button className="button-primary auth-submit" type="submit" disabled={busy}>
            {busy
              ? isRegistering ? "Creating account…" : "Signing in…"
              : isRegistering ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="auth-footnote">
          Demo only. Use a unique password; never enter banking credentials or
          sensitive personal information.
        </p>
      </section>
    </div>
  );
}
