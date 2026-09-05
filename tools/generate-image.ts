#!/usr/bin/env bun
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const script = fileURLToPath(new URL("../scripts/openrouter_image.py", import.meta.url));
const args = process.argv.slice(2).map(arg => arg === "--reasoning-trace" ? "--reasoning-include-trace" : arg);
const result = spawnSync(process.env.PYTHON || "python3", [script, "generate", ...(args.length ? args : ["--help"])], { stdio: "inherit" });
if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
