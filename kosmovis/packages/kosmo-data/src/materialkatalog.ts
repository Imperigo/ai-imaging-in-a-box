/**
 * Materialkatalog (Q14) — EIN Materialschlüssel, drei Gesichter:
 * PBR fürs 3D (Viewport/GLB), SIA-Schraffur für den Plan, Lambda für den
 * U-Wert. Aufbauten (bauteilkatalog) referenzieren dieselben Schlüssel.
 *
 * v0.6.3 / B4 (Owner-Befund K21, Materialbibliothek Stufe 1): additive
 * Herkunfts-/Klassifikations-Felder — `quelle` (Pflicht bei NEUEN Einträgen;
 * dieser Alt-Katalog trägt ehrlich «Quelle unbelegt (Altbestand)», weil die
 * ursprüngliche Herkunft der PBR-/Lambda-Werte nicht dokumentiert wurde),
 * `materialArt` (Rohmaterial vs. Baumaterial) und optional `region`/
 * `dimensionen` (lieferbare Grössen/Dicken — Basis für den 3D-Würfel in der
 * Vorschau). Stufe 2 (externer Quellen-Ingest inkl. Lizenzprüfung, echte
 * 4k/8k-Fotomaps, HSLU-Materialdatenbank) bleibt offen — hier nur Datenmodell
 * + Vorschau.
 */

/** Rohmaterial (naturbelassen/kaum verarbeitet) vs. Baumaterial (industriell verarbeitetes Bauprodukt). */
export type MaterialArt = 'rohmaterial' | 'baumaterial' | 'unbekannt';

/** Eine lieferbare Grösse/Dicke — frei benannt, aber typisierte Masse in mm. */
export interface MaterialGroesse {
  bezeichnung: string;
  laenge_mm?: number;
  breite_mm?: number;
  dicke_mm?: number;
}

/** Lieferbare Grössen/Dicken eines Materials (K21) — Basis für den 3D-Würfel. */
export interface MaterialDimensionen {
  lieferbar: MaterialGroesse[];
  /** Einschränkung/Richtwert-Hinweis, z.B. wenn Grössen produktabhängig streuen. */
  hinweis?: string;
}

export interface MaterialEintrag {
  key: string;
  name: string;
  pbr: { color: number; roughness: number; metalness?: number };
  /** Schraffur-/Poché-Klasse im Grundriss (SIA-Stiftsatz). */
  sia: 'beton' | 'mauerwerk' | 'holz' | 'daemmung' | 'putz' | 'sonstig';
  /** W/(m·K), wo sinnvoll. */
  lambda?: number;
  beschrieb: string;
  /** Herkunft der Angaben (K21) — Pflicht bei NEUEN Einträgen, s. Datei-Kopfkommentar. */
  quelle: string;
  /** Rohmaterial vs. Baumaterial (K21). */
  materialArt: MaterialArt;
  /** Regionale Zuordnung, optional (K21) — dieser Katalog ist durchgehend SIA/CH-Kontext. */
  region?: string;
  /** Lieferbare Grössen/Dicken, optional (K21) — nur wo verlässlich bekannt, sonst weggelassen statt erfunden. */
  dimensionen?: MaterialDimensionen;
}

const ALTBESTAND_QUELLE = 'Quelle unbelegt (Altbestand)';
const CH_KONTEXT = 'Schweiz (SIA-Kontext)';

export const materialkatalog: MaterialEintrag[] = [
  { key: 'beton', name: 'Stahlbeton', pbr: { color: 0xc9c5bc, roughness: 0.9 }, sia: 'beton', lambda: 2.3, beschrieb: 'Sichtbeton/Konstruktionsbeton — das Schweizer Rückgrat.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'beton-rc', name: 'Recyclingbeton', pbr: { color: 0xc2bdb2, roughness: 0.92 }, sia: 'beton', lambda: 2.3, beschrieb: 'RC-Beton mit Mischgranulat — Standard für Kerne.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  {
    key: 'backstein', name: 'Backstein', pbr: { color: 0xb0705a, roughness: 0.85 }, sia: 'mauerwerk', lambda: 0.44,
    beschrieb: 'Sichtbar oder verputzt — die klassische Zweischale.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT,
    dimensionen: { lieferbar: [{ bezeichnung: 'NF (Normalformat)', laenge_mm: 250, breite_mm: 120, dicke_mm: 65 }] },
  },
  {
    key: 'kalksandstein', name: 'Kalksandstein', pbr: { color: 0xd8d2c6, roughness: 0.88 }, sia: 'mauerwerk', lambda: 1.0,
    beschrieb: 'Masse für den Schallschutz, wohnungstrennend.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT,
    dimensionen: {
      lieferbar: [{ bezeichnung: 'Blockstein', laenge_mm: 248, breite_mm: 115, dicke_mm: 113 }],
      hinweis: 'Richtwert — Formate streuen je Hersteller, projektspezifisch prüfen.',
    },
  },
  { key: 'holz', name: 'Holz (Fichte/Tanne)', pbr: { color: 0xb08d5e, roughness: 0.8 }, sia: 'holz', lambda: 0.13, beschrieb: 'Schalung, Balken, Tafeln.', quelle: ALTBESTAND_QUELLE, materialArt: 'rohmaterial', region: CH_KONTEXT },
  { key: 'holz-bsp', name: 'Brettsperrholz', pbr: { color: 0xc19a68, roughness: 0.78 }, sia: 'holz', lambda: 0.13, beschrieb: 'Massive Holztafeln, tragend und sichtbar.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'lattung', name: 'Lattung/Hinterlüftung', pbr: { color: 0xa98a5f, roughness: 0.85 }, sia: 'holz', lambda: 0.13, beschrieb: 'Konterlattung, Luftschicht.', quelle: ALTBESTAND_QUELLE, materialArt: 'rohmaterial', region: CH_KONTEXT },
  { key: 'putz', name: 'Aussenputz', pbr: { color: 0xe4ded2, roughness: 0.95 }, sia: 'putz', lambda: 0.87, beschrieb: 'Mineralischer Deckputz.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'putz-innen', name: 'Innenputz', pbr: { color: 0xefeae0, roughness: 0.95 }, sia: 'putz', lambda: 0.7, beschrieb: 'Gips-/Kalkputz innen.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  {
    key: 'gips', name: 'Gipsplatte', pbr: { color: 0xf0ece4, roughness: 0.93 }, sia: 'putz', lambda: 0.25,
    beschrieb: 'Beplankung im Trockenbau.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT,
    dimensionen: {
      lieferbar: [{ bezeichnung: 'Standardplatte', laenge_mm: 2600, breite_mm: 1200, dicke_mm: 12.5 }],
      hinweis: 'Richtwert — auch als 2000/3000 mm und 9.5/15/18 mm Dicke lieferbar.',
    },
  },
  { key: 'daemmung-mw', name: 'Mineralwolle', pbr: { color: 0xdcd6a8, roughness: 1.0 }, sia: 'daemmung', lambda: 0.036, beschrieb: 'Nicht brennbar — Standard hinterlüftet.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  {
    key: 'daemmung-eps', name: 'EPS', pbr: { color: 0xe8e8e2, roughness: 1.0 }, sia: 'daemmung', lambda: 0.031,
    beschrieb: 'Kompaktfassade.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT,
    dimensionen: {
      lieferbar: [{ bezeichnung: 'Fassadenplatte (Beispieldicke)', laenge_mm: 1200, breite_mm: 600, dicke_mm: 140 }],
      hinweis: 'Dicke produktabhängig 20–300 mm — 140 mm ist ein Beispielwert, kein Fixmass.',
    },
  },
  { key: 'daemmung-pur', name: 'PUR/PIR', pbr: { color: 0xe0d5b0, roughness: 1.0 }, sia: 'daemmung', lambda: 0.025, beschrieb: 'Schlank, wo Höhe fehlt (Flachdach/Boden).', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'daemmung-hf', name: 'Holzfaser', pbr: { color: 0xcbb287, roughness: 1.0 }, sia: 'daemmung', lambda: 0.04, beschrieb: 'Diffusionsoffen, sommerlicher Wärmeschutz.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'zementestrich', name: 'Zementestrich', pbr: { color: 0xb5b2aa, roughness: 0.85 }, sia: 'sonstig', lambda: 1.4, beschrieb: 'Schwimmend auf Trittschall.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'trittschall', name: 'Trittschalldämmung', pbr: { color: 0xd6d2c2, roughness: 1.0 }, sia: 'daemmung', lambda: 0.033, beschrieb: 'Unter dem Estrich.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'abdichtung', name: 'Abdichtung', pbr: { color: 0x3a3835, roughness: 0.6 }, sia: 'sonstig', lambda: 0.23, beschrieb: 'Bitumen-/Kunststoffbahn.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'kies', name: 'Kies', pbr: { color: 0xb9b4a8, roughness: 1.0 }, sia: 'sonstig', lambda: 0.7, beschrieb: 'Auflast und Schutz auf dem Warmdach.', quelle: ALTBESTAND_QUELLE, materialArt: 'rohmaterial', region: CH_KONTEXT },
  { key: 'ziegel', name: 'Dachziegel', pbr: { color: 0x9a5b45, roughness: 0.8 }, sia: 'sonstig', lambda: 0.7, beschrieb: 'Ton, auf Lattung.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'glas', name: 'Glas', pbr: { color: 0xaec6c9, roughness: 0.1, metalness: 0.2 }, sia: 'sonstig', beschrieb: '3-fach-IV im Standard.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
  { key: 'stahl', name: 'Stahl', pbr: { color: 0x8a8d90, roughness: 0.45, metalness: 0.8 }, sia: 'sonstig', beschrieb: 'Stützen, Unterzüge, Beschläge.', quelle: ALTBESTAND_QUELLE, materialArt: 'baumaterial', region: CH_KONTEXT },
];

/** PBR-Nachschlag fürs 3D (Viewport/GLB) — Schlüssel → Parameter. */
export const pbrPalette: Record<string, { color: number; roughness: number; metalness?: number }> =
  Object.fromEntries(materialkatalog.map((m) => [m.key, m.pbr]));
