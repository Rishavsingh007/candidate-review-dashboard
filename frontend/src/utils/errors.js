export function formatApiError(detail, fallback = "Something went wrong") {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        typeof item === "string" ? item : item.msg || item.message || fallback,
      )
      .join("; ");
  }
  return fallback;
}

export function formatAxiosError(error, fallback = "Something went wrong") {
  return formatApiError(error?.response?.data?.detail, fallback);
}
