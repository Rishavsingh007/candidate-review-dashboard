import { useQuery } from "@tanstack/react-query";
import { fetchCandidates } from "../api/candidates";

export function useCandidates(filters) {
  return useQuery({
    queryKey: ["candidates", filters],
    queryFn: () => fetchCandidates(filters),
  });
}
