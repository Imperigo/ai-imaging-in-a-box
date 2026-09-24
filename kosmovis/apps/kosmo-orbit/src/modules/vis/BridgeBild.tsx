import { useEffect, useState } from 'react';
import { bildBlob } from './vis-jobs';

/**
 * Bridge-Artefakt als Bild (HS3-Nachbesserung/Fable-Auflage 1). Ein direktes
 * `<img src="http://localhost:8600/…">` wird von der CSP `img-src` geblockt
 * (seit Serie I/B2) UND kann keinen Token-Header tragen — es zeigte still ein
 * kaputtes 16×16-Kästchen, während `toBeVisible()` grün blieb. Darum: das
 * Artefakt per `bridgeFetch` (Token + connect-src) als Blob holen und als
 * `blob:`-URL rendern (img-src erlaubt `blob:`). Fehlt/scheitert das Bild,
 * steht ein ehrlicher Hinweis statt eines toten Rahmens.
 */
export function BridgeBild({
  jobId,
  imageName,
  alt,
  testid,
  style,
  className,
}: {
  jobId: string;
  imageName: string;
  alt: string;
  testid?: string;
  style?: React.CSSProperties;
  /** v0.8.0B / P5 (Spez §3 B-22, Inline-Styles raus): additiv neben `style` —
   * der Aufrufer bringt sein Aussehen jetzt meist über eine Klasse mit. */
  className?: string;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [fehler, setFehler] = useState(false);

  useEffect(() => {
    let abgebrochen = false;
    let objektUrl: string | null = null;
    setFehler(false);
    setUrl(null);
    void bildBlob(jobId, imageName)
      .then((blob) => {
        if (abgebrochen) return;
        objektUrl = URL.createObjectURL(blob);
        setUrl(objektUrl);
      })
      .catch(() => {
        if (!abgebrochen) setFehler(true);
      });
    return () => {
      abgebrochen = true;
      if (objektUrl) URL.revokeObjectURL(objektUrl);
    };
  }, [jobId, imageName]);

  if (fehler) {
    return (
      <div
        data-testid={testid ? `${testid}-fehler` : undefined}
        className={className}
        style={{ ...style, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: 'var(--k-danger)', border: '1px dashed var(--k-line-strong)', minHeight: 60 }}
      >
        Bild nicht ladbar
      </div>
    );
  }
  if (!url) {
    return (
      <div
        className={className}
        style={{ ...style, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: 'var(--k-ink-faint)', border: '1px dashed var(--k-line)', minHeight: 60 }}
      >
        lädt …
      </div>
    );
  }
  return <img src={url} alt={alt} data-testid={testid} className={className} style={style} />;
}
