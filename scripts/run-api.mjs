#!/usr/bin/env node
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const isWin = process.platform === "win32";
const rootDir = process.cwd();
const venvPython = isWin
  ? path.join(rootDir, ".venv", "Scripts", "python.exe")
  : path.join(rootDir, ".venv", "bin", "python");

if (!fs.existsSync(venvPython)) {
  console.error("Virtual environment not found. Please run: npm run setup");
  process.exit(1);
}

const args = ["-m", "uvicorn", "backend.app.main:app", "--reload", "--port", "8000", "--app-dir", "."];
const child = spawn(venvPython, args, { stdio: "inherit", cwd: rootDir });

child.on("exit", (code) => {
  process.exit(code ?? 0);
});
