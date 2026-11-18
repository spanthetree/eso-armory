import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

const backend = 'http://localhost:5000';

export default defineConfig({
  plugins: [svelte()],
  // Built files are served by FastAPI's existing /static mount.
  base: '/static/dist/',
  build: { outDir: '../static/dist', emptyOutDir: true },
  server: {
    proxy: {
      '/api': backend,
      '/events': backend,
      '/assets': backend,
      '/esoicons': backend,
    },
  },
});
