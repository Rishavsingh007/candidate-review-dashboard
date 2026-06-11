import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Filters from "../components/Filters";
import { useAuth } from "../hooks/useAuth";
import { useCandidates } from "../hooks/useCandidates";
import { PAGE_SIZE } from "../utils/constants";
import { formatAxiosError } from "../utils/errors";
import { formatAverage, formatStatus } from "../utils/formatters";

const emptyFilters = {
  status: "",
  role_applied: "",
  skill: "",
  keyword: "",
};

export default function CandidateListPage() {
  const { isAdmin } = useAuth();
  const [filters, setFilters] = useState(emptyFilters);
  const [appliedFilters, setAppliedFilters] = useState(emptyFilters);
  const [offset, setOffset] = useState(0);

  const queryParams = useMemo(
    () => ({
      offset,
      limit: PAGE_SIZE,
      ...(appliedFilters.status ? { status: appliedFilters.status } : {}),
      ...(appliedFilters.role_applied
        ? { role_applied: appliedFilters.role_applied }
        : {}),
      ...(appliedFilters.skill ? { skill: appliedFilters.skill } : {}),
      ...(appliedFilters.keyword ? { keyword: appliedFilters.keyword } : {}),
    }),
    [appliedFilters, offset],
  );

  const { data, isLoading, isError, error } = useCandidates(queryParams);

  useEffect(() => {
    if (!data || data.total === 0) return;
    if (offset >= data.total) {
      const lastPageOffset = Math.floor((data.total - 1) / PAGE_SIZE) * PAGE_SIZE;
      setOffset(lastPageOffset);
    }
  }, [data?.total, offset]);

  const handleFilterChange = (field, value) => {
    setFilters((current) => ({ ...current, [field]: value }));
  };

  const handleApplyFilters = (event) => {
    event.preventDefault();
    setAppliedFilters(filters);
    setOffset(0);
  };

  const handleResetFilters = () => {
    setFilters(emptyFilters);
    setAppliedFilters(emptyFilters);
    setOffset(0);
  };

  const total = data?.total || 0;
  const canGoPrev = offset > 0;
  const canGoNext = offset + PAGE_SIZE < total;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Candidates</h1>
          <p className="muted">Filter, paginate, and open a candidate to score them.</p>
        </div>
      </div>

      <Filters
        values={filters}
        onChange={handleFilterChange}
        onSubmit={handleApplyFilters}
        onReset={handleResetFilters}
      />

      {isLoading && <div className="status-box status-box--loading">Loading candidates...</div>}

      {isError && (
        <div className="status-box status-box--error">
          {formatAxiosError(error, "Failed to load candidates.")}
        </div>
      )}

      {!isLoading && !isError && (
        <>
          <div className="table-wrap card">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Skills</th>
                  <th>{isAdmin ? "Avg score" : "My avg"}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data?.items?.length ? (
                  data.items.map((candidate) => (
                    <tr key={candidate.id}>
                      <td>
                        <div className="cell-title">{candidate.name}</div>
                        <div className="muted">{candidate.email}</div>
                      </td>
                      <td>{candidate.role_applied}</td>
                      <td>
                        <span className={`badge badge--${candidate.status}`}>
                          {formatStatus(candidate.status)}
                        </span>
                      </td>
                      <td>{candidate.skills?.join(", ") || "—"}</td>
                      <td>
                        {formatAverage(
                          isAdmin ? candidate.average_score : candidate.my_average_score,
                        )}
                      </td>
                      <td>
                        <Link className="btn btn-secondary" to={`/candidates/${candidate.id}`}>
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="muted">
                      No candidates match these filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              type="button"
              className="btn btn-secondary"
              disabled={!canGoPrev}
              onClick={() => setOffset(Math.max(offset - PAGE_SIZE, 0))}
            >
              Previous
            </button>
            <span className="muted">
              Showing {total === 0 ? 0 : offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of{" "}
              {total}
            </span>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={!canGoNext}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
