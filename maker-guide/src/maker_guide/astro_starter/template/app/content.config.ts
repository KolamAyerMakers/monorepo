import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const pages = defineCollection({
  loader: glob({
    base: new URL("../pages", import.meta.url).pathname,
    pattern: "**/*.md",
  }),
  schema: z.object({
    title: z.string().optional(),
  }),
});

export const collections = { pages };
