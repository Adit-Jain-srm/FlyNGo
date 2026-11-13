#!/usr/bin/env node
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const rootDir = process.cwd();
const webDir = path.join(rootDir, "web");

if (!fs.existsSync(webDir)) {
  console.error("Web directory not found at " + webDir);
  process.exit(1);
}

// Spawn Vite's JS entry with Node. Spawning npm.cmd on Windows fails with EINVAL
// under Node 20+ unless shell is enabled.
const viteBin = path.join(webDir, "node_modules", "vite", "bin", "vite.js");
if (!fs.existsSync(viteBin)) {
  console.error("Vite is not installed. Please run: npm run setup");
  process.exit(1);
}

const child = spawn(process.execPath, [viteBin, "--port", "5173"], {
  stdio: "inherit",
  cwd: webDir,
});

child.on("exit", (code) => {
  process.exit(code ?? 0);
});
