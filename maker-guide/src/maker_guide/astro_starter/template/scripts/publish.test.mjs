import assert from "node:assert/strict";
import { access, mkdtemp, readFile, rename, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { publish } from "./publish.mjs";

const homeDirectory = await mkdtemp(join(tmpdir(), "maker-guide-publish-"));
const outputDirectory = join(homeDirectory, "public_html");
const stagingDirectory = join(homeDirectory, ".public_html-staging");
const previousDirectory = join(homeDirectory, ".public_html-previous");
const publicationFailure = new Error("final rename failed");

try {
  await writeFile(outputDirectory, "previous site");
  await writeFile(stagingDirectory, "new site");
  await assert.rejects(
    publish(stagingDirectory, outputDirectory, previousDirectory, async (source, destination) => {
      if (source === stagingDirectory && destination === outputDirectory) throw publicationFailure;
      await rename(source, destination);
    }),
    (error) => error === publicationFailure,
  );
  assert.equal(await readFile(outputDirectory, "utf8"), "previous site");
  await assert.rejects(access(stagingDirectory));
  await assert.rejects(access(previousDirectory));
} finally {
  await rm(homeDirectory, { force: true, recursive: true });
}

const cleanupHomeDirectory = await mkdtemp(join(tmpdir(), "maker-guide-publish-"));
const cleanupOutputDirectory = join(cleanupHomeDirectory, "public_html");
const cleanupStagingDirectory = join(cleanupHomeDirectory, ".public_html-staging");
const cleanupPreviousDirectory = join(cleanupHomeDirectory, ".public_html-previous");
let previousCleanupAttempts = 0;

try {
  await writeFile(cleanupOutputDirectory, "previous site");
  await writeFile(cleanupStagingDirectory, "new site");
  await publish(
    cleanupStagingDirectory,
    cleanupOutputDirectory,
    cleanupPreviousDirectory,
    rename,
    async (directory, options) => {
      if (directory === cleanupPreviousDirectory && ++previousCleanupAttempts === 2) {
        throw new Error("recovery cleanup failed");
      }
      await rm(directory, options);
    },
  );
  assert.equal(await readFile(cleanupOutputDirectory, "utf8"), "new site");
  assert.equal(await readFile(cleanupPreviousDirectory, "utf8"), "previous site");
} finally {
  await rm(cleanupHomeDirectory, { force: true, recursive: true });
}
