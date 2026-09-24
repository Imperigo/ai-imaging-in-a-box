import type { ComponentType, ReactNode } from 'react';

/**
 * Island-Glyphen-Bibliothek (v0.8.4 W1, `docs/V084-SPEZ.md` §3 E8 + §7
 * Sanktion 3) — 20 neue SVG-Icons für alle Katalog-Werkzeuge
 * (`island-katalog.ts`), die bisher nur die Text-Platzhalter-`glyphe`
 * (zweistelliges Mono-Kürzel) tragen, plus 4 Pill-Icons für die vier
 * Island-Bühnen selbst (Zeichnen/Ansicht/Projekt/Austausch-Pille,
 * `IslandShell.tsx:415-420`).
 *
 * **UNVERDRAHTET (bewusst):** diese Datei importiert NICHTS aus
 * `island-katalog.ts`/`IslandShell.tsx` und wird von KEINEM der beiden
 * eingebunden — die Verdrahtung (welches Werkzeug welches Icon zeigt)
 * gehört PB2 (design) bzw. den PC-Paketen je Station (Hotspot-Matrix
 * `V084-SPEZ.md` §5). `island-katalog.ts`s `glyphe`-Feld ist bereits
 * `string | ComponentType<{ size?: number }>` (E8) — genau der Typ, den die
 * beiden Records unten liefern; das Verkabeln selbst bleibt bewusst
 * jemand anderem überlassen.
 *
 * **Bauvorschrift (BINDEND, `werkzeug-icons.tsx:1-31` + `shell/werkzeug-
 * glyphen.tsx` — dieselbe 24er-Norm, hier 1:1 fortgeschrieben):**
 * - `viewBox="0 0 24 24"`, `strokeWidth="1.75"`, runde Kappen/Joins
 *   (`strokeLinecap`/`strokeLinejoin="round"`).
 * - GENAU EIN Akzentpunkt-Kreis pro Icon (`r="1.13"`,
 *   `fill="var(--k-accent)"`, `stroke="none"`) — der einzige Ort, an dem
 *   eine Farbe ausserhalb von `currentColor` auftaucht (Sanktion 3: "keine
 *   hartkodierte Farbe ausser dem Akzent-Token").
 * - Alles andere (`stroke`) ist `currentColor`, `fill="none"` (vererbt vom
 *   `<svg>`-Wurzelelement, nicht je Pfad wiederholt).
 * - `aria-hidden="true"`, `focusable={false}` — rein dekorativ, der
 *   zugängliche Name sitzt am Button (Muster `werkzeug-icons.tsx:6-8`).
 * - KEIN `<text>`-Kind — leerer `textContent`, unabhängig vom Icon-Inhalt.
 *
 * 20 Werkzeug-Icons (Katalog-Ids aus `island-katalog.ts`, die drei
 * ZEICHNEN-Lücken + alle 6 ANSICHT + alle 6 PROJEKT + alle 6 AUSTAUSCH,
 * §3-Aufzählung aus dem Bauauftrag): `oeffnung`, `messen`, `kommentare`,
 * `darstellung`, `sonne`, `ebenen`, `achsen`, `trace`, `graph`,
 * `kennzahlen`, `checks`, `varianten`, `liste`, `export`,
 * `import`, `rendern`, `blaetter`, `sync`, `manuell`. Die bestehenden 9
 * `werkzeug-icons.tsx`-Icons decken `auswahl`/`wand`/`volumen`/`zone`/
 * `dach`/`treppe`/`stuetze`/`mesh` bereits ab, macht 8 der 11
 * ZEICHNEN-Werkzeuge.
 *
 * **PE2 (v0.8.4, Bauauftrag Punkt 2):** `skizze` — die letzte Katalog-Id
 * ohne echtes SVG, bisher Text-Kürzel `'SK'` (`D12`s "~20 fehlen" zählte
 * sie bewusst nicht mit) — bekommt hier ihr 21. Icon, nach derselben
 * Bauvorschrift. `ISLAND_GLYPHEN` trägt jetzt 21 Einträge, alle 29
 * Katalog-Werkzeuge sind damit SVG-vollständig (8 `werkzeug-icons.tsx` +
 * 21 hier), der `string`-Zweig von `IslandWerkzeug.glyphe` bleibt ein
 * echter, aber ab jetzt ungenutzter Fallback-Typ.
 *
 * 4 Pill-Icons (`ISLAND_PILL_GLYPHEN`, Katalog-`IslandId`s als Strings,
 * ebenfalls ohne Typ-Import): `zeichnen`, `ansicht`, `projekt`,
 * `austausch`.
 *
 * **PE2 (v0.8.4, Bauauftrag Punkt 3):** + 7 weitere Pill-Icons für die
 * Insel-Ids der anderen drei Stationen, die NICHT schon einen der vier
 * design-Namen teilen (`ansicht`/`projekt`/`austausch` sind bereits
 * abgedeckt, `IslandShell.tsx` löst die Pille rein über den String-
 * Insel-Id auf, stationsunabhängig): `graph`/`stimmung` (vis,
 * `vis-island-katalog.ts`), `blatt`/`darstellung` (publish,
 * `publish-island-katalog.ts`), `aufnahme`/`wissen`/`bestand` (prepare,
 * `prepare-island-katalog.ts`) — macht 11 Pill-Icons total.
 *
 * **v0.9.1 P-B2 (`docs/V091-SPEZ.md` §P-B2):** + 2 weitere Werkzeug-Icons für
 * die neuen ZEICHNEN-Werkzeuge `gelaender`/`rampe` (`island-katalog.ts`) —
 * `ISLAND_GLYPHEN` trägt jetzt 23 Einträge, derselben Bauvorschrift folgend.
 *
 * **v0.9.2 P-P2 (`docs/V092-SPEZ.md` §P-P2):** + 1 weiteres Werkzeug-Icon für
 * das neue PROJEKT-Werkzeug `profil` (Profil-Manager, `island-katalog.ts`) —
 * `ISLAND_GLYPHEN` trägt jetzt 24 Einträge, derselben Bauvorschrift folgend.
 *
 * **v0.9.4 P-KI (Folgepaket zu 653/661, «Koten-Werkzeuge in Insel und
 * Inspector»):** + 3 weitere Werkzeug-Icons für die neuen ZEICHNEN-Werkzeuge
 * `hoehenkote`/`winkelmass`/`radialmass` (P-KW/P-PB haben Entität+Command+
 * Klickkette bereits gebaut, s. `island-katalog.ts`) — `ISLAND_GLYPHEN`
 * trägt jetzt 28 Einträge, derselben Bauvorschrift folgend (Detail-Import
 * bleibt jüngstes Icon vor diesen dreien).
 *
 * **v0.9.7 P-UI (`docs/V097-SPEZ.md` §2 P-UI):** + 6 weitere Werkzeug-Icons
 * für die neuen ZEICHNEN-Werkzeuge `notiz`/`linienzug`/`kreis`/
 * `schraffurflaeche`/`unterzug`/`decke` — `ISLAND_GLYPHEN` trägt jetzt 34
 * Einträge, derselben Bauvorschrift folgend.
 *
 * **B77 (`docs/AUFTRAG-B77-VIER-PANELS.md`, Abnahme `docs/V0954-SPEZ.md`
 * C-5 bis C-8):** + 4 weitere Werkzeug-Icons für die vier neuen
 * PROJEKT-Werkzeuge `kv`/`maengel`/`bauablauf`/`draw` — `ISLAND_GLYPHEN`
 * trägt jetzt 37 Einträge, derselben Bauvorschrift folgend. Ohne diese vier
 * Einträge wirft `island-katalog.ts`s `icon()` bereits BEIM MODUL-LADEN
 * (dort: «kein ISLAND_GLYPHEN-Icon für …»), die Glyphe ist also kein
 * Nachtrag, sondern Teil desselben Schnitts wie der Katalog-Eintrag.
 */

const WURZEL_ATTRIBUTE = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
  focusable: false,
} as const;

interface GlyphProps {
  size?: number;
}

/** Baut aus dem reinen Pfad-/Kreis-Inhalt (OHNE `<svg>`-Hülle) eine fertige
 *  Icon-Komponente — die Hülle selbst trägt die ganze Bauvorschrift, jedes
 *  Icon liefert nur seine individuelle Zeichnung + genau einen Akzentpunkt. */
function glyphe(inhalt: ReactNode): ComponentType<GlyphProps> {
  function Glyphe({ size = 18 }: GlyphProps) {
    return (
      <svg {...WURZEL_ATTRIBUTE} width={size} height={size}>
        {inhalt}
      </svg>
    );
  }
  return Glyphe;
}

/** Der eine erlaubte Akzentpunkt (r=1.13, `var(--k-accent)`, kein Stroke). */
function akzent(cx: number, cy: number) {
  return <circle cx={cx} cy={cy} r={1.13} fill="var(--k-accent)" stroke="none" />;
}

// ── 20 Werkzeug-Icons ──────────────────────────────────────────────────

/** Öffnung — Türblatt-Anschlag mit Schwenkbogen (Grundriss-Norm), Akzent am Anschlag/Scharnier. */
const oeffnung = glyphe(
  <>
    <path d="M4 20 H20 M6 20 V6" />
    <path d="M6 6 A14 14 0 0 1 20 20" />
    {akzent(6, 20)}
  </>,
);

/** Messen — Mass-Linie mit Begrenzungs-Ticks an beiden Enden, Akzent am Messwert-Punkt (Mitte). */
const messen = glyphe(
  <>
    <path d="M4 13 V21 M20 13 V21 M4 17 H20" />
    <path d="M3 15 L5 19 M19 15 L21 19" />
    {akzent(12, 17)}
  </>,
);

/** Kommentare — Sprechblase mit Schwanz, Akzent als Benachrichtigungs-Punkt oben rechts. */
const kommentare = glyphe(
  <>
    <path d="M4 5 H20 V15 H10 L6 19 V15 H4 Z" />
    {akzent(18, 7)}
  </>,
);

/** Darstellung — Bildschirm mit Horizont-Trenner (Ansichts-Umschaltung), Akzent oben links. */
const darstellung = glyphe(
  <>
    <rect x="3" y="4.5" width="18" height="14" rx="1.5" />
    <path d="M3 11.5 H21" />
    {akzent(7, 8)}
  </>,
);

/** Sonne — Scheibe mit acht Strahlen, Akzent als Kern-Punkt im Zentrum. */
const sonne = glyphe(
  <>
    <circle cx="12" cy="12" r="4.5" />
    <path d="M12 3 V5.5 M12 18.5 V21 M3 12 H5.5 M18.5 12 H21 M5.6 5.6 L7.4 7.4 M16.6 16.6 L18.4 18.4 M18.4 5.6 L16.6 7.4 M7.4 16.6 L5.6 18.4" />
    {akzent(12, 12)}
  </>,
);

/** Ebenen — drei gestapelte Rauten (Layer-Stapel), Akzent an der obersten Spitze. */
const ebenen = glyphe(
  <>
    <path d="M12 4 L21 9 L12 14 L3 9 Z" />
    <path d="M3 12.5 L12 17.5 L21 12.5" />
    <path d="M3 16 L12 21 L21 16" />
    {akzent(12, 4)}
  </>,
);

/** Achsen — X/Y-Achsenkreuz mit Pfeilspitzen, Akzent im Ursprung. */
const achsen = glyphe(
  <>
    <path d="M5 19 V3 M5 3 L3 6.5 M5 3 L7 6.5" />
    <path d="M5 19 H21 M21 19 L17.5 17 M21 19 L17.5 21" />
    {akzent(5, 19)}
  </>,
);

/** Trace — gebrochener Strahlweg (Pfad-Verfolgung), Akzent an der Lichtquelle. */
const trace = glyphe(
  <>
    <path d="M3 5 L10 12 L7 19 L16 14 L21 6" />
    {akzent(3, 5)}
  </>,
);

/** Graph — zwei umrandete Knoten, verbunden zu einem dritten Akzent-Knoten. */
const graph = glyphe(
  <>
    <circle cx="6" cy="7" r="2.4" />
    <circle cx="18" cy="7" r="2.4" />
    <path d="M8.2 8.4 L15.8 8.4 M7.2 9.1 L11 17 M16.8 9.1 L13 17" />
    {akzent(12, 18)}
  </>,
);

/** Kennzahlen — Balkendiagramm mit Grundlinie, Akzent über dem höchsten Balken. */
const kennzahlen = glyphe(
  <>
    <path d="M3 20 H21 M5 20 V13 M11 20 V8 M17 20 V16" />
    {akzent(11, 8)}
  </>,
);

/** Checks — zwei Listenzeilen (offen/erledigt), Akzent als Fortschritts-Punkt. */
const checks = glyphe(
  <>
    <rect x="4" y="5" width="3.4" height="3.4" rx="0.8" />
    <path d="M10 6.7 H20" />
    <rect x="4" y="15" width="3.4" height="3.4" rx="0.8" />
    <path d="M4.8 16.7 L5.6 17.6 L7.4 15.4 M10 16.7 H20" />
    {akzent(20, 16)}
  </>,
);

/** Varianten — Gabelung mit zwei Ästen, Akzent markiert den gewählten Ast. */
const varianten = glyphe(
  <>
    <path d="M12 20 V13 M12 13 L6 6 M12 13 L18 6" />
    <circle cx="6" cy="6" r="1.8" />
    {akzent(18, 6)}
  </>,
);

/** Phase — Fahnenmast mit Wimpel, Akzent an der Mastspitze (Meilenstein). */
/** Liste — drei Zeilen mit Aufzählungspunkten, Akzent als dritter (aktueller) Punkt. */
const liste = glyphe(
  <>
    <path d="M9 6 H20 M9 12 H20 M9 18 H20" />
    <circle cx="5" cy="6" r="1.3" />
    <circle cx="5" cy="12" r="1.3" />
    {akzent(5, 18)}
  </>,
);

/** Export — Ablage-Wanne mit Pfeil nach oben heraus, Akzent an der Pfeilspitze. */
const exportGlyphe = glyphe(
  <>
    <path d="M4 15 V19 H20 V15" />
    <path d="M12 16 V4 M8 8 L12 4 L16 8" />
    {akzent(12, 4)}
  </>,
);

/** Import — Ablage-Wanne mit Pfeil nach unten hinein, Akzent an der Pfeilspitze. */
const importGlyphe = glyphe(
  <>
    <path d="M4 15 V19 H20 V15" />
    <path d="M12 4 V16 M8 12 L12 16 L16 12" />
    {akzent(12, 16)}
  </>,
);

/** Rendern — Kamerakörper mit Objektiv, Akzent als Linsen-Reflex. */
const rendern = glyphe(
  <>
    <path d="M4 8 H8 L10 6 H14 L16 8 H20 V18 H4 Z" />
    <circle cx="12" cy="13" r="3.4" />
    {akzent(10.6, 11.6)}
  </>,
);

/** Blätter — zwei versetzt gestapelte Blattflächen, Akzent an der oberen Ecke. */
const blaetter = glyphe(
  <>
    <rect x="7" y="4" width="13" height="16" rx="1" />
    <rect x="4" y="7" width="13" height="16" rx="1" />
    {akzent(15, 9)}
  </>,
);

/** Sync — zwei gegenläufige Kreisbögen mit Pfeilspitzen, Akzent am Startpunkt. */
const sync = glyphe(
  <>
    <path d="M17 6 A8 8 0 1 0 19.5 12.5" />
    <path d="M19.5 12.5 L21 9.5 M19.5 12.5 L16.5 11.5" />
    <path d="M7 18 A8 8 0 0 0 5 11" />
    {akzent(17, 6)}
  </>,
);

/** Manuell — Schalter-Pille mit Knopf, Akzent als Bedienpunkt (Handsteuerung statt Automatik). */
const manuell = glyphe(
  <>
    <rect x="4" y="9" width="16" height="8" rx="4" />
    <circle cx="9" cy="13" r="2.6" />
    {akzent(9, 13)}
  </>,
);

/** Skizze — Freihandstift zieht eine Linie zu Papier, Akzent an der Stiftspitze (Bauauftrag Punkt 2). */
const skizze = glyphe(
  <>
    <path d="M14.5 5.5 L18.5 9.5 L9 19 H5 V15 Z" />
    <path d="M12.5 7.5 L16.5 11.5" />
    {akzent(5, 19)}
  </>,
);

/** Geländer — Handlauf-Band über gleichmässig geteilten Staketen (Muster
 *  `derive/gelaender.ts`s Pfosten-/Handlauf-Zerlegung), Akzent am linken
 *  Handlauf-Ende (v0.9.1 P-B2, `docs/V091-SPEZ.md` §P-B2). */
const gelaender = glyphe(
  <>
    <path d="M4 8 H20 M6 8 V18 M10 8 V18 M14 8 V18 M18 8 V18" />
    {akzent(4, 8)}
  </>,
);

/** Rampe — geneigte Lauffläche mit Grundlinie + Steigungspfeil (Muster
 *  `derive/rampe.ts`s Plan-Steigungspfeil, Schaft am Fuss, Spitze am Kopf),
 *  Akzent an der Pfeilspitze (v0.9.1 P-B2, `docs/V091-SPEZ.md` §P-B2). */
const rampe = glyphe(
  <>
    <path d="M4 20 H20 M4 20 L18 8" />
    <path d="M14 8 H18 V12" />
    {akzent(18, 8)}
  </>,
);

/** Profil — I-Profil-Querschnitt (zwei Flansche + Steg, Muster
 *  `profilOutline()`s stahl-i-Zerlegung, `model/entities.ts`), Akzent am
 *  oberen Flansch (v0.9.2 P-P2, `docs/V092-SPEZ.md` §P-P2). */
const profil = glyphe(
  <>
    <path d="M5 5 H19 M5 19 H19 M12 5 V19" />
    <path d="M8 5 V7.5 M16 5 V7.5 M8 16.5 V19 M16 16.5 V19" />
    {akzent(12, 5)}
  </>,
);

/** Detail — Ausschnitt-Rechteck mit Lupen-Kreis über der Ecke (Muster
 *  `DetailMarker`-Rechteck a/b + Vergrösserungs-Gedanke 1:n), Akzent im
 *  Lupenzentrum (v0.9.2 P-D-Nachzug, `docs/V092-SPEZ.md` §P-D). */
const detail = glyphe(
  <>
    <path d="M4 8 H14 V18 H4 Z" strokeDasharray="2.5 2" />
    <circle cx={16.5} cy={7.5} r={4.5} fill="none" />
    <path d="M19.8 10.8 L22 13" />
    {akzent(16.5, 7.5)}
  </>,
);

/** Höhenkote — Koten-Dreieck auf der Grundlinie mit Aufsatzlinie zur oberen
 *  Massband-Marke (Muster des gedruckten Koten-Symbols, `koteDreieckSvg`/
 *  `PlanView.tsx`s `plan-hoehenkote` — hier bewusst NUR die Dreieckskontur
 *  ohne Füllzustand, da die Insel-Glyphe das Werkzeug zeigt, nicht den
 *  gewählten Bezug), Akzent an der oberen Marke (v0.9.4 P-KI). */
const hoehenkote = glyphe(
  <>
    <path d="M12 20 L8 13 H16 Z" />
    <path d="M12 13 V4" />
    <path d="M9 4 H15" />
    {akzent(12, 4)}
  </>,
);

/** Winkelmass — Scheitel mit zwei Schenkeln + kleinem Gradbogen dazwischen
 *  (Muster `winkelGrad`/`PlanView.tsx`s `plan-winkelmass`-Bogen), Akzent am
 *  Scheitel (v0.9.4 P-KI). */
const winkelmass = glyphe(
  <>
    <path d="M6 19 V5 M6 19 L19 10" />
    <path d="M9.6 19 A4 4 0 0 1 8.9 14.9" />
    {akzent(6, 19)}
  </>,
);

/** Radialmass — Viertelbogen mit Radiuslinie + Pfeilspitze zum Bogenpunkt
 *  (Muster `radialLabel`/`PlanView.tsx`s `plan-radialmass`-Pfeil), Akzent im
 *  Zentrum (v0.9.4 P-KI). */
const radialmass = glyphe(
  <>
    <path d="M7 17 A8 8 0 0 1 17 7" />
    <path d="M12 12 L17 7" />
    <path d="M14.3 6.2 L17 7 L16.2 9.7" />
    {akzent(12, 12)}
  </>,
);

/** Notiz — Textzeile mit Ankerpunkt darunter (Muster des gedruckten
 *  Annotations-Textes, `derive/plansvg.ts`), Akzent am Ankerpunkt (v0.9.7
 *  P-UI, `docs/V097-SPEZ.md` §2 P-UI). */
const notiz = glyphe(
  <>
    <path d="M5 6 H19 M5 11 H15" />
    <path d="M5 17 V21" />
    {akzent(5, 21)}
  </>,
);

/** Linienzug — offener Streckenzug über drei Punkte (Muster der freien
 *  Annotation, `AnnotationLinienzug`), Akzent am letzten Eckpunkt (v0.9.7
 *  P-UI). */
const linienzug = glyphe(
  <>
    <path d="M4 18 L10 7 L15 14 L21 5" />
    {akzent(21, 5)}
  </>,
);

/** Kreis — freier, nicht materialgebundener Annotations-Kreis mit
 *  Radiuslinie (Muster Radialmass, aber ohne Pfeilkopf — reine Form, kein
 *  Mass), Akzent im Zentrum (v0.9.7 P-UI). */
const kreis = glyphe(
  <>
    <circle cx="12" cy="12" r="8" />
    <path d="M12 12 L18 12" />
    {akzent(12, 12)}
  </>,
);

/** Fläche (freie Schraffurfläche) — Polygon mit parallelen Schraffurlinien
 *  (Muster `AnnotationFlaeche.schraffur`, `derive/plansvg.ts`), Akzent an
 *  der obersten Polygon-Ecke (v0.9.7 P-UI). */
const schraffurflaeche = glyphe(
  <>
    <path d="M12 4 L21 10 L17 20 L7 20 L3 10 Z" />
    <path d="M6.5 12 L15 6 M5.5 15.5 L15.5 9 M7 19 L17.5 12" />
    {akzent(12, 4)}
  </>,
);

/** Unterzug — Achse a→b mit den zwei Flansch-Linien des hängenden Balkens
 *  (Muster `PlanView.tsx`s Unterzug-Doppellinie), Akzent am Fusspunkt
 *  (v0.9.7 P-UI). */
const unterzug = glyphe(
  <>
    <path d="M3 15 H21 M3 19 H21" />
    <path d="M3 15 V19 M21 15 V19" />
    {akzent(3, 19)}
  </>,
);

/** Decke — Polygon-Umriss mit Diagonal-Schnittzeichen (Muster des
 *  gedruckten Decken-Symbols in Schnitten), Akzent an der oberen Kante
 *  (v0.9.7 P-UI). */
const decke = glyphe(
  <>
    <rect x="4" y="9" width="16" height="7" rx="0.5" />
    <path d="M4 9 L20 16 M4 16 L20 9" />
    {akzent(12, 9)}
  </>,
);

/** Kostenvoranschlag — Beleg mit gezacktem Abriss und zwei Positionszeilen,
 *  Akzent auf der Summenzeile (die eine Zahl, um die es geht). B77
 *  (`docs/AUFTRAG-B77-VIER-PANELS.md`, C-5). */
const kv = glyphe(
  <>
    <path d="M6 3 H18 V21 L15 19 L12 21 L9 19 L6 21 Z" />
    <path d="M9 8 H15 M9 12 H15" />
    {akzent(15, 16)}
  </>,
);

/** Maengelprotokoll — Warndreieck; der Akzentpunkt IST der Punkt des
 *  Ausrufezeichens (kein `<text>`-Kind, Bauvorschrift). B77, C-6. */
const maengel = glyphe(
  <>
    <path d="M12 4 L21 20 H3 Z" />
    <path d="M12 10 V14" />
    {akzent(12, 17)}
  </>,
);

/** Bauablauf — Zeitachse mit drei versetzten Vorgangsbalken (Gantt-Muster
 *  des `bauablaufBlattSvg`), Akzent am Ende des letzten Balkens
 *  (Endtermin). B77, C-7. */
const bauablauf = glyphe(
  <>
    <path d="M3 5 V20 H21" />
    <path d="M6 8.5 H13 M8 12.5 H18 M11 16.5 H16" />
    {akzent(16, 16.5)}
  </>,
);

/** KosmoDraw — Modellbaum: Wurzelknoten, Stamm, zwei Kindknoten (das
 *  Panel ist zuerst ein Baum, dann Mengen/Ausmass), Akzent am ersten
 *  Verzweigungspunkt. B77, C-8. */
const draw = glyphe(
  <>
    <rect x="3" y="3.5" width="7" height="4" rx="0.8" />
    <path d="M6.5 7.5 V18.5" />
    <path d="M6.5 12 H13 M6.5 18.5 H13" />
    <rect x="13" y="10" width="8" height="4" rx="0.8" />
    <rect x="13" y="16.5" width="8" height="4" rx="0.8" />
    {akzent(6.5, 12)}
  </>,
);

/** Die 37 Werkzeug-Icons, geschlüsselt nach `island-katalog.ts`s `IslandWerkzeug.id`. */
export const ISLAND_GLYPHEN: Record<string, ComponentType<GlyphProps>> = {
  oeffnung,
  messen,
  kommentare,
  darstellung,
  sonne,
  ebenen,
  achsen,
  trace,
  graph,
  kennzahlen,
  checks,
  varianten,
  liste,
  export: exportGlyphe,
  import: importGlyphe,
  rendern,
  blaetter,
  sync,
  manuell,
  skizze,
  gelaender,
  rampe,
  profil,
  detail,
  hoehenkote,
  winkelmass,
  radialmass,
  notiz,
  linienzug,
  kreis,
  schraffurflaeche,
  unterzug,
  decke,
  // B77 (`docs/AUFTRAG-B77-VIER-PANELS.md`, `docs/V0954-SPEZ.md` C-5..C-8):
  // vier neue PROJEKT-Werkzeuge — die Insel-Blaetter der bis dahin nur in
  // der Oberflaeche «manuell» erreichbaren Panels.
  kv,
  maengel,
  bauablauf,
  draw,
};

// ── 4 Island-Pill-Icons ────────────────────────────────────────────────

/** Zeichnen-Pille — Stift zieht eine geschwungene Linie, Akzent an der Stiftspitze. */
const zeichnenPille = glyphe(
  <>
    <path d="M4 19 C 8 19, 8 13, 12 13 S 16 7, 20 7" />
    {akzent(20, 7)}
  </>,
);

/** Ansicht-Pille — Auge (Iris + Pupille), Akzent als Pupille. */
const ansichtPille = glyphe(
  <>
    <path d="M3 12 C 6 6, 18 6, 21 12 C 18 18, 6 18, 3 12 Z" />
    <circle cx="12" cy="12" r="2.6" />
    {akzent(12, 12)}
  </>,
);

/** Projekt-Pille — Ordner mit Lasche, Akzent an der Laschen-Ecke. */
const projektPille = glyphe(
  <>
    <path d="M3 7 H9 L11 9 H21 V18 H3 Z" />
    {akzent(9, 7)}
  </>,
);

/** Austausch-Pille — zwei gegenläufige Pfeile, Akzent an der oberen Pfeilspitze. */
const austauschPille = glyphe(
  <>
    <path d="M5 8 H18 M18 8 L14.5 4.5 M18 8 L14.5 11.5" />
    <path d="M19 16 H6 M6 16 L9.5 12.5 M6 16 L9.5 19.5" />
    {akzent(18, 8)}
  </>,
);

// ── PE2 (v0.8.4, Bauauftrag Punkt 3) — 7 weitere Pill-Icons für die
// Insel-Ids der anderen drei Stationen (`vis-island-katalog.ts`,
// `publish-island-katalog.ts`, `prepare-island-katalog.ts`), die NICHT
// schon einen der vier design-Namen teilen. `IslandShell.tsx` löst die
// Pille rein über den String-Insel-Id auf (`ISLAND_PILL_GLYPHEN[island]`,
// `IslandShell.tsx:495`) — stationsunabhängig, keine weitere Verdrahtung
// nötig, sobald der Schlüssel hier existiert. Absichtlich EIGENE Motive,
// nicht die gleichnamigen Werkzeug-Icons oben wiederverwendet (`graph`/
// `darstellung` existieren als Katalog-Id in BEIDEN Namensräumen —
// Werkzeug-Icon vs. Insel-Pille sind aber unterschiedliche Zeichnungen).

/** Graph-Pille (vis) — drei Knoten im Dreieck um den Ziel-Knoten oben, Akzent am Ziel-Knoten. */
const graphPille = glyphe(
  <>
    <circle cx="6" cy="18" r="2.2" />
    <circle cx="18" cy="18" r="2.2" />
    <circle cx="12" cy="6" r="2.2" />
    <path d="M7.7 16.5 L11 8.5 M16.3 16.5 L13 8.5 M8.2 18 H15.8" />
    {akzent(12, 6)}
  </>,
);

/** Stimmung-Pille (vis) — Bild-Kachel mit Sonne über Horizontlinie, Akzent am Horizont-Ansatz. */
const stimmungPille = glyphe(
  <>
    <rect x="3" y="4" width="18" height="16" rx="2" />
    <circle cx="16" cy="9" r="2.4" />
    <path d="M3 16 L8.5 10.5 L12.5 14 L21 7" />
    {akzent(3, 16)}
  </>,
);

/** Blatt-Pille (publish) — Planblatt mit Plankopf-Streifen unten, Akzent am Streifen. */
const blattPille = glyphe(
  <>
    <rect x="5" y="3" width="14" height="18" rx="1" />
    <path d="M5 16 H19" />
    {akzent(19, 16)}
  </>,
);

/** Darstellung-Pille (publish) — Lupe über einer Blattansicht (Zoom/Massstab), Akzent im Lupenglas. */
const darstellungPille = glyphe(
  <>
    <rect x="3" y="4" width="12" height="10" rx="1" />
    <circle cx="15" cy="16" r="4" />
    <path d="M18 19 L21 22" />
    {akzent(15, 16)}
  </>,
);

/** Aufnahme-Pille (prepare) — schräg einfliegendes Dokument über einer Ablage-Wanne, Akzent am Dokument. */
const aufnahmePille = glyphe(
  <>
    <path d="M4 15 V19 H20 V15" />
    <rect x="9" y="3" width="8" height="10" rx="1" transform="rotate(12 13 8)" />
    {akzent(13, 8)}
  </>,
);

/** Wissen-Pille (prepare) — aufgeschlagenes Buch mit Rücken, Akzent am Rücken oben. */
const wissenPille = glyphe(
  <>
    <path d="M12 6 C 9 4, 5 4, 3 5.5 V18 C 5 16.5, 9 16.5, 12 18 C 15 16.5, 19 16.5, 21 18 V5.5 C 19 4, 15 4, 12 6 Z" />
    <path d="M12 6 V18" />
    {akzent(12, 6)}
  </>,
);

/** Bestand-Pille (prepare) — Archivkiste mit Deckel-Kontur, Akzent an der Deckelnaht. */
const bestandPille = glyphe(
  <>
    <path d="M3 9 H21 V20 H3 Z" />
    <path d="M3 9 L6 4 H18 L21 9" />
    {akzent(12, 9)}
  </>,
);

/**
 * Sonne-Pille (vis, v0.8.9 §9 E11, `docs/V089-SPEZ.md`, PBL2) — Sonne über
 * einer Horizontlinie mit zwei Schrägstrahlen (Sonnenstand/Schattenwurf-
 * Andeutung), Akzent im Sonnenkern. Bewusst ein DRITTES, eigenes Motiv
 * (weder das design-Werkzeug-Icon `sonne` (Z.138, Strahlenkranz-Kreis) noch
 * `vis-glyphen.tsx`s `sonnenstunden` (Sonnenuhr-Strahlenkranz) — die
 * Distinktheits-Probe (`island-glyphen.test.tsx`) verlangt paarweise
 * verschiedene Zeichnungen über ALLE Werkzeug-/Pill-Icons hinweg).
 */
const sonnePille = glyphe(
  <>
    <circle cx="12" cy="9" r="3.4" />
    <path d="M3 18 H21 M6 18 L9 13 M18 18 L15 13" />
    {akzent(12, 9)}
  </>,
);

/** Die 12 Pill-Icons — 4 design-Inseln + 8 weitere Insel-Ids der anderen
 *  drei Stationen (Bauauftrag Punkt 3 + v0.8.9 §9 E11 SONNE). Geschlüsselt
 *  nach der jeweiligen Katalog-`IslandId` (design/vis/publish/prepare teilen
 *  den String-Raum, s. Kommentar oben). */
export const ISLAND_PILL_GLYPHEN: Record<string, ComponentType<GlyphProps>> = {
  zeichnen: zeichnenPille,
  ansicht: ansichtPille,
  projekt: projektPille,
  austausch: austauschPille,
  graph: graphPille,
  stimmung: stimmungPille,
  blatt: blattPille,
  darstellung: darstellungPille,
  aufnahme: aufnahmePille,
  wissen: wissenPille,
  bestand: bestandPille,
  sonne: sonnePille,
};
