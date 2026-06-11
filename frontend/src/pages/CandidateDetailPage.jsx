import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import AISummary from "../components/AISummary";
import NotesPanel from "../components/NotesPanel";
import ScoreForm from "../components/ScoreForm";
import ScoreList from "../components/ScoreList";
import { deleteCandidate, fetchCandidate } from "../api/candidates";
import { useAuth } from "../hooks/useAuth";
import { useSubmitScore } from "../hooks/useScores";
import { formatAxiosError } from "../utils/errors";
import { formatAverage, formatCategory, formatDate, formatStatus } from "../utils/formatters";

export default function CandidateDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["candidate", id],
    queryFn: () => fetchCandidate(id),
  });

  const scoreMutation = useSubmitScore(id);

  const deleteMutation = useMutation({
    mutationFn: () => deleteCandidate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
      navigate("/candidates");
    },
  });

  if (isLoading) {
    return <div className="status-box status-box--loading">Loading candidate...</div>;
  }

  if (isError) {
    return (
      <div className="status-box status-box--error">
        {formatAxiosError(error, "Failed to load candidate.")}
      </div>
    );
  }

  const average = isAdmin ? data.average_score : data.my_average_score;

  return (
    <div className="page detail-page">
      <div className="page-header">
        <div>
          <Link to="/candidates" className="back-link">
            ← Back to list
          </Link>
          <h1>{data.name}</h1>
          <p className="muted">
            {data.email} · {data.role_applied} · {formatStatus(data.status)}
          </p>
        </div>
        {isAdmin && (
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Archiving..." : "Archive candidate"}
          </button>
        )}
      </div>

      <div className="detail-grid">
        <section className="card profile-card">
          <h3>Profile</h3>
          <dl className="detail-list">
            <div>
              <dt>Name</dt>
              <dd>{data.name}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{data.email}</dd>
            </div>
            <div>
              <dt>Role applied</dt>
              <dd>{data.role_applied}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <span className={`badge badge--${data.status}`}>
                  {formatStatus(data.status)}
                </span>
              </dd>
            </div>
            <div>
              <dt>Applied on</dt>
              <dd>{formatDate(data.created_at)}</dd>
            </div>
            <div>
              <dt>Skills</dt>
              <dd>{data.skills?.join(", ") || "—"}</dd>
            </div>
            <div>
              <dt>{isAdmin ? "Average score" : "My average score"}</dt>
              <dd>{formatAverage(average)}</dd>
            </div>
            {isAdmin && data.category_averages?.length > 0 && (
              <div>
                <dt>Category averages</dt>
                <dd>
                  {data.category_averages
                    .map((item) => `${formatCategory(item.category)}: ${item.average}`)
                    .join(" · ")}
                </dd>
              </div>
            )}
          </dl>
        </section>

        <ScoreForm
          onSubmit={(payload) => scoreMutation.mutateAsync(payload)}
          isSubmitting={scoreMutation.isPending}
          errorMessage={
            scoreMutation.isError
              ? formatAxiosError(scoreMutation.error, "Failed to save score.")
              : ""
          }
        />
      </div>

      <section className="card">
        <h3>{isAdmin ? "All reviewer scores" : "Your scores"}</h3>
        <ScoreList scores={data.scores} isAdmin={isAdmin} />
      </section>

      <AISummary candidateId={id} initialSummary={data.ai_summary} />

      {isAdmin && (
        <NotesPanel candidateId={id} initialNotes={data.internal_notes} />
      )}

      {deleteMutation.isError && (
        <p className="error-text">
          {formatAxiosError(deleteMutation.error, "Failed to archive candidate.")}
        </p>
      )}
    </div>
  );
}
