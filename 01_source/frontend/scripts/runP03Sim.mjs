import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "..");
const vitestEntry = path.join(frontendRoot, "node_modules", "vitest", "vitest.mjs");

const raw = process.argv.slice(2);
let presencial = false;
const forwarded = [];
for (const a of raw) {
  if (a === "--presencial") presencial = true;
  else forwarded.push(a);
}

const env = { ...process.env };
if (presencial) env.P03_SIM_PRESENCIAL = "1";

const childArgs = [
  vitestEntry,
  "run",
  "src/utils/fiscalSprint3IncidentRunbook.test.js",
  ...forwarded,
];
const r = spawnSync(process.execPath, childArgs, {
  cwd: frontendRoot,
  stdio: "inherit",
  env,
});
process.exit(r.status === null ? 1 : r.status);
