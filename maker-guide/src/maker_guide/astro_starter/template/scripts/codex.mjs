import { mkdtemp, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { homedir, userInfo } from "node:os";
import { join, relative } from "node:path";
import { spawn } from "node:child_process";

const run = (command, commandArguments, options = {}) => new Promise((resolve, reject) => {
  const child = spawn(command, commandArguments, { stdio: "inherit", ...options });
  child.on("error", reject);
  child.on("exit", (status) => status === 0 ? resolve() : reject(new Error(`${command} exited ${status}`)));
});

const markdownFence = (content) => "`".repeat(Math.max(3, ...[...content.matchAll(/`+/g)].map((match) => match[0].length + 1)));

const appendFiles = async (sections, directory, heading) => {
  try {
    for (const name of (await readdir(directory)).sort()) {
      const path = join(directory, name);
      const content = await readFile(path, "utf8");
      const fence = markdownFence(content);
      sections.push(`## ${heading}: ${name}\n\n${fence}\n${content}\n${fence}\n`);
    }
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
};

export const buildCodex = async (outputDirectory) => {
  const homeDirectory = homedir();
  const handle = userInfo().username;
  const temporaryDirectory = await mkdtemp(join(homeDirectory, ".codex-"));
  try {
    const sections = [`% ${handle}'s Codex\n% Kolam Ayer Makers\n\n# Pages\n`];
    await appendFiles(sections, join(homeDirectory, "src", "pages"), "Page");
    await appendFiles(sections, join(homeDirectory, "bin"), "Script");
    await appendFiles(sections, join("/makers", handle, "citations"), "Citation");
    const sourcePath = join(temporaryDirectory, "codex.md");
    await writeFile(sourcePath, sections.join("\n"), "utf8");
    await run("pandoc", [
      "--from=markdown-raw_html-raw_tex",
      "--pdf-engine=xelatex",
      "--output",
      join(outputDirectory, `${handle}-codex.pdf`),
      sourcePath,
    ]);
  } finally {
    await rm(temporaryDirectory, { force: true, recursive: true });
  }
};
