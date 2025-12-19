#!/usr/bin/env node
/**
 * Small wrapper to tee Next.js dev/start output into dated log files when LOG_ROOT is set.
 * Falls back to pass-through when no LOG_ROOT is provided.
 */

const { spawn } = require("node:child_process");
const { mkdirSync, createWriteStream, existsSync, unlinkSync, symlinkSync } = require("node:fs");
const { join } = require("node:path");
try {
  require("dotenv").config({ path: join(process.cwd(), ".env.local") });
  require("dotenv").config({ path: join(process.cwd(), ".env") });
} catch (err) {
  // If dotenv is missing, continue; Next.js will still load env for its process.
}

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("Usage: with-log-root.js <command> [args...]");
  process.exit(1);
}

const logRootEnv = process.env.LOG_ROOT;
if (!logRootEnv) {
  const passthrough = spawn(args[0], args.slice(1), { stdio: "inherit" });
  passthrough.on("exit", (code) => process.exit(code ?? 0));
  return;
}

function formatLocalDate() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const today = formatLocalDate();
const baseRoot = join(logRootEnv, today, "frontend");
mkdirSync(baseRoot, { recursive: true });

// Maintain var/log/current symlink when possible
try {
  const current = join(logRootEnv, "current");
  if (existsSync(current)) {
    unlinkSync(current);
  }
  symlinkSync(join(logRootEnv, today), current, "dir");
} catch (err) {
  // Non-fatal
}

const allPath = join(baseRoot, "all.log");
const errorPath = join(baseRoot, "error.log");
const allStream = createWriteStream(allPath, { flags: "a" });
const errorStream = createWriteStream(errorPath, { flags: "a" });

const child = spawn(args[0], args.slice(1), { stdio: ["inherit", "pipe", "pipe"] });

let shuttingDown = false;
function forwardSignal(signalName) {
  if (shuttingDown) return;
  shuttingDown = true;
  try {
    child.kill(signalName);
  } catch (_err) {
    // ignore
  }
}

process.on("SIGINT", () => forwardSignal("SIGINT"));
process.on("SIGTERM", () => forwardSignal("SIGTERM"));
process.on("SIGHUP", () => forwardSignal("SIGHUP"));

child.stdout.on("data", (chunk) => {
  process.stdout.write(chunk);
  allStream.write(chunk);
});

child.stderr.on("data", (chunk) => {
  process.stderr.write(chunk);
  allStream.write(chunk);
  errorStream.write(chunk);
});

child.on("exit", (code) => {
  allStream.end();
  errorStream.end();
  process.exit(code ?? 0);
});

process.on("exit", () => {
  // Best-effort: ensure the child doesn't linger if the wrapper is terminated.
  try {
    if (!child.killed) child.kill("SIGTERM");
  } catch (_err) {
    // ignore
  }
});
