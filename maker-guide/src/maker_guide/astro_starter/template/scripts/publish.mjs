import { rename, rm } from "node:fs/promises";

export const publish = async (
  stagingDirectory,
  outputDirectory,
  previousDirectory,
  move = rename,
  remove = rm,
) => {
  let previousSiteMoved = false;
  try {
    await remove(previousDirectory, { force: true, recursive: true });
    try {
      await move(outputDirectory, previousDirectory);
      previousSiteMoved = true;
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    try {
      await move(stagingDirectory, outputDirectory);
    } catch (error) {
      if (previousSiteMoved) {
        try {
          await move(previousDirectory, outputDirectory);
        } catch {
          // Keep the recovery directory when restoring it fails.
        }
      }
      throw error;
    }
    await remove(previousDirectory, { force: true, recursive: true }).catch(() => {});
  } finally {
    await remove(stagingDirectory, { force: true, recursive: true }).catch(() => {});
  }
};
