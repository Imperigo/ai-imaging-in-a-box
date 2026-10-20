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
 *  - der Einstellungs-Kreis (`island-einstellungen-kreis`) — öffnet bis S4 die Einstellungen der App;
 *  - der Speichern-Kreis (`SpeichernKreis`) mit der Lage aus `graph-sichern.ts`; ohne Handgriffe, weil
 *    Visbox still auf dem Heim-PC sichert und keine .kosmo-Datei kennt («Öffnen» ist Ausnahme);
 *  - die Zweitgruppe (`InselZweitgruppe`): Heim-PC-Chip in der Optik des Sync-Chips (Klick: «Wer
 *    rechnet?», Entscheid 116 (5)), Rückgängig, Wiederholen, die Fassung der App; kein Rundgang
 *    (116 (7): er hat keine Vis-Schritte);
 *  - die Claude-Marke mit Karten (`ClaudeAnschluss`), an ihr die Selbständigkeit (der Modus-Schalter),
 *    der Fensterrahmen der Vollautomatik und die Erzählzeile.
 *
 * Was KosmoOrbit dort zeigt und Visbox nicht hat, steht mit Grund in `kosmovis/UI_AUSNAHMEN.json`;
 * die Probe `tests/test_kosmovis_ui_gleichheit.py` hält beides zusammen.
 */
import { KIcon, KSwitch, StationLogo } from '@kosmo/ui';
import { WerkzeugPalette } from '../../kosmo-orbit/src/shell/werkzeug-palette/WerkzeugPalette';
import { registrierePalettenQuelle, type PalettenGruppe } from '../../kosmo-orbit/src/shell/werkzeug-palette/werkzeug-palette';
import { SpeichernKreis } from '../../kosmo-orbit/src/shell/speichern-kreis/SpeichernKreis';
import { InselZweitgruppe, type InselChip } from '../../kosmo-orbit/src/modules/design/island/InselKopf';
import { ClaudeAnschluss } from '../../kosmo-orbit/src/shell/claude-anschluss/ClaudeAnschluss';
import { ClaudeFensterRahmen } from '../../kosmo-orbit/src/shell/claude-anschluss/ClaudeFensterRahmen';
import { ErzaehlZeile } from '../../kosmo-orbit/src/shell/claude-anschluss/ErzaehlZeile';
import { VollautomatikSchalter } from '../../kosmo-orbit/src/shell/kosmo-maus/KosmoCoop';
import { eigen } from '../../kosmo-orbit/src/shell/kosmo-maus/KosmoMausSchalter';
import { modusAus, setzeCoop, useKosmoCoop, type VisboxModus } from '../../kosmo-orbit/src/state/kosmo-coop';
import '../../kosmo-orbit/src/modules/design/island/island.css';
import { sende, useWirt, type RechnerLage } from './wirt-bruecke';

/** Die Ziele der Palette (Entscheid 116 (1)). «Knoten» ist die offene Fläche. */
export const VISBOX_PALETTE: readonly PalettenGruppe[] = [
  { id: 'knoten', titel: 'Knoten', kurz: 'Knoten', logo: 'vis', station: 'vis', werkzeuge: [] },
  { id: 'visbox-seite', titel: 'Visbox-Seite', kurz: 'Seite', logo: 'doc', station: 'vis', werkzeuge: [], ziel: 'visbox-seite' },
];

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
  karte: 'Jede Änderung von Claude kommt als Karte zum Anwenden.',
  coop: 'Im Coop ändert Claude den Render-Graph ohne Karte; du nimmst es unten links zurück. Löschen und Rendern bleiben Karten.',
  voll: 'Vollautomatik: wie Coop, auch für Pakete. Löschen bleibt eine Karte, die Grafikkarte gibst du am Render-Knoten frei.',
};

/**
 * Der Modus-Schalter an der Claude-Marke: «Coop – ändert frei» und «Vollautomatik» aus KosmoOrbit,
 * zusammen die Selbständigkeit der App (Karte | Coop | Voll). Nimmt nur echte Klicks, wie dort.
 */
export function ModusSchalter() {
  const coop = useKosmoCoop((z) => z.an.claude);
  const modus = useKosmoCoop((z) => modusAus(z));
  return (
    <div className="kosmo-maus-gruppen" data-testid="visbox-modus" data-modus={modus} {...eigen()}>
      <fieldset className="kosmo-maus-gruppe" data-urheber="claude">
        <legend className="kosmo-maus-gruppe-name">Claude</legend>
        <KSwitch
          className="kosmo-maus-schalter-zeile"
          role="switch"
          label="Coop – ändert frei"
          aria-label="Claude: Coop – ändert das Projekt ohne Karte"
          data-testid="kosmo-maus-freigabe-claude-coop"
          checked={coop}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            if (!e.nativeEvent.isTrusted) return;
            setzeCoop('claude', e.target.checked);
          }}
        />
      </fieldset>
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
          onZielOeffnen={(ziel) => sende({ art: 'oeffne', ziel: ziel === 'visbox-seite' ? 'visbox-seite' : 'startansicht' })}
          logo={<StationLogo logo="vis" size={30} beschriftung="" />}
        />
      </div>
      <button
        onClick={() => sende({ art: 'einstellung' })}
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
        onSyncToggle={() => sende({ art: 'rechner' })}
        chip={heimChip(rechner)}
      />
    </>
  );
}

/** Die Claude-Teile neben der Wurzel, wie `main.tsx` in KosmoOrbit sie neben `<App />` legt. */
export function VisboxClaude() {
  return (
    <>
      <ClaudeAnschluss ausklapper={{ titel: 'Selbständigkeit', inhalt: <ModusSchalter /> }} />
      <ClaudeFensterRahmen />
      <ErzaehlZeile />
    </>
  );
}
