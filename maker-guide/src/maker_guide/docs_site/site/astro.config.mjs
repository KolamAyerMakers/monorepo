import { defineConfig } from "astro/config";

export default defineConfig({
  build: { format: "directory" },
  srcDir: "./app",
});
