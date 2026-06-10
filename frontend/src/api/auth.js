import apiClient from "./client";

export async function login(email, password) {
  const { data } = await apiClient.post("/auth/login", { email, password });
  return data;
}

export async function register(email, password) {
  const { data } = await apiClient.post("/auth/register", { email, password });
  return data;
}

export async function fetchCurrentUser() {
  const { data } = await apiClient.get("/auth/me");
  return data;
}
