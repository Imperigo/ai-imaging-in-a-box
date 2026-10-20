import { useEffect, useState } from 'react';
import { bildBlob } from './vis-jobs';

/**
 * Zwischenbild eines laufenden Renders (R37 `progress.vorschau`, Video L5-16/Nr. 71) im Warteplatz des
 * Render-Knotens: das Cycles-Bild der zuletzt fertigen Kamera. Geholt wie `BridgeBild` (Blob über
 * `bridgeFetch`, Token und CSP), aber **still**: bis das Bild da ist und wenn es nicht kommt, zeichnet es
 * nichts — der Warteplatz trägt schon Text und Balken, ein zweites «Bild wird geholt» läge darüber.
 */
export function RenderVorschauBild({ jobId, imageName }: { jobId: string; imageName: string }) {
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
  return <img src={url} alt="Zwischenbild der letzten fertigen Kamera" className="vis-node-warteort-vorschau" data-testid="render-vorschau" />;
}
