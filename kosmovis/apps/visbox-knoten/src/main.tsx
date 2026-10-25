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
 * Entscheide 95/95a (14.10.2026, Blatt 25): Diese Seite meldet dem Knoten «Skizze vom iPad» die
 * Skizzen der Mappe an (`registriereSkizzenQuelle(skizzenQuelleDerMappe())`). In KosmoOrbit ruft
 * das niemand, und der Knoten sagt dort, dass es Skizzen vom iPad in Visbox gibt.
 *
 * Entscheid 91 (14.10.2026, Blatt 22): `legeAnfangBeimOeffnen(true)` — eine leere Mappe zeigt den
 * fertigen Anfang (Modell, Auto-Kamera, Stimmung, Prompt → Render → Bildvergleich), mit
 * «Datei laden …» im Modell-Knoten. KosmoOrbit zeigt ihn als Vorschlag mit Knopf.
 *
 * KI-Bedienung Stufe 3 (Entscheide 105–106f, 108, 114, 20.10.2026): `haengeKiAn(window)` stellt
 * den KI-Werkzeugsatz als `window.visboxKi` bereit und reicht seine Ereignisse an die Mac-App
 * (`webkit.messageHandlers.visboxKi`) — nach dem gesicherten Graph, damit Claude den Stand der
 * Mappe liest und nicht den leeren Anfang. Strg+Z nimmt danach nur die eigenen Schritte zurück.
 *
 * Kopfteile (Plan UI-Gleichheit S1/S2, Entscheide 115/116, 20.10.2026), wie `App.tsx` unter
 * `bodenDockAusgeblendet` und `main.tsx` dort: das dunkle Thema vor dem ersten Bild (`legeThema`),
 * in der Wurzel die Kopfteile (`VisboxKopf`: «zu schmal», Palette am Logo, Einstellungs- und
 * Speichern-Kreis, Zweitgruppe mit Heim-PC-Chip), daneben die Claude-Teile (`VisboxClaude`: Marke
 * mit Karten und Selbständigkeit, Fensterrahmen, Erzählzeile). Die zweite Brücke `visboxWirt`
 * (`wirt-bruecke.ts`) bringt, was nur die App weiss — Rechner, Claude-Lage, Fassung, Modus, Thema.
 * Die Mac-Kopfleiste und die KI-Leiste fallen in der Knotenansicht weg.
 *
 * S3/S4 (Plan UI-Gleichheit, 20.10.2026): die Kugel der Vis-Station (wortgleich, `KosmoOrb`) öffnet das
 * Gesprächsfeld des Assistenten (`VisboxAssistent`; das Gespräch führt die Mac-App), der Name
 * «Assistent» ist vor dem ersten Bild angemeldet (`meldeAssistentAn`). Der Einstellungs-Kreis und der
 * Heim-PC-Chip öffnen die Einstellungs-Insel (`VisboxEinstellungen`). Die Assistent-Leiste der Mac-App
 * fällt in der Knotenansicht weg.
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
import { setzeBlattDa } from '../../kosmo-orbit/src/modules/vis/bild-ablage-kern';
import { registriereExportStamm } from '../../kosmo-orbit/src/modules/vis/bild-ablage';
import { registriereSkizzenQuelle } from '../../kosmo-orbit/src/modules/vis/skizze-quelle';
import { registriereStandpunkteAbfrage } from '../../kosmo-orbit/src/modules/vis/heim-standpunkte';
import { haengeVerlaufKurztastenAn } from './kurztasten';
import { graphDerNeuenMappe, ladeGesichertenGraph, sichereBeiAenderung } from './graph-sichern';
import { haengeKiAn } from './ki-wirt';
import { haengeWirtAn, meldeSichern } from './wirt-bruecke';
import { legeThema } from './thema';
import { meldeAssistentAn, meldePaletteAn, VisboxAssistent, VisboxClaude, VisboxKopf, wechsleGespraech } from './kopf';
import { VisboxEinstellungen } from './einstellungen';
import { haengeAnWerkzeugsatz } from '../../kosmo-orbit/src/state/claude-anschluss';
import { haengeAnKiVerlauf } from '../../kosmo-orbit/src/state/kosmo-coop';
import {
  aufDemVisboxServer,
  brueckeAufDiesenServer,
  imEigenenSchema,
  brueckeSagtDenSatz,
  koerperAlsBytes,
  ladeMappe,
  ladeWirt,
  nimmFertigesLadenAn,
  offeneMappeName,
  registriereMappenWechsel,
  skizzenQuelleDerMappe,
  standpunkteAbfrageDerMappe,
  verfolge,
  type LadeSicht,
} from './mappe';
import './visbox.css';

function VisboxKnoten() {
  // Wie App.tsx dort: `revision` abonniert, damit die Marke umspringt, sobald die Mappe da ist.
  const revision = useProject((s) => s.revision);
  void revision;
  return (
    <div className="app-wurzel" data-station="vis">
      <VisboxKopf />
      <main className="visbox-buehne">
        <KFehlerzone bereich="KosmoVis">
          <div
            className="k-einblenden app-station-huelle"
            data-vis-aktives-projekt={szeneBauteileAnzahl(useProject.getState().doc) > 0 ? 'ja' : 'nein'}
          >
            <VisWorkspace onKosmoOeffnen={wechsleGespraech} />
          </div>
        </KFehlerzone>
        <VisboxAssistent />
      </main>
      <VisboxEinstellungen />
      <KMeldungen />
      <KAnsageBereich />
      <KBestaetigung />
    </div>
  );
}

// Gemerkte Schriftgrösse und Bewegung vor dem ersten Bild an <html>, sonst springt die Schrift.
ladeAnzeige();
// Das Thema wie KosmoOrbit (Vorgabe «orbit», dunkel) — vor dem ersten Bild, sonst blitzt es hell.
legeThema();
// Die Ziele der Palette am Logo: «Knoten» und «Visbox-Seite» statt der Stationen von KosmoOrbit.
meldePaletteAn();
// Der Name des Assistenten an Kugel, Fensterkopf und Coop-Teilen (Entscheid 116 (2)).
meldeAssistentAn();

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
// Bild aufs Blatt (Video-Befunde L4-16/L3-A4, 21.10.2026): Visbox hat kein Blatt und kein Projekt, das Bilder behaelt —
// kein Ablegen ins Projekt, in der grossen Ansicht nur «Exportieren» (Ausnahme in UI_AUSNAHMEN.json, werkzeug_ausnahmen).
setzeBlattDa(false);
// Gegenprobe 328 (S9): Der exportierte Name beginnt mit der Mappe («gegenprobe-Lauf-2-sSE.png»), nicht mit dem
// Projektnamen des Dokuments — der heisst in Visbox immer «Unbenannt».
registriereExportStamm(offeneMappeName);

// AUF DEM VISBOX-SERVER: Brücke hierher, dann das Modell der Mappe. Im Entwicklungsserver
// (`npm run dev`) gibt es beides nicht — die Ansicht läuft dann leer, wie ohne Mappe.

// IN DER MAC-APP (eigenes Adressschema, Schritt 1 von «Visbox eigenständig»): jeder Rumpf als
// fertige Bytes, bevor die App ihn an den Heim-PC weiterreicht (`koerperAlsBytes`). Seit Schritt 2:
// Ohne Rechner steht am Render-Knoten der Satz der App, nicht «antwortet mit: 503»
// (`brueckeSagtDenSatz`).
if (imEigenenSchema()) {
  window.fetch = brueckeSagtDenSatz(koerperAlsBytes(window.fetch.bind(window)));
}

if (aufDemVisboxServer()) {
  brueckeAufDiesenServer();
  registriereModellLaden(ladeWirt());
  registriereSkizzenQuelle(skizzenQuelleDerMappe());
  // Bauplan «Neue Knoten» F2: die Kegel des Knotens «Kamera» mit seinen Einstellungen.
  registriereStandpunkteAbfrage(standpunkteAbfrageDerMappe());
  // Generalprobe 327 (S2): nach «Datei laden …» in eine andere Mappe deren Graph (oder der fertige
  // Anfang) — vorher erst nach dem Neuladen der Seite.
  registriereMappenWechsel(() => graphDerNeuenMappe());
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
      } else {
        // BEFUND «ANDERE DATEI» (Mac 0.3.67): fertig am Heim-PC, aber nicht in der Mappe am Mac → nachholen.
        const nachgeholt = await nimmFertigesLadenAn(sicht.laden);
        if (nachgeholt) setzeModellLadeZustand(nachgeholt);
      }
    })
    .catch(() => {
      // Ohne Antwort bleibt der Knopf mit leerer Formatliste; das Laden selbst sagt dann,
      // woran es liegt.
    });
}

// DER GRAPH UEBERSTEHT DAS NEULADEN (15.10.2026, auf-20261015-286): erst den gesicherten Graph
// der Mappe legen, dann das erste Bild — sonst legte der fertige Anfang einen zweiten an.
async function zeige(): Promise<void> {
  if (aufDemVisboxServer()) {
    await ladeGesichertenGraph();
    sichereBeiAenderung(undefined, undefined, meldeSichern);
  }
  haengeKiAn(window);
  // Die Claude-Teile lesen die Karten, die Tätigkeit und die Schritte ohne Karte des Werkzeugsatzes.
  haengeAnWerkzeugsatz();
  haengeAnKiVerlauf();
  // Zuletzt die zweite Brücke: «bereit» an die App, die mit ihrer Lage antwortet.
  haengeWirtAn(window);
  const wurzel = document.getElementById('root');
  if (!wurzel) throw new Error('Kein #root in index.html');
  createRoot(wurzel).render(
    <StrictMode>
      <VisboxKnoten />
      <VisboxClaude />
    </StrictMode>,
  );
}
void zeige();
