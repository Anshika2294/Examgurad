import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// ---- Register ----
export async function registerUser({ name, email, password, role }) {
  const response = await api.post("/auth/register", { name, email, password, role });
  return response.data;
}

// ---- Login ----
export async function loginUser({ email, password }) {
  const response = await api.post("/auth/login", { email, password });
  return response.data; // { access_token, token_type }
}

// ---- Get current user ----
export async function getCurrentUser(token) {
  const response = await api.get("/auth/me", { params: { token } });
  return response.data;
}

export default api;