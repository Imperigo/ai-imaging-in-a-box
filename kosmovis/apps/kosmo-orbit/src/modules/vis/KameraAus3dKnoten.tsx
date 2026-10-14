import { fovHorizontalGrad, kameraAus3dAusParams, type VisGraph, type VisNode } from '@kosmo/kernel';
import { KButton, KTooltip, melde, meldeFehler } from '@kosmo/ui';
import { bestellformatFuer, KEINE_3D_ANSICHT_SATZ, kameraUebernehmen } from './kamera-aus-3d';

/**
 * Körper des Knotens «Kamera aus 3D-Ansicht» (14.10.2026). Eigene Datei, damit `NodeCanvas.tsx`
 * nur Einfuhr, Höhe und einen `case` dazubekommt. Höhe: `KOERPER_H.kameraAus3d` dort — vier
 * Zeilen (Auge, Blickfeld, Objektiv-Shift, Umgebung) und der Knopf; jede Zeile bleibt einzeilig,
 * ein langer Satz endet mit «…» und steht ganz in der Kurzhilfe.
 *
 * Gelesen wird die Kamera NUR auf den Knopf (und beim Anlegen, `vis-graph-aktionen.ts` /
 * `kamera-aus-3d.ts`) — nie laufend. Was der Knoten zeigt, ist die gespeicherte Kamera.
 */
export function KameraAus3dKoerper({ graph, node }: { graph: VisGraph; node: VisNode }) {
  const kamera = kameraAus3dAusParams(node.params);
  const umgebung = typeof node.params?.['umgebung'] === 'string' ? node.params['umgebung'] : '';
  const umgebungMit = node.params?.['umgebungMit'] === true;
  const format = bestellformatFuer(graph, node.id);

  const uebernehmen = () => {
    try {
      const k = kameraUebernehmen(graph.id, node.id);
      if (!k) melde(KEINE_3D_ANSICHT_SATZ, { ton: 'info' });
    } catch (err) {
      meldeFehler(err);
    }
  };

  const knopf = (
    <KButton size="sm" tone="ghost" data-testid="kamera-aus-3d-uebernehmen" onClick={uebernehmen}>
      Kamera übernehmen
    </KButton>
  );

  if (!kamera) {
    return (
      <div className="vis-node-kamera-liste" data-testid="kamera-aus-3d" onPointerDown={(e) => e.stopPropagation()}>
        <span className="vis-node-kamera-leer" data-testid="kamera-aus-3d-leer">
          {KEINE_3D_ANSICHT_SATZ}
        </span>
        {knopf}
      </div>
    );
  }

  const seite = format ? format[0] / format[1] : kamera.seitenverhaeltnis;
  const fovH = fovHorizontalGrad(kamera.fovVertikalGrad, seite);
  const fuer = format ? `${format[0]} × ${format[1]}` : 'Leinwand';
  const p = kamera.position.map((w) => w.toFixed(1)).join(' · ');
  const umgebungSatz = umgebung ? (umgebungMit ? umgebung : `Ohne Umgebung: ${umgebung}`) : '';

  return (
    <div className="vis-node-kamera-liste" data-testid="kamera-aus-3d" onPointerDown={(e) => e.stopPropagation()}>
      <span className="vis-node-kamera-zeile" data-testid="kamera-aus-3d-auge">
        Auge {p} m
      </span>
      <span className="vis-node-kamera-zeile" data-testid="kamera-aus-3d-blickfeld">
        Blickfeld waagrecht {Number.isFinite(fovH) ? `${Math.round(fovH)}°` : '—'} ({fuer})
      </span>
      <span className="vis-node-kamera-nicht-bestellt vis-node-kamera-zeile" data-testid="kamera-aus-3d-shift">
        ohne Objektiv-Shift
      </span>
      {umgebungSatz && (
        <KTooltip text={umgebungSatz} lage="unten" className="vis-bild-kachel-grund-huelle">
          <span
            tabIndex={0}
            className={
              umgebungMit
                ? 'vis-node-kamera-nicht-bestellt vis-bild-kachel-grund-zeile'
                : 'vis-bild-kachel-qa-vorbehalt vis-bild-kachel-grund-zeile'
            }
            data-testid="kamera-aus-3d-umgebung"
          >
            {umgebungSatz}
          </span>
        </KTooltip>
      )}
      {knopf}
    </div>
  );
}
