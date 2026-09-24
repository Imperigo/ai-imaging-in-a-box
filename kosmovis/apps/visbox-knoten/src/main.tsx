/**
 * Visbox-eigen — die Wirtsseite der Knotenansicht (E26, 24.09.2026).
 *
 * Startet das aus KosmoOrbit kopierte Vis-Werkzeug so, wie `App.tsx` dort die Vis-Station
 * startet: dieselbe Wurzel (`.app-wurzel[data-station='vis']`), dieselbe Stationshülle,
 * dieselben drei Wirte für Meldungen, Ansagen und Bestätigungen. Alles Weitere ist die
 * Kopie selbst. Diese Datei geht im Februar NICHT mit zurück — dort ist `App.tsx` der Wirt.
 */
import '../../kosmo-orbit/src/zod-jitless'; // muss der erste Import bleiben, s. Datei-Kopf dort
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '@kosmo/ui/aura.css';
import '@kosmo/ui/skizze-tokens.css';
import '@kosmo/ui/skizze-motion.css';
import '../../kosmo-orbit/src/fonts.css';
import '../../kosmo-orbit/src/app.css';
import { KAnsageBereich, KBestaetigung, KFehlerzone, KMeldungen } from '@kosmo/ui';
import { melde } from '@kosmo/ui';
import { VisWorkspace } from '../../kosmo-orbit/src/modules/vis/VisWorkspace';
import { aufDemVisboxServer, brueckeAufDiesenServer, ladeMappe } from './mappe';
import './visbox.css';

function VisboxKnoten() {
  return (
    <div className="app-wurzel" data-station="vis">
      <main className="visbox-buehne">
        <KFehlerzone bereich="KosmoVis">
          <div className="k-einblenden app-station-huelle">
            <VisWorkspace />
          </div>
        </KFehlerzone>
      </main>
      <KMeldungen />
      <KAnsageBereich />
      <KBestaetigung />
    </div>
  );
}

// AUF DEM VISBOX-SERVER: Brücke hierher, dann das Modell der Mappe. Im Entwicklungsserver
// (`npm run dev`) gibt es beides nicht — die Ansicht läuft dann leer, wie ohne Mappe.
if (aufDemVisboxServer()) {
  brueckeAufDiesenServer();
  void ladeMappe()
    .then((satz) => melde(satz))
    .catch((fehler: unknown) => melde(`Die Mappe liess sich nicht laden: ${String(fehler)}`, { ton: 'fehler' }));
}

const wurzel = document.getElementById('root');
if (!wurzel) throw new Error('Kein #root in index.html');
createRoot(wurzel).render(
  <StrictMode>
    <VisboxKnoten />
  </StrictMode>,
);
