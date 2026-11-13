#!/usr/bin/env node
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const isWin = process.platform === "win32";
const rootDir = process.cwd();
const venvDir = path.join(rootDir, ".venv");
const venvPython = isWin
  ? path.join(venvDir, "Scripts", "python.exe")
  : path.join(venvDir, "bin", "python");

console.log("=== FlyNGo Setup ===");

// 1. Python virtual environment
if (!fs.existsSync(venvPython)) {
  console.log("Creating Python virtual environment in .venv...");
  const pythonCmd = isWin ? "python" : "python3";
  execSync(`${pythonCmd} -m venv .venv`, { stdio: "inherit" });
} else {
  console.log("Python virtual environment already exists.");
}

// 2. Install backend dependencies
console.log("Installing backend dependencies...");
const pipCmd = `"${venvPython}" -m pip install --upgrade pip && "${venvPython}" -m pip install -r backend/requirements.txt`;
execSync(pipCmd, { stdio: "inherit" });

// 3. Install web dependencies if web directory exists
const webPkg = path.join(rootDir, "web", "package.json");
if (fs.existsSync(webPkg)) {
  console.log("Installing web dependencies...");
  execSync("npm install --prefix web", { stdio: "inherit" });
}

console.log("=== Setup completed successfully ===");
