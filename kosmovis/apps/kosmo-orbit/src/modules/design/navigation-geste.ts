/**
 * navigation-geste — P-GRIFF (Vorbedingung für v0.9.32,
 * `docs/V0932-VORMERKUNG-CAD-BEDIENUNG.md` §3): die Navigations-Grammatik
 * (Rad-Zoom, Ist-das-Navigation?) stand seit P-NAV2 wortgleich in
 * `PlanView.tsx` und nachgebaut in `SectionView.tsx` — dort mit dem
 * ausdrücklichen Kopfkommentar «hier nachgebaut, nicht importiert», weil
 * `PlanView.tsx` damals fremder Dateibesitz eines parallelen Pakets war.
 * Dieses Bauteil ist die Zusammenführung: REINE Funktionen, kein
 * React-Zustand, ohne Browser testbar.
 *
 * Zwei Familien:
 *
 *  1. **Gestenerkennung** (`istNavGeste`) — sagt aus einem Zeigerereignis,
 *     ob es Navigation ist (Mitteltaste, Rechtsklick, Alt-Klick, oder linke
 *     Taste in einem Navigations-Bereitschaftszustand). Wortgleich in
 *     beiden Dateien bis auf EINEN echten Unterschied: `PlanView.tsx` kennt
 *     einen Pan-Modus-Knopf der Nav-Leiste (`navModus2d === 'pan'`),
 *     `SectionView.tsx` hat keine eigene Werkzeugleiste und kennt diesen
 *     Zustand nicht. Das ist kein Kompromiss, sondern ein Parameter
 *     (`pan2dAktiv`) — `SectionView.tsx` lässt ihn schlicht weg.
 *
 *  2. **Rad-Zoom** — «aus Rad-Ausschlag und Zeigerposition einen neuen
 *     Ausschnitt rechnen». Hier gibt es KEINE gemeinsame Formel, sondern
 *     zwei: `PlanView.tsx` führt die Kamera als `{cx, cy, scale}` (Bezugs-
 *     punkt + ein Massstab, der direkt in den SVG-`transform` einfliesst)
 *     und rechnet den Anker als BILDSCHIRM-Versatz zur SVG-Mitte (kein
 *     Umweg über Weltkoordinaten — bewusst, s. `zoomKameraAnPunkt`
 *     unten). `SectionView.tsx` führt ein `viewBox`-Fenster
 *     `{breite, hoehe, mitteX, mitteY}` (Auto-Fit-Basis) plus einen additiven
 *     Zoom-/Verschiebe-Zustand `{dx, dy, zoom}` und rechnet den Anker als
 *     WELT-Punkt (aus `getScreenCTM()`, das das `preserveAspectRatio`-
 *     Lettern schon mitbringt). Beide Formeln sind über die Fenster-
 *     Fraktion `fx = (anker−minX)/breite` algebraisch ineinander
 *     überführbar — aber sie zu einer einzigen Funktion zu zwingen, hiesse,
 *     eine der beiden bestehenden, bereits gepinnten Invarianten
 *     (`plan-zoom.test.tsx`s `zoomAnPunkt`-Kette, `zoomFensterAnPunkt`s
 *     Auto-Fit-Fraktion) über einen zusätzlichen Rechenweg zu leiten und
 *     ihr byte-für-byte gleiches Verhalten aufs Spiel zu setzen. Der
 *     gemeinsame Nenner ist darum NICHT die Formel, sondern die Kurve, die
 *     beide vor der eigentlichen Fensterrechnung anwenden
 *     (`radZoomFaktor`) — GENAU die Zahl, die in beiden Dateien bisher als
 *     eigenes `Math.exp(-e.deltaY * 0.0012)`-Literal stand.
 *
 *  3. **Kontextmenü-vs-Zug-Schwelle** (`istKontextKlick`, P-RECHTS,
 *     v0.9.32, `docs/V0932-SPEZ.md` §1 P-RECHTS) — Serie J/J2 aus
 *     `Viewport3D.tsx` (dortiger Kommentar: «Rechtsklick OHNE Drag
 *     (<4 px) öffnet das Kontextmenü; ein Rechts-Drag bleibt Pan») hinauf
 *     in dieses gemeinsame Bauteil gehoben. Gemessen (nicht angenommen —
 *     ein eigenes Skript gegen echtes Headless-Chromium, s. Bauagenten-
 *     Bericht v0.9.32 P-RECHTS): das native `contextmenu`-Ereignis feuert
 *     SOFORT beim `pointerdown` der rechten Taste — VOR jeder Bewegung
 *     und VOR dem `pointerup`, unabhängig davon, ob anschliessend gezogen
 *     wird. Es lässt sich darum NICHT selbst als Zugbeweis lesen;
 *     `Viewport3D.tsx` unterdrückt es deshalb bereits IMMER
 *     (`onContextMenu = (ev) => ev.preventDefault()`) und entscheidet
 *     stattdessen selbst, beim `pointerup`, anhand der Bildschirmdistanz
 *     zwischen Druck- und Loslass-Punkt — genau die Distanz, die
 *     `istKontextKlick` hier prüft.
 */

/** Empfindlichkeit der Rad-Zoom-Kurve — bisher als Literal `0.0012` in
 *  `PlanView.tsx#radZoom` UND (nachgebaut) `SectionView.tsx#radZoom`. */
export const NAV_RAD_EMPFINDLICHKEIT = 0.0012;

/** Cursor-verankerter Rad-Zoom, EIN Wheel-Tick → Zoomfaktor. Byte-identisch
 *  mit dem bisherigen `Math.exp(-e.deltaY * 0.0012)` in beiden Dateien. */
export function radZoomFaktor(deltaY: number): number {
  return Math.exp(-deltaY * NAV_RAD_EMPFINDLICHKEIT);
}

/** Ein Zeiger-Druck, so weit reduziert, wie die Gestenerkennung ihn braucht
 *  — dieselbe minimale Form, die `SketchOverlay.tsx`s `istNavGeste`-Prop
 *  bereits verlangt. */
export interface NavGesteZeiger {
  readonly button: number;
  readonly altKey: boolean;
  readonly pointerType?: string;
}

export interface NavGesteOptionen {
  /** `PlanView.tsx`s Nav-Leisten-Zustand `navModus2d === 'pan'` — macht die
   *  LINKE Taste zusätzlich zu einer Navigations-Taste. `SectionView.tsx`
   *  hat keine eigene Nav-Leiste und lässt dieses Feld weg. */
  readonly pan2dAktiv?: boolean;
  /** Leertaste gehalten — macht die LINKE Taste ebenfalls zu einer
   *  Navigations-Taste. In beiden Dateien vorhanden. */
  readonly spaceGedrueckt?: boolean;
}

/**
 * Ist dieser Zeiger-Druck eine NAVIGATIONS-Geste? Mitteltaste, Rechtsklick
 * und Alt-Klick sind es IMMER; die linke Taste nur im Navigations-
 * Bereitschaftszustand (`pan2dAktiv` und/oder `spaceGedrueckt`). Touch ist
 * NIE Navigation (Ein-Finger-Touch zeichnet/klickt, Zwei-Finger-Pinch läuft
 * über eine eigene Geste, keine dieser Bedingung).
 */
export function istNavGeste(e: NavGesteZeiger, optionen: NavGesteOptionen = {}): boolean {
  if (e.pointerType === 'touch') return false;
  return (
    e.button === 1 ||
    e.button === 2 ||
    e.altKey ||
    (e.button === 0 && Boolean(optionen.pan2dAktiv || optionen.spaceGedrueckt))
  );
}

/** Ober-/Untergrenze eines Zoom-Faktors — je Aufrufer eigene Zahlen
 *  (`PlanView.tsx`: `PLAN_ZOOM_MIN/MAX` = 0.005…1, Weltmassstab-Grössen;
 *  `SectionView.tsx`: 0.1…20, ein dimensionsloser Faktor auf die
 *  Auto-Fit-Basis) — ein echter Unterschied, kein Kompromiss, darum
 *  Parameter statt Konstante. */
export interface ZoomGrenzen {
  readonly min: number;
  readonly max: number;
}

/**
 * `PlanView.tsx`s Kamera-Zoom — byte-identisch zur bisherigen `zoomAnPunkt`
 * (dort weiterhin unter diesem Namen exportiert, s. Kopfkommentar dort;
 * `plan-zoom.test.tsx` bleibt unverändert grün). `px`/`py` ist der
 * Zeiger-Offset zur SVG-Mitte in Bildschirm-px (dasselbe Bezugssystem wie
 * `weltAmPunkt`), y wächst nach unten.
 *
 * Invariante: der Weltpunkt unter dem Zeiger ist vor und nach dem Schritt
 * identisch — über beliebige Ketten von Schritten hinweg, und rein+raus
 * (f, dann 1/f) führt zum Ausgangszustand zurück (ausser die Klemme
 * greift).
 */
export function zoomKameraAnPunkt(
  v: { cx: number; cy: number; scale: number },
  faktor: number,
  px: number,
  py: number,
  grenzen: ZoomGrenzen,
): { cx: number; cy: number; scale: number } {
  const scale = Math.min(grenzen.max, Math.max(grenzen.min, v.scale * faktor));
  if (scale === v.scale) return v;
  return {
    cx: v.cx + px / v.scale - px / scale,
    cy: v.cy - py / v.scale + py / scale,
    scale,
  };
}

/** Auto-Fit-Basisfenster in Welt-Einheiten — `SectionView.tsx`s `basis`
 *  (Bounds + Rand, unabhängig von Pan/Zoom). */
export interface Ausschnitt {
  readonly breite: number;
  readonly hoehe: number;
  readonly mitteX: number;
  readonly mitteY: number;
}

/** `SectionView.tsx`s additiver Nav-Zustand — wirkt rein additiv auf die
 *  Auto-Fit-Basis (`Ausschnitt`), s. dortiger Kopfkommentar. */
export interface AusschnittNav {
  readonly dx: number;
  readonly dy: number;
  readonly zoom: number;
}

/**
 * `SectionView.tsx`s Fenster-Zoom — byte-identisch zur bisherigen Inline-
 * Rechnung in `radZoom`. `ankerWeltX`/`ankerWeltY` ist die Zeigerposition
 * bereits in WELT-Koordinaten (aus `getScreenCTM().inverse()` — das
 * `preserveAspectRatio`-Lettern ist darin schon aufgelöst, s. Kopfkommentar
 * dieser Datei).
 *
 * Die Bruchteil-Position des Zeigers im AKTUELLEN Fenster bleibt erhalten —
 * funktioniert unabhängig vom Lettern, weil beide (alt/neu) dieselbe
 * Seitenverhältnis-Achse behalten (Breite/Höhe skalieren gleich).
 */
export function zoomFensterAnPunkt(
  nav: AusschnittNav,
  basis: Ausschnitt,
  faktor: number,
  ankerWeltX: number,
  ankerWeltY: number,
  grenzen: ZoomGrenzen,
): AusschnittNav {
  const zielZoom = Math.min(grenzen.max, Math.max(grenzen.min, nav.zoom * faktor));
  const altBreite = basis.breite / nav.zoom;
  const altHoehe = basis.hoehe / nav.zoom;
  const altMinX = basis.mitteX + nav.dx - altBreite / 2;
  const altMinY = basis.mitteY + nav.dy - altHoehe / 2;
  const fx = altBreite > 0 ? (ankerWeltX - altMinX) / altBreite : 0.5;
  const fy = altHoehe > 0 ? (ankerWeltY - altMinY) / altHoehe : 0.5;
  const neuBreite = basis.breite / zielZoom;
  const neuHoehe = basis.hoehe / zielZoom;
  const neuMinX = ankerWeltX - fx * neuBreite;
  const neuMinY = ankerWeltY - fy * neuHoehe;
  return {
    dx: neuMinX + neuBreite / 2 - basis.mitteX,
    dy: neuMinY + neuHoehe / 2 - basis.mitteY,
    zoom: zielZoom,
  };
}

/** Bildschirm-px, unter der ein Rechtsklick als Kontextmenü-Klick statt als
 *  Zug gilt — dieselbe Zahl wie `Viewport3D.tsx`s Serie-J/J2-Schwelle. */
export const NAV_KONTEXT_SCHWELLE_PX = 4;

/**
 * P7 «Trackpad-Konvention (a)» (v0.9.36, O-T19, Owner-Freigabe 17.08.2026,
 * Herleitung/Unsicherheit/Messwerte ausführlich in `docs/P7-TRACKPAD-
 * MESSUNG.md` §4): Ist EIN `deltaY`-Ausschlag (ohne begleitendes `deltaX`,
 * ohne `ctrlKey` — das entscheidet der Aufrufer) eher ein feiner
 * TRACKPAD-Schritt (→ soll pannen) als ein grober, rastender MAUSRAD-Notch
 * (→ soll zoomen)?
 *
 * Solange eine Geste diagonal ist (`deltaX !== 0`) oder `ctrlKey` gesetzt
 * ist (Pinch), ist die Quelle eindeutig — das ist bereits `radZoom`s
 * bestehender Zweig (P-NAV/O-T19 Teil 1). Offen war ausschliesslich der
 * Fall EIN reines `deltaY` ohne `deltaX`.
 *
 * NACHBESSERUNG (Führungs-Einwand, s. Bauagenten-Bericht): die erste
 * Fassung dieser Funktion nahm eine reine Betragsschwelle
 * (`Math.abs(deltaY) < 50`) — verworfen, weil ein echtes Mausrad unter
 * macOS/Chromium je nach OS-Scrollgeschwindigkeit durchaus `deltaY`-Werte
 * IM EINSTELLIGEN/ZWEISTELLIGEN Bereich liefert; die Schwelle hätte genau
 * DAS Mausrad-Zoomen gefährdet, das dieses Paket ausdrücklich erhalten
 * soll (derselbe Fehlertyp wie O-T11 in `lehren/v0.9.35.md` §2 — ein Fix
 * verschlimmert einen Nachbarbefund). Ersetzt durch zwei Signale:
 *
 *  1. **Bruchwert (`deltaY` selbst)** — ein Trackpad liefert Sub-Pixel-
 *     Deltas aus der Beschleunigungskurve des Betriebssystems; kein
 *     Mausrad-Treiber liefert nicht-ganzzahlige Notch-Grössen. Ein
 *     Bruchwert gilt darum UNABHÄNGIG vom Betrag als Trackpad — kostet
 *     nichts, hängt an keiner Schwelle.
 *  2. **`WheelEvent.wheelDelta` (Chromium/WebKit, nicht standardisiert,
 *     von TypeScripts DOM-Lib nicht deklariert)** — die Windows-
 *     `WHEEL_DELTA`-Konvention (120 je Notch), die Chromium für Mausrad-
 *     Ereignisse spiegelt: **gemessen, nicht angenommen** — ein Probelauf
 *     gegen die reale Chromium-Binärdatei dieses Containers
 *     (`/opt/pw-browsers/chromium-1194`, `page.mouse.wheel(0, deltaY)` für
 *     `deltaY` aus `{-120, 120, -300, -400, ±20000, -6000, 40, -1, -5, 5,
 *     100, -3, 3, 2.5}`, EIN echter `wheel`-Listener liest `e.wheelDelta`)
 *     ergab: **`wheelDelta` ist für JEDEN dieser Werte exakt `±120`** —
 *     unabhängig vom angeforderten `deltaY`. Ein sauberes Vielfaches von
 *     120 gilt darum als Mausrad-Notch → Zoom; jeder andere Wert als
 *     Trackpad → Pan.
 *
 * **Grenze der Messung, ehrlich benannt:** der Probelauf beweist nur die
 * HÄLFTE der Regel — dass ein von Chromium als "ein Notch" interpretiertes
 * Ereignis `wheelDelta` exakt `±120` liefert. Playwrights `mouse.wheel()`
 * hat KEINE Gegenstelle für ein echtes, kontinuierliches Trackpad-Wischen
 * (kein CDP-Primitiv dafür) — die ANDERE Hälfte («ein echtes
 * Trackpad-Wischen liefert KEIN sauberes Vielfaches von 120») bleibt am
 * Container unbewiesen, ebenso das Verhalten auf einem echten macOS-Gerät
 * (dieser Container ist Linux). Bekannt UND unabhängig von diesem
 * Container: Firefox implementiert `wheelDelta` überhaupt nicht — dort ist
 * das Feld immer `undefined`.
 *
 * **Fehlt `wheelDelta`** (Firefox; oder ein Test-Fake ohne das Feld —
 * dieselbe Sorte Falle wie `deltaX`/`deltaMode`, `wissen/training/claude/
 * lehren/v0.9.35.md` §5, `new MouseEvent('wheel', …)` setzt es nicht):
 * **Prinzip «im Zweifel Zoom»** (Führungs-Vorgabe) — ohne das Primärsignal
 * bleibt ein ganzzahliger `deltaY` Mausrad/Zoom, NICHT Trackpad/Pan. Nur
 * der Bruchwert-Fall (Signal 1) wirkt dann noch.
 */
export function istTrackpadSchritt(deltaY: number, wheelDelta?: number): boolean {
  if (deltaY === 0) return false;
  if (!Number.isInteger(deltaY)) return true;
  if (typeof wheelDelta === 'number' && Number.isFinite(wheelDelta)) {
    return wheelDelta % 120 !== 0;
  }
  return false;
}

/**
 * Ist die Bildschirm-Distanz zwischen Rechtsklick-Druck- und -Loslasspunkt
 * UNTER der Schwelle? `true` heisst «Kontextmenü öffnen», `false` heisst
 * «das war ein Zug — Pan/Orbit, kein Menü» (P-RECHTS, v0.9.32,
 * `docs/V0932-SPEZ.md` §1). Reine Distanzfrage, unabhängig von der Taste
 * selbst — der Aufrufer entscheidet, für welche Taste er sie stellt.
 */
export function istKontextKlick(downX: number, downY: number, upX: number, upY: number): boolean {
  return Math.hypot(upX - downX, upY - downY) < NAV_KONTEXT_SCHWELLE_PX;
}
