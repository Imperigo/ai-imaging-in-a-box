import { lazy, Suspense, useCallback, useRef, useState, useSyncExternalStore } from 'react';
import { createPortal } from 'react-dom';
import { exportGlb, type KosmoDoc } from '@kosmo/kernel';
import { KButton, KWarteOrt } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import {
  abonniereModellLaden,
  ladeModellDatei,
  modellLadeStand,
  szeneZeile,
  type ModellLadeZustand,
} from './modell-laden';
import './modell-knoten-3d.css';

/*
 * F1 (Bauplan «Neue Knoten» vom 20.10.2026, Owner-Entscheid 109 A): das kleine 3D-Fenster
 * unter der Szenen-Zeile, Doppelklick öffnet es gross. Hülle und grosse Ansicht kommen per
 * `lazy` — sie sind eigene Teile des Baus, der Haupt-Teil wächst nur um diese Zeilen. Der Kern
 * mit three lädt die Hülle selbst erst, wenn sie zeichnet (`modell-vorschau-3d.tsx`).
 */
const ModellVorschau3d = lazy(() => import('./modell-vorschau-3d').then((m) => ({ default: m.ModellVorschau3d })));
const ModellVorschau3dGross = lazy(() =>
  import('./modell-vorschau-3d-gross').then((m) => ({ default: m.ModellVorschau3dGross })),
);

/** Höhe des 3D-Fensters im Knoten (Bauplan F1: etwa 248 × 140; die Breite ist die des
 *  Knotenkörpers, 184 px — ein breiterer Knoten hätte alle Abstände im Graph verschoben). */
export const MODELL_3D_H = 140;
/** Die Zeile unter dem Fenster (Blatt «Modell und Kamera», Feld 1). */
export const MODELL_3D_HILFE = 'Doppelklick: gross';
/** Ihre Höhe, eine Zeile Kleinschrift. */
export const MODELL_3D_HILFE_H = 14;
/** Abstand zwischen den Zeilen des Körpers (`--k-s2`, wie `.vis-modell-laden`). */
const ABSTAND = 4;
/** Was das Fenster samt Zeile darunter zum Körper beiträgt — gleich mit und ohne Wirt.
 *  `NodeCanvas.tsx` rechnet damit `KOERPER_H.modell` und `MODELL_KOERPER_H_MIT_LADEN`. */
export const MODELL_3D_ZUSATZ = ABSTAND + MODELL_3D_H + ABSTAND + MODELL_3D_HILFE_H;

/**
 * Stand des Modells für das 3D-Fenster: zählt hoch, sobald sich ein Bauteil ändert — die
 * Bauteile sind unveränderliche Objekte, die `doc.apply` ersetzt. Der Vis-Graph selbst
 * (`visgraph`) zählt nicht mit: ein Regler am Knoten exportiert das Modell nicht neu.
 * Rein über das Dokument, ohne Haken; der letzte Stand je Dokument liegt in einer WeakMap.
 */
const standJeDoc = new WeakMap<KosmoDoc, { teile: readonly unknown[]; nr: number }>();
export function modellStand(doc: KosmoDoc): number {
  const teile: unknown[] = [];
  for (const e of doc.entities.values()) if (e.kind !== 'visgraph') teile.push(e);
  const alt = standJeDoc.get(doc);
  if (alt && alt.teile.length === teile.length && alt.teile.every((t, i) => t === teile[i])) return alt.nr;
  const nr = (alt?.nr ?? 0) + 1;
  standJeDoc.set(doc, { teile, nr });
  return nr;
}

/** Welches Modell das Fenster zeigt: ohne Wirt das des Entwurfs (sofern Bauteile da sind),
 *  mit Wirt das geladene — auch das, das nach einer unlesbaren Datei weiter gilt. */
function zeigtModell(wirt: boolean, zustand: ModellLadeZustand, bauteile: number): boolean {
  if (!wirt) return bauteile > 0;
  return zustand.stand === 'geladen' || (zustand.stand === 'fehler' && zustand.noch !== undefined);
}

/**
 * Das 3D-Fenster im Modell-Knoten. glb über `exportGlb(doc)` — in KosmoOrbit aus dem Entwurf,
 * in Visbox derselbe Name im Stellvertreter (die Bytes der Mappe). Die Funktion behält ihre
 * Identität, solange sich das Modell nicht ändert (`useCallback`), sonst exportierte jedes
 * Zeichnen neu.
 */
function ModellFenster({ hatModell, schluessel, knotenZoom }: { hatModell: boolean; schluessel: unknown; knotenZoom: number }) {
  const doc = useProject((s) => s.doc);
  // `schluessel` trägt Modellstand und Fassung: eine neue Identität heisst neu exportieren.
  const quelle = useCallback(() => {
    void schluessel;
    return exportGlb(doc, doc.settings.projectName);
  }, [doc, schluessel]);
  const [gross, setGross] = useState(false);
  const glb = hatModell ? quelle : null;
  return (
    <>
      <Suspense fallback={<div className="vis-modell-3d-platz" data-testid="modell-3d-platz" />}>
        <ModellVorschau3d
          glb={glb}
          knotenZoom={knotenZoom}
          onGross={() => setGross(true)}
          breite="100%"
          hoehe={MODELL_3D_H}
          className="vis-modell-3d--knoten"
        />
      </Suspense>
      <div className="vis-modell-3d-zeile" data-testid="modell-3d-hilfe">
        {MODELL_3D_HILFE}
      </div>
      {gross && typeof document !== 'undefined'
        ? createPortal(
            <Suspense fallback={null}>
              <ModellVorschau3dGross glb={glb} onClose={() => setGross(false)} />
            </Suspense>,
            document.body,
          )
        : null}
    </>
  );
}

/**
 * Der Körper des Modell-Knotens (Owner-Entscheid 90 der Visbox, Blatt 21).
 *
 * **Ohne Wirt** (KosmoOrbit: das Gebäude kommt aus dem Entwurf) bleibt es die eine Zeile
 * von vorher, «Szene: N Bauteile (GLB)» — kein Knopf, keine Formate, dieselbe Höhe.
 *
 * **Mit Wirt** (`registriereModellLaden`, Visbox) die vier Zustände des Blatts:
 * (1) leer → «Datei laden …» und die Formate darunter; (2) läuft → was gerade geschieht,
 * mit Balken (gefüllt nur aus echtem Fortschritt, sonst atmet er); (3) geladen →
 * «Szene: N Bauteile (aus IFC)», die Mappe, «Andere Datei …»; (4) nicht lesbar → der Satz
 * des Wirts, und wieder ein Knopf, damit es weitergeht.
 *
 * **3D-Fenster** (F1, Entscheid 109 A): unter der Szenen-Zeile das Modell, das der Render
 * bekommt — ziehen dreht, Doppelklick öffnet es gross. Ohne Wirt immer, mit Wirt, sobald ein
 * Modell geladen ist (auch das, das nach einer unlesbaren Datei weiter gilt).
 *
 * Der Dateiwähler ist ein verstecktes `<input type="file">`, ausgelöst vom Knopf. In einer
 * eingebetteten Webansicht (Visbox am Mac: `WKWebView`) öffnet er sich nur, wenn der
 * Gastgeber den Wähler bereitstellt — das ist Sache des Wirts, nicht dieses Knotens.
 */
export function ModellKnotenKoerper({
  bauteileImDokument,
  knotenZoom = 1,
}: {
  bauteileImDokument: number;
  /** Zoom der Knotenansicht — das 3D-Fenster zeichnet entsprechend schärfer. */
  knotenZoom?: number;
}) {
  const { wirt, zustand } = useSyncExternalStore(abonniereModellLaden, modellLadeStand, modellLadeStand);
  const waehler = useRef<HTMLInputElement>(null);
  const doc = useProject((s) => s.doc);
  // Neu zeichnen, wenn sich das Dokument ändert (die Revision zählt jede Änderung).
  useProject((s) => s.revision);
  const stand = modellStand(doc);
  const fenster = (
    <ModellFenster
      hatModell={zeigtModell(wirt !== null, zustand, bauteileImDokument)}
      schluessel={wirt ? `${stand}·${zustandKennung(zustand)}` : stand}
      knotenZoom={knotenZoom}
    />
  );

  if (!wirt) {
    return (
      <div className="vis-modell-mit-3d">
        <div className="vis-node-info-zeile">Szene: {bauteileImDokument} Bauteile (GLB)</div>
        {fenster}
      </div>
    );
  }

  const oeffne = () => waehler.current?.click();
  const knopf = (text: string) => (
    <KButton
      size="sm"
      tone={zustand.stand === 'geladen' ? 'quiet' : 'accent'}
      data-testid="modell-datei-laden"
      onClick={oeffne}
      onPointerDown={(e) => e.stopPropagation()}
      className="vis-modell-knopf"
    >
      {text}
    </KButton>
  );

  return (
    <div className="vis-modell-laden" data-testid="modell-laden" data-stand={zustand.stand}>
      <input
        ref={waehler}
        type="file"
        accept={wirt.annehmen}
        hidden
        data-testid="modell-datei-waehler"
        onChange={(e) => {
          const datei = e.target.files?.[0];
          // Zurücksetzen, damit dieselbe Datei ein zweites Mal gewählt werden kann
          // (Entscheid 90b: dieselbe Datei noch einmal = neue Fassung).
          e.target.value = '';
          if (datei) void ladeModellDatei(datei);
        }}
      />
      {zustand.stand === 'leer' && (
        <>
          {knopf('Datei laden …')}
          <div className="vis-modell-formate" data-testid="modell-formate">
            {wirt.formate.join(', ')}
          </div>
          {zustand.satz ? <div className="vis-modell-satz">{zustand.satz}</div> : null}
        </>
      )}
      {zustand.stand === 'laeuft' && (
        <>
          <div className="vis-modell-satz" data-testid="modell-satz">{zustand.satz}</div>
          <KWarteOrt
            form="leiste"
            text={`läuft · ${zustand.datei}`}
            {...(zustand.anteil !== undefined ? { fortschritt: zustand.anteil } : {})}
          />
        </>
      )}
      {zustand.stand === 'geladen' && (
        <>
          <div className="vis-node-info-zeile" data-testid="modell-szene">
            {szeneZeile(zustand.bauteile, zustand.herkunft)}
          </div>
          {fenster}
          <div className="vis-modell-mappe" data-testid="modell-mappe">
            Mappe «{zustand.mappe}»{zustand.fassung && zustand.fassung > 1 ? ` · Fassung ${zustand.fassung}` : ''}
          </div>
          {knopf('Andere Datei …')}
        </>
      )}
      {zustand.stand === 'fehler' && (
        <>
          <div className="vis-modell-satz vis-modell-satz--fehler" role="alert" data-testid="modell-satz">
            {zustand.satz}
          </div>
          {/* KV-STARTGRAPH: das vorige Modell gilt weiter — der Knoten sagt es. */}
          {zustand.noch ? (
            <>
              <div className="vis-modell-mappe" data-testid="modell-noch">
                Noch geladen: Mappe «{zustand.noch.mappe}» · {szeneZeile(zustand.noch.bauteile, zustand.noch.herkunft)}
              </div>
              {fenster}
            </>
          ) : null}
          {knopf('Andere Datei …')}
        </>
      )}
    </div>
  );
}

/** Was eine neue Fassung von der vorigen unterscheidet (Mappe und Fassung), für den Schlüssel. */
function zustandKennung(z: ModellLadeZustand): string {
  if (z.stand === 'geladen') return `${z.mappe}#${z.fassung ?? 1}`;
  if (z.stand === 'fehler' && z.noch) return `${z.noch.mappe}#${z.noch.fassung ?? 1}`;
  return '';
}
