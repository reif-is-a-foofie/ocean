#!/usr/bin/env node
/**
 * After `npm install`, wire the Python package (editable) so `ocean` works.
 * Skip with OCEAN_SKIP_PY_INSTALL=1
 *
 * Prefer ./venv (matches bin/ocean.js). If missing, create venv with Python 3.11+,
 * upgrade pip/setuptools (Apple CLT python ships pip 21.x and cannot install PEP517 editable).
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

if (process.env.OCEAN_SKIP_PY_INSTALL === "1") {
  process.exit(0);
}

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const isWin = process.platform === "win32";

function venvPython() {
  if (isWin) {
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

function pyOk311(cmd) {
  const r = spawnSync(
    cmd,
    ["-c", "import sys; raise SystemExit(0 if sys.version_info[:2]>=(3,11) else 1)"],
    { stdio: "ignore" },
  );
  return r.status === 0;
}

/** First interpreter on PATH that is Python 3.11+. */
function pickBootstrapPython() {
  const candidates = ["python3.14", "python3.13", "python3.12", "python3.11", "python3"];
  const override = process.env.PYTHON?.trim();
  if (override && pyOk311(override)) return override;
  for (const c of candidates) {
    if (pyOk311(c)) return c;
  }
  return null;
}

function run(py, args) {
  return spawnSync(py, args, { cwd: root, stdio: "inherit" });
}

let py = venvPython();

if (!py) {
  const boot = pickBootstrapPython();
  if (boot) {
    console.log(`ocean: creating venv with ${boot}…`);
    const ve = run(boot, ["-m", "venv", "venv"]);
    if (ve.status !== 0) {
      console.warn("ocean: venv creation failed — trying system python for pip install.");
      py = boot;
    } else {
      py = venvPython();
    }
  }
}

if (!py) {
  py = process.env.PYTHON?.trim() || (isWin ? "python" : "python3");
  console.warn(
    "ocean: No Python 3.11+ found on PATH (try brew install python@3.12). Using:",
    py,
  );
}

console.log("ocean: upgrading pip / setuptools / wheel…");
run(py, ["-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]);

console.log("ocean: pip install -e . (Python backend)…");
const r = run(py, ["-m", "pip", "install", "-e", root]);

if (r.status !== 0) {
  console.warn(
    "ocean: pip install -e . failed — ensure Python 3.11+ and a recent pip, then from the package root run:\n  " +
      py +
      " -m pip install --upgrade pip setuptools wheel\n  " +
      py +
      " -m pip install -e .\n",
  );
} else {
  console.log(
    "ocean: Python package installed. Run `npx ocean` or ./venv/bin/ocean — default TTY UI is `ocean` (Textual).",
  );
}
process.exit(0);
