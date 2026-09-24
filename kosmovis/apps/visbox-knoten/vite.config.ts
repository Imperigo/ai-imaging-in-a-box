import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Visbox-eigen. `publicDir` zeigt auf die kopierten Schriften der KosmoOrbit-App, damit
// `fonts.css` sie unter `/fonts/…` findet wie im Original. `base: './'` erlaubt, den Bau
// unter einem Unterpfad des Visbox-Servers auszuliefern.
export default defineConfig({
  base: './',
  publicDir: '../kosmo-orbit/public',
  define: {
    __APP_VERSION__: JSON.stringify('0.1.4-visbox'),
  },
  plugins: [react()],
});
