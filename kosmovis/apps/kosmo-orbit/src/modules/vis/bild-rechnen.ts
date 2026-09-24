// NAHT GESCHLOSSEN (16.09.2026): `belichtung` kam wie seine zwei Nachbarn
// aus dem Paket selbst, nicht mehr ueber einen Dateipfad quer durch die
// Paketgrenze. A3 hatte die fehlende Zeile beschrieben und durfte `index.ts`
// nicht anfassen; sie steht jetzt dort.
import {
  BELICHTUNG_WAS_GEAENDERT_WURDE,
  HEBUNG_VORGABE,
  WAS_GEAENDERT_WURDE,
  belichtung,
  UEBERNAHME_BEREICH_LABEL,
  UEBERNAHME_BEREICH_VORBEHALT,
  UEBERNAHME_EIGENSCHAFT_LABEL,
  UEBERNAHME_WAS_GEAENDERT_WURDE,
  farbangleich,
  nachbearbeitung,
  uebernahme,
  type BereichName,
  type Bild,
  type BelichtungBericht,
  type EigenschaftName,
  type UebernahmeBericht,
  type UebernahmePosten,
} from '@kosmo/kernel';
// NAHT GESCHLOSSEN (17.09.2026): `uebernahme` kommt wie seine drei Nachbarn
// aus dem Paket selbst. Der Erbauer hatte den Dateipfad als vorlaeufigen Weg
// gewaehlt und die fehlende Exportzeile gemeldet, statt eine fremde Datei
// anzufassen — genau richtig; sie steht jetzt dort. Das war beim dritten
// Modul (`belichtung`) dieselbe Lage und dieselbe Loesung.
import { melde, meldeFehler } from '@kosmo/ui';
import { bescheideBridgeCatch, bildBlob } from './vis-jobs';
import { useVisRuntime, type GehobenesBild, type GerechnetesBild } from './vis-runtime';
import type { KuratierQuelle } from './varianten-diff';

/**
 * Die Griffe ins fertige Bild — zwei angeschlossen (12.09.2026), der dritte
 * dazu (16.09.2026), der vierte am 17.09.2026.
 *
 * DER VIERTE ist `uebernahme` (Abnahmeliste Zeile 54): aus einem Vorbild
 * EINZELNE, BENANNTE Eigenschaften holen — und nur diese. Er sitzt neben dem
 * Farbangleich, weil er dessen Berichtigung ist: «sry nur decke uebernehmen»
 * (08:00) folgt auf «nutze sie um einen grund ai imaging layer zu erstellen»
 * (07:16). Der Farbangleich nimmt das Vorbild als Ganzes; Zeile 54 verlangt
 * eine Auswahl — WAS (Farbton, Sättigung, Helligkeit einzeln) und WO (ein
 * gemessener Bereich). Seine Ablage liegt vorläufig in DIESER Datei; warum,
 * steht bei `UebernommenesBild`.
 *
 * DER DRITTE ist `belichtung` (Abnahmeliste Zeile 49): das Bild heller
 * stellen, ohne dass der Aussenraum ausbrennt. Er gehört an dieselbe Stelle
 * wie die zwei anderen und aus demselben Grund — nur nimmt er als Eingabe
 * das, was gerade ZU SEHEN ist, statt immer das Original: der Zuruf lautet
 * «DANACH bitte bild noch minimal grundsätzlich heller als aktuell». Zwei
 * Stellen, an denen er sich heute noch von den zwei anderen unterscheidet,
 * stehen weiter unten benannt (Import-Pfad, `BelichtungAnzeige`); beide sind
 * je eine Zeile in einer Datei, die dieser Lauf nicht anfassen durfte.
 *
 * WAS HIER ANGESCHLOSSEN WIRD: `packages/kosmo-kernel/src/bild/farbangleich.ts`
 * und `.../nachbearbeitung.ts`, beide seit dem 10.09.2026 fertig, gegen die
 * Python-Vorlage Byte für Byte gemessen — und von keiner Datei dieser
 * Anwendung importiert. Sie konnten rechnen; es gab nur keinen Weg, ihnen ein
 * Bild zu geben und keinen Ort für das Ergebnis.
 *
 * WO SIE HINGEHÖREN — GEMESSEN, NICHT GEWÄHLT: ein fertiges Bild taucht in
 * dieser Oberfläche an genau vier Stellen auf. Am Render-Node
 * (`NodeCanvas.tsx`, `BridgeBild`), im Aufnahme-Node (dieselbe Datei,
 * `dataUrl`), als Karte in der Kuratierfläche und — gross, mit Meta-Zeilen,
 * Herkunft, Bewertung und «Ins Projekt übernehmen» — im Kurations-Inspektor
 * (`KuratierInspektor.tsx`). Die ersten drei ZEIGEN ein Bild; die vierte ist
 * die Stelle, an der man mit einem fertigen Bild etwas TUT. Dorthin gehört
 * ein Griff ins fertige Bild, und nirgendwo sonst wurde dafür eine Stelle
 * erfunden.
 *
 * WAS ES NICHT GAB, und was darum neu ist: einen Ort für das ERGEBNIS.
 * `NodeLauf.bild` ist ein Dateiname auf der Brücke, kein Bildinhalt;
 * `Aufnahme.dataUrl` gehört dem Aufnahme-Node. Das Rechenergebnis liegt
 * darum in `vis-runtime.ts` als `GerechnetesBild` — Laufzeit, wie jedes
 * andere Bild in dieser Station (s. dortiger Kommentar).
 *
 * DAS ORIGINAL BLEIBT UNANGETASTET. Das gerechnete Bild liegt DARÜBER, in
 * einer eigenen Ablage, und ein Klick wirft es weg. Weder das Job-Artefakt
 * auf der Brücke noch die Viewport-Aufnahme wird überschrieben — sonst wäre
 * die einzige Fassung des Bildes eine, die niemand mehr zurücknehmen kann.
 *
 * KEIN CANVAS IM KERN: die beiden Kernmodule nehmen rohe Bildpunkte und
 * kennen weder DOM noch Dateisystem («der Kern läuft im Web Worker»). Das
 * Laden und Zurückschreiben ist darum Sache dieser Datei — hier gibt es ein
 * `<canvas>`, und es kommt keine Abhängigkeit dazu.
 */

/** Die Zusage der Nachbearbeitung, wörtlich aus deren Kopfkommentar. */
const ZUSAGE_NACHBEARBEITUNG =
  'nur Helligkeit und Sättigung innerhalb einer gemessenen Maske; kein Bildpunkt wandert, ' +
  'nichts entsteht, nichts verschwindet';

/**
 * Bildpunkte aus einer Bild-URL holen.
 *
 * `createImageBitmap` + `OffscreenCanvas` wären knapper, sind aber nicht
 * überall da (und in der Testumgebung dieser App gar nicht) — `<img>` +
 * `<canvas>` ist der Weg, den jeder Browser trägt, den diese Anwendung
 * unterstützt.
 *
 * `kanaele: 4`, weil `getImageData` immer RGBA liefert. Beide Kernmodule
 * reichen den Alphakanal unverändert durch — er gehört nicht zur
 * Farbstimmung.
 */
async function bildpunkteAus(url: string): Promise<Bild> {
  const img = new Image();
  // Die Brücken-Bilder kommen als `blob:`-URL derselben Herkunft, die
  // Aufnahmen als `data:` — beides braucht kein CORS. Der Wert steht
  // trotzdem, weil ein späteres `http:`-Bild sonst ein «getaintes» Canvas
  // ergäbe und `getImageData` mit einem Sicherheitsfehler abbräche, den
  // niemand mit dem Bild in Verbindung brächte.
  img.crossOrigin = 'anonymous';
  await new Promise<void>((fertig, fehler) => {
    img.onload = () => fertig();
    img.onerror = () => fehler(new Error('Das Bild liess sich nicht laden.'));
    img.src = url;
  });
  const breite = img.naturalWidth;
  const hoehe = img.naturalHeight;
  if (!(breite > 0) || !(hoehe > 0)) {
    throw new Error('Das Bild hat keine messbare Grösse.');
  }
  const flaeche = document.createElement('canvas');
  flaeche.width = breite;
  flaeche.height = hoehe;
  const stift = flaeche.getContext('2d');
  if (!stift) throw new Error('Diese Umgebung stellt kein 2D-Canvas bereit.');
  stift.drawImage(img, 0, 0);
  const daten = stift.getImageData(0, 0, breite, hoehe);
  return { daten: daten.data, breite, hoehe, kanaele: 4 };
}

/** Bildpunkte zurück in eine PNG-dataURL. */
function alsDataUrl(bild: Bild): string {
  const flaeche = document.createElement('canvas');
  flaeche.width = bild.breite;
  flaeche.height = bild.hoehe;
  const stift = flaeche.getContext('2d');
  if (!stift) throw new Error('Diese Umgebung stellt kein 2D-Canvas bereit.');
  // IMMER kopieren statt `instanceof`-Weiche: `ImageData` verlangt ein
  // `Uint8ClampedArray` ueber einem echten `ArrayBuffer`, der Kern gibt das
  // Feld aber als `Uint8ClampedArray | Uint8Array` ueber einem beliebigen
  // Puffer zurueck (er laeuft im Worker und darf dort auch auf einem
  // geteilten Puffer rechnen). Die Kopie ist ein Durchlauf ueber die
  // Bildpunkte — an einem 1600x1000-Bild Millisekunden — und spart die
  // Klasse von Fehlern, die erst auf einer anderen Maschine auftritt.
  const feld = new ImageData(Uint8ClampedArray.from(bild.daten), bild.breite, bild.hoehe);
  stift.putImageData(feld, 0, 0);
  // PNG, nicht JPEG: ein Werkzeug, das ausdrücklich keinen Bildpunkt
  // verschiebt, darf sein Ergebnis nicht durch eine verlustbehaftete
  // Kompression schicken — die Zusage wäre danach nicht mehr messbar.
  return flaeche.toDataURL('image/png');
}

/**
 * Eine Kuratier-Quelle in eine URL auflösen, aus der Bildpunkte kommen.
 *
 * Zwei Fälle, wie überall in dieser Station: eine Viewport-Aufnahme trägt
 * ihre `dataUrl` selbst, ein Brücken-Artefakt muss geholt werden (per
 * `bridgeFetch` mit Token — ein direktes `<img src="http://localhost:8600/…">`
 * blockiert die CSP, s. `BridgeBild.tsx`).
 *
 * Der zweite Rückgabewert räumt die `blob:`-URL wieder ab; wer ihn nicht
 * ruft, lässt Speicher liegen.
 */
async function quellUrl(quelle: KuratierQuelle): Promise<{ url: string; abraeumen: () => void }> {
  if ('dataUrl' in quelle) return { url: quelle.dataUrl, abraeumen: () => {} };
  const blob = await bildBlob(quelle.jobId, quelle.bild);
  const url = URL.createObjectURL(blob);
  return { url, abraeumen: () => URL.revokeObjectURL(url) };
}

function zahl(v: number, stellen = 2): string {
  return v.toFixed(stellen);
}

/**
 * Der Bericht der Nachbearbeitung in Klartextzeilen.
 *
 * Die Zahlen sind die GEMESSENEN Maskenflächen und die Werte vorher/nachher
 * — genau das, was das Kernmodul mitliefert, damit nachprüfbar bleibt, ob
 * eine Maske das Richtige getroffen hat.
 */
function berichtNachbearbeitung(b: ReturnType<typeof nachbearbeitung>['bericht']): string[] {
  return [
    `Bild ${b.bild[0]} × ${b.bild[1]}`,
    `Decke: Faktor ${zahl(b.decke.faktor)}, Maske über ${zahl(b.decke.hoeheAnteil)} der Bildhöhe, ` +
      `${zahl(b.decke.erfassteFlaecheProzent, 1)} % der Fläche erfasst`,
    `Oberes Fünftel R/G/B: ${b.decke.oberesFuenftelVorher.map((v) => zahl(v, 1)).join('/')} → ` +
      `${b.decke.oberesFuenftelNachher.map((v) => zahl(v, 1)).join('/')}`,
    `Grün: Faktor ${zahl(b.gruen.faktor)}, ${zahl(b.gruen.erfassteFlaecheProzent, 1)} % der Fläche erfasst, ` +
      `Sättigung ${zahl(b.gruen.saettigungImGruenVorher, 3)} → ${zahl(b.gruen.saettigungImGruenNachher, 3)}`,
  ];
}

/** Der Bericht des Farbangleichs in Klartextzeilen. */
function berichtFarbangleich(e: ReturnType<typeof farbangleich>): string[] {
  const m = (v: { mittel: number; saettigung: number; schwarzpunkt: number; rbSchatten: number }) =>
    `Helligkeit ${zahl(v.mittel, 3)}, Sättigung ${zahl(v.saettigung, 3)}, ` +
    `Schwarzpunkt ${zahl(v.schwarzpunkt, 3)}, Rot−Blau im Schatten ${zahl(v.rbSchatten, 1)}`;
  return [
    `Stärke ${zahl(e.staerke)}, Kennlinie aus ${e.kennlinien[0].length} Stützstellen je Kanal`,
    `vorher:  ${m(e.vorher)}`,
    `Vorbild: ${m(e.vorbildWerte)}`,
    `nachher: ${m(e.nachher)}`,
  ];
}

/**
 * Die zwei gemessenen Masken auf ein fertiges Bild anwenden (Deckenholz
 * dunkler, Grün kräftiger — die Vorgaben der Vorlage).
 *
 * Rechnet im Hauptfaden. An einem 1600×1000-Bild sind das 1.6 Mio.
 * Bildpunkte; das Kernmodul misst seine grosse Probe an 376 000 und läuft
 * dort in Millisekunden. Ein Web Worker wäre sauberer und ist hier bewusst
 * NICHT gebaut: er brächte eine zweite Bau-Naht (Worker-Bündelung), und ob
 * sie nötig ist, ist ungemessen. Wird das Bild spürbar gross, ist DAS der
 * Moment für den Worker — nicht vorher.
 */
export async function rechneNachbearbeitung(nodeId: string, quelle: KuratierQuelle): Promise<void> {
  let abraeumen = () => {};
  try {
    const { url, abraeumen: weg } = await quellUrl(quelle);
    abraeumen = weg;
    const ergebnis = nachbearbeitung(await bildpunkteAus(url));
    const eintrag: GerechnetesBild = {
      dataUrl: alsDataUrl(ergebnis.bild),
      art: 'nachbearbeitung',
      bericht: berichtNachbearbeitung(ergebnis.bericht),
      zusage: ZUSAGE_NACHBEARBEITUNG,
    };
    useVisRuntime.getState().setzeGerechnetesBild(nodeId, eintrag);
    melde(
      `Nachbearbeitet: Decke ${zahl(ergebnis.bericht.decke.erfassteFlaecheProzent, 1)} %, ` +
        `Grün ${zahl(ergebnis.bericht.gruen.erfassteFlaecheProzent, 1)} % der Fläche erfasst. ` +
        'Das Original bleibt darunter liegen.',
      { ton: 'erfolg' },
    );
  } catch (err) {
    // Der Brücken-Zweig ist ein `bridgeFetch` — derselbe Übersetzer wie
    // überall sonst in dieser Station, damit ein 401 nicht als «offline»
    // erscheint (s. `bescheideBridgeCatch`).
    if ('jobId' in quelle) await bescheideBridgeCatch(err);
    else meldeFehler(err);
  } finally {
    abraeumen();
  }
}

/**
 * Die Farbstimmung eines ANDEREN Bildes auf dieses übertragen
 * (Histogrammangleich je Kanal).
 *
 * `vorbild` ist eine zweite Karte derselben Fläche — es gibt in dieser
 * Oberfläche keine andere Quelle für ein Vorbild, und eine zu erfinden
 * (mitgelieferte «Stimmungen») hiesse, eine Farbe zu behaupten, die aus
 * keinem Bild dieses Projekts stammt. Gibt es keine zweite Karte, bietet der
 * Inspektor den Knopf gar nicht erst an und sagt warum.
 */
export async function rechneFarbangleich(
  nodeId: string,
  quelle: KuratierQuelle,
  vorbild: KuratierQuelle,
  staerke = 1.0,
): Promise<void> {
  let abraeumenA = () => {};
  let abraeumenB = () => {};
  try {
    const a = await quellUrl(quelle);
    abraeumenA = a.abraeumen;
    const b = await quellUrl(vorbild);
    abraeumenB = b.abraeumen;
    const ergebnis = farbangleich(await bildpunkteAus(a.url), await bildpunkteAus(b.url), { staerke });
    const eintrag: GerechnetesBild = {
      dataUrl: alsDataUrl(ergebnis.bild),
      art: 'farbangleich',
      bericht: berichtFarbangleich(ergebnis),
      // Wörtlich die Zusage des Kernmoduls (`WAS_GEAENDERT_WURDE`) — nicht
      // nacherzählt, damit Zusage und Rechnung an einer Stelle gepflegt
      // bleiben.
      zusage: WAS_GEAENDERT_WURDE,
    };
    useVisRuntime.getState().setzeGerechnetesBild(nodeId, eintrag);
    melde(
      `Farbe angeglichen (Stärke ${zahl(staerke)}): Helligkeit ${zahl(ergebnis.vorher.mittel, 3)} → ` +
        `${zahl(ergebnis.nachher.mittel, 3)}, Vorbild ${zahl(ergebnis.vorbildWerte.mittel, 3)}. ` +
        'Das Original bleibt darunter liegen.',
      { ton: 'erfolg' },
    );
  } catch (err) {
    if ('jobId' in quelle || 'jobId' in vorbild) await bescheideBridgeCatch(err);
    else meldeFehler(err);
  } finally {
    abraeumenA();
    abraeumenB();
  }
}

/**
 * Das Ergebnis einer Belichtung, so wie der Inspektor es anzeigt.
 *
 * SEIT 17.09.2026 IM STORE, wie die zwei Nachbarn. Vorher lag es in einem
 * `useState` des Inspektors, weil `GerechnetesBild.art` nur zwei Werte kannte
 * und `vis-runtime.ts` damals einem anderen Agenten gehörte. Der Unterschied
 * war benannt und real: die Belichtung überlebte keinen Neuaufbau der
 * Komponente, die zwei Nachbarn schon.
 *
 * Die Lösung ist NICHT ein dritter Wert in `art` geworden, sondern eine
 * EIGENE Ablage (`gehobeneBilder`). Grund: die Belichtung ersetzt die zwei
 * anderen nicht, sie liegt darüber und rechnet auf deren Ergebnis — der Zuruf
 * sagt «DANACH». In dieselbe Ablage geschrieben wäre die Schicht darunter
 * verloren, und «Belichtung zurücknehmen» käme nirgends mehr hin.
 */
export type BelichtungAnzeige = GehobenesBild;

// ---------------------------------------------------------------------------
// Zeile 54 — nur benannte Eigenschaften aus einem Vorbild übernehmen
// ---------------------------------------------------------------------------

/**
 * Das Ergebnis einer Übernahme, so wie der Inspektor es anzeigt.
 *
 * Es liegt in derselben SCHICHT wie Farbangleich und Nachbearbeitung, nicht
 * darüber: «sry nur decke uebernehmen» (08:00) ist die BERICHTIGUNG des
 * Farbangleichs von 07:16, kein zweiter Griff daneben. Die Belichtung («danach
 * bitte bild noch minimal grundsätzlich heller») rechnet weiterhin auf dem,
 * was darunter liegt — also auch auf einer Übernahme.
 */
/**
 * Das Ergebnis einer Uebernahme, so wie der Inspektor es anzeigt.
 *
 * SEIT 17.09.2026 IST DAS EIN `GerechnetesBild` — dieselbe Ablage wie
 * Farbangleich und Nachbearbeitung, nicht eine eigene daneben.
 *
 * WARUM DIESELBE UND NICHT EINE EIGENE: die Uebernahme liegt in DERSELBEN
 * Schicht wie die zwei anderen — sie ERSETZT den Farbangleich, sie stapelt
 * sich nicht darauf. In getrennten Ablagen bliebe der Farbangleich darunter
 * liegen und kaeme beim Zuruecknehmen der Uebernahme wieder zum Vorschein:
 * ein Bild, das niemand zurueckgeholt hat. Der Erbauer hatte die getrennte
 * Ablage als vorlaeufigen Weg gewaehlt, ihre Kosten offen benannt und die
 * fehlende Zeile gemeldet, statt eine fremde Datei anzufassen — genau
 * richtig. Sie steht jetzt dort.
 *
 * DER UNTERSCHIED ZUR BELICHTUNG, damit niemand sie zusammenlegt: die liegt
 * wirklich DARUEBER und rechnet auf dem Ergebnis dieser drei. Darum hat sie
 * eine eigene Ablage (`gehobeneBilder`) — und `verwirfGerechnetesBild`
 * raeumt sie mit weg, weil ihr Bericht sonst zu einer Grundlage gehoerte,
 * die es nicht mehr gibt.
 */
export type UebernommenesBild = GerechnetesBild & { nodeId: string };

/**
 * Der Bericht der Übernahme in Klartextzeilen.
 *
 * ER NENNT AUCH, WAS SICH NICHT BEWEGT HAT — und das ist bei dieser Zeile der
 * eigentliche Punkt. «Und nur diese» ist sonst ein Versprechen; hier steht es
 * als Zahl: wieviele Bildpunkte die nicht benannten Grössen bewegt haben und
 * um wieviel höchstens.
 */
function berichtUebernahme(b: UebernahmeBericht): string[] {
  const zeilen = [
    `Bild ${b.bild[0]} × ${b.bild[1]}, Vorbild ${b.vorbild[0]} × ${b.vorbild[1]}`,
  ];
  for (const p of b.posten) {
    const kopf =
      `${UEBERNAHME_EIGENSCHAFT_LABEL[p.eigenschaft]} aus «${UEBERNAHME_BEREICH_LABEL[p.bereich]}»` +
      (p.staerke === 1 ? '' : ` (Stärke ${zahl(p.staerke)})`) +
      `: ${zahl(p.erfassteFlaecheProzent, 1)} % der Fläche erfasst`;
    zeilen.push(kopf);
    if (p.eigenschaft === 'farbton') {
      zeilen.push(
        `  Farbton ${zahl(p.wertVorher, 1)}° → Vorbild ${zahl(p.wertVorbild, 1)}° ` +
          `= Drehung ${zahl(p.drehungGrad ?? 0, 1)}°, danach ${zahl(p.wertNachher, 1)}° ` +
          `(Bündelung ${zahl(p.buendelungBild ?? 0, 2)} / ${zahl(p.buendelungVorbild ?? 0, 2)})`,
      );
    } else {
      zeilen.push(
        `  ${zahl(p.wertVorher, 1)} → Vorbild ${zahl(p.wertVorbild, 1)} → danach ` +
          `${zahl(p.wertNachher, 1)} Byte, Kennlinie aus ${p.kennlinie?.length ?? 0} Stützstellen`,
      );
      if (p.farblosUebergangenProzent !== undefined && p.farblosUebergangenProzent > 0) {
        zeilen.push(
          `  ${zahl(p.farblosUebergangenProzent, 1)} % der erfassten Fläche ist farblos und blieb ` +
            'unangetastet — sonst hätte die Rechnung dort eine Farbe erfunden.',
        );
      }
    }
    if (p.vorbildGanz) {
      zeilen.push('  Im Vorbild wurde das ganze Bild gemessen — es lag keine Vorbild-Maske vor.');
    }
  }
  const g = b.eigenschaftenGesamt;
  zeilen.push(
    `Unangetastet: ${zahl(b.ausserhalbProzent, 1)} % der Fläche liegt in keinem Bereich, ` +
      `${zahl(b.unveraenderteBildpunkteProzent, 1)} % der Bildpunkte sind Byte für Byte gleich`,
  );
  zeilen.push(
    `Farbton höchstens ${zahl(g.farbton.groessteAbweichung, 2)}° bewegt (${g.farbton.bildpunkteBewegt} Punkte), ` +
      `Sättigung ${zahl(g.saettigung.groessteAbweichung, 2)} Byte (${g.saettigung.bildpunkteBewegt}), ` +
      `Helligkeit ${zahl(g.helligkeit.groessteAbweichung, 2)} Byte (${g.helligkeit.bildpunkteBewegt})`,
  );
  if (b.ueberlappungProzent > 0) {
    zeilen.push(
      `${zahl(b.ueberlappungProzent, 1)} % der Fläche liegt in mehr als einem Bereich — ` +
        'dort wirken mehrere Posten auf denselben Bildpunkt.',
    );
  }
  return zeilen;
}

/**
 * Aus einem Vorbild EINZELNE, BENANNTE Eigenschaften übernehmen — und nur
 * diese (Abnahmeliste Zeile 54).
 *
 * Der Unterschied zum Farbangleich daneben ist die AUSWAHL, und zwar in zwei
 * Richtungen: WAS (Farbton, Sättigung, Helligkeit — einzeln) und WO
 * (ein gemessener Bereich statt des ganzen Bildes). Der Zuruf, der das
 * verlangt hat, nennt beides in einem Satz: «wir uebernehmen von diesem
 * referenzbild die saettigung und farbe der decke».
 *
 * `quelle` ist das ORIGINAL der Karte und nicht das, was gerade zu sehen ist:
 * eine Übernahme ersetzt einen Farbangleich, sie stapelt sich nicht darauf.
 *
 * Gibt `null` zurück, wenn etwas schiefging; gemeldet wurde dann schon.
 */
export async function rechneUebernahme(
  nodeId: string,
  quelle: KuratierQuelle,
  vorbild: KuratierQuelle,
  vorbildLabel: string,
  eigenschaften: readonly EigenschaftName[],
  bereich: BereichName,
): Promise<UebernommenesBild | null> {
  let abraeumenA = () => {};
  let abraeumenB = () => {};
  try {
    const a = await quellUrl(quelle);
    abraeumenA = a.abraeumen;
    const b = await quellUrl(vorbild);
    abraeumenB = b.abraeumen;
    const posten: UebernahmePosten[] = eigenschaften.map((eigenschaft) => ({ eigenschaft, bereich }));
    const ergebnis = uebernahme(await bildpunkteAus(a.url), await bildpunkteAus(b.url), { posten });
    const benannt = eigenschaften.map((e) => UEBERNAHME_EIGENSCHAFT_LABEL[e]).join(' und ');
    const eintrag: UebernommenesBild = {
      nodeId,
      art: 'uebernahme',
      dataUrl: alsDataUrl(ergebnis.bild),
      bericht: berichtUebernahme(ergebnis.bericht),
      // Wörtlich die Zusage des Kernmoduls — dieselbe Regel wie bei den drei
      // Nachbarn: Zusage und Rechnung bleiben an einer Stelle gepflegt.
      zusage: UEBERNAHME_WAS_GEAENDERT_WURDE,
      kopfzeile:
        `${benannt} aus «${vorbildLabel}», nur im Bereich ` +
        `«${UEBERNAHME_BEREICH_LABEL[bereich]}» — gerechnet, nicht erzeugt.`,
    };
    useVisRuntime.getState().setzeGerechnetesBild(nodeId, eintrag);
    melde(
      `Übernommen: ${benannt} aus «${vorbildLabel}» im Bereich ` +
        `«${UEBERNAHME_BEREICH_LABEL[bereich]}» — ` +
        `${zahl(ergebnis.bericht.unveraenderteBildpunkteProzent, 1)} % der Bildpunkte sind ` +
        'Byte für Byte unverändert geblieben. Das Original bleibt darunter liegen.',
      { ton: 'erfolg' },
    );
    return eintrag;
  } catch (err) {
    if ('jobId' in quelle || 'jobId' in vorbild) await bescheideBridgeCatch(err);
    else meldeFehler(err);
    return null;
  } finally {
    abraeumenA();
    abraeumenB();
  }
}

/** Der Vorbehalt eines Bereichs — was er wirklich erfasst, nicht was er heisst. */
export function bereichsVorbehalt(bereich: BereichName): string {
  return UEBERNAHME_BEREICH_VORBEHALT[bereich];
}

/**
 * Was die Oberfläche zur Auswahl stellt. Hier gebündelt, damit der Pfad quer
 * durch die Paketgrenze (s. Kopf) an EINER Stelle steht und nicht in zwei.
 */
export const UEBERNAHME_EIGENSCHAFTEN: readonly EigenschaftName[] = [
  'farbton',
  'saettigung',
  'helligkeit',
];

/**
 * Die wählbaren Bereiche — `eigeneMaske` ist BEWUSST NICHT dabei.
 *
 * Sie nähme eine fertige Maske von aussen entgegen, und die gibt es in dieser
 * Oberfläche noch nicht: das Material-Bild aus dem Renderlauf ist Zeile 59 und
 * liegt in Welle 5 an der Fremdnaht. Ein Eintrag, den man wählen kann und der
 * dann nur den Ablehnungstext des Kerns vorführt, wäre eine Attrappe.
 */
export const UEBERNAHME_BEREICHE: readonly BereichName[] = [
  'deckenholz',
  'bewuchs',
  'helleFlaechen',
  'ganzesBild',
];

/** Beschriftungen, wörtlich aus dem Kernmodul. */
export const EIGENSCHAFT_LABEL = UEBERNAHME_EIGENSCHAFT_LABEL;
export const BEREICH_LABEL = UEBERNAHME_BEREICH_LABEL;
export type { BereichName, EigenschaftName };

/**
 * Was Zeile 54 verlangt hat und aus einem fertigen Bild NICHT zu holen ist —
 * wörtlich für die Oberfläche, damit dort kein Regler steht, der es
 * verspricht.
 *
 * Der Zuruf nennt sechs Wünsche; drei rechnet dieses Werkzeug, zwei kann
 * grundsätzlich kein Bildwerkzeug, und bei zweien fehlt der Bereich. Die
 * Begründung steht Wunsch für Wunsch im Kopf von `bild/uebernahme.ts`.
 */
export const UEBERNAHME_WAS_FEHLT =
  'Vorhang, Esstisch und Küchenfront lassen sich in einem fertigen Bild nicht als Bauteil ' +
  'ansprechen — dafür fehlt ein Material-Bild aus dem Renderlauf. Durchlässigkeit und Textur ' +
  'sind gar keine Eigenschaften eines Bildes; die gehören ans Modell.';

/** Der Bericht der Belichtung in Klartextzeilen. */
function berichtBelichtung(b: BelichtungBericht): string[] {
  const zeilen = [
    `Bild ${b.bild[0]} × ${b.bild[1]}, Hebung ${zahl(b.hebungAngewendet, 3)}`,
    `Maske über dem Spitzkanal max(R,G,B), Knie ${zahl(b.schutzUnten)}/${zahl(b.schutzOben)}: ` +
      `${zahl(b.vollGehoben.anteilProzent, 1)} % voll gehoben, ` +
      `${zahl(b.teilweise.anteilProzent, 1)} % teilweise, ` +
      `${zahl(b.unangetastet.anteilProzent, 1)} % unangetastet`,
    `Gehobene Fläche ${zahl(b.vollGehoben.vorher, 1)} → ${zahl(b.vollGehoben.nachher, 1)} Byte, ` +
      `Lichter ${zahl(b.unangetastet.vorher, 1)} → ${zahl(b.unangetastet.nachher, 1)} Byte`,
    `Ausgebrannt ${zahl(b.ausgebranntVorherProzent, 4)} → ${zahl(b.ausgebranntNachherProzent, 4)} %, ` +
      `Sättigung ${zahl(b.saettigungVorher, 4)} → ${zahl(b.saettigungNachher, 4)}`,
  ];
  // Die Klemmung wird NUR dann gemeldet, wenn sie greift — aber dann
  // ungekürzt. Eine Hebung still kleiner zu rechnen als verlangt, ohne es zu
  // sagen, wäre genau die Sorte Beschönigung, gegen die der Bericht da ist.
  if (b.geklemmt) {
    zeilen.push(
      `Angefragt war ${zahl(b.hebungAngefragt, 3)} — bei diesem Knie trägt die Kurve nur bis ` +
        `${zahl(b.hebungGrenze, 3)}, darüber liefe sie rückwärts. Gerechnet wurde die Grenze.`,
    );
  }
  return zeilen;
}

/**
 * Das fertige Bild heller stellen, ohne dass die Lichter ausbrennen
 * (Abnahmeliste Zeile 49).
 *
 * `quelle` ist bewusst das, was gerade ZU SEHEN ist, und nicht immer das
 * Original: der Zuruf lautet «DANACH bitte bild noch minimal grundsätzlich
 * heller als aktuell» — die Belichtung kommt nach den anderen Korrekturen,
 * nicht neben ihnen.
 *
 * Gibt `null` zurück, wenn etwas schiefging; gemeldet wurde dann schon.
 */
export async function rechneBelichtung(
  nodeId: string,
  quelle: KuratierQuelle,
  grundlage: string,
  hebung: number = HEBUNG_VORGABE,
): Promise<BelichtungAnzeige | null> {
  let abraeumen = () => {};
  try {
    const { url, abraeumen: weg } = await quellUrl(quelle);
    abraeumen = weg;
    const ergebnis = belichtung(await bildpunkteAus(url), { hebung });
    const b = ergebnis.bericht;
    melde(
      `Heller gerechnet (Hebung ${zahl(b.hebungAngewendet, 3)}): gehobene Fläche ` +
        `${zahl(b.vollGehoben.vorher, 1)} → ${zahl(b.vollGehoben.nachher, 1)} Byte, ` +
        `Lichter unverändert, ausgebrannt ${zahl(b.ausgebranntNachherProzent, 4)} %. ` +
        'Das Original bleibt darunter liegen.',
      { ton: 'erfolg' },
    );
    const eintrag: GehobenesBild = {
      nodeId,
      dataUrl: alsDataUrl(ergebnis.bild),
      bericht: berichtBelichtung(b),
      // Wörtlich die Zusage des Kernmoduls, nicht nacherzählt — dieselbe
      // Regel wie beim Farbangleich oben: Zusage und Rechnung bleiben an
      // einer Stelle gepflegt.
      zusage: BELICHTUNG_WAS_GEAENDERT_WURDE,
      grundlage,
    };
    useVisRuntime.getState().setzeGehobenesBild(nodeId, eintrag);
    return eintrag;
  } catch (err) {
    if ('jobId' in quelle) await bescheideBridgeCatch(err);
    else meldeFehler(err);
    return null;
  } finally {
    abraeumen();
  }
}
