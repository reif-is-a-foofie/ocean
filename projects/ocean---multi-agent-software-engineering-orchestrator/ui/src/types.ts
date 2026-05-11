export type Actor = {
  id: string;
  name: string;
  role: string;
  mission: string;
  phase: string;
  skills: string[];
  tools: string[];
  active: boolean;
};

export type Artifact = {
  kind: string;
  label: string;
  path: string;
};

export type TeamMessage = {
  actor_id: string;
  actor_name: string;
  role: string;
  phase: string;
  body: string;
  artifacts?: Artifact[];
};

export type Job = {
  id: string;
  actor_id: string;
  actor_name: string;
  phase: string;
  title: string;
  cursor_prompt: string;
};

export type FileItem = {
  path: string;
  size: number;
};

export type ChatEntry = {
  ts: string;
  message: string;
  response: string;
  screenshots?: Array<{ name: string; path: string; mime: string; note: string }>;
  test_notes?: string;
  file_updates?: Array<{ path: string; mode: string }>;
  team_messages?: TeamMessage[];
  job_plan?: { jobs: Job[] };
};

export type SetupProfile = {
  project_root: string;
  github_url: string;
  working_directory: string;
  token_budget_per_hour: number;
  vision_guess: string;
  audience_guess: string;
  saved: boolean;
};

export type AppState = {
  project_root: string;
  actors: Actor[];
  doctrine: Record<string, string>;
  setup?: SetupProfile;
};
