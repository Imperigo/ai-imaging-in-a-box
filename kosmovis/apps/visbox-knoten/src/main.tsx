/**
 * Visbox-eigen — die Wirtsseite der Knotenansicht (E26, 24.09.2026).
 *
 * Startet das aus KosmoOrbit kopierte Vis-Werkzeug so, wie `App.tsx` dort die Vis-Station
 * startet: dieselbe Wurzel (`.app-wurzel[data-station='vis']`), dieselbe Stationshülle,
 * dieselben drei Wirte für Meldungen, Ansagen und Bestätigungen. Alles Weitere ist die
 * Kopie selbst. Diese Datei geht im Februar NICHT mit zurück — dort ist `App.tsx` der Wirt.
 *
 * Runde 26 (14.10.2026) wie `main.tsx`/`App.tsx` dort: die Bewegungs-Tokens an der Wurzel
 * (`@kosmo/ui/bewegung.css`), die gemerkte Schriftgrösse und Bewegung vor dem ersten Bild
 * (`ladeAnzeige`), und an der Stationshülle `data-vis-aktives-projekt` — ob das Modell der
 * Mappe im Dokument angekommen ist, mit derselben Zählung wie die Render-Sperre.
 *
 * Entscheid 90 (14.10.2026, Blatt 21): Auf dem Visbox-Server stellt diese Seite dem
 * Modell-Knoten die Lade-Fähigkeit bereit (`registriereModellLaden(ladeWirt(…))`) — vor dem
 * ersten Bild, damit der Knoten gleich in seiner Höhe mit Knopf steht. In KosmoOrbit ruft das
 * niemand, und der Knoten bleibt die eine Zeile von dort.
 *
 * Entscheid 91 (14.10.2026, Blatt 22): `legeAnfangBeimOeffnen(true)` — eine leere Mappe zeigt den
 * fertigen Anfang (Modell, Auto-Kamera, Stimmung, Prompt → Render → Bildvergleich), mit
 * «Datei laden …» im Modell-Knoten. KosmoOrbit zeigt ihn als Vorschlag mit Knopf.
 */
import '../../kosmo-orbit/src/zod-jitless'; // muss der erste Import bleiben, s. Datei-Kopf dort
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '@kosmo/ui/aura.css';
import '@kosmo/ui/bewegung.css'; // wie main.tsx dort: an die Wurzel, nicht je Station
import '@kosmo/ui/skizze-tokens.css';
import '@kosmo/ui/skizze-motion.css';
import '../../kosmo-orbit/src/fonts.css';
import '../../kosmo-orbit/src/app.css';
import { KAnsageBereich, KBestaetigung, KFehlerzone, KMeldungen, ladeAnzeige, melde } from '@kosmo/ui';
import { VisWorkspace } from '../../kosmo-orbit/src/modules/vis/VisWorkspace';
import { szeneBauteileAnzahl } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { registriereModellLaden, setzeModellLadeZustand } from '../../kosmo-orbit/src/modules/vis/modell-laden';
import { legeAnfangBeimOeffnen } from '../../kosmo-orbit/src/modules/vis/start-graph';
import { haengeVerlaufKurztastenAn } from './kurztasten';
import { aufDemVisboxServer, brueckeAufDiesenServer, ladeMappe, ladeWirt, verfolge, type LadeSicht } from './mappe';
import './visbox.css';

function VisboxKnoten() {
  // Wie App.tsx dort: `revision` abonniert, damit die Marke umspringt, sobald die Mappe da ist.
  const revision = useProject((s) => s.revision);
  void revision;
  return (
    <div className="app-wurzel" data-station="vis">
      <main className="visbox-buehne">
        <KFehlerzone bereich="KosmoVis">
          <div
            className="k-einblenden app-station-huelle"
            data-vis-aktives-projekt={szeneBauteileAnzahl(useProject.getState().doc) > 0 ? 'ja' : 'nein'}
          >
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

// Gemerkte Schriftgrösse und Bewegung vor dem ersten Bild an <html>, sonst springt die Schrift.
ladeAnzeige();

// STRG+Z / ⌘Z (auf-20261014-284 D5): In KosmoOrbit haengt das Kuerzel am Hauptprogramm, das
// nicht kopiert ist — hier darum der Wirt selbst (`kurztasten.ts`).
haengeVerlaufKurztastenAn(window, {
  undo: () => useProject.getState().undo(),
  redo: () => useProject.getState().redo(),
});

// ENTSCHEID 91 (Blatt 22): Die Knotenansicht beginnt mit dem fertigen Anfang statt «Noch kein
// Render-Graph» — hier von selbst, weil das Dokument nur in dieser Seite lebt (kein Tresor, keine
// Mitarbeitenden; Begruendung im Kopf von `start-graph.ts`). Auch im Entwicklungsserver.
legeAnfangBeimOeffnen(true);

// AUF DEM VISBOX-SERVER: Brücke hierher, dann das Modell der Mappe. Im Entwicklungsserver
// (`npm run dev`) gibt es beides nicht — die Ansicht läuft dann leer, wie ohne Mappe.

if (aufDemVisboxServer()) {
  brueckeAufDiesenServer();
  registriereModellLaden(ladeWirt());
  void ladeMappe()
    .then((satz) => melde(satz))
    .catch((fehler: unknown) => melde(`Die Mappe liess sich nicht laden: ${String(fehler)}`, { ton: 'fehler' }))
    .then(() => fetch('./modell-laden'))
    .then(async (antwort) => {
      if (!antwort.ok) return;
      const sicht = (await antwort.json()) as LadeSicht;
      registriereModellLaden(ladeWirt(sicht));
      // LAEUFT SCHON EINES (die Seite wurde waehrend einer IFC neu geladen): weiter verfolgen.
      if (sicht.laden?.stand === 'laeuft') {
        setzeModellLadeZustand(await verfolge(sicht.laden, setzeModellLadeZustand));
      }
    })
    .catch(() => {
      // Ohne Antwort bleibt der Knopf mit leerer Formatliste; das Laden selbst sagt dann,
      // woran es liegt.
    });
}

const wurzel = document.getElementById('root');
if (!wurzel) throw new Error('Kein #root in index.html');
createRoot(wurzel).render(
  <StrictMode>
    <VisboxKnoten />
  </StrictMode>,
);
