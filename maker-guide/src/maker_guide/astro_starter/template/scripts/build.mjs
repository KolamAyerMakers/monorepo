import { chmod, mkdtemp, rm } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";
import { spawn } from "node:child_process";

import { buildCodex } from "./codex.mjs";
import { publish } from "./publish.mjs";

const projectDirectory = process.cwd();
const homeDirectory = homedir();
const outputDirectory = join(homeDirectory, "public_html");
const stagingDirectory = await mkdtemp(join(homeDirectory, ".public_html-"));
const previousDirectory = join(homeDirectory, ".public_html-previous");

const run = (command, commandArguments, options = {}) => new Promise((resolve, reject) => {
  const child = spawn(command, commandArguments, options);
  child.on("error", reject);
  child.on("exit", (status) => status === 0 ? resolve() : reject(new Error(`${command} exited ${status}`)));
});

try {
  await run(join(projectDirectory, "node_modules", ".bin", "astro"), ["build"], {
    cwd: projectDirectory,
    env: {
      ...process.env,
      ASTRO_TELEMETRY_DISABLED: "1",
      KOLAM_OUTPUT_DIRECTORY: stagingDirectory,
    },
    stdio: "inherit",
  });
  await buildCodex(stagingDirectory);
  await chmod(stagingDirectory, 0o755);
  await publish(stagingDirectory, outputDirectory, previousDirectory);
} catch (error) {
  await rm(stagingDirectory, { force: true, recursive: true }).catch(() => {});
  throw error;
}
