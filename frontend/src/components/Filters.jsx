import { CANDIDATE_STATUSES, FILTER_SKILLS, ROLES_APPLIED } from "../utils/constants";

export default function Filters({ values, onChange, onSubmit, onReset }) {
  return (
    <form className="filters" onSubmit={onSubmit}>
      <label>
        Status
        <select
          value={values.status}
          onChange={(event) => onChange("status", event.target.value)}
        >
          {CANDIDATE_STATUSES.map((option) => (
            <option key={option.value || "all"} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Role
        <select
          value={values.role_applied}
          onChange={(event) => onChange("role_applied", event.target.value)}
        >
          {ROLES_APPLIED.map((option) => (
            <option key={option.value || "all-roles"} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Skill
        <select
          value={values.skill}
          onChange={(event) => onChange("skill", event.target.value)}
        >
          {FILTER_SKILLS.map((option) => (
            <option key={option.value || "all-skills"} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Keyword
        <input
          type="text"
          value={values.keyword}
          onChange={(event) => onChange("keyword", event.target.value)}
          placeholder="Search name or email"
        />
      </label>

      <div className="filters__actions">
        <button type="submit" className="btn btn-primary">
          Apply filters
        </button>
        <button type="button" className="btn btn-secondary" onClick={onReset}>
          Reset
        </button>
      </div>
    </form>
  );
}
