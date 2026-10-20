import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react';
import { StationLogo, useFokusSchleier, useOverlaySchliessen, type ModuleId } from '@kosmo/ui';
import { bogenLagen, farbTokenFuer, palettenGruppen, type PalettenGruppe } from './werkzeug-palette';
import '@kosmo/ui/bewegung.css';
import './werkzeug-palette.css';

/**
 * B/C · die Palette am Kosmo-Logo (Entwurf `docs/entwuerfe/palette-und-speichern/
 * pb-*`, `pc-*`; Owner 30.09.2026: «nur ein symbol das kosmologo und dann wenn
 * man draufklick zum hauptmenü und wenn man einfach drüber hovert es ausfächert
 * wie eine farbpalette … ein orbitales radiales ausfächern»).
 *
 * **U4 (v0.1.7, Owner 01.10.2026, Entwurf A «zweiter Bogen»):** die Palette hat
 * zwei Bogen. Auf dem inneren stehen die Hauptwerkzeuge KosmoDesign und
 * KosmoData; ein Antippen faechert dessen Unterwerkzeuge auf einem aeusseren
 * Bogen auf, je in der Farbe ihrer Station. Ein Antippen eines Unterwerkzeugs
 * oeffnet seine Station; ein zweites Antippen des Hauptwerkzeugs oeffnet dessen
 * Hauptstation (KosmoDesign → KosmoDraw, KosmoData → KosmoReference; ist die
 * schon offen, klappt der Bogen nur zu).
 *
 * * **Klick aufs Logo** fuehrt zur Zentrale.
 * * **Darueberfahren** (Maus) oeffnet den inneren Bogen. Der Name erscheint
 *   beim Darueberfahren eines Tupfers.
 * * **iPad (Finger, kein Hover):** der erste Tipp aufs Logo oeffnet die
 *   Palette, der zweite fuehrt zur Zentrale. Die Namen stehen **sichtbar** an
 *   jedem Tupfer — es gibt kein Darueberfahren. Die Palette bleibt offen,
 *   bis man daneben tippt oder Escape drueckt (Messlauf 01.10.2026: sie
 *   klappte nach dem Tipp von selbst zu — der Nachlauf unten galt auch fuer den
 *   Finger, der beim Loslassen den Zeiger «verlaesst»). Kein Langdruck (E-8).
 * * **Tastatur:** das Logo mit Fokus oeffnet die Palette, Enter fuehrt zur
 *   Zentrale, Tab erreicht die Tupfer, Escape schliesst.
 *
 * Schliessen: Escape, Klick daneben, und nur bei der **Maus** 700 ms Nachlauf
 * nach dem Verlassen (eigener Zeitgeber statt `hoverRueckklappMs`, das auch
 * Finger und Stift zaehlt).
 *
 * **Bewegung** (Leitfaden V2): Eintritt `--k-feder`, gestaffelt entlang des
 * Bogens, die Beschriftung zuletzt; Austritt alles zugleich mit
 * `--k-motion-fast`; bei «weniger Bewegung» steht sie sofort da. Kein
 * festgehaltenes Endbild — die Transformation sitzt nur auf den Tupfern, die
 * nichts `position:fixed` in sich tragen (Kopf von `bewegung.css`).
 */

const NACHLAUF_MS = 700;

export interface WerkzeugPaletteProps {
  /** Die offene Station — ihr Werkzeug fehlt auf der Palette. */
  aktivesModul: ModuleId | 'orbit';
  onZentrale: () => void;
  onStationOeffnen: (station: ModuleId) => void;
  /** Das Kosmo-Logo, wie es heute im Kopf steht. */
  logo: ReactNode;
  /**
   * Nahtstelle fuer einen zweiten Wirt (Visbox, `registrierePalettenQuelle`): eine Gruppe mit
   * `ziel` oeffnet dieses Ziel hier. KosmoOrbit reicht es nicht.
   */
  onZielOeffnen?: (ziel: string) => void;
  /** Wohin das Logo fuehrt, fuer Vorlesen und Hinweis — in KosmoOrbit die «Zentrale». */
  heimName?: string;
}

export function WerkzeugPalette({ aktivesModul, onZentrale, onStationOeffnen, logo, onZielOeffnen, heimName = 'Zentrale' }: WerkzeugPaletteProps) {
  const [offen, setOffen] = useState(false);
  // Welches Hauptwerkzeug seinen zweiten Bogen zeigt.
  const [gruppe, setGruppe] = useState<string | null>(null);
  // Mit dem Finger geoeffnet? Dann sagt der Hinweis «Nochmals tippen» und die
  // Namen stehen dauernd da.
  const [perTipp, setPerTipp] = useState(false);
  const wurzelRef = useRef<HTMLDivElement | null>(null);
  // Womit der letzte Druck aufs Logo kam — `null` heisst Tastatur (Enter).
  const druckArt = useRef<string | null>(null);
  const nachlauf = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stoppNachlauf = () => {
    if (nachlauf.current !== null) {
      clearTimeout(nachlauf.current);
      nachlauf.current = null;
    }
  };
  const schliesse = () => {
    stoppNachlauf();
    setOffen(false);
    setGruppe(null);
    setPerTipp(false);
  };
  // Escape und Klick daneben; der Nachlauf ist unten selbst gebaut (nur Maus).
  useOverlaySchliessen(wurzelRef, schliesse, { esc: true, aussenklick: true });
  // E232 Fokus-Schleier (Art «Wählen»): offen tritt alles andere leicht zurück; ein Klick daneben schliesst nur.
  const schleier = useFokusSchleier(wurzelRef, { offen, onSchliessen: schliesse });
  useEffect(() => stoppNachlauf, []);

  // Daneben tippen schliesst auch ohne Mausereignis: ein Finger erzeugt je
  // nach Geraet kein `mousedown` (der Hook oben hoert nur darauf).
  useEffect(() => {
    if (!offen) return undefined;
    const aussen = (e: PointerEvent) => {
      const el = wurzelRef.current;
      if (el && e.target instanceof Node && !el.contains(e.target)) schliesse();
    };
    document.addEventListener('pointerdown', aussen);
    return () => document.removeEventListener('pointerdown', aussen);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen]);

  const gruppen = palettenGruppen(aktivesModul);
  const hauptLagen = bogenLagen(gruppen.length, 0);

  const hauptTipp = (g: PalettenGruppe) => {
    // OHNE UNTERWERKZEUGE (nur bei einem zweiten Wirt, `registrierePalettenQuelle`): kein zweiter
    // Bogen, den ein erster Tipp aufklappen koennte — der Tipp oeffnet gleich. Die offene Station
    // klappt die Palette nur zu. In KosmoOrbit hat jedes Hauptwerkzeug Unterwerkzeuge.
    if (g.werkzeuge.length === 0) {
      schliesse();
      if (g.ziel && onZielOeffnen) onZielOeffnen(g.ziel);
      else if (g.station !== aktivesModul) onStationOeffnen(g.station);
      return;
    }
    if (gruppe !== g.id) {
      setGruppe(g.id);
      return;
    }
    // Zweites Antippen: die Hauptstation oeffnen — ausser sie ist schon offen.
    if (g.station === aktivesModul) {
      setGruppe(null);
      return;
    }
    schliesse();
    onStationOeffnen(g.station);
  };

  return (
    <>
      {/* Der Schleier steht NEBEN der Palette, nicht in ihr: als ihr Kind zählte die Maus über dem Schleier für
          React noch als «auf der Palette», und der Nachlauf schlösse sie nie. */}
      {schleier}
      <div
        ref={wurzelRef}
        className={`wp-wurzel${offen ? ' wp-offen' : ''}`}
        data-testid="werkzeug-palette"
        data-tipp={perTipp ? 'ja' : 'nein'}
        data-gruppe={gruppe ?? ''}
        onPointerOver={(e) => {
          if (e.pointerType === 'mouse' && !offen) setOffen(true);
        }}
        onBlur={(e) => {
          // E232: wandert der Fokus aus der Palette hinaus (Tab), klappt sie zu — sonst bliebe sie samt Schleier
          // offen, und der Fokusring des nächsten Knopfs läge auf dem getönten Grund (gemessen:
          // `e2e/fokusring-zweifarbig.spec.ts`, 2,31:1 und 1,42:1). Ein Klick auf den Schleier verschiebt den Fokus
          // nicht (er verhindert den Druck), schliesst also nur über sich selbst.
          const nach = e.relatedTarget;
          if (offen && nach instanceof Node && !e.currentTarget.contains(nach)) schliesse();
        }}
        onPointerEnter={(e) => {
          if (e.pointerType === 'mouse') stoppNachlauf();
        }}
        onPointerLeave={(e) => {
          // Nur die Maus «verlaesst» die Palette von selbst; ein Finger oder Stift
          // tut es bei jedem Loslassen und darf sie nicht zuklappen.
          if (e.pointerType !== 'mouse' || !offen) return;
          stoppNachlauf();
          nachlauf.current = setTimeout(() => {
            nachlauf.current = null;
            schliesse();
          }, NACHLAUF_MS);
        }}
      >
        <button
          type="button"
          className="wp-logo"
          data-testid="werkzeug-palette-logo"
          aria-label={`Zur ${heimName}`}
          aria-expanded={offen}
          aria-controls="werkzeug-palette-ring"
          onPointerDown={(e) => {
            druckArt.current = e.pointerType || 'mouse';
          }}
          onFocus={(e) => {
            // Nur Tastaturfokus oeffnet — ein Mausdruck fokussiert auch, und
            // dann soll der Klick zur Zentrale fuehren, nicht erst oeffnen.
            let tastatur = false;
            try {
              tastatur = e.currentTarget.matches(':focus-visible');
            } catch {
              tastatur = false;
            }
            if (tastatur) setOffen(true);
          }}
          onClick={() => {
            const art = druckArt.current;
            druckArt.current = null;
            if ((art === 'touch' || art === 'pen') && !offen) {
              setOffen(true);
              setPerTipp(true);
              return;
            }
            schliesse();
            onZentrale();
          }}
        >
          {logo}
        </button>
        <span className="wp-hinweis" data-testid="werkzeug-palette-hinweis" aria-hidden="true">
          {perTipp ? `Nochmals tippen: ${heimName}` : `Klick: ${heimName}`}
        </span>
        <div id="werkzeug-palette-ring" className="wp-ring" data-testid="werkzeug-palette-ring" inert={!offen} role="group" aria-label="Werkzeuge">
          {/* Innerer Bogen: die Hauptwerkzeuge. */}
          {gruppen.map((g, i) => {
            const lage = hauptLagen[i]!;
            const aufgefaechert = gruppe === g.id;
            const hauptOffen = aufgefaechert && g.station !== aktivesModul;
            // Ohne Unterwerkzeuge (zweiter Wirt): der Tupfer oeffnet gleich, die offene Station ist markiert.
            const ohneBogen = g.werkzeuge.length === 0;
            const istOffen = ohneBogen && !g.ziel && g.station === aktivesModul;
            return (
              <button
                key={g.id}
                type="button"
                className={`wp-punkt wp-punkt--haupt wp-sichtbar${aufgefaechert ? ' wp-aufgefaechert' : ''}`}
                data-testid={`werkzeug-palette-haupt-${g.id}`}
                aria-label={
                  ohneBogen ? (istOffen ? `${g.titel} — offen` : `${g.titel} öffnen`) : hauptOffen ? `${g.titel} öffnen` : `${g.titel}: Werkzeuge zeigen`
                }
                aria-expanded={ohneBogen ? undefined : aufgefaechert}
                aria-current={istOffen ? 'page' : undefined}
                aria-controls={ohneBogen ? undefined : `werkzeug-palette-bogen-${g.id}`}
                style={
                  {
                    '--wp-x': `${lage.x.toFixed(1)}px`,
                    '--wp-y': `${lage.y.toFixed(1)}px`,
                    '--wp-i': String(i),
                    '--wp-farbe': `var(${farbTokenFuer(g.logo)})`,
                  } as CSSProperties
                }
                onClick={() => hauptTipp(g)}
              >
                <span className="wp-tupfer" aria-hidden="true">
                  <StationLogo logo={g.logo} size={40} beschriftung="" />
                </span>
                <span className="wp-name" aria-hidden="true">
                  {g.kurz}
                </span>
              </button>
            );
          })}
          {/* Aeusserer Bogen: die Unterwerkzeuge des angetippten Hauptwerkzeugs. */}
          {gruppen.map((g) => {
            const lagen = bogenLagen(g.werkzeuge.length, 1);
            const sichtbar = gruppe === g.id;
            return (
              <div key={g.id} id={`werkzeug-palette-bogen-${g.id}`} role="group" aria-label={`${g.titel}: Werkzeuge`} className="wp-bogen">
                {g.werkzeuge.map((w, i) => {
                  const lage = lagen[i]!;
                  return (
                    <button
                      key={w.id}
                      type="button"
                      className={`wp-punkt${sichtbar ? ' wp-sichtbar' : ''}`}
                      data-testid={`werkzeug-palette-${w.id}`}
                      aria-label={`${w.titel} öffnen`}
                      inert={!sichtbar}
                      style={
                        {
                          '--wp-x': `${lage.x.toFixed(1)}px`,
                          '--wp-y': `${lage.y.toFixed(1)}px`,
                          '--wp-i': String(i),
                          '--wp-farbe': `var(${farbTokenFuer(w.logo)})`,
                        } as CSSProperties
                      }
                      onClick={() => {
                        schliesse();
                        onStationOeffnen(w.moduleId);
                      }}
                    >
                      <span className="wp-tupfer" aria-hidden="true">
                        <StationLogo logo={w.logo} size={40} beschriftung="" />
                      </span>
                      {/* Der Name: mit der Maus eine Kurzhilfe beim Darueberfahren,
                          am Finger dauernd sichtbar (`data-tipp`, siehe CSS).
                          Vorgelesen wird das `aria-label` des Knopfs. */}
                      <span className="wp-name" aria-hidden="true">
                        {w.kurz}
                      </span>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
