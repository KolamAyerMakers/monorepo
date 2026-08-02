import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";

const docs = defineCollection({
  loader: glob({ base: "./app/content", pattern: "**/*.md" }),
});

export const collections = { docs };
