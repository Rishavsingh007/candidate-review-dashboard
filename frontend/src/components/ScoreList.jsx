import { formatCategory, formatDate } from "../utils/formatters";

export default function ScoreList({ scores, isAdmin }) {
  if (!scores?.length) {
    return <p className="muted">No scores submitted yet.</p>;
  }

  return (
    <div className="score-list">
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Score</th>
            {isAdmin && <th>Reviewer</th>}
            <th>Note</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {scores.map((score) => (
            <tr key={score.id}>
              <td>{formatCategory(score.category)}</td>
              <td>{score.score}</td>
              {isAdmin && <td>{score.reviewer_email || score.reviewer_id}</td>}
              <td>{score.note || "—"}</td>
              <td>{formatDate(score.updated_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
