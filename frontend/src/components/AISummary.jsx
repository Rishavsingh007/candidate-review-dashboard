import { useMutation, useQueryClient } from "@tanstack/react-query";
import { generateSummary } from "../api/candidates";
import { formatAxiosError } from "../utils/errors";

export default function AISummary({ candidateId, initialSummary }) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ force }) => generateSummary(candidateId, force),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidate", candidateId] });
    },
  });

  const summary = mutation.data?.ai_summary ?? initialSummary;

  return (
    <section className="card">
      <div className="section-header">
        <h3>AI Summary</h3>
        <div className="section-header__actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => mutation.mutate({ force: false })}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Generating..." : "Generate summary"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => mutation.mutate({ force: true })}
            disabled={mutation.isPending}
          >
            Regenerate
          </button>
        </div>
      </div>

      {mutation.isPending && (
        <div className="status-box status-box--loading">
          Generating AI summary… this may take a couple of seconds.
        </div>
      )}

      {mutation.isError && (
        <div className="status-box status-box--error">
          {formatAxiosError(mutation.error, "Failed to generate summary. Please try again.")}
        </div>
      )}

      {!mutation.isPending && !mutation.isError && summary && (
        <p className="summary-text">{summary}</p>
      )}

      {!mutation.isPending && !mutation.isError && !summary && (
        <p className="muted">No summary yet. Click generate to create one.</p>
      )}
    </section>
  );
}
