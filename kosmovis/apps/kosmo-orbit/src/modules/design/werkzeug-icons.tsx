/**
 * Serie K A5 (K15, Owner «Oberfläche minimal»): Inline-SVG-Icons für die vier
 * meistgenutzten Zeichenwerkzeuge der KosmoDesign-Werkzeugleiste — bewusst
 * KEINE Fremd-Icon-Library (Owner-Auflage), reine handgezeichnete Linien im
 * Gestaltungskonzept-Ton (`docs/GESTALTUNGSKONZEPT.md`: Tusche auf Papier,
 * 1px/1.4px-Linien, kaum Rundung). Jedes Icon ist rein dekorativ
 * (`aria-hidden`) — der zugängliche Name sitzt am Button (`title`+`aria-label`
 * in `DesignWorkspace.tsx`), nicht am Icon selbst.
 *
 * Auswahl der vier Icon-Kandidaten (Bauauftrag 1, dokumentiert auch im
 * ROADMAP-Eintrag): ohne echte Nutzungstelemetrie (frisches Projekt, leerer
 * `kosmo.adaption.v1`-Speicher) ist "häufigste Nutzung" eine Architektur-
 * Annahme, keine Messung — Auswahl (Dauerwerkzeug, ArchiCAD-Grundzustand),
 * Wand (meistgezeichnetes Bauteil), Zone (Raumprogramm/SIA-Flächen) und
 * Volumen (Massenstudien) sind die vier, die in praktisch jeder Sitzung
 * vorkommen. Dach/Treppe/Stütze/Schnitt/Skizze/Mesh bleiben bewusst Text —
 * seltener, spezialisierter, teils (Treppe) ohnehin durch einen bestehenden
 * Text-Selektor vertraglich gebunden (`e2e/module.spec.ts`
 * `button:text-is("Treppe")`).
 *
 * V0.7.2 W1-B (Paket 02): die vier Icons unten (Auswahl/Wand/Volumen/Zone)
 * sind im neuen Strichstil der Glyphen-Bibliothek (`shell/werkzeug-
 * glyphen.tsx`, Spec-§3 Grundregel) nachgezogen — sw-Verhältnis 1.75/24
 * skaliert auf die 16er-Geometrie dieser Datei (≈1.17), runde Kappen/Joins,
 * genau EIN Akzent-Punkt-Kreis (r ≈ 1.7·16/24 ≈ 1.13). Bewusst NICHT die
 * `WerkzeugGlyphe`-Komponente selbst (24er-ViewBox, `var(--k-ink)`) — diese
 * vier bleiben `currentColor`-only/16×16 (Vertrag `werkzeug-icons.test.tsx` +
 * `e2e/oberflaeche-minimal.spec.ts`: aria-Label am Button, LEERER innerText,
 * keine hartkodierte Farbe). Dach/Treppe/Stütze/Schnitt/Mesh/Entwurfs-/Dock-
 * Icons bleiben unangetastet (ausserhalb dieses Auftrags).
 */

const basis = {
  width: 16,
  height: 16,
  viewBox: '0 0 16 16',
  'aria-hidden': true,
  focusable: false,
} as const;

/** Auswahl — Zeigepfeil (Cursor) als Kontur, Spitze = Hotspot (Akzent-Punkt,
 *  wie das Cursor-System in Spec-§8: «Spitze = Hotspot»). */
export function IconAuswahl() {
  return (
    <svg {...basis}>
      <path
        d="M3 2.2 L3 12.6 L5.7 10.1 L7.5 13.9 L9.2 13.1 L7.4 9.3 L10.6 9 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.17"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="3" cy="2.2" r="1.13" fill="currentColor" />
    </svg>
  );
}

/** Wand — Poché-Balken (Wandschnitt in Draufsicht) als Kontur, Akzent-Punkt
 *  am rechten Wandende. */
export function IconWand() {
  return (
    <svg {...basis}>
      <rect
        x="2"
        y="6.3"
        width="12"
        height="3.4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.17"
        strokeLinejoin="round"
      />
      <circle cx="14" cy="8" r="1.13" fill="currentColor" />
    </svg>
  );
}

/** Volumen — Drahtgitter-Würfel (isometrisch), Massenkörper-Symbol, Akzent-
 *  Punkt am obersten Scheitelpunkt. */
export function IconVolumen() {
  return (
    <svg {...basis}>
      <path
        d="M8 1.6 L14 5 L14 11 L8 14.4 L2 11 L2 5 Z M2 5 L8 8.4 L14 5 M8 8.4 L8 14.4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.17"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="8" cy="1.6" r="1.13" fill="currentColor" />
    </svg>
  );
}

/** Zone — dünn umrissenes Raumfeld (SIA-Fläche), Akzent-Punkt an der
 *  Eckmarke oben links. */
export function IconZone() {
  return (
    <svg {...basis}>
      <rect
        x="2.4"
        y="2.4"
        width="11.2"
        height="11.2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.17"
        strokeLinejoin="round"
      />
      <circle cx="2.4" cy="2.4" r="1.13" fill="currentColor" />
    </svg>
  );
}

/**
 * Stream B (W1b, Aufgabe 7): fünf weitere Registry-Icons für die bislang
 * reinen Text-Werkzeuge Dach/Treppe/Stütze/Schnitt/Mesh — additiv, gleicher
 * 16px/1.5px-Tusche-Stil wie oben. **Additiv vor dem sichtbaren Text**: die
 * Buttons zeigen künftig Icon UND Label (nicht Icon-ODER-Label wie bei den
 * vier bestehenden Icon-Werkzeugen oben) — die `toHaveText('Treppe'
 * /'Dach'/…)`-Verträge (`e2e/oberflaeche-minimal.spec.ts`,
 * `e2e/module.spec.ts` `button:text-is("Treppe")`) bleiben so unangetastet
 * wahr, ein SVG ohne `<text>`-Kind trägt nichts zum Text-Inhalt bei.
 */

/** Dach — Giebellinie (Firstlinie über zwei Dachflächen), Grundriss-Symbol. */
export function IconDach() {
  return (
    <svg {...basis}>
      <path
        d="M1.6 10.6 L8 3.2 L14.4 10.6 M4.4 7.4 V13 M11.6 7.4 V13"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Treppe — Stufenprofil (Seitenansicht), klassisches Treppensymbol. */
export function IconTreppe() {
  return (
    <svg {...basis}>
      <path
        d="M2 13.4 H5 V10.4 H8 V7.4 H11 V4.4 H14"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="miter"
      />
    </svg>
  );
}

/** Stütze — Rundstütze im Grundriss (Kreis mit Fusskreuz, Statik-Anmutung). */
export function IconStuetze() {
  return (
    <svg {...basis}>
      <circle cx="8" cy="8" r="3.4" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 1.8 V4.2 M8 11.8 V14.2 M1.8 8 H4.2 M11.8 8 H14.2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

/** Schnitt — Schnittlinie mit Blickrichtungs-Pfeilen an beiden Enden (Norm-Symbol). */
export function IconSchnitt() {
  return (
    <svg {...basis}>
      <path d="M2.2 12.4 L13.8 3.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="2.6 1.6" />
      <path d="M2.2 12.4 L4.6 12 M2.2 12.4 L2.6 10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M13.8 3.6 L11.4 4 M13.8 3.6 L13.4 6" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Mesh — trianguliertes Drahtgitter (Freiform-Netz, Buildplan FM3). */
export function IconMesh() {
  return (
    <svg {...basis}>
      <path
        d="M2 5.4 L8 2.2 L14 5.4 L14 10.6 L8 13.8 L2 10.6 Z M2 5.4 L8 8 L14 5.4 M8 8 L8 13.8 M2 10.6 L8 8 L14 10.6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * K16 A6 (Entwurfs-Einstieg, linke Kante): drei weitere Icons für den
 * Entwurfs-Dock — Sprechen/Schreiben, Skizzieren, manuelles CAD. Gleicher
 * aura-Stil wie oben (nur Linien, `currentColor`, `aria-hidden`).
 */

/** Sprechen/Schreiben — Sprechblase mit Punkten (Text/Dialog, kein Mikrofon-Klischee). */
export function IconEntwurfSprechen() {
  return (
    <svg {...basis}>
      <path
        d="M2.2 3.4 H13.8 V9.8 H6.6 L3.6 12.6 V9.8 H2.2 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="5.6" cy="6.6" r="0.7" fill="currentColor" />
      <circle cx="8" cy="6.6" r="0.7" fill="currentColor" />
      <circle cx="10.4" cy="6.6" r="0.7" fill="currentColor" />
    </svg>
  );
}

/** Skizzieren — Stift über einer angedeuteten Freihandlinie (dieselbe Geste wie das ✎-Werkzeug). */
export function IconEntwurfSkizzieren() {
  return (
    <svg {...basis}>
      <path
        d="M2.4 12.4 C5 11.4 6.5 9.4 8.6 8.6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M8.2 8.9 L11.6 5.5 A1.2 1.2 0 0 1 13.3 7.2 L9.9 10.6 L7.6 11.2 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Manuelles CAD — T-Winkel/Lineal (klassisches Zeichenwerkzeug, ArchiCAD-Anmutung). */
export function IconEntwurfCad() {
  return (
    <svg {...basis}>
      <path
        d="M2.2 2.2 H13.8 V4.6 H4.6 V13.8 H2.2 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M6.8 4.6 V7.4 M9.4 4.6 V7.4 M12 4.6 V7.4" stroke="currentColor" strokeWidth="1.5" />
      <path d="M2.2 8.8 H4.6 M2.2 11.2 H4.6" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

/**
 * K17/A7 (Owner-Befund, wörtlich: «Spezialfähigkeiten hinter Icons»): sechs
 * Icons für die neue «Fähigkeiten»-Gruppe der Design-Werkzeugleiste —
 * Sonnenstudie, Volumenstudien, KV, Bauablauf, Mängel, Submissions-Check.
 * Gleicher Stil wie oben (nur Linien/Flächen aus `currentColor`, `aria-hidden`,
 * 16×16, kaum Rundung). `IconFaehigkeitStudien` ist bewusst ANDERS als das
 * bestehende `IconVolumen` (Zeichenwerkzeug «Volumen», ein einzelner Baukörper)
 * — hier mehrere gestapelte Baukörper, weil «Volumenstudien» Varianten
 * VERGLEICHT statt eine Masse zu zeichnen; eine Verwechslung der beiden wäre
 * genau der Fehler, den zwei visuell identische Icons für zwei verschiedene
 * Fähigkeiten erzeugen würden.
 */

/** Sonnenstudie — Sonnenscheibe mit Strahlen (Schattenwurf/2h-Nachweis). */
export function IconFaehigkeitSonne() {
  return (
    <svg {...basis}>
      <circle cx="8" cy="8" r="3.1" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M8 1.6 V3.3 M8 12.7 V14.4 M1.6 8 H3.3 M12.7 8 H14.4 M3.2 3.2 L4.4 4.4 M11.6 11.6 L12.8 12.8 M12.8 3.2 L11.6 4.4 M4.4 11.6 L3.2 12.8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

/** Volumenstudien — zwei gestapelte/verglichene Baukörper (Varianten). */
export function IconFaehigkeitStudien() {
  return (
    <svg {...basis}>
      <path
        d="M2.4 10.4 L5.6 8.6 L8.8 10.4 L8.8 13.6 L5.6 15.4 L2.4 13.6 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
        transform="translate(0 -2.4)"
      />
      <path
        d="M7.2 5 L10.4 3.2 L13.6 5 L13.6 8.2 L10.4 10 L7.2 8.2 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** KV — stilisiertes Franken-Zeichen (Kostenvoranschlag-Grobschätzung). */
export function IconFaehigkeitKv() {
  return (
    <svg {...basis}>
      <path
        d="M4.6 2.4 H12.2 M4.6 2.4 V13.6 M4.6 7.4 H10.4 M4.6 2.4 L3 4 M4.6 7.4 L3 9"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="square"
      />
    </svg>
  );
}

/** Bauablauf — Gantt-Balken (Grob-Terminplan aus Mengen/Geschossen). */
export function IconFaehigkeitBauablauf() {
  return (
    <svg {...basis}>
      <path
        d="M2.4 3.6 H8.2 M2.4 7.6 H12.4 M2.4 11.6 H6.6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="butt"
      />
    </svg>
  );
}

/** Mängel — Haken im Schild (Abnahme/Schlussbegehung). */
export function IconFaehigkeitMaengel() {
  return (
    <svg {...basis}>
      <path
        d="M8 1.8 L13.4 3.8 V8.2 C13.4 11.4 11 13.4 8 14.4 C5 13.4 2.6 11.4 2.6 8.2 V3.8 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M5.6 8.2 L7.3 10 L10.6 6.2" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Submissions-Check — Checkliste (Lückenliste vor der Ausschreibung). */
export function IconFaehigkeitSubmission() {
  return (
    <svg {...basis}>
      <rect x="2.6" y="2" width="10.8" height="12" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M4.8 5.2 H11.2 M4.8 8 H11.2 M4.8 10.8 H8.8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path d="M4.4 5.2 L4.9 5.7 L5.9 4.4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * v0.7.2 W4-H (Restfix, Bauprotokoll Tag 1 Befund c): die vier Stations-
 * Icons Draw/Vis/Publish/Prepare («A7, EntwurfsDock-Grundicons») standen
 * hier bis W1-B (Paket 02) — seither rendert `EntwurfsDock.tsx` seine
 * Stations-Verknüpfungen selbst über `STATION_GLYPHE`/`WerkzeugGlyphe`
 * (`shell/werkzeug-glyphen.tsx`), der einzige Aufrufer (`DesignWorkspace.tsx`)
 * importierte sie nur noch ungenutzt. Tote Exporte entfernt statt weiter
 * mitgeschleppt — kein Ersatz nötig, es gibt keinen zweiten Verwender mehr.
 */
