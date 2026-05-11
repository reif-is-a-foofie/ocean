#!/usr/bin/env node
/**
 * npm-installed `ocean` entry — runs the Typer/Python CLI via `python -m ocean`.
 * Package root is one level above this file (repo root when linked / extracted).
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");

function venvPython() {
  if (process.platform === "win32") {
    const a = path.join(root, "venv", "Scripts", "python.exe");
    if (fs.existsSync(a)) return a;
    const b = path.join(root, "venv", "Scripts", "python3.exe");
    if (fs.existsSync(b)) return b;
    return null;
  }
  const p3 = path.join(root, "venv", "bin", "python3");
  if (fs.existsSync(p3)) return p3;
  const p = path.join(root, "venv", "bin", "python");
  if (fs.existsSync(p)) return p;
  return null;
}

const python = venvPython() || process.env.PYTHON?.trim() || (process.platform === "win32" ? "python" : "python3");

const env = { ...process.env };
const sep = path.delimiter;
env.PYTHONPATH = [root, env.PYTHONPATH].filter(Boolean).join(sep);

const args = process.argv.slice(2);
const result = spawnSync(python, ["-m", "ocean", ...args], {
  cwd: root,
  env,
  stdio: "inherit",
});

if (result.error) {
  console.error("ocean: could not run Python:", result.error.message);
  console.error("Install Python 3.11+, then: npm install (runs pip install -e .)");
  process.exit(127);
}

process.exit(result.status === null ? 1 : result.status);
