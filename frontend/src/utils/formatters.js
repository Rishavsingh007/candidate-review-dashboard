import { SCORE_CATEGORIES } from "./constants";

export function formatAverage(value) {
  if (value === null || value === undefined) return "—";
  return Number(value).toFixed(1);
}

export function formatCategory(category) {
  const match = SCORE_CATEGORIES.find((item) => item.value === category);
  return match ? match.label : category;
}

export function formatStatus(status) {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}
