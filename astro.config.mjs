// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

// ...existing code...
export default defineConfig({
  integrations: [react()],
  // ...other config...
});