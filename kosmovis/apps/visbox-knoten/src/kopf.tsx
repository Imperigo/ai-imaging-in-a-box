/**
 * Visbox-eigen — die Kopfteile der Knotenansicht (Plan UI-Gleichheit S1/S2, Entscheide 115/116,
 * 20.10.2026).
 *
 * In KosmoOrbit setzt `App.tsx` diese Teile unter `bodenDockAusgeblendet` über jede Insel-Station,
 * auch über die Vis-Station, und `main.tsx` legt die Claude-Teile neben die App. **Dieselben Bausteine
 * stehen hier, wortgleich kopiert und in derselben Reihenfolge und Lage** (`app.css`, `island.css`):
 *
 *  - der Hinweis «zu schmal» (`app-schmal-hinweis`, nur unter 700 px sichtbar);
 *  - die Palette am Logo (`WerkzeugPalette`): Klick = Startansicht, aufgefächert «Knoten» (offen) und
 *    «Visbox-Seite» (Entscheid 116 (1));
 *  - der Einstellungs-Kreis (`island-einstellungen-kreis`) — öffnet seit S4 die Einstellungs-Insel
 *    (`einstellungen.tsx`, Schale und Abschnitte wortgleich aus KosmoOrbit);
 *  - der Speichern-Kreis (`SpeichernKreis`) mit der Lage aus `graph-sichern.ts`; ohne Handgriffe, weil
 *    Visbox still auf dem Heim-PC sichert und keine .kosmo-Datei kennt («Öffnen» ist Ausnahme);
 *  - die Zweitgruppe (`InselZweitgruppe`): Heim-PC-Chip in der Optik des Sync-Chips (Klick: «Wer
 *    rechnet?» in der Einstellungs-Insel, Entscheid 116 (5)), Rückgängig, Wiederholen, die Fassung der App; kein Rundgang
 *    (116 (7): er hat keine Vis-Schritte);
 *  - die Claude-Marke mit Karten (`ClaudeAnschluss`), an ihr «Mitschauen und Bedienen» samt Coop und
 *    Vollautomatik (seit Stufe 6 wortgleich die Schalter von dort), der Fensterrahmen der Vollautomatik,
 *    die Erzählzeile und die Maus-Ebene (`KosmoMausEbene`: Figur, Leiste «… bedient — Esc beendet»,
 *    die Sperrzonen gestrichelt, solange eine KI bedient), wie `main.tsx` dort;
 *  - seit S3 das Gesprächsfeld des Assistenten (`VisboxAssistent`): die Kugel steht wortgleich in der
 *    Vis-Station (`KosmoOrb` in `VisWorkspace`), ihr Klick öffnet das Feld (`KosmoPanel`, Stellvertreter
 *    mit der Anatomie von dort). Der Name ist «Assistent» (Entscheid 116 (2), `ASSISTENT_NAME`,
 *    angemeldet über `registriereKosmoName`).
 *
 * Was KosmoOrbit dort zeigt und Visbox nicht hat, steht mit Grund in `kosmovis/UI_AUSNAHMEN.json`;
 * die Probe `tests/test_kosmovis_ui_gleichheit.py` hält beides zusammen.
 */
import { KIcon, StationLogo } from '@kosmo/ui';
import { WerkzeugPalette } from '../../kosmo-orbit/src/shell/werkzeug-palette/WerkzeugPalette';
import { registrierePalettenQuelle, type PalettenGruppe } from '../../kosmo-orbit/src/shell/werkzeug-palette/werkzeug-palette';
import { SpeichernKreis } from '../../kosmo-orbit/src/shell/speichern-kreis/SpeichernKreis';
import { InselZweitgruppe, type InselChip } from '../../kosmo-orbit/src/modules/design/island/InselKopf';
import { ClaudeAnschluss } from '../../kosmo-orbit/src/shell/claude-anschluss/ClaudeAnschluss';
import { ClaudeFensterRahmen } from '../../kosmo-orbit/src/shell/claude-anschluss/ClaudeFensterRahmen';
import { ErzaehlZeile } from '../../kosmo-orbit/src/shell/claude-anschluss/ErzaehlZeile';
import { VollautomatikSchalter } from '../../kosmo-orbit/src/shell/kosmo-maus/KosmoCoop';
import { eigen, KosmoMausFreigabeSchalter } from '../../kosmo-orbit/src/shell/kosmo-maus/KosmoMausSchalter';
import { KosmoMausEbene } from '../../kosmo-orbit/src/shell/kosmo-maus/KosmoMausEbene';
import { modusAus, useKosmoCoop, type VisboxModus } from '../../kosmo-orbit/src/state/kosmo-coop';
import { registriereKosmoName } from '../../kosmo-orbit/src/state/kosmo-name';
import { KosmoPanel } from '../../kosmo-orbit/src/shell/KosmoPanel';
import { useKosmoGespraech, zeigeKosmo } from '../../kosmo-orbit/src/shell/kosmo-gespraech';
import { oeffneEinstellungen } from './einstellungen';
import '../../kosmo-orbit/src/modules/design/island/island.css';
import { OHNE_APP_ASSISTENT, sende, useWirt, type RechnerLage, type WirtZiel } from './wirt-bruecke';

/** Der Name des Assistenten (Entscheid 116 (2)) — derselbe wie im Kern der App (`Knotenwirt.assistentName`). */
export const ASSISTENT_NAME = 'Assistent';

/** Vor dem ersten Bild (`main.tsx`): Kugel, Fensterkopf und Coop-Teile tragen «Assistent» statt «Kosmo». */
export function meldeAssistentAn(): void {
  registriereKosmoName(ASSISTENT_NAME);
}

/** Der Klick auf die Kugel: das Feld auf oder zu (wie `setKosmoOpen` in KosmoOrbit). */
export function wechsleGespraech(): void {
  zeigeKosmo(useKosmoGespraech.getState().ansicht === 'gross' ? 'zu' : 'gross');
}

/** Die Ziele der Palette (Entscheid 116 (1)). «Knoten» ist die offene Fläche. */
export const VISBOX_PALETTE: readonly PalettenGruppe[] = [
  { id: 'knoten', titel: 'Knoten', kurz: 'Knoten', logo: 'vis', station: 'vis', werkzeuge: [] },
  { id: 'visbox-seite', titel: 'Visbox-Seite', kurz: 'Seite', logo: 'doc', station: 'vis', werkzeuge: [], ziel: 'visbox-seite' },
  // «VISBOX EIGENSTÄNDIG», SCHRITT 3 (21.10.2026, Blatt 36): die Mappen am Mac — öffnen, anlegen, «An den Mac
  // holen». Das Fenster ist nativ in der App (die Mappe ist ein Ordner am Mac, nicht Sache des Knotencodes).
  { id: 'mappen', titel: 'Mappen …', kurz: 'Mappen', logo: 'doc', station: 'vis', werkzeuge: [], ziel: 'mappen' },
];

/** Wohin ein Ziel der Palette führt — Unbekanntes zur Startansicht. */
export function zielDerPalette(ziel: string): WirtZiel {
  return ziel === 'visbox-seite' || ziel === 'mappen' ? ziel : 'startansicht';
}

/** Meldet die Ziele an der Palette an — vor dem ersten Bild (`main.tsx`). */
export function meldePaletteAn(): void {
  registrierePalettenQuelle(() => [...VISBOX_PALETTE]);
}

/** Der Chip, solange die App noch nichts gesagt hat. */
export const RECHNER_UNBEKANNT: RechnerLage = { text: 'Heim-PC · …', ton: 'aus' };

export function heimChip(rechner: RechnerLage | null): InselChip {
  const r = rechner ?? RECHNER_UNBEKANNT;
  return { text: r.text, ton: r.ton, label: `${r.text} — «Wer rechnet?» öffnen`, testid: 'heimpc-chip' };
}

/** Der Satz unter den Schaltern je Selbständigkeit — wie die Regel in der App (`Mcpfreigabe`). */
export const MODUS_SATZ: Record<VisboxModus, string> = {
  karte: 'Jede Änderung von Claude und dem Assistenten kommt als Karte zum Anwenden — auch, wenn sie mit eigenem Zeiger klicken.',
  coop: 'Im Coop ändern Claude und der Assistent den Render-Graph ohne Karte; du nimmst es zurück. Löschen und Rendern bleiben Karten.',
  voll: 'Vollautomatik: wie Coop, auch für Pakete. Löschen bleibt eine Karte, die Grafikkarte gibst du am Render-Knoten frei.',
};

/** Der Titel an der Marke — wie KosmoOrbit ohne Ausklapper («Mitschauen und Bedienen»). */
export const MARKE_TITEL = 'Mitschauen und Bedienen';

/**
 * Was an der Claude-Marke aufklappt (Plan KI-Bedienung Stufe 6, 21.10.2026; vorher nur die
 * Selbständigkeit): die Schalter «Mitschauen», «Bedienen» und «Coop – ändert frei» je Agent wortgleich
 * aus KosmoOrbit (`KosmoMausFreigabeSchalter`), darunter «Vollautomatik» und ein Satz zur Regel. Die
 * Selbständigkeit der App gilt fuer beide Agenten zugleich (`setzeCoop` im Stellvertreter) — die zwei
 * Coop-Schalter stehen darum immer gleich. Alle nehmen nur echte Klicks, wie dort.
 */
export function ModusSchalter() {
  const modus = useKosmoCoop((z) => modusAus(z));
  return (
    <div className="kosmo-maus-gruppen" data-testid="visbox-modus" data-modus={modus} {...eigen()}>
      <KosmoMausFreigabeSchalter vorsatz="kosmo-maus" />
      <VollautomatikSchalter />
      <p className="claude-anschluss-hinweis" data-testid="visbox-modus-satz">
        {MODUS_SATZ[modus]}
      </p>
    </div>
  );
}

/** Die Kopfteile in der Wurzel (`.app-wurzel`), wie unter `bodenDockAusgeblendet` in `App.tsx`. */
export function VisboxKopf() {
  const rechner = useWirt((z) => z.rechner);
  const version = useWirt((z) => z.version);
  const sichern = useWirt((z) => z.sichern);
  return (
    <>
      <div className="app-schmal-hinweis" data-testid="schmal-hinweis" role="status">
        Bildschirm zu schmal — bitte am Computer oder iPad öffnen.
      </div>
      <div className="app-werkzeug-palette-lage">
        <WerkzeugPalette
          aktivesModul="vis"
          heimName="Startansicht"
          onZentrale={() => sende({ art: 'oeffne', ziel: 'startansicht' })}
          onStationOeffnen={() => undefined}
          onZielOeffnen={(ziel) => sende({ art: 'oeffne', ziel: zielDerPalette(ziel) })}
          logo={<StationLogo logo="vis" size={30} beschriftung="" />}
        />
      </div>
      <button
        onClick={() => oeffneEinstellungen()}
        className="k-druck isl-einstellungen-kreis"
        aria-label="Einstellungen öffnen"
        title="Einstellungen"
        data-testid="island-einstellungen-kreis"
      >
        <KIcon name="zahnrad" size={16} />
      </button>
      <div className="app-speichern-kreis-lage">
        <SpeichernKreis lage={sichern} />
      </div>
      <InselZweitgruppe
        syncStatus="aus"
        peers={0}
        syncOffen={false}
        version={version ?? ''}
        onSyncToggle={() => oeffneEinstellungen('rechner')}
        chip={heimChip(rechner)}
      />
    </>
  );
}

/** Die Claude-Teile neben der Wurzel, wie `main.tsx` in KosmoOrbit sie neben `<App />` legt. */
export function VisboxClaude() {
  return (
    <>
      <ClaudeAnschluss ausklapper={{ titel: MARKE_TITEL, inhalt: <ModusSchalter /> }} />
      <KosmoMausEbene />
      <ClaudeFensterRahmen />
      <ErzaehlZeile />
    </>
  );
}

/**
 * Das Gesprächsfeld des Assistenten (S3) — in der Wurzel, wie `KosmoPanel` in KosmoOrbit in `<main>`
 * der `.app-wurzel` steht (die Regeln `.app-wurzel:has(.kp-panel--seitenfenster)` brauchen das).
 * Ohne App führt niemand das Gespräch: Das Feld sagt dann, wo es den Assistenten gibt.
 */
export function VisboxAssistent() {
  const offen = useKosmoGespraech((z) => z.ansicht === 'gross');
  if (!offen) return null;
  return <KosmoPanel sichtbar station="vis" onClose={() => zeigeKosmo('zu')} ohneMotorSatz={OHNE_APP_ASSISTENT} />;
}
