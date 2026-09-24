import type { KosmoDoc } from '../model/doc';
import type { Anstrich, Assembly, Koernung, Slab, Wall } from '../model/entities';

/**
 * Render-Prompt-Bausteine (V2-V8): Das Modell spricht mit — die äussersten
 * Wandschichten und das Dach werden zu Prompt-Phrasen, damit KosmoVis
 * rendert, was gebaut ist. Transparenz statt Blackbox: der finale Prompt
 * wird angezeigt und ist überschreibbar.
 */

const PHRASEN: [RegExp, string][] = [
  [/sichtbeton|beton/, 'Sichtbeton-Fassade'],
  [/putz/, 'mineralisch verputzte Fassade'],
  [/holz|laerche|fichte/, 'Holzfassade (vertikale Lattung)'],
  [/klinker|backstein|ziegel(?!dach)/, 'Klinker-Mauerwerk'],
  [/kalksandstein/, 'Kalksandstein-Mauerwerk sichtbar'],
  [/metall|blech|alu/, 'Metallfassade'],
];

/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  DAS WORT FUER DEN ANSTRICH — Abnahmezeile 35
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * «da bitte einen layer drauflegen fuer ‹weiss gestrichen› also das holz wird
 * weiss gestrichen» — und die Abnahmeliste sagt dazu: **ohne dessen Struktur
 * zu verlieren.**
 *
 * HIER STEHT DIESE STRUKTUR. Die Tafel unten macht aus einer Holz-Aussenschicht
 * «Holzfassade (vertikale Lattung)». Die Lattung ist die Struktur. Ein Anstrich
 * haengt sich darum HINTEN AN diese Phrase und ersetzt sie nicht — der Bildkanal
 * erfaehrt beides, und die Maserung geht nicht verloren.
 *
 * NUR GENANNT, WAS SICH BENENNEN LAESST. Ein Farbton ist eine Zahl, ein Wort
 * ist eine Behauptung. Diese Funktion vergibt darum genau drei Farbwoerter, und
 * jedes an einer nachrechenbaren Grenze:
 *
 *   · «weiss»   — der KLEINSTE Kanal liegt bei 0.6 oder darueber (linear),
 *                 auf dem Bildschirm etwa #CB und heller.
 *   · «schwarz» — der GROESSTE Kanal liegt bei 0.05 oder darunter, etwa #3F
 *                 und dunkler.
 *   · «grau»    — dazwischen, und die drei Kanaele liegen hoechstens 0.02
 *                 auseinander (also unbunt).
 *
 * Alles andere bekommt KEIN Farbwort. «Gestrichen» allein ist wahr; ein
 * geratenes «beige gestrichen» waere es nicht — und ein falsches Wort im Prompt
 * faerbt das ganze Bild, nicht nur eine Wand.
 *
 * DAS VERB TRENNT DECKEND VON LASIERT: unter 0.8 Deckung scheint der Untergrund
 * sichtbar durch, und das heisst im Handwerk nicht «gestrichen», sondern
 * «lasiert». Der Bildkanal soll den Unterschied hoeren.
 */
/**
 * DAS FARBVOKABULAR DES BILDKANALS — EINE Liste, von Anstrich UND Koernung
 * benutzt.
 *
 * Ein Farbton ist eine Zahl, ein Wort ist eine Behauptung. Darum gibt es genau
 * vier Woerter, jedes an einer nachrechenbaren Grenze (alle Werte LINEAR):
 *
 *   · «weiss»   — der KLEINSTE Kanal liegt bei 0.6 oder darueber (Bildschirm
 *                 etwa #CB und heller).
 *   · «schwarz» — der GROESSTE Kanal liegt bei 0.05 oder darunter (#3F und
 *                 dunkler).
 *   · «grau»    — dazwischen, und die Kanaele liegen hoechstens 0.02
 *                 auseinander, also unbunt.
 *   · «beige»   — warm und flau: Rot >= Gruen >= Blau, der Abstand von Rot zu
 *                 Blau liegt zwischen 0.03 und 0.30, und Rot selbst zwischen
 *                 0.10 und 0.65. Das ist der Bereich, den der Owner
 *                 «beigetoenen» nennt — kein Ocker, kein Braun, kein Sand in
 *                 der Sonne.
 *
 * Alles andere bekommt KEIN Wort. Ein geratenes Farbwort faerbt im Bildkanal
 * die ganze Szene, nicht nur eine Flaeche.
 */
export function farbwort(rgba: readonly [number, number, number, number]): string {
  const [r, g, b] = rgba;
  const min = Math.min(r, g, b);
  const max = Math.max(r, g, b);
  if (min >= 0.6) return 'weiss';
  if (max <= 0.05) return 'schwarz';
  if (max - min <= 0.02) return 'grau';
  if (r >= g && g >= b && r - b >= 0.03 && r - b <= 0.3 && r >= 0.1 && r <= 0.65) return 'beige';
  return '';
}

/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  DAS WORT FUER DEN ANSTRICH — Abnahmezeile 35
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Haengt sich HINTEN AN die Materialphrase (s. unten) und ersetzt sie nicht —
 * so bleibt die Struktur stehen, die die Abnahmezeile verlangt.
 *
 * DAS VERB TRENNT DECKEND VON LASIERT: unter 0.8 Deckung scheint der
 * Untergrund sichtbar durch, und das heisst im Handwerk nicht «gestrichen»,
 * sondern «lasiert». Der Bildkanal soll den Unterschied hoeren. Dieselbe
 * Grenze steuert im 3D-Fenster, ob die Farbkarte des Untergrunds wegfaellt —
 * EIN Wert, zwei Wirkungen.
 */
export function anstrichWort(a: Anstrich): string {
  const verb = a.deckung >= 0.8 ? 'gestrichen' : 'lasiert';
  const wort = farbwort(a.rgba);
  return wort ? `${wort} ${verb}` : verb;
}

/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  DAS WORT FUER DIE KOERNUNG — Abnahmezeile 36, viermal zugerufen
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * «der boden soll ein geschliffener unterlagsbodenbelag sein» · «damit man
 * minimale kiessteine geschnitten sieht» · «diese koernung in beigetoenen» ·
 * «und noch etwas mehr groessere koernung zeigen».
 *
 * WARUM DIE ZAHL MITGEHT und nicht nur ein Wort: Der Owner hat die Groesse
 * ZWEIMAL nachgestellt. «Fein» und «grob» sind Kategorien, 2 mm und 4 mm sind
 * Groessen — und nur die zweite Sorte laesst sich nachstellen. Der Bildkanal
 * bekommt beides: das Wort, damit der Satz lesbar bleibt, und die Zahl, damit
 * er genau ist.
 *
 * DIE GRENZEN, nachrechenbar wie ueberall hier: unter 1.5 mm «fein», unter
 * 4 mm «mittel», darueber «grob». Das sind die Groessen, die ein geschliffener
 * Unterlagsboden wirklich zeigt — Sand, Kies, grober Kies.
 *
 * DIE DICHTE bekommt nur dann ein Wort, wenn sie auffaellt: unter 0.15
 * «sparsam», ab 0.5 «dicht». Dazwischen ist sie das, was man erwartet, und
 * ein Wort dafuer waere Fuellung.
 */
export function koernungWort(k: Koernung): string {
  const grob = k.groesse_mm < 1.5 ? 'feine' : k.groesse_mm < 4 ? 'mittlere' : 'grobe';
  const ton = farbwort(k.ton);
  const dicht = k.dichte < 0.15 ? ', sparsam' : k.dichte >= 0.5 ? ', dicht' : '';
  return `${grob} Körnung ${k.groesse_mm} mm${ton ? ` in ${ton}` : ''}${dicht}`;
}

/**
 * ABNAHMEZEILE 46 — DIE SONNE IM BILDKANAL.
 *
 * Bis hierher kam in dieser Datei **kein einziges Wort ueber Licht** vor:
 * keine Sonne, kein Schatten, keine Tageszeit. Ein Bildwerkzeug, das den
 * Prompt liest, konnte darum gar nicht wissen, ob es hell oder truebe sein
 * soll — und ein Regler im 3D-Fenster waere ein Regler ohne Wirkung auf das
 * Bild gewesen. Genau die dritte Form der Luecke: das Feld ohne Leser.
 *
 * DIE DREI STUFEN SIND NICHT FEIN ABGESTUFT, und das ist Absicht. Ein
 * Bildwerkzeug liest Sprache, keine Kommazahl; «Sonnenlicht 1.37x» hilft ihm
 * nicht. Was hilft, ist die Unterscheidung, die ein Fotograf auch machen
 * wuerde: weiches Licht, klares Licht, hartes Licht. Die Grenzen 0.7 und 1.3
 * liegen dort, weil der Owner «etwas staerker» gesagt hat und nicht «doppelt»
 * — ein Schritt von 1 auf 1.3 soll das Wort schon wechseln.
 *
 * DER SCHATTEN WIRD MITGENANNT, weil der Zuruf ihn ausdruecklich nennt
 * («mit minimal staerkerem schattenwurf»). Ohne ihn kaeme ein helleres Bild
 * mit denselben weichen Schatten heraus — und das ist genau das, was der
 * Owner NICHT wollte.
 */
export function sonnenWort(staerke: number): string {
  if (staerke < 0.7) return 'weiches diffuses Tageslicht, kaum Schlagschatten';
  if (staerke > 1.3) return 'starkes direktes Sonnenlicht, harte tiefe Schlagschatten';
  return 'direktes Sonnenlicht, klar gezeichnete Schlagschatten';
}

export function renderPromptBausteine(doc: KosmoDoc): string[] {
  const bausteine: string[] = [];
  const gesehen = new Set<string>();
  for (const w of doc.byKind<Wall>('wall')) {
    const asm = doc.get<Assembly>(w.assemblyId);
    if (asm?.kind !== 'assembly' || asm.layers.length === 0) continue;
    // äusserste Schicht = erste (Konvention: aussen → innen, model/entities.ts
    // `Assembly`). P-DP (GOLDEN-WECHSEL-096) ändert NUR, welche geometrische
    // SEITE (`wandReferenzseite`) als Referenzseite gilt — nie die
    // Array-Reihenfolge: `wallLayerOutlines`/-`Mitered`/`wallLayerFaces`
    // beginnen JEDE Stapelung bei `layers[0]`, gleich welche Seite das ist
    // (siehe dort: `step`/`cursor` wechseln, der Schichtindex nie). `layers[0]`
    // bleibt darum in JEDEM Fall die tatsächliche Aussenschicht — geprüft mit
    // einer geschlossenen (gekippten) Testschleife, s. kernel.test.ts.
    const mat = asm.layers[0]!.material.toLowerCase();
    // A35: der Anstrich haengt HINTEN AN die Materialphrase. Die Entdoppelung
    // laeuft danach ueber den fertigen Satz — eine gestrichene und eine rohe
    // Holzwand ergeben darum zwei Bausteine, und das ist richtig: im Bild sind
    // es zwei verschiedene Fassaden.
    const anstrich = w.meta?.aussehen?.anstrich;
    for (const [re, phrase] of PHRASEN) {
      if (!re.test(mat)) continue;
      const satz = anstrich ? `${phrase}, ${anstrichWort(anstrich)}` : phrase;
      if (gesehen.has(satz)) continue;
      gesehen.add(satz);
      bausteine.push(satz);
    }
  }
  // ── A36: DER BODEN KOMMT IM BILDKANAL VOR, und bis heute tat er das nicht ──
  //
  // Diese Funktion sah AUSSCHLIESSLICH Waende an. Ein Boden konnte im Prompt
  // gar nicht vorkommen — die dritte Form der Luecke: das Feld ohne Leser.
  // Der Owner hat den Boden VIERMAL korrigiert; er ist keine Nebenflaeche.
  //
  // Genannt wird nur, was jemand GESTELLT hat: eine Decke ohne Koernung
  // erzeugt weiterhin keinen Baustein. Sonst stuende in jedem Prompt ein Satz
  // ueber einen Boden, den niemand angefasst hat.
  for (const d of doc.byKind<Slab>('slab')) {
    const k = d.meta?.aussehen?.koernung;
    if (!k) continue;
    const satz = `geschliffener Unterlagsboden, ${koernungWort(k)}`;
    if (gesehen.has(satz)) continue;
    gesehen.add(satz);
    bausteine.push(satz);
  }

  // ── A46: DIE SONNE — und zwar NUR, wenn jemand sie gestellt hat ──────
  //
  // Dieselbe Regel wie beim Boden darueber: Ein Dokument, in dem niemand die
  // Sonne angefasst hat, bekommt keinen Lichtsatz. Sonst stuende in jedem
  // Prompt eine Aussage ueber ein Licht, das nie jemand gewaehlt hat — und
  // der Unterschied zwischen «nie gestellt» und «auf 1 gestellt» waere im
  // Bild nicht mehr ablesbar. Genau dafuer traegt `sonnenStaerke` sein
  // ausdrueckliches `| undefined`.
  const sonne = doc.settings.sonnenStaerke;
  if (sonne !== undefined) bausteine.push(sonnenWort(sonne));

  // Gezeichnete Fassadenmodule (Modul-Editor): Rastermass + Fensteranteil
  const modul = doc.settings.fassadenModule[0];
  if (modul && modul.elemente.length > 0) {
    const fensterFlaeche = modul.elemente
      .filter((e) => e.typ === 'fenster')
      .reduce((sum, e) => sum + e.b * e.h, 0);
    const anteil = Math.round((fensterFlaeche / (modul.breite * modul.hoehe)) * 100);
    bausteine.push(
      `regelmässiges Fassadenraster ${(modul.breite / 1000).toFixed(1)} × ${(modul.hoehe / 1000).toFixed(1)} m${anteil > 0 ? `, Fensteranteil ~${anteil}%` : ''}`,
    );
  }
  return bausteine;
}

/** Finaler Prompt: Stimmung + Nutzertext + Material-Bausteine, ohne Leeres. */
export function finalerRenderPrompt(stil: string, nutzer: string, bausteine: string[]): string {
  return [stil, nutzer, ...bausteine].filter((t) => t.trim().length > 0).join(', ');
}
