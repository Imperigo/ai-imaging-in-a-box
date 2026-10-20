import { useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import {
  KCheckbox,
  KIcon,
  setzeBewegung,
  setzeSchrift,
  useAnzeigeWahl,
  useHerkunft,
  useOverlaySchliessen,
  type BewegungsWahl,
  type Schriftgroesse,
  type ThemeName,
} from '@kosmo/ui';
import { AKZENTE } from './akzente';
import { setTouchUndoGesteEingestellt, touchUndoGesteAktiv } from '../state/touch-undo';
import './orbit-065.css';
import './einstellungen.css';

/**
 * **Die Teile des Einstellungs-Panels, die ein Wirt wortgleich uebernehmen kann** (KosmoVis-Kopf S4,
 * 20.10.2026; Visbox-Entscheide 115/116).
 *
 * Bis hierher stand alles in `Einstellungen.tsx` — 1700 Zeilen, die fast jeden Zustand der App lesen
 * (Heimrechner, Phase, Sonne, Kosmo, Leistung, Lizenzen …). Visbox zeigt dieselbe Einstellungs-Insel
 * mit eigenen Abschnitten (Heim-PC, «Wer rechnet?», Claude über MCP); die Datei als Ganzes kaeme darum
 * nur als Stellvertreter hinueber, und ein Stellvertreter einer sichtbaren Datei ist eine zweite
 * Oberflaeche, die still veraltet. Hier stehen darum die Teile, die nichts aus der App lesen:
 *
 *  - **die Schale** (`einstellungen-scrim`, `einstellungen-panel`, Kopf mit `einstellungen-schliessen`,
 *    Koerper) samt Fokusfalle, Escape und Herkunft — wie bisher, nur eine Datei weiter;
 *  - **Darstellung** (Thema Papier/Kosmos, Akzent), **Anzeige** (Schrift, Bewegung) und der Rahmen von
 *    **Bewegung & Klang** (die Schalter darin bringt der Aufrufer; der Rueckgaengig-Schalter fuer zwei
 *    Finger steht hier, weil er nur `state/touch-undo` liest).
 *
 * `Einstellungen.tsx` setzt sie unveraendert ein: dieselben Kennungen, dieselben Klassen, dieselbe
 * Reihenfolge — sichtbar aendert sich nichts (Probe `kv-einstellungen-teile.test.tsx`).
 */

/** U14: die Wahlmöglichkeiten der Anzeige (Reihenfolge = Reihenfolge im Segment). */
export const SCHRIFT_WAHL: ReadonlyArray<{ key: Schriftgroesse; label: string }> = [
  { key: 'klein', label: 'Klein' },
  { key: 'normal', label: 'Normal' },
  { key: 'gross', label: 'Gross' },
];
export const BEWEGUNG_WAHL: ReadonlyArray<{ key: BewegungsWahl; label: string }> = [
  { key: 'geraet', label: 'Wie das Gerät' },
  { key: 'voll', label: 'Voll' },
  { key: 'ruhig', label: 'Ruhig' },
  { key: 'aus', label: 'Aus' },
];

export interface EinstellungenSchaleProps {
  /** Der Titel im Kopf («Einstellungen», mit Station «Einstellungen — KosmoDesign»). */
  titel: string;
  onClose: () => void;
  /** Was vor dem Kopf in der Box steht (das Panel legt dort `WerkzeugSetup` hin). */
  vorKopf?: ReactNode;
  children: ReactNode;
}

/**
 * Die Schale des Panels. `KDialog` wird bewusst NICHT instanziiert (Kopfkommentar `Einstellungen.tsx`:
 * die Kennung `einstellungen-panel` gehoert auf die BOX) — dieselben Klassen von Hand.
 */
export function EinstellungenSchale({ titel, onClose, vorKopf, children }: EinstellungenSchaleProps) {
  /**
   * Das eine Haus-Gesetz statt der eigenen Abschrift (Schichtungs-Entscheide 20a, 24a, 37a, 38b, 39a
   * vom 21.09.2026): `modal: true` bringt Falle und Fokusrueckgabe mit, `aussenklick: false` — der
   * Klick daneben laeuft ueber den Scrim unten. Owner C5 (01.10.2026): das Fenster waechst aus dem
   * Knopf, der es geoeffnet hat (`useHerkunft`, Muster `KDialog`).
   *
   * Die Effekte dieser Schale laufen VOR denen des Aufrufers (React: Kind vor Eltern) — ein Sprung des
   * Panels zu einem Abschnitt (C3, Fokus ins Token-Feld) steht darum weiter NACH der Fokusfalle.
   */
  const boxRef = useRef<HTMLDivElement | null>(null);
  useOverlaySchliessen(boxRef, onClose, { modal: true, aussenklick: false });
  useHerkunft(boxRef);
  return createPortal(
    <div
      data-testid="einstellungen-scrim"
      role="dialog"
      aria-modal
      aria-label="Einstellungen"
      className="k-dialog-scrim es-scrim"
      onClick={onClose}
    >
      <div
        ref={boxRef}
        data-testid="einstellungen-panel"
        className="k-dialog-box k-dialog k-aus-ausloeser es-panel"
        onClick={(e) => e.stopPropagation()}
      >
        {vorKopf}
        <div className="k-dialog-kopf">
          <span className="k-titel k-dialog-kopf-titel">{titel}</span>
          <button
            type="button"
            aria-label="Schliessen"
            className="k-dialog-kopf-schliessen"
            data-testid="einstellungen-schliessen"
            onClick={onClose}
          >
            <KIcon name="schliessen" size={16} />
          </button>
        </div>

        <div className="k-dialog-koerper orbit065-einstellungen-koerper es-koerper-scroll">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export interface AbschnittDarstellungProps {
  theme: ThemeName;
  setTheme: (t: ThemeName) => void;
  akzent: string;
  setAkzent: (a: string) => void;
}

/** «Darstellung»: Thema Papier/Kosmos und der Farbakzent — dieselben Setter wie die Kopfleiste. */
export function AbschnittDarstellung({ theme, setTheme, akzent, setAkzent }: AbschnittDarstellungProps) {
  return (
    <section data-testid="einstellungen-darstellung" className="orbit065-einstellungen-sektion">
      <div className="orbit065-einstellungen-sektionstitel">Darstellung</div>
      <div className="es-darstellung-reihe">
        {/* v0.7.3 D7 (Owner-Entscheid, Gestaltungs-Spez): Tinte entfernt —
            der 3-Segment-Wähler (0.7.2 §1) schrumpft zurück auf 2
            Segmente PAPIER/KOSMOS. `data-testid="einstellung-thema"`
            bleibt auf dem Segment-CONTAINER (Vertrag), aber
            `e2e/einstellungen.spec.ts` klickt seit D7 gezielt ein
            Segment statt den Container — mit nur zwei Segmenten läge ein
            Container-Klick (Playwright klickt die Bounding-Box-Mitte)
            GENAU auf der Grenze zwischen beiden Buttons, ein
            browserabhängig unklares Ziel statt des früheren, zuverlässig
            mittleren «Tinte»-Segments. */}
        <span data-testid="einstellung-thema" role="group" aria-label="Thema" className="es-segment">
          {(
            [
              { key: 'paper' as const, label: 'Papier' },
              { key: 'orbit' as const, label: 'Kosmos' },
            ]
          ).map((seg) => (
            <button
              key={seg.key}
              type="button"
              data-testid={`einstellung-thema-${seg.key}`}
              aria-pressed={theme === seg.key}
              onClick={() => setTheme(seg.key)}
              className={`es-segment-item${theme === seg.key ? ' es-segment-item--aktiv' : ''}`}
            >
              {seg.label}
            </button>
          ))}
        </span>
        <span className="es-akzent-reihe">
          {AKZENTE.map((a) => (
            <button
              key={a.key}
              onClick={() => setAkzent(a.key)}
              title={`Akzent ${a.name}`}
              aria-label={`Akzent ${a.name}`}
              data-testid={`einstellung-akzent-${a.key}`}
              className={`es-akzent-swatch${akzent === a.key ? ' es-akzent-swatch--aktiv' : ''}`}
              style={{ background: a.farbe ?? 'var(--k-technik)' }}
            />
          ))}
        </span>
      </div>

      {/* U25 Phase 6/7 (Owner 01.10.2026, «nur noch Insel»): hier standen die Werkzeug-Anordnung des Docks
          (A/B), die Dock-Vorlagen Fokus/Arbeiten/Prüfen und die drei Häkchen «Manuelle Ansicht» für Design,
          Publish und Prepare. Mit dem Dock und der alten Oberfläche sind alle fünf ohne Gegenstand. */}
    </section>
  );
}

/**
 * U14 (Owner B6/B18, 01.10.2026): Schrift und Bewegung einstellbar. Die Wirkung steckt in `@kosmo/ui`
 * (`anzeige.ts`: setzt `data-schrift`/`data-bewegung` an <html> und merkt die Wahl) — hier nur die Wahl,
 * im selben Segment-Muster wie «Thema». Eigener Abschnitt neben «Bewegung & Klang»: jene Schalter
 * betreffen Zeiger/Klänge/Kosmo-Zeichnen, diese hier jede Animation der App.
 */
export function AbschnittAnzeige() {
  const anzeige = useAnzeigeWahl();
  return (
    <section data-testid="einstellungen-anzeige" className="orbit065-einstellungen-sektion">
      <div className="orbit065-einstellungen-sektionstitel">Anzeige</div>

      <div className="es-feld-block">
        <span className="es-feld-label">Schrift</span>
        <span data-testid="einstellung-schrift" role="group" aria-label="Schrift" className="es-segment es-segment--umbrechen">
          {SCHRIFT_WAHL.map((seg) => (
            <button
              key={seg.key}
              type="button"
              data-testid={`einstellung-schrift-${seg.key}`}
              aria-pressed={anzeige.schrift === seg.key}
              onClick={() => setzeSchrift(seg.key)}
              className={`es-segment-item${anzeige.schrift === seg.key ? ' es-segment-item--aktiv' : ''}`}
            >
              {seg.label}
            </button>
          ))}
        </span>
        <span className="es-feld-hinweis">Die Grösse aller Texte. Wirkt sofort und bleibt nach dem Neustart.</span>
      </div>

      <div className="es-feld-block">
        <span className="es-feld-label">Bewegung</span>
        <span data-testid="einstellung-bewegung" role="group" aria-label="Bewegung" className="es-segment es-segment--umbrechen">
          {BEWEGUNG_WAHL.map((seg) => (
            <button
              key={seg.key}
              type="button"
              data-testid={`einstellung-bewegung-${seg.key}`}
              aria-pressed={anzeige.bewegung === seg.key}
              onClick={() => setzeBewegung(seg.key)}
              className={`es-segment-item${anzeige.bewegung === seg.key ? ' es-segment-item--aktiv' : ''}`}
            >
              {seg.label}
            </button>
          ))}
        </span>
        <span className="es-feld-hinweis">
          Wie das Gerät: gilt, was du am Gerät eingestellt hast. voll: alle Übergänge. ruhig: Übergänge ja, nichts
          kreist oder atmet. aus: nichts bewegt sich.
        </span>
      </div>
    </section>
  );
}

/**
 * v0.7.2 W4-H (Kritik-Auflage «Einstellungs-Verdrahtung», Spec §5/§7/§8/§9): der Abschnitt «Bewegung &
 * Klang». Seine Schalter lesen dieselben Funktionen wie die jeweiligen Module selbst (keine Zweitlogik)
 * und stehen beim Aufrufer, der diese Module hat; hier nur der Rahmen und der Schalter, der nur
 * `state/touch-undo` liest.
 */
export function AbschnittBewegungKlang({ children }: { children: ReactNode }) {
  return (
    <section data-testid="einstellungen-bewegung-klang" className="orbit065-einstellungen-sektion">
      <div className="orbit065-einstellungen-sektionstitel">Bewegung &amp; Klang</div>
      {children}
    </section>
  );
}

/**
 * v0.8.3 / P8 (E10 §10.2, `docs/V083-SPEZ.md`): Zwei-Finger-Doppeltipp-Undo — reiner localStorage-Spiegel,
 * Default AUS (§8-1 bleibt Owner-offen, s. `state/touch-undo.ts`-Kopfkommentar).
 */
export function SchalterTouchUndo() {
  const [touchUndoGesteAn, setTouchUndoGesteAnState] = useState(() => touchUndoGesteAktiv());
  return (
    <KCheckbox
      className="es-schalter-label"
      data-testid="einstellung-touch-undo-geste"
      checked={touchUndoGesteAn}
      onChange={(e) => {
        setTouchUndoGesteEingestellt(e.target.checked);
        setTouchUndoGesteAnState(e.target.checked);
      }}
      label="Zwei-Finger-Doppeltipp auf dem Viewport löst Rückgängig aus (iPad, Default aus)"
    />
  );
}
