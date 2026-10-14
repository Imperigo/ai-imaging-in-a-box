import { alsPng, type Kachel } from '@kosmo/kernel';

/**
 * P16 — eine Kachel aus `derive/textur.ts` als anzeigbare/downloadbare
 * `blob:`-URL.
 *
 * `alsPng()` liefert bereits echte PNG-Bytes, ohne Canvas (der ganze Sinn
 * der Datei, s. deren Kopfkommentar: der Kern hat kein DOM). Diese Funktion
 * kodiert darum NICHT ein zweites Mal ueber ein `<canvas>` (Muster
 * `bild-rechnen.ts`s `alsDataUrl`) — sie packt die Bytes nur in einen Blob.
 *
 * Der Aufrufer raeumt mit `URL.revokeObjectURL` ab, sobald die URL nicht
 * mehr gezeigt wird (Muster `bild-rechnen.ts`s `quellUrl`) — sonst haeuft
 * jeder Klick eine weitere URL im Speicher des Browsers an.
 */
export function kachelBlobUrl(k: Kachel): string {
  const bytes = alsPng(k);
  // `Uint8Array<ArrayBufferLike>` (generischer Puffertyp seit neueren
  // TS-Lib-Definitionen) ist kein `BlobPart` — `Uint8Array.from()` kopiert
  // auf einen echten `ArrayBuffer`, ohne die Bytes zweimal zu kodieren.
  const blob = new Blob([Uint8Array.from(bytes)], { type: 'image/png' });
  return URL.createObjectURL(blob);
}
