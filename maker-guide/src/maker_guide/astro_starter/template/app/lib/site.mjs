import { readFileSync } from "node:fs";
import { userInfo } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

const courseHostname = "lf2607.kolamayermakers.org";

const readProjection = (handle, name) => {
  try {
    return readFileSync(join("/makers", handle, name), "utf8").trim() || "Not available yet";
  } catch {
    return "Not available yet";
  }
};

const readQuestProgress = (handle) => {
  try {
    return JSON.parse(readFileSync(join("/makers", handle, "quests.json"), "utf8"));
  } catch {
    return { completed: [], remaining: [], total: 0 };
  }
};

const readObjectiveProgress = (handle) => {
  try {
    return JSON.parse(readFileSync(join("/makers", handle, "objectives.json"), "utf8"));
  } catch {
    return { completed: [], total: 0 };
  }
};

const readSessionProgress = (handle) => {
  try {
    return JSON.parse(readFileSync(join("/makers", handle, "sessions.json"), "utf8"));
  } catch {
    return { reached: [], remaining: [] };
  }
};

export const learnerProgress = () => {
  const handle = userInfo().username;
  return {
    handle,
    rank: readProjection(handle, "rank"),
    score: readProjection(handle, "score"),
    sessions: readSessionProgress(handle),
    tier: readProjection(handle, "tier"),
    quests: readQuestProgress(handle),
    objectives: readObjectiveProgress(handle),
  };
};

export const webring = () => {
  const { handle } = learnerProgress();
  try {
    if (!/^webring\s*=\s*true\s*$/m.test(readFileSync("site.toml", "utf8"))) {
      return null;
    }
    const members = execFileSync("/usr/bin/getent", ["group", "linux-foundations"], {
      encoding: "utf8",
    })
      .trim()
      .split(":")[3]
      .split(",")
      .filter(Boolean)
      .sort();
    const position = members.indexOf(handle);
    if (position === -1 || members.length < 2) {
      return null;
    }
    const previous = members[(position - 1 + members.length) % members.length];
    const next = members[(position + 1) % members.length];
    return {
      next,
      previous,
      url: (member) => `https://${courseHostname}/~${member}/`,
    };
  } catch {
    return null;
  }
};
