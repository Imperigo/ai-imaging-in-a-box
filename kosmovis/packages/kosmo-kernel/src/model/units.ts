/**
 * Einheiten — der Kern rechnet ausschliesslich in ganzzahligen Millimetern.
 * Ganzzahlen machen 2D-Boolesche Operationen exakt (Clipper2 ist nativ int64)
 * und eliminieren Gleitkomma-Drift in Plänen. Winkel in Radiant (float).
 */

/** Länge in ganzen Millimetern. */
export type Mm = number;

export const MM_PER_M = 1000;

export function mm(valueInMm: number): Mm {
  return Math.round(valueInMm);
}

/** SIA-übliche Massformatierung: Meter mit Punkt, ohne überflüssige Nullen. */
export function formatLength(v: Mm): string {
  const m = v / MM_PER_M;
  const s = m.toFixed(3).replace(/0+$/, '').replace(/\.$/, '.0');
  return `${s} m`;
}

export function formatArea(mm2: number): string {
  const m2 = mm2 / (MM_PER_M * MM_PER_M);
  return `${m2.toFixed(m2 >= 100 ? 0 : 1)} m²`;
}

/** 2D-Punkt in mm (Weltkoordinaten: x nach Osten, y nach Norden). */
export interface Pt {
  readonly x: Mm;
  readonly y: Mm;
}

export const pt = (x: number, y: number): Pt => ({ x: Math.round(x), y: Math.round(y) });

export function dist(a: Pt, b: Pt): number {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

export function add(a: Pt, b: Pt): Pt {
  return { x: a.x + b.x, y: a.y + b.y };
}

export function sub(a: Pt, b: Pt): Pt {
  return { x: a.x - b.x, y: a.y - b.y };
}

export function scale(a: Pt, f: number): Pt {
  return pt(a.x * f, a.y * f);
}

export function lerp(a: Pt, b: Pt, t: number): Pt {
  return pt(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t);
}

/** Einheitsvektor a→b (float, nicht gerundet — nur für Richtungen). */
export function dir(a: Pt, b: Pt): { x: number; y: number } {
  const d = dist(a, b);
  if (d === 0) return { x: 1, y: 0 };
  return { x: (b.x - a.x) / d, y: (b.y - a.y) / d };
}

/** Linke Normale der Richtung a→b. */
export function normal(a: Pt, b: Pt): { x: number; y: number } {
  const d = dir(a, b);
  return { x: -d.y, y: d.x };
}

/**
 * Signierte Fläche eines Polygons in mm² (positiv = gegen Uhrzeigersinn).
 *
 * **Das Vorzeichen ist der Zweck dieser Funktion, nicht ihr Nebeneffekt.**
 * Sie beantwortet «in welche Richtung läuft dieser Umriss?» — `skeleton.ts`,
 * `wall.ts` und `mesh.ts` drehen daran Umrisse und Löcher zurecht.
 *
 * **Wer eine FLÄCHE MISST, nimmt `polygonFlaeche()`.** Ein Umriss, den ein
 * Mensch im Uhrzeigersinn gezeichnet hat, ist genauso gross wie derselbe
 * Umriss andersherum; nur die Richtung unterscheidet sie. P-VORZEICHEN
 * (v0.9.33) hat zwei Stellen gefunden, die das verwechselt haben — die
 * eine meldete «Raum 1 hat −28.5 m²», die andere liess eine Variante der
 * Volumenstudie lautlos verschwinden, weil eine negative Fläche unter
 * jeder Mindestgrösse liegt.
 */
export function polygonArea(poly: readonly Pt[]): number {
  let s = 0;
  for (let i = 0; i < poly.length; i++) {
    const a = poly[i]!;
    const b = poly[(i + 1) % poly.length]!;
    s += a.x * b.y - b.x * a.y;
  }
  return s / 2;
}

/**
 * Fläche eines Polygons in mm² — **richtungsunabhängig**, immer ≥ 0.
 *
 * Die Messfunktion für alles, was eine Grösse wissen will: Raumflächen,
 * Grundflächen, Anteile, Schwellenvergleiche. Ein entartetes Polygon
 * (weniger als drei Punkte spannen keine Fläche auf) misst 0 statt
 * `NaN` — damit ein Schwellenvergleich eine Antwort bekommt statt still
 * `false` zu ergeben.
 *
 * Eingeführt mit P-VORZEICHEN (v0.9.33, B43 §9 und der Zwilling in
 * `volumenstudie.ts`). Der Wächter `flaechen-vorzeichen-waechter.test.ts`
 * hält fest, welche Aufrufer `polygonArea` roh benutzen dürfen — jede neue
 * rohe Verwendung muss sich dort mit einer Begründung eintragen.
 */
export function polygonFlaeche(poly: readonly Pt[]): number {
  if (poly.length < 3) return 0;
  return Math.abs(polygonArea(poly));
}
