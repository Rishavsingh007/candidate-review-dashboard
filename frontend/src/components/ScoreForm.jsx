import { useState } from "react";
import { SCORE_CATEGORIES } from "../utils/constants";

const initialForm = {
  category: SCORE_CATEGORIES[0].value,
  score: 3,
  note: "",
};

export default function ScoreForm({ onSubmit, isSubmitting, errorMessage }) {
  const [form, setForm] = useState(initialForm);

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await onSubmit({
        category: form.category,
        score: Number(form.score),
        note: form.note.trim() || null,
      });
    } catch {
      // Parent mutation exposes error state.
    }
  };

  return (
    <form className="card score-form" onSubmit={handleSubmit}>
      <h3>Submit score</h3>

      <label>
        Category
        <select
          value={form.category}
          onChange={(event) => setForm({ ...form, category: event.target.value })}
        >
          {SCORE_CATEGORIES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Score (1–5)
        <input
          type="number"
          min="1"
          max="5"
          value={form.score}
          onChange={(event) => setForm({ ...form, score: event.target.value })}
          required
        />
      </label>

      <label>
        Note (optional)
        <textarea
          value={form.note}
          onChange={(event) => setForm({ ...form, note: event.target.value })}
          rows={3}
        />
      </label>

      {errorMessage && <p className="error-text">{errorMessage}</p>}

      <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
        {isSubmitting ? "Saving..." : "Save score"}
      </button>
    </form>
  );
}
