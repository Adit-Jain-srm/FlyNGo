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

const isWin = process.platform === "win32";
const npmCmd = isWin ? "npm.cmd" : "npm";
const child = spawn(npmCmd, ["run", "dev", "--prefix", "web"], { stdio: "inherit", cwd: rootDir });

child.on("exit", (code) => {
  process.exit(code ?? 0);
});
