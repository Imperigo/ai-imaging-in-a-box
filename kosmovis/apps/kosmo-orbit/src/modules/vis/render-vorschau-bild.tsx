import { useEffect, useState } from 'react';
import { ZWISCHENBILD_BLEIBT } from './render-warteort';
import { bildBlob } from './vis-jobs';

/**
 * Zwischenbild eines laufenden Renders (R37 `progress.vorschau`, Video L5-16/Nr. 71) im Warteplatz des
 * Render-Knotens: das Cycles-Bild der zuletzt fertigen Kamera. Geholt wie `BridgeBild` (Blob über
 * `bridgeFetch`, Token und CSP), aber **still**: bis das Bild da ist und wenn es nicht kommt, zeichnet es
 * nichts — der Warteplatz trägt schon Text und Balken, ein zweites «Bild wird geholt» läge darüber.
 *
 * Blatt 29 (B): steht das Bild, trägt es oben seine Beschriftung («Zwischenbild — Kamera 1, fertig») und den Satz
 * «Das Zwischenbild bleibt beim Abbrechen.» — erst dann, nie über einem leeren Platz.
 */
export function RenderVorschauBild({ jobId, imageName, text }: { jobId: string; imageName: string; text?: string | undefined }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    let weg = false;
    let objektUrl: string | null = null;
    void bildBlob(jobId, imageName)
      .then((blob) => {
        if (weg) return;
        objektUrl = URL.createObjectURL(blob);
        setUrl(objektUrl);
      })
      .catch(() => {});
    return () => {
      weg = true;
      if (objektUrl) URL.revokeObjectURL(objektUrl);
    };
  }, [jobId, imageName]);
  if (!url) return null;
  const beschriftung = text ?? 'Zwischenbild — letzte fertige Kamera';
  return (
    <>
      <img src={url} alt={beschriftung} className="vis-node-warteort-vorschau" data-testid="render-vorschau" />
      <span className="vis-node-warteort-vorschau-text" data-testid="render-vorschau-text">
        <span className="vis-node-warteort-vorschau-titel">{beschriftung}</span> {ZWISCHENBILD_BLEIBT}
      </span>
    </>
  );
}
