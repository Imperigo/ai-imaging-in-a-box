import { useRef, useSyncExternalStore } from 'react';
import { KButton, KWarteOrt } from '@kosmo/ui';
import {
  abonniereModellLaden,
  ladeModellDatei,
  modellLadeStand,
  szeneZeile,
} from './modell-laden';

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
 * Der Dateiwähler ist ein verstecktes `<input type="file">`, ausgelöst vom Knopf. In einer
 * eingebetteten Webansicht (Visbox am Mac: `WKWebView`) öffnet er sich nur, wenn der
 * Gastgeber den Wähler bereitstellt — das ist Sache des Wirts, nicht dieses Knotens.
 */
export function ModellKnotenKoerper({ bauteileImDokument }: { bauteileImDokument: number }) {
  const { wirt, zustand } = useSyncExternalStore(abonniereModellLaden, modellLadeStand, modellLadeStand);
  const waehler = useRef<HTMLInputElement>(null);

  if (!wirt) {
    return <div className="vis-node-info-zeile">Szene: {bauteileImDokument} Bauteile (GLB)</div>;
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
            <div className="vis-modell-mappe" data-testid="modell-noch">
              Noch geladen: Mappe «{zustand.noch.mappe}» · {szeneZeile(zustand.noch.bauteile, zustand.noch.herkunft)}
            </div>
          ) : null}
          {knopf('Andere Datei …')}
        </>
      )}
    </div>
  );
}
