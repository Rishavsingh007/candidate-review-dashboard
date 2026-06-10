import { useMutation, useQueryClient } from "@tanstack/react-query";
import { submitScore } from "../api/candidates";

export function useSubmitScore(candidateId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) => submitScore(candidateId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidate", candidateId] });
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
    },
  });
}
