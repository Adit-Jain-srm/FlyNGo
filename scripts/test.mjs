#!/usr/bin/env node
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const isWin = process.platform === "win32";
const rootDir = process.cwd();
const venvPytest = isWin
  ? path.join(rootDir, ".venv", "Scripts", "pytest.exe")
  : path.join(rootDir, ".venv", "bin", "pytest");

console.log("=== Running Backend Pytest ===");
if (!fs.existsSync(venvPytest)) {
  console.error("Pytest not found in .venv. Please run: npm run setup");
  process.exit(1);
}

try {
  execSync(`"${venvPytest}" backend/tests`, { stdio: "inherit", cwd: rootDir });
} catch (err) {
  console.error("Backend tests failed.");
  process.exit(1);
}

const webPkgPath = path.join(rootDir, "web", "package.json");
if (fs.existsSync(webPkgPath)) {
  const pkg = JSON.parse(fs.readFileSync(webPkgPath, "utf-8"));
  if (pkg.scripts && pkg.scripts.test) {
    console.log("\n=== Running Frontend Tests ===");
    try {
      execSync("npm test --prefix web", { stdio: "inherit", cwd: rootDir });
    } catch (err) {
      console.error("Frontend tests failed.");
      process.exit(1);
    }
  }
}

console.log("\n=== All tests passed! ===");
