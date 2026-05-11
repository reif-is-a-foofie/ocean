import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Clipboard,
  FileText,
  FolderOpen,
  ImageUp,
  RefreshCw,
  Send,
} from "lucide-react";
import "../styles.css";
import type { AppState, ChatEntry, FileItem, Job, TeamMessage } from "./types";

declare global {
  interface Window {
    API_BASE?: string;
  }
}

type ScreenshotDraft = {
  name: string;
  data_url: string;
  note: string;
};

type FilePreview = {
  path: string;
  content: string;
};

const DEFAULT_ROOT = "/Users/reify/Classified/ocean";
const CHARACTER_EMOJI: Record<string, string> = {
  captain: "🧭",
  edna: "🎨",
  q: "🛠️",
  mario: "🚢",
  scrooge: "💰",
  ocean: "🌊",
  user: "👤",
};

function apiUrl(path: string): string {
  const base = (window.API_BASE || "").replace(/\/$/, "");
  return `${base}${path}`;
}

async function apiGet<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(apiUrl(`${path}${query ? `?${query}` : ""}`));
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

function App() {
  const [projectRoot, setProjectRoot] = useState(DEFAULT_ROOT);
  const [state, setState] = useState<AppState | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [chat, setChat] = useState<ChatEntry[]>([]);
  const [message, setMessage] = useState("");
  const [testNotes, setTestNotes] = useState("");
  const [updateFeedback, setUpdateFeedback] = useState(false);
  const [useAdvisor, setUseAdvisor] = useState(false);
  const [screenshots, setScreenshots] = useState<ScreenshotDraft[]>([]);
  const [filter, setFilter] = useState("");
  const [preview, setPreview] = useState<FilePreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [healthy, setHealthy] = useState(false);

  async function refresh(root = projectRoot) {
    setBusy(true);
    setError("");
    try {
      const [health, nextState, fileResult, history] = await Promise.all([
        fetch(apiUrl("/healthz")).then((response) => response.ok).catch(() => false),
        apiGet<AppState>("/api/state", { project_root: root }),
        apiGet<{ files: FileItem[] }>("/api/files", { project_root: root }),
        apiGet<{ messages: ChatEntry[] }>("/api/chat", { project_root: root }),
      ]);
      setHealthy(health);
      setState(nextState);
      setFiles(fileResult.files);
      setChat(history.messages);
    } catch (err) {
      setHealthy(false);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const visibleFiles = useMemo(() => {
    const term = filter.trim().toLowerCase();
    if (!term) {
      return files;
    }
    return files.filter((file) => file.path.toLowerCase().includes(term));
  }, [files, filter]);

  async function readFile(path: string) {
    setError("");
    try {
      const result = await apiPost<FilePreview>("/api/files/read", {
        project_root: projectRoot,
        path,
      });
      setPreview(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = message.trim();
    if (!text || busy) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await apiPost<{
        chat_entry: ChatEntry;
      }>("/api/chat", {
        project_root: projectRoot,
        message: text,
        screenshots,
        test_notes: testNotes,
        update_feedback: updateFeedback,
        use_advisor: useAdvisor,
      });
      setChat((items) => [...items, result.chat_entry]);
      setMessage("");
      setScreenshots([]);
      setTestNotes("");
      await refresh(projectRoot);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function loadScreenshots(filesToLoad: FileList | null) {
    if (!filesToLoad) {
      return;
    }
    const loaded = await Promise.all(
      Array.from(filesToLoad).map(
        (file) =>
          new Promise<ScreenshotDraft>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve({ name: file.name, data_url: String(reader.result), note: "" });
            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(file);
          }),
      ),
    );
    setScreenshots((items) => [...items, ...loaded]);
  }

  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <div className="mark">🌊</div>
          <div>
            <h1>Ocean</h1>
            <p>Product loop control room</p>
          </div>
        </div>

        <label className="repo-field">
          <span>Project root</span>
          <input value={projectRoot} onChange={(event) => setProjectRoot(event.target.value)} />
          <button className="secondary" onClick={() => void refresh(projectRoot)} type="button">
            <RefreshCw size={16} /> Refresh
          </button>
        </label>

        <section className="side-section">
          <div className="section-head">
            <h2>Crew</h2>
            <span>{state?.actors.length || 0}/5</span>
          </div>
          <div className="actor-list">
            {(state?.actors || []).map((actor) => (
              <article className="actor" key={actor.id}>
                <div className="actor-top">
                  <h3>
                    <span className="emoji">{CHARACTER_EMOJI[actor.id] || "•"}</span>
                    {actor.name}
                  </h3>
                  <small>{actor.phase}</small>
                </div>
                <p>{actor.mission}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="side-section files-section">
          <div className="section-head">
            <h2>Files</h2>
            <span>{visibleFiles.length}</span>
          </div>
          <input
            className="filter"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Filter files"
          />
          <div className="file-list">
            {visibleFiles.map((file) => (
              <button className="file-row" key={file.path} onClick={() => void readFile(file.path)} type="button">
                <span>
                  <FolderOpen size={14} /> {file.path}
                </span>
                <small>{formatBytes(file.size)}</small>
              </button>
            ))}
          </div>
        </section>
      </aside>

      <main className="chat">
        <header className="chat-head">
          <div>
            <h2>Product Conversation</h2>
            <p>{projectRoot}</p>
          </div>
          <div className="runtime">
            <span className={`dot ${healthy ? "ok" : ""}`} />
            <span>{busy ? "Working" : healthy ? "Ready" : "Offline"}</span>
          </div>
        </header>

        {error ? <div className="note">{error}</div> : null}

        <section className="messages">
          <div className="chat-intro">
            <span>Chat first</span>
            <p>Send a product signal, screenshot, or test note. Ocean will capture it, rank the next move, and hand Cursor a job.</p>
          </div>
          {chat.length === 0 ? <div className="empty">No conversation yet.</div> : null}
          {chat.map((entry, index) => (
            <ChatMessage
              entry={entry}
              key={`${entry.ts}-${index}`}
              projectRoot={projectRoot}
              onOpenArtifact={(path) => void readFile(path)}
            />
          ))}
        </section>

        {preview ? (
          <section className="file-preview">
            <strong>
              <FileText size={16} /> {preview.path}
            </strong>
            <pre>{preview.content}</pre>
          </section>
        ) : null}

        <form className="composer" onSubmit={submit}>
          <textarea
            rows={4}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Tell Ocean what changed, what felt wrong, or what should happen next."
          />
          <textarea
            rows={2}
            value={testNotes}
            onChange={(event) => setTestNotes(event.target.value)}
            placeholder="Test notes"
          />
          <div className="composer-row">
            <label className="file-input">
              <ImageUp size={16} />
              <span>Screenshots</span>
              <input
                accept="image/*"
                multiple
                onChange={(event) => void loadScreenshots(event.target.files)}
                type="file"
              />
            </label>
            <label className="checkline">
              <input
                checked={updateFeedback}
                onChange={(event) => setUpdateFeedback(event.target.checked)}
                type="checkbox"
              />
              <span>Record feedback</span>
            </label>
            <label className="checkline">
              <input checked={useAdvisor} onChange={(event) => setUseAdvisor(event.target.checked)} type="checkbox" />
              <span>Use advisor</span>
            </label>
            <button disabled={busy || !message.trim()} type="submit">
              <Send size={16} /> Send
            </button>
          </div>
          {screenshots.length ? (
            <div className="shot-preview">
              {screenshots.map((shot) => (
                <span key={shot.name}>{shot.name}</span>
              ))}
            </div>
          ) : null}
        </form>
      </main>
    </div>
  );
}

function ChatMessage({
  entry,
  projectRoot,
  onOpenArtifact,
}: {
  entry: ChatEntry;
  projectRoot: string;
  onOpenArtifact: (path: string) => void;
}) {
  const jobs = entry.job_plan?.jobs || [];
  return (
    <article className="msg">
      <div className="meta">{formatDate(entry.ts)}</div>
      <div className="bubble user">
        <strong>
          <span className="emoji">{CHARACTER_EMOJI.user}</span>
          You
        </strong>
        <p>{entry.message}</p>
      </div>
      <div className="team-stream">
        {(entry.team_messages || []).map((team) => (
          <TeamBubble key={`${entry.ts}-${team.actor_id}`} message={team} projectRoot={projectRoot} onOpen={onOpenArtifact} />
        ))}
      </div>
      <div className="bubble">
        <strong>
          <span className="emoji">{CHARACTER_EMOJI.ocean}</span>
          Ocean
        </strong>
        <p>{entry.response}</p>
      </div>
      {jobs.length ? (
        <div className="jobs">
          {jobs.map((job) => (
            <JobCard job={job} key={job.id} />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function TeamBubble({
  message,
  projectRoot,
  onOpen,
}: {
  message: TeamMessage;
  projectRoot: string;
  onOpen: (path: string) => void;
}) {
  const emoji = CHARACTER_EMOJI[message.actor_id] || initials(message.actor_name);
  return (
    <div className={`team-msg phase-${message.phase}`}>
      <div className="avatar">{emoji}</div>
      <div className="team-body">
        <div className="team-meta">
          <strong>
            <span className="emoji">{emoji}</span>
            {message.actor_name}
          </strong>
          <span>{message.role}</span>
        </div>
        <p>{message.body}</p>
        {message.artifacts?.length ? (
          <div className="artifacts">
            {message.artifacts.map((artifact) =>
              artifact.kind === "screenshot" ? (
                <a
                  className="artifact screenshot-artifact"
                  href={artifactUrl(projectRoot, artifact.path)}
                  key={`${artifact.kind}-${artifact.path}`}
                  rel="noreferrer"
                  target="_blank"
                >
                  <img alt={artifact.label} src={artifactUrl(projectRoot, artifact.path)} />
                  <strong>{artifact.label}</strong>
                </a>
              ) : (
                <button className="artifact" key={`${artifact.kind}-${artifact.path}`} onClick={() => onOpen(artifact.path)} type="button">
                  <span>{artifact.kind}</span>
                  <strong>{artifact.label}</strong>
                </button>
              ),
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function JobCard({ job }: { job: Job }) {
  const emoji = CHARACTER_EMOJI[job.actor_id] || "•";
  return (
    <details className="job">
      <summary>
        <span className="emoji">{emoji}</span>
        {job.title}
      </summary>
      <button className="ghost" onClick={() => void navigator.clipboard.writeText(job.cursor_prompt)} type="button">
        <Clipboard size={16} /> Copy
      </button>
      <pre>{job.cursor_prompt}</pre>
    </details>
  );
}

function artifactUrl(projectRoot: string, path: string): string {
  const query = new URLSearchParams({ project_root: projectRoot, path }).toString();
  return apiUrl(`/api/artifacts?${query}`);
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${Math.round(size / 1024)} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
