// API client for the FastAPI backend.
// The base URL comes from VITE_API_BASE_URL (see frontend/.env.example),
// with a fallback to the local development server.

export const API_BASE_URL = "http://127.0.0.1:8000";

async function fetchApi(path, options) {
  try {
    return await fetch(`${API_BASE_URL}${path}`, options);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Cannot reach the API at ${API_BASE_URL}. Make sure the FastAPI server is running and its ALLOWED_ORIGINS setting includes this frontend address.`
      );
    }
    throw error;
  }
}

async function request(path, options) {
  const response = await fetchApi(path, options);
  if (!response.ok) {
    // FastAPI returns {detail: ...} on errors; 422 returns an
    // array of validation issues in detail.
    const data = await response.json().catch(() => ({}));
    throw new Error(apiErrorMessage(response.status, data));
  }
  return response.json();
}

// Turn FastAPI error responses into a readable message.
function apiErrorMessage(status, data) {
  if (status === 422 && Array.isArray(data.detail)) {
    const items = data.detail.map((item) => {
      const field = item.loc?.slice(1).join(".") || "field";
      return `${field}: ${item.msg}`;
    });
    return `Validation failed:\n${items.join("\n")}`;
  }
  return data.detail || `API request failed (HTTP ${status})`;
}

// GET /api/health - used by the dashboard to show backend connection status.
export function fetchHealth() {
  return request("/api/health");
}

// GET / - API name and version.
export function fetchRoot() {
  return request("/");
}

// GET /api/model/dashboard/summary - live transaction and prediction totals.
export function fetchDashboardSummary() {
  return request("/api/model/dashboard/summary");
}

// GET /api/model/status - artifact availability and runtime model settings.
export function fetchModelStatus() {
  return request("/api/model/status");
}

// GET /api/model/metrics - measured evaluation metrics from model training.
export function fetchModelMetrics() {
  return request("/api/model/metrics");
}

const AUTH_TOKEN_KEY = "fraud-demo-auth-token";

export function getAuthToken() {
  return sessionStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAuthToken(token) {
  sessionStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAuthToken() {
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
}

export function registerUser(payload) {
  return request("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload) {
  return request("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchCurrentUser(token) {
  return request("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// GET /api/transactions - paginated transaction history.
export function fetchTransactions({ skip = 0, limit = 20 } = {}) {
  const query = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  return request(`/api/transactions?${query}`);
}

// GET /api/transactions/{id} - full transaction and prediction details.
export function fetchTransaction(transactionId) {
  return request(`/api/transactions/${transactionId}`);
}

// POST /api/predict - analyze one transaction.
// Returns the prediction result (probability, score, category,
// class, disclaimer) or throws with a readable error message.
export function predictTransaction(payload) {
  return request("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// POST /api/dataset/upload - validate a CSV and get a preview.
// Uses multipart/form-data (fetch sets the boundary automatically).
export function uploadDataset(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/api/dataset/upload", {
    method: "POST",
    body: formData,
  });
}

// POST /api/predict/batch - analyze every valid row of a CSV.
export function runBatchAnalysis(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/api/predict/batch", {
    method: "POST",
    body: formData,
  });
}

// GET /api/dataset/sample - download the synthetic sample CSV.
export async function downloadSampleDataset() {
  const response = await fetchApi("/api/dataset/sample");
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(apiErrorMessage(response.status, data));
  }
  return response.blob();
}
