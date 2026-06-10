export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export const TOKEN_KEY = "crd_token";

export const CANDIDATE_STATUSES = [
  { value: "", label: "All statuses" },
  { value: "new", label: "New" },
  { value: "reviewed", label: "Reviewed" },
  { value: "hired", label: "Hired" },
  { value: "rejected", label: "Rejected" },
];

export const ROLES_APPLIED = [
  { value: "", label: "All roles" },
  { value: "Backend Engineer", label: "Backend Engineer" },
  { value: "Frontend Engineer", label: "Frontend Engineer" },
  { value: "Full Stack Engineer", label: "Full Stack Engineer" },
  { value: "Data Engineer", label: "Data Engineer" },
  { value: "DevOps Engineer", label: "DevOps Engineer" },
];

export const SCORE_CATEGORIES = [
  { value: "technical", label: "Technical" },
  { value: "communication", label: "Communication" },
  { value: "problem_solving", label: "Problem Solving" },
  { value: "culture_fit", label: "Culture Fit" },
];

export const FILTER_SKILLS = [
  { value: "", label: "All skills" },
  { value: "accessibility", label: "Accessibility" },
  { value: "aws", label: "AWS" },
  { value: "ci/cd", label: "CI/CD" },
  { value: "css", label: "CSS" },
  { value: "docker", label: "Docker" },
  { value: "fastapi", label: "FastAPI" },
  { value: "go", label: "Go" },
  { value: "graphql", label: "GraphQL" },
  { value: "java", label: "Java" },
  { value: "kafka", label: "Kafka" },
  { value: "kubernetes", label: "Kubernetes" },
  { value: "mongodb", label: "MongoDB" },
  { value: "node", label: "Node.js" },
  { value: "postgresql", label: "PostgreSQL" },
  { value: "python", label: "Python" },
  { value: "react", label: "React" },
  { value: "spark", label: "Spark" },
  { value: "spring", label: "Spring" },
  { value: "sql", label: "SQL" },
  { value: "terraform", label: "Terraform" },
  { value: "typescript", label: "TypeScript" },
  { value: "vite", label: "Vite" },
];

export const PAGE_SIZE = 20;
