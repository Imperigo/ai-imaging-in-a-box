/**
 * Farbangleich — eine Farbstimmung von einem Bild auf ein anderes uebertragen,
 * GERECHNET statt erzeugt.
 *
 * WARUM DAS UEBERHAUPT IM KERN STEHT: die Stimmung, die der Owner haben will,
 * kam aus einem KI-Stillauf. Sie ein zweites Mal durch ein Diffusionsmodell zu
 * holen hiesse, das Bild neu erfinden zu lassen — und genau das ist am
 * 10.09.2026 gemessen schiefgegangen: der generative Durchgang sollte eine
 * Flaeche bearbeiten und hat dabei die Bepflanzung, das Weinglas und
 * Verdeckungen mitveraendert. Fuer ein Architekturbild ist das unbrauchbar:
 * was gezeichnet wurde, muss stehenbleiben.
 *
 * Eine Farbstimmung ist aber keine Erfindung, sondern eine KENNLINIE. Sie
 * laesst sich messen und uebertragen: fuer jeden Kanal wird die
 * Summenverteilung des Quellbilds auf die des Vorbilds gelegt
 * (Histogrammangleich). Das aendert Farbe und Kontrast — und sonst NICHTS.
 * Kein Bildpunkt wandert, kein Gegenstand entsteht, keiner verschwindet. Das
 * ist keine Behauptung, sondern eine Eigenschaft der Rechnung: jeder
 * Ausgabepunkt haengt nur vom Wert DESSELBEN Eingabepunkts ab. Die Probe
 * `test/bild-farbe.test.ts` haelt das fest, indem sie die Bildpunkte
 * durcheinanderwirft und nachweist, dass die Ausgabe genauso durcheinander
 * kommt und sich sonst nicht bewegt.
 *
 * VORLAGE IST `kosmo-render/werkzeug/farbangleich.py` (90 Zeilen, numpy +
 * Pillow). Diese Fassung ist deren Uebersetzung, absichtlich Zahl fuer Zahl
 * gleich. Die Proben messen gegen Bytes, die die PYTHON-Fassung geschrieben
 * hat, nicht gegen die eigene Ausgabe — ein Vergleich mit sich selbst koennte
 * nicht widersprechen und waere darum keine Probe.
 *
 * KEIN CANVAS, KEIN sharp, KEINE neue Abhaengigkeit: der Kern laeuft im Web
 * Worker und hat weder DOM noch Dateisystem. Eingabe sind rohe Bildpunkte,
 * wer sie laedt, entscheidet ausserhalb — dieselbe Linie wie beim
 * 3DS-Kameraleser (`src/import/kamera3ds.ts`).
 *
 * ZUR RECHENGENAUIGKEIT — und warum hier ueberall `Math.fround` steht: die
 * Vorlage rechnet in `float32` (`astype(np.float32) / 255.0`), numpy rundet
 * nach JEDEM Rechenschritt auf 32 Bit. JavaScript rechnet in 64 Bit. Wer das
 * ignoriert, bekommt ein Bild, das «fast» stimmt — und kann nie sagen, ob eine
 * Abweichung von einem Byte Gleitkomma-Rauschen ist oder ein Denkfehler.
 * `Math.fround` rundet einen Wert auf die naechste `float32`-Zahl und bildet
 * damit den Schritt der Vorlage nach. Der Preis sind haessliche Klammern; der
 * Ertrag ist, dass die Probe auf das einzelne Byte genau messen KANN. Genau
 * dort, wo die Vorlage in 64 Bit rechnet (`np.quantile`, `np.interp`, beide
 * geben `float64` zurueck), steht hier bewusst kein `fround`.
 */

/** `Math.fround` bildet den Schritt nach, mit dem numpy in ein `float32`-Feld schreibt. */
const f32 = Math.fround;

/**
 * Rohe Bildpunkte, zeilenweise, ohne Rand.
 *
 * `kanaele: 4` ist der Normalfall aus einem `ImageData` im Web Worker. Der
 * Alphakanal wird von beiden Werkzeugen UNVERAENDERT durchgereicht — er
 * gehoert nicht zur Farbstimmung, und ihn mitzuziehen hiesse, Deckung zu
 * veraendern, wo nur Farbe gemeint war.
 */
export interface Bild {
  readonly daten: Uint8ClampedArray | Uint8Array;
  readonly breite: number;
  readonly hoehe: number;
  readonly kanaele: 3 | 4;
}

/**
 * Zahl der Stuetzstellen der ausgegebenen Kennlinie: 256, eine je moeglichem
 * Byte-Wert. Die Vorlage legt sie mit `np.linspace(0, 1, 256)` an.
 */
export const KENNLINIE_PUNKTE = 256;

/**
 * Zahl der Quantilstufen, ueber die Quelle und Vorbild verglichen werden
 * (`stufen=512` in der Vorlage). Mehr Stufen heisst feinere Kennlinie; die 512
 * sind der Wert, gegen den gemessen wird, und stehen darum als Konstante hier.
 */
export const KENNLINIE_STUETZEN = 512;

/**
 * Wortlaut aus dem Bericht der Vorlage. Steht hier als Konstante, damit die
 * Zusage und die Rechnung an derselben Stelle gepflegt werden.
 */
export const WAS_GEAENDERT_WURDE =
  'ausschliesslich Farbe und Kontrast je Kanal; kein Bildpunkt wandert, nichts entsteht, nichts verschwindet';

/** Die vier Masszahlen, die die Vorlage vor und nach dem Angleich meldet. */
export interface FarbMass {
  /** Mittlere Helligkeit (Rec.709-Leuchtdichte), 0 bis 1. */
  mittel: number;
  /** Mittlere Saettigung, 0 bis 1. */
  saettigung: number;
  /** 1-Prozent-Quantil der Leuchtdichte — wie tief das Schwarz sitzt. */
  schwarzpunkt: number;
  /** Rot minus Blau im dunkelsten Fuenftel, in Byte-Schritten: warmer oder kalter Schatten. */
  rbSchatten: number;
}

export interface FarbangleichOptionen {
  /**
   * Mischung zwischen Original (0) und voller Kennlinie (1); Vorgabe 1.0 wie
   * in der Vorlage. Der Regler sitzt NACH der Kennlinie, nicht in ihr — die
   * Kennlinie bleibt darum bei jeder Staerke dieselbe und bleibt vergleichbar.
   */
  staerke?: number;
  /** Quantilstufen, Vorgabe {@link KENNLINIE_STUETZEN}. */
  stufen?: number;
}

export interface FarbangleichErgebnis {
  /** Das angeglichene Bild, gleiche Masse und gleiche Kanalzahl wie die Eingabe. */
  bild: Bild;
  /**
   * Die drei Kennlinien (R, G, B) mit je {@link KENNLINIE_PUNKTE} Werten:
   * `kennlinien[k][j]` ist der Ausgabewert fuer den Eingabewert `j/255`.
   *
   * Sie wird MITGEGEBEN, nicht nur angewendet — sonst waere das Werkzeug eine
   * Blackbox, die man nur am Bild beurteilen kann. Mit der Kennlinie in der
   * Hand ist nachpruefbar, ob die Stimmung uebertragen oder das Bild nur
   * dunkler gemacht wurde.
   */
  kennlinien: readonly [Float64Array, Float64Array, Float64Array];
  staerke: number;
  vorher: FarbMass;
  vorbildWerte: FarbMass;
  nachher: FarbMass;
  wasGeaendertWurde: string;
}

// ---------------------------------------------------------------------------
// numpy-Bausteine, Schritt fuer Schritt nachgebaut
// ---------------------------------------------------------------------------

/**
 * `np.linspace(0.0, 1.0, n)`.
 *
 * Nachgebaut statt naiv gerechnet: numpy bildet `arange(n) * (1/(n-1))` und
 * setzt den LETZTEN Wert danach hart auf 1.0. Wer stattdessen `i/(n-1)`
 * rechnet, bekommt an einzelnen Stellen ein anderes letztes Bit — und damit
 * eine Kennlinie, die um ein Byte danebenliegen kann.
 */
function linspace01(n: number): Float64Array {
  const y = new Float64Array(n);
  if (n <= 1) return y;
  const schritt = 1 / (n - 1);
  for (let i = 0; i < n; i++) y[i] = i * schritt;
  y[n - 1] = 1;
  return y;
}

/**
 * `np.quantile(sortiert, p)` mit der Vorgabemethode `'linear'`, auf einem
 * bereits sortierten Feld.
 *
 * numpy rechnet `vi = p * (n - 1)`, nimmt die beiden Nachbarn und mischt sie —
 * aber NICHT mit der naheliegenden Formel: unterhalb der Mitte mischt es von
 * links (`a + (b-a)*g`), ab der Mitte von rechts (`b - (b-a)*(1-g)`). Das
 * haelt den Fehler an beiden Enden klein; die zwei Formen koennen sich im
 * letzten Bit unterscheiden. EHRLICH GEMESSEN: an den Fixtures der Probe tun
 * sie es nicht — laesst man den zweiten Zweig weg, bleibt alles gruen. Der
 * Zweig steht hier, weil er in der Vorlage steht, nicht weil eine Probe ihn
 * bisher fordert.
 *
 * Ergebnis ist bewusst `number` (64 Bit): numpy gibt hier auch bei einem
 * `float32`-Feld `float64` zurueck, weil die Mischung ueber das `float64`-Feld
 * der Quantilstufen laeuft.
 */
function quantilSortiert(sortiert: Float32Array, p: number): number {
  const n = sortiert.length;
  const vi = p * (n - 1);
  if (vi >= n - 1) return sortiert[n - 1]!;
  if (vi < 0) return sortiert[0]!;
  const i = Math.floor(vi);
  const g = vi - i;
  const a = sortiert[i]!;
  const b = sortiert[i + 1]!;
  const d = b - a;
  return g < 0.5 ? a + d * g : b - d * (1 - g);
}

/**
 * `np.interp(x, xp, fp)` fuer einen einzelnen Wert — stueckweise linear, mit
 * Festhalten an beiden Enden.
 *
 * Die Sonderfaelle sind aus `numpy/_core/src/multiarray/compiled_base.c`
 * (`arr_interp`) uebernommen und nicht erfunden:
 *  - `x` groesser als die letzte Stuetzstelle → letzter Wert, nicht
 *    extrapoliert;
 *  - `x` kleiner als die erste → erster Wert;
 *  - trifft `x` eine Stuetzstelle genau, wird deren Wert DIREKT genommen und
 *    nicht durch die Geradengleichung geschickt. Das ist der Grund, warum
 *    doppelte Stuetzstellen hier keine Division durch null ausloesen: gesucht
 *    ist der LETZTE Index mit `xp[j] <= x`, also ist `xp[j+1]` immer echt
 *    groesser.
 */
function interp(x: number, xp: Float64Array, fp: Float64Array): number {
  const n = xp.length;
  if (Number.isNaN(x)) return Number.NaN;
  if (x > xp[n - 1]!) return fp[n - 1]!;
  if (x < xp[0]!) return fp[0]!;
  let lo = 0;
  let hi = n;
  while (lo < hi) {
    const mitte = (lo + hi) >> 1;
    if (x >= xp[mitte]!) lo = mitte + 1;
    else hi = mitte;
  }
  const j = lo - 1;
  if (j >= n - 1) return fp[n - 1]!;
  if (xp[j]! === x) return fp[j]!;
  const steigung = (fp[j + 1]! - fp[j]!) / (xp[j + 1]! - xp[j]!);
  return steigung * (x - xp[j]!) + fp[j]!;
}

// ---------------------------------------------------------------------------
// Kennlinie
// ---------------------------------------------------------------------------

/**
 * Die Abbildung, die die Verteilung von `quelle` auf die von `vorbild` legt.
 *
 * Beide Felder sind EIN Kanal in 0..1, in beliebiger Reihenfolge — die
 * Verteilung ist von der Lage der Bildpunkte unabhaengig, und genau deshalb
 * kann diese Rechnung nichts verschieben. Die Bilder duerfen verschieden gross
 * sein; fuer die Verteilung zaehlt nur der Inhalt.
 *
 * Rueckgabe: {@link KENNLINIE_PUNKTE} Werte, Stuetzstelle `j` gehoert zum
 * Eingabewert `j/255`.
 */
export function kennlinie(
  quelle: Float32Array,
  vorbild: Float32Array,
  stufen: number = KENNLINIE_STUETZEN,
): Float64Array {
  const qs = Float32Array.from(quelle).sort();
  const vs = Float32Array.from(vorbild).sort();
  const p = linspace01(stufen);
  const qP = new Float64Array(stufen);
  const vP = new Float64Array(stufen);
  for (let i = 0; i < stufen; i++) {
    qP[i] = quantilSortiert(qs, p[i]!);
    vP[i] = quantilSortiert(vs, p[i]!);
  }
  const gitter = linspace01(KENNLINIE_PUNKTE);
  const kl = new Float64Array(KENNLINIE_PUNKTE);
  for (let j = 0; j < KENNLINIE_PUNKTE; j++) kl[j] = interp(gitter[j]!, qP, vP);
  return kl;
}

// ---------------------------------------------------------------------------
// Bildpunkte lesen und schreiben
// ---------------------------------------------------------------------------

/**
 * Bild in drei getrennte Kanalfelder in 0..1 zerlegen (`float32`, wie die
 * Vorlage).
 *
 * Getrennt statt verschraenkt, weil die Kennlinie je Kanal SORTIERT — ein
 * verschraenktes Feld muesste dafuer ohnehin kopiert werden.
 */
export function alsKanaele(bild: Bild): [Float32Array, Float32Array, Float32Array] {
  const n = bild.breite * bild.hoehe;
  const k = bild.kanaele;
  const r = new Float32Array(n);
  const g = new Float32Array(n);
  const b = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    r[i] = f32(bild.daten[i * k]! / 255);
    g[i] = f32(bild.daten[i * k + 1]! / 255);
    b[i] = f32(bild.daten[i * k + 2]! / 255);
  }
  return [r, g, b];
}

/**
 * Drei Kanalfelder zurueck in Bildpunkte.
 *
 * `abschneiden: true` bildet `(x*255).astype(np.uint8)` der Vorlage nach —
 * numpy SCHNEIDET dort ab, es rundet nicht. `abschneiden: false` bildet
 * `(x*255 + 0.5).astype(np.uint8)` der Nachbearbeitung nach, also echtes
 * Runden. Die zwei Werkzeuge sind an dieser Stelle wirklich verschieden; das
 * gleichzuziehen waere bequem und falsch (im Mittel ein halbes Byte
 * Verschiebung ueber das ganze Bild).
 */
export function ausKanaelen(
  kanaele: readonly [Float32Array, Float32Array, Float32Array],
  vorlage: Bild,
  abschneiden: boolean,
): Bild {
  const n = vorlage.breite * vorlage.hoehe;
  const k = vorlage.kanaele;
  const aus = new Uint8ClampedArray(n * k);
  const zugabe = abschneiden ? 0 : f32(0.5);
  for (let c = 0; c < 3; c++) {
    const feld = kanaele[c]!;
    for (let i = 0; i < n; i++) {
      const x = Math.min(Math.max(feld[i]!, 0), 1);
      aus[i * k + c] = Math.trunc(f32(f32(x * 255) + zugabe));
    }
  }
  if (k === 4) for (let i = 0; i < n; i++) aus[i * 4 + 3] = vorlage.daten[i * 4 + 3]!;
  return { daten: aus, breite: vorlage.breite, hoehe: vorlage.hoehe, kanaele: vorlage.kanaele };
}

// ---------------------------------------------------------------------------
// Masszahlen
// ---------------------------------------------------------------------------

const EPS_SAT = f32(1e-6);

/**
 * Die vier Masszahlen der Vorlage (`mass()`), auf drei Kanalfeldern in 0..1.
 *
 * `schwarzpunkt` und die Schattengrenze laufen ueber dieselbe Quantilrechnung
 * wie die Kennlinie — `np.percentile(x, 20)` ist `np.quantile(x, 0.2)`.
 *
 * Leuchtdichte und Saettigung werden in `float32` gerechnet, die Mittelwerte
 * danach in 64 Bit summiert. Der Grund fuer die `float32`-Haelfte ist nicht
 * Genauigkeit, sondern die AUSWAHL: `rbSchatten` mittelt ueber die Punkte
 * unterhalb des 20-Prozent-Quantils, und ein Punkt genau auf der Schwelle
 * faellt bei 64-Bit-Leuchtdichte anders herum als bei numpy. Die Summen selbst
 * duerfen abweichen — numpy summiert paarweise in `float32`, was hier nicht
 * nachgebaut ist; der Unterschied liegt bei rund 1e-7 und damit weit unter der
 * Stelle, auf die die Vorlage ihren Bericht rundet.
 */
export function farbMass(kanaele: readonly [Float32Array, Float32Array, Float32Array]): FarbMass {
  const [r, g, b] = kanaele;
  const n = r.length;
  const lum = new Float32Array(n);
  let satSumme = 0;
  for (let i = 0; i < n; i++) {
    const ri = r[i]!;
    const gi = g[i]!;
    const bi = b[i]!;
    lum[i] = f32(f32(f32(f32(0.2126) * ri) + f32(f32(0.7152) * gi)) + f32(f32(0.0722) * bi));
    const mx = Math.max(ri, gi, bi);
    const mn = Math.min(ri, gi, bi);
    satSumme += mx > 0 ? f32(f32(mx - mn) / Math.max(mx, EPS_SAT)) : 0;
  }
  let lumSumme = 0;
  for (let i = 0; i < n; i++) lumSumme += lum[i]!;

  // `np.percentile(x, p)` ist NICHT einfach `np.quantile(x, p/100)`: bei einem
  // `float32`-Feld rechnet numpy `p/100` selbst in `float32` und arbeitet
  // danach mit 0.20000000298… statt 0.2 weiter. EHRLICH GEMESSEN: an den
  // Fixtures der Probe aendert das nichts — beide Schreibweisen liefern
  // dasselbe Byte, die Probe bleibt gruen, wenn man das `f32` hier
  // wegnimmt. Es steht trotzdem so da, weil es die Vorlage so tut und weil
  // der Fall, in dem es beisst (ein Bildpunkt genau auf der
  // Schattengrenze), von dieser Probe nicht abgedeckt ist.
  const sortiert = Float32Array.from(lum).sort();
  const schwarzpunkt = quantilSortiert(sortiert, f32(1 / 100));
  const schwelle = quantilSortiert(sortiert, f32(20 / 100));

  let dunkel = 0;
  let rSumme = 0;
  let bSumme = 0;
  for (let i = 0; i < n; i++) {
    if (lum[i]! < schwelle) {
      dunkel++;
      rSumme += r[i]!;
      bSumme += b[i]!;
    }
  }
  const rbSchatten = dunkel > 0 ? (rSumme / dunkel - bSumme / dunkel) * 255 : 0;
  return { mittel: lumSumme / n, saettigung: satSumme / n, schwarzpunkt, rbSchatten };
}

// ---------------------------------------------------------------------------
// Das Werkzeug
// ---------------------------------------------------------------------------

/**
 * Bild `bild` farblich an `vorbild` angleichen.
 *
 * Die zwei Bilder duerfen verschieden gross sein und muessen es meist auch
 * sein — das Vorbild ist ein anderes Bild derselben Szene, kein Ueberzug.
 *
 * Der Ablauf, Schritt fuer Schritt wie in der Vorlage:
 *  1. Bildpunkte nach 0..1;
 *  2. je Kanal die Kennlinie aus beiden Verteilungen;
 *  3. je Bildpunkt den Wert durch die Kennlinie schicken;
 *  4. mit der Staerke gegen das Original mischen und auf 0..1 begrenzen;
 *  5. abschneiden (nicht runden) auf ganze Bytes.
 */
export function farbangleich(
  bild: Bild,
  vorbild: Bild,
  optionen: FarbangleichOptionen = {},
): FarbangleichErgebnis {
  const staerke = optionen.staerke ?? 1.0;
  const stufen = optionen.stufen ?? KENNLINIE_STUETZEN;
  const q = alsKanaele(bild);
  const v = alsKanaele(vorbild);
  const n = bild.breite * bild.hoehe;

  const gitter = linspace01(KENNLINIE_PUNKTE);
  const sF = f32(staerke);
  const gF = f32(1 - staerke);
  const kurven: Float64Array[] = [];
  const aus: Float32Array[] = [];

  for (let c = 0; c < 3; c++) {
    const kl = kennlinie(q[c]!, v[c]!, stufen);
    kurven.push(kl);
    const quelle = q[c]!;
    const ziel = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      // Der Angleich landet in einem float32-Feld (`aus[..., k] = ...`), erst
      // danach mischt die Vorlage — die Reihenfolge der Rundungen zaehlt.
      const angeglichen = f32(interp(quelle[i]!, gitter, kl));
      const gemischt = f32(f32(quelle[i]! * gF) + f32(angeglichen * sF));
      ziel[i] = Math.min(Math.max(gemischt, 0), 1);
    }
    aus.push(ziel);
  }

  const ausKanaeleTripel = aus as [Float32Array, Float32Array, Float32Array];
  return {
    bild: ausKanaelen(ausKanaeleTripel, bild, true),
    kennlinien: kurven as [Float64Array, Float64Array, Float64Array],
    staerke,
    vorher: farbMass(q),
    vorbildWerte: farbMass(v),
    nachher: farbMass(ausKanaeleTripel),
    wasGeaendertWurde: WAS_GEAENDERT_WURDE,
  };
}
