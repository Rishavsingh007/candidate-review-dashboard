import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { updateInternalNotes } from "../api/candidates";

export default function NotesPanel({ candidateId, initialNotes }) {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState(initialNotes || "");

  useEffect(() => {
    setNotes(initialNotes || "");
  }, [initialNotes]);

  const mutation = useMutation({
    mutationFn: (internal_notes) => updateInternalNotes(candidateId, internal_notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidate", candidateId] });
    },
  });

  return (
    <section className="card notes-panel notes-panel--admin">
      <div className="section-header">
        <h3>Internal notes</h3>
        <span className="badge badge--admin">Admin only</span>
      </div>
      <p className="muted notes-panel__hint">
        Private notes for the recruitment team. Reviewers cannot view or edit this section.
      </p>
      <textarea
        rows={5}
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
        placeholder="Add internal notes about this candidate…"
      />
      {mutation.isError && (
        <p className="error-text">Failed to save notes. Please try again.</p>
      )}
      <button
        type="button"
        className="btn btn-primary"
        onClick={() => mutation.mutate(notes)}
        disabled={mutation.isPending}
      >
        {mutation.isPending ? "Saving..." : "Save notes"}
      </button>
    </section>
  );
}
