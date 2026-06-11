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

function parseApiDate(value) {
  if (!value) return null;
  if (typeof value === "string") {
    
    const hasTimezone = value.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(value);
    return new Date(hasTimezone ? value : `${value}Z`);
  }
  return new Date(value);
}

export function formatDate(value) {
  const date = parseApiDate(value);
  if (!date || Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString();
}
