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
 *  - seit dem 22.10.2026 (Entscheide 132/133, Blätter 47/48, Kleinauftrag vor der Demo) die zwei Zeichen von
 *    Visbox: am Logo der Palette die Visbox-Box (`VisboxLogo`) statt der Kosmo-Spirale, an der Kugel unten
 *    rechts das Lot statt der roten Kugel — das Lot allein über `visbox.css`, ohne Eingriff in die Kopie.
 *
 * Was KosmoOrbit dort zeigt und Visbox nicht hat, steht mit Grund in `kosmovis/UI_AUSNAHMEN.json`;
 * die Probe `tests/test_kosmovis_ui_gleichheit.py` hält beides zusammen.
 */
import { KIcon } from '@kosmo/ui';
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

/**
 * Das Logo von Visbox am Kopf der Palette (Entscheid 132, Blatt 47; Owner-Ausnahme von Entscheid 115): die Box
 * aus dem App-Symbol (`ipad/Marke/visbox-icon.svg`), ohne die Linie, die in 30 px nicht mehr lesbar ist. Die
 * Palette dahinter bleibt wortgleich — nur das Zeichen, das sie trägt, ist das von Visbox.
 */
export function VisboxLogo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" aria-hidden="true" data-testid="visbox-logo" data-logo="visbox">
      <rect width="1024" height="1024" rx="228" fill="#12161c" />
      <path
        d="M512 210 L790 360 L790 664 L512 814 L234 664 L234 360 Z M234 360 L512 510 L790 360 M512 510 L512 814"
        fill="none"
        stroke="#e8eaed"
        strokeWidth="56"
        strokeLinejoin="round"
      />
      <path d="M512 510 L790 360 L790 664 L512 814 Z" fill="#2f6fd6" />
    </svg>
  );
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

/** Der Name jeder Selbständigkeit — derselbe wie am Schalter («Coop – ändert frei», «Vollautomatik»). */
export const MODUS_NAME: Record<VisboxModus, string> = { karte: 'Karte', coop: 'Coop', voll: 'Vollautomatik' };

/**
 * Der Satz unter den Schaltern je Selbständigkeit — wie die Regel in der App (`Mcpfreigabe`). **Eine Quelle:**
 * Schalter und Satz lesen beide `modusAus(useKosmoCoop)`; der Satz beginnt mit dem Namen des Modus, damit er
 * nie für einen anderen Modus stehen bleibt (Bildschirmfoto des Owners, 0.3.54: «kommt als Karte» bei
 * eingeschalteter Vollautomatik). Ändert sich die Regel (Vollautomatik ohne Klick), ändert sich nur dieser Satz.
 */
export const MODUS_SATZ: Record<VisboxModus, string> = {
  karte: 'Karte: Jede Änderung von Claude und dem Assistenten kommt als Karte zum Anwenden — auch, wenn sie mit eigenem Zeiger klicken.',
  coop: 'Coop: Claude und der Assistent ändern den Render-Graph ohne Karte; du nimmst es zurück. Löschen und Rendern bleiben Karten.',
  // Entscheid 155 (27.10.2026): auch der eigene Klick in der Knotenansicht rechnet in «Voll» ohne «Freigeben».
  voll: 'Vollautomatik: Claude und der Assistent wenden ihre Vorschläge selbst an und rechnen Bilder ohne Freigabe — deine Klicks in der Knotenansicht auch. Karten bleiben: Löschen, Modelle mit offener Lizenz und mehr als 5 Läufe pro Stunde.',
};

/** Der Titel an der Marke — wie KosmoOrbit ohne Ausklapper («Mitschauen und Bedienen»). */
export const MARKE_TITEL = 'Mitschauen und Bedienen';

/**
 * Was an der Claude-Marke aufklappt (Plan KI-Bedienung Stufe 6, 21.10.2026; vorher nur die
 * Selbständigkeit): die Schalter «Mitschauen», «Bedienen» und «Coop – ändert frei» je Agent wortgleich
 * aus KosmoOrbit (`KosmoMausFreigabeSchalter`), darunter «Vollautomatik» und EIN Satz zur Regel. Die
 * Selbständigkeit der App gilt fuer beide Agenten zugleich (`setzeCoop` im Stellvertreter) — die zwei
 * Coop-Schalter stehen darum immer gleich. Alle nehmen nur echte Klicks, wie dort.
 *
 * Layout (Bildschirmfoto des Owners, 0.3.54): Die Hülle ist eine eigene Spalte (`visbox-modus`), nicht
 * noch einmal das Zwei-Spalten-Raster `kosmo-maus-gruppen` — sonst lagen beide Agenten in einer halben
 * Spalte, die Schalter über ihren Wörtern und «Coop – ändert frei» Wort für Wort umbrochen. Breite und
 * Umbruch regelt `visbox.css`; der feste Erklärtext der Vollautomatik aus KosmoOrbit tritt dort zurück,
 * damit nur der Satz je Modus steht.
 */
export function ModusSchalter() {
  const modus = useKosmoCoop((z) => modusAus(z));
  return (
    <div className="visbox-modus" data-testid="visbox-modus" data-modus={modus} {...eigen()}>
      <KosmoMausFreigabeSchalter vorsatz="kosmo-maus" />
      <VollautomatikSchalter />
      <p className="claude-anschluss-hinweis" data-testid="visbox-modus-satz" data-modus={modus}>
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
          logo={<VisboxLogo size={30} />}
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
