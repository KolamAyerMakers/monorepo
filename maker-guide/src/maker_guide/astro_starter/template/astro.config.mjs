import { defineConfig } from "astro/config";
import { userInfo } from "node:os";

export default defineConfig({
  base: `/~${userInfo().username}/`,
  build: {
    format: "file",
  },
  outDir: process.env.KOLAM_OUTPUT_DIRECTORY ?? "./dist",
  srcDir: "./app",
});
