/**
 * K8 — Kreismenue am Zeiger (`docs/AUFTRAG-EINBAU-B163-KOSMODESIGN-AN-INTEGRATOR.md`
 * §K8, Bild a3, Paket d8-kreismenue).
 *
 * Taste Q oeffnet am Zeiger einen Kreis: in der Mitte die Suche, im Ring die
 * sechs Gruppen, aussen die Werkzeuge der gezeigten Gruppe. Esc schliesst.
 * Der Kreis ist ein Kurzweg ZUSAETZLICH zur Gruppenschiene, nicht statt ihr:
 * er bekommt seine Gruppen und Werkzeuge von der Insel (`IslandShell.tsx`,
 * dieselbe Quelle wie die Schiene: `ZEICHNEN_GRUPPEN` in `island-katalog.ts`)
 * und gibt eine Wahl an dieselbe Aktivierung zurueck, die auch ein Klick auf
 * die Schiene nimmt. Er kennt keinen Store und keinen Befehl.
 *
 * Bedienung: Ein Zeiger ueber einer Gruppe oder ein Klick darauf zeigt ihre
 * Werkzeuge aussen; Tippen in der Mitte ersetzt die Auswahl durch die Treffer
 * der Suche (Enter nimmt den ersten). Nicht Leertaste (haelt das Schieben im
 * Plan), nicht Rechtsklick (oeffnet das Kontextmenue).
 *
 * Lage: die Mitte sitzt am Zeiger, wird aber so geklammert, dass der ganze
 * Kreis im Fenster bleibt; ein kleines Fenster verkleinert den Kreis, statt
 * ihn abzuschneiden. Kein Rollbalken, kein Text ausserhalb seines Kastens.
 *
 * Nicht gebaut (ehrlich): der lange Druck auf Beruehrung. Er braucht einen
 * Zeigerhoerer auf der Zeichenflaeche (`PlanView.tsx`, `Viewport3D`), die
 * ausserhalb des Dateikreises dieses Pakets liegen.
 */

import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import type { IslandGruppe, IslandGruppeId, IslandWerkzeug } from './island-katalog';

/** Halbmesser der Suchmitte. */
export const KREIS_MITTE_RADIUS_PX = 54;
/** Aussen-/Innenhalbmesser des Gruppenrings. */
export const KREIS_RING_INNEN_PX = 58;
export const KREIS_RING_AUSSEN_PX = 142;
/** Mitte der Ring-Knoepfe. */
const KREIS_RING_MITTE_PX = 100;
/** Halbmesser, auf dem die Werkzeug-Kacheln sitzen. */
export const KREIS_WERKZEUG_RADIUS_PX = 250;
/** Kachelgroesse aussen. */
const KACHEL_BREITE_PX = 84;
const KACHEL_HOEHE_PX = 60;
/** Ganzer Kreis: Werkzeug-Halbmesser plus halbe Kachel (Diagonale). */
export const KREIS_AUSSENRADIUS_PX = KREIS_WERKZEUG_RADIUS_PX + 54;
/** Rand zum Fensterrand. */
const RAND_PX = 8;
/** Winkelabstand zweier Kacheln auf dem Aussenbogen (Sehne >= Kachel-Diagonale, sonst ueberdecken sich schraeg stehende Kacheln). */
const KACHEL_WINKEL_GRAD = 26;

export interface KreisLage {
  /** Mitte in Fensterkoordinaten. */
  x: number;
  y: number;
  /** 1 = volle Groesse, kleiner auf kleinen Fenstern. */
  massstab: number;
}

/**
 * Reine Lage: Mitte am Zeiger, geklammert, sodass der ganze Kreis im Fenster
 * liegt; passt er auch dann nicht, wird er verkleinert.
 */
export function kreisLage(zeigerX: number, zeigerY: number, fensterBreite: number, fensterHoehe: number): KreisLage {
  const kleinste = Math.min(fensterBreite, fensterHoehe) - 2 * RAND_PX;
  const massstab = Math.min(1, Math.max(0.4, kleinste / (2 * KREIS_AUSSENRADIUS_PX)));
  const r = KREIS_AUSSENRADIUS_PX * massstab + RAND_PX;
  const klammer = (v: number, gesamt: number): number => Math.min(Math.max(v, r), Math.max(r, gesamt - r));
  return { x: klammer(zeigerX, fensterBreite), y: klammer(zeigerY, fensterHoehe), massstab };
}

/** Mittelpunktwinkel (Grad, 0 = oben, im Uhrzeigersinn) der i-ten von n Gruppen. */
function gruppenWinkel(i: number, n: number): number {
  return (360 / n) * i;
}

function polar(radius: number, gradVonOben: number): { x: number; y: number } {
  const rad = ((gradVonOben - 90) * Math.PI) / 180;
  return { x: radius * Math.cos(rad), y: radius * Math.sin(rad) };
}

/** Pfad eines Ringstuecks von `von` bis `bis` Grad (0 = oben). */
function ringStueck(von: number, bis: number): string {
  const a1 = polar(KREIS_RING_AUSSEN_PX, von);
  const a2 = polar(KREIS_RING_AUSSEN_PX, bis);
  const i1 = polar(KREIS_RING_INNEN_PX, bis);
  const i2 = polar(KREIS_RING_INNEN_PX, von);
  const gross = bis - von > 180 ? 1 : 0;
  return [
    `M ${a1.x.toFixed(2)} ${a1.y.toFixed(2)}`,
    `A ${KREIS_RING_AUSSEN_PX} ${KREIS_RING_AUSSEN_PX} 0 ${gross} 1 ${a2.x.toFixed(2)} ${a2.y.toFixed(2)}`,
    `L ${i1.x.toFixed(2)} ${i1.y.toFixed(2)}`,
    `A ${KREIS_RING_INNEN_PX} ${KREIS_RING_INNEN_PX} 0 ${gross} 0 ${i2.x.toFixed(2)} ${i2.y.toFixed(2)}`,
    'Z',
  ].join(' ');
}

export interface KreismenueGruppe {
  gruppe: IslandGruppe;
  werkzeuge: readonly IslandWerkzeug[];
}

export interface KreismenueProps {
  /** Zeigerort beim Oeffnen (Fensterkoordinaten). */
  zeigerX: number;
  zeigerY: number;
  gruppen: readonly KreismenueGruppe[];
  /** Gruppe, die beim Oeffnen gezeigt wird (etwa die des aktiven Werkzeugs). */
  startGruppe: IslandGruppeId;
  aktivesWerkzeugId?: string | undefined;
  /** Zeichnet das Symbol eines Werkzeugs (die Insel kennt die Glyphen). */
  zeichneGlyphe: (w: IslandWerkzeug) => ReactNode;
  zeichneGruppenGlyphe: (g: IslandGruppe) => ReactNode;
  onWahl: (w: IslandWerkzeug) => void;
  onSchliessen: () => void;
}

export function Kreismenue({
  zeigerX,
  zeigerY,
  gruppen,
  startGruppe,
  aktivesWerkzeugId,
  zeichneGlyphe,
  zeichneGruppenGlyphe,
  onWahl,
  onSchliessen,
}: KreismenueProps) {
  const [gezeigt, setGezeigt] = useState<IslandGruppeId>(startGruppe);
  const [suche, setSuche] = useState('');
  const feldRef = useRef<HTMLInputElement | null>(null);
  const lage = kreisLage(zeigerX, zeigerY, window.innerWidth, window.innerHeight);

  useLayoutEffect(() => {
    feldRef.current?.focus();
  }, []);

  // Esc schliesst, bevor irgendein anderer Hoerer «zurueck zur Auswahl» daraus
  // macht (Aufnahmephase am Fenster, kein Weiterreichen).
  useEffect(() => {
    function aufTaste(e: KeyboardEvent): void {
      if (e.key !== 'Escape') return;
      e.preventDefault();
      e.stopPropagation();
      onSchliessen();
    }
    window.addEventListener('keydown', aufTaste, true);
    return () => window.removeEventListener('keydown', aufTaste, true);
  }, [onSchliessen]);

  const text = suche.trim().toLowerCase();
  const aktuelleGruppe = gruppen.find((g) => g.gruppe.id === gezeigt) ?? gruppen[0];
  const treffer: readonly IslandWerkzeug[] =
    text !== ''
      ? gruppen.flatMap((g) => g.werkzeuge).filter((w) => w.name.toLowerCase().includes(text))
      : (aktuelleGruppe?.werkzeuge ?? []);
  const gruppenIndex = Math.max(0, gruppen.findIndex((g) => g.gruppe.id === aktuelleGruppe?.gruppe.id));
  // Mitte des Aussenbogens: bei der gezeigten Gruppe, bei der Suche oben.
  const bogenMitte = text !== '' ? 0 : gruppenWinkel(gruppenIndex, Math.max(1, gruppen.length));
  const n = treffer.length;
  const halbeSpanne = ((n - 1) * KACHEL_WINKEL_GRAD) / 2;

  const hoehe = 2 * KREIS_AUSSENRADIUS_PX;
  return createPortal(
    <div
      className="kreismenue-huelle"
      data-testid="island-kreismenue"
      role="dialog"
      aria-label="Kreismenü"
      style={{ left: `${lage.x}px`, top: `${lage.y}px`, width: `${hoehe}px`, height: `${hoehe}px`, transform: `translate(-50%, -50%) scale(${lage.massstab})` }}
      // Ein Klick neben den Bedienelementen schliesst nicht: der Kreis ist
      // gross und leer dazwischen; Schliessen geht ueber Esc oder Q.
    >
      <svg className="kreismenue-ring" viewBox={`${-KREIS_AUSSENRADIUS_PX} ${-KREIS_AUSSENRADIUS_PX} ${hoehe} ${hoehe}`} aria-hidden="true">
        <circle className="kreismenue-scheibe" r={KREIS_RING_AUSSEN_PX} />
        {gruppen.map((g, i) => {
          const mitte = gruppenWinkel(i, gruppen.length);
          const halb = 180 / gruppen.length;
          return (
            <path
              key={g.gruppe.id}
              className={`kreismenue-stueck${g.gruppe.id === aktuelleGruppe?.gruppe.id && text === '' ? ' kreismenue-stueck--an' : ''}`}
              d={ringStueck(mitte - halb + 1.5, mitte + halb - 1.5)}
            />
          );
        })}
      </svg>

      <div className="kreismenue-mitte">
        <input
          ref={feldRef}
          type="text"
          className="kreismenue-suche"
          data-testid="kreismenue-suche"
          aria-label="Werkzeug oder Befehl suchen"
          placeholder="Suchen"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && treffer.length > 0) {
              e.preventDefault();
              onWahl(treffer[0]!);
            }
          }}
        />
      </div>

      {gruppen.map((g, i) => {
        const p = polar(KREIS_RING_MITTE_PX, gruppenWinkel(i, gruppen.length));
        const an = g.gruppe.id === aktuelleGruppe?.gruppe.id && text === '';
        return (
          <button
            key={g.gruppe.id}
            type="button"
            className={`kreismenue-gruppe${an ? ' kreismenue-gruppe--an' : ''}`}
            data-testid={`kreismenue-gruppe-${g.gruppe.id}`}
            aria-pressed={an}
            style={{ left: `calc(50% + ${p.x.toFixed(1)}px)`, top: `calc(50% + ${p.y.toFixed(1)}px)` }}
            onPointerEnter={(e) => {
              if (e.pointerType === 'mouse') {
                setSuche('');
                setGezeigt(g.gruppe.id);
              }
            }}
            onClick={() => {
              setSuche('');
              setGezeigt(g.gruppe.id);
            }}
          >
            <span className="kreismenue-gruppe-zeichen" aria-hidden="true">
              {zeichneGruppenGlyphe(g.gruppe)}
            </span>
            <span className="kreismenue-gruppe-titel">{g.gruppe.label}</span>
          </button>
        );
      })}

      {treffer.map((w, i) => {
        const p = polar(KREIS_WERKZEUG_RADIUS_PX, bogenMitte - halbeSpanne + i * KACHEL_WINKEL_GRAD);
        const aktiv = aktivesWerkzeugId === w.id;
        return (
          <button
            key={w.id}
            type="button"
            className={`kreismenue-werkzeug${aktiv ? ' kreismenue-werkzeug--an' : ''}`}
            data-testid={`kreismenue-werkzeug-${w.id}`}
            aria-pressed={aktiv}
            style={{
              left: `calc(50% + ${p.x.toFixed(1)}px)`,
              top: `calc(50% + ${p.y.toFixed(1)}px)`,
              width: `${KACHEL_BREITE_PX}px`,
              minHeight: `${KACHEL_HOEHE_PX}px`,
            }}
            onClick={() => onWahl(w)}
          >
            <span className="kreismenue-werkzeug-zeichen" aria-hidden="true">
              {zeichneGlyphe(w)}
            </span>
            <span className="kreismenue-werkzeug-titel">{w.name}</span>
            {w.marke !== undefined ? <span className="kreismenue-werkzeug-marke">{w.marke}</span> : null}
          </button>
        );
      })}
      {text !== '' && treffer.length === 0 ? (
        <p className="kreismenue-leer" data-testid="kreismenue-leer">
          Kein Werkzeug gefunden.
        </p>
      ) : null}
    </div>,
    document.body,
  );
}
