#!/usr/bin/env node
/**
 * After `npm install`, wire the Python package (editable) so `ocean` works.
 * Skip with OCEAN_SKIP_PY_INSTALL=1
 */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

if (process.env.OCEAN_SKIP_PY_INSTALL === "1") {
  process.exit(0);
}

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const py =
  process.env.PYTHON?.trim() ||
  (process.platform === "win32" ? "python" : "python3");

console.log("ocean: pip install -e . (Python backend)…");
const r = spawnSync(py, ["-m", "pip", "install", "-e", root], {
  cwd: root,
  stdio: "inherit",
});

if (r.status !== 0) {
  console.warn(
    "ocean: pip install -e . failed — from the package root run:\n  " +
      py +
      " -m pip install -e .\n",
  );
}
process.exit(0);
