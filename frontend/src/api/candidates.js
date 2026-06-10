import apiClient from "./client";

export async function fetchCandidates(params) {
  const { data } = await apiClient.get("/candidates", { params });
  return data;
}

export async function fetchCandidate(id) {
  const { data } = await apiClient.get(`/candidates/${id}`);
  return data;
}

export async function submitScore(id, payload) {
  const { data } = await apiClient.post(`/candidates/${id}/scores`, payload);
  return data;
}

export async function generateSummary(id, force = false) {
  const { data } = await apiClient.post(`/candidates/${id}/summary`, null, {
    params: { force },
  });
  return data;
}

export async function updateInternalNotes(id, internal_notes) {
  const { data } = await apiClient.patch(`/candidates/${id}/internal-notes`, {
    internal_notes,
  });
  return data;
}

export async function deleteCandidate(id) {
  await apiClient.delete(`/candidates/${id}`);
}
