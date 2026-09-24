import type { Entity } from './entities';
import type { Mm, Pt } from './units';

/**
 * KosmoDoc — der Entity-Store des Projekts.
 *
 * Mutationen laufen ausschliesslich über Patches: { id, before, after }.
 * Ein Patch ist trivial invertierbar (before/after tauschen) — das trägt
 * Undo/Redo, das Journal und später die Yjs-Bindung (Commands sind die
 * einzigen Schreiber; CRDT und Journal werden daraus abgeleitet).
 */

/** Dossier-Eintrag (Phase 0): harte Regel oder Fakt aus dem Wettbewerbsprogramm. */
export interface DossierEintrag {
  typ: 'do' | 'dont' | 'fakt';
  text: string;
}

/** Ein Posten des Wettbewerbs-Raumprogramms (HNF-Soll je Wohnungstyp, m²). */
export interface RaumprogrammPosten {
  typ: string;
  hnfSoll: number;
}

/**
 * SIA-Bauphase (Owner-Auftrag 03.07.) — steuert NUR den Detaillierungsgrad
 * der Pläne (Poché vs. Schichten vs. volle Materialschraffur, 1:200/1:100/
 * 1:50). Regelwerk: docs/PLAN-DETAILLIERUNG.md (Hochbauzeichner-Konvention,
 * Abgleich mit den Lehrheften folgt über KosmoPrepare).
 *
 * WICHTIG (v0.6.3, s. `SiaPhase` unten): `BauPhase` ist NICHT die aktuelle
 * SIA-Teilphase des Projekts — es ist rein der Plan-Zeichenstil. Ein Projekt
 * in der Wettbewerbsphase kann z.B. bereits mit `phase: 'werkplan'` gezeichnet
 * sein (voller Detailgrad für eine Studie), und ein Projekt in der
 * Ausführung kann testweise auf `'vorprojekt'`-Poché zurückgestellt werden.
 * Die beiden Zustände sind bewusst getrennt (`doc.settings.phase` vs.
 * `doc.settings.siaPhase`) und werden NICHT automatisch gekoppelt.
 */
export type BauPhase = 'wettbewerb' | 'vorprojekt' | 'bauprojekt' | 'baueingabe' | 'werkplan';

export function phaseLabel(phase: BauPhase): string {
  switch (phase) {
    case 'wettbewerb':
      return 'Wettbewerb (SIA 22)';
    case 'vorprojekt':
      return 'Vorprojekt (SIA 31)';
    case 'bauprojekt':
      return 'Bauprojekt (SIA 32)';
    case 'baueingabe':
      return 'Baueingabe (SIA 33)';
    case 'werkplan':
      return 'Werkplan (SIA 51)';
  }
}

/**
 * Frühe Entwurfsphasen (Wettbewerb/Vorprojekt) zeichnen mit reduziertem
 * Detail: Fenster als EINE Glaslinie, keine Etiketten/Möblierung, keine
 * Rohboden-Linie (v0.7.0 E1 — Wettbewerb erbt die Vorprojekt-Reduktion).
 * Reine Phasen-Frage; die FARBE entscheidet `derive/poche.ts` separat.
 */
export function fruehePhase(phase: BauPhase): boolean {
  return phase === 'wettbewerb' || phase === 'vorprojekt';
}

/**
 * Aktuelle SIA-Teilphase des Projekts (v0.6.3, `docs/V063-VOLLPROJEKT-KONZEPT.md`
 * Abschnitt 2 + Lücken-Batch 1) — der reale Projektstand im SIA-102/112-Zyklus
 * vom Wettbewerb bis zur Gebäudeabnahme. Zeichnet NICHTS, steuert NICHTS am
 * Plan-Detaillierungsgrad (das bleibt `BauPhase` oben) — reiner
 * Kosmo-sichtbarer Statuszustand, additiv zu `DocSettings`, kein Kernel-Bruch.
 *
 * `'strategie'` = SIA 112 Phase 1 (Strategische Planung — Bedarf/Ziele/
 * Machbarkeit, VOR der eigentlichen Auswahlverfahren-Nummerierung; additiv
 * v0.7.2, `docs/V072-VISUELLES-UPDATE-SPEZ.md` §4), `'wettbewerb'` = SIA 4.22
 * (Auswahlverfahren/Studie, vor der eigentlichen SIA-102-Nummerierung),
 * `'vorprojekt'` = SIA 31, `'bauprojekt'` = SIA 32, `'bewilligung'` = SIA 33
 * (Baugesuch), `'ausschreibung'` = SIA 41, `'ausfuehrung'` = SIA 51/52
 * (Ausführungsprojekt/Werkplanung/Bauausführung), `'abnahme'` =
 * Gebäudeabnahme nach Bauende — SIA 102 kennt dafür keine eigene
 * Teilphase-Nummer im OCR-Korpus, hier ehrlich als eigene, unbelegte
 * Arbeitsphase geführt (kein SIA-Zitat erfunden).
 */
export type SiaPhase =
  | 'strategie'
  | 'wettbewerb'
  | 'vorprojekt'
  | 'bauprojekt'
  | 'bewilligung'
  | 'ausschreibung'
  | 'ausfuehrung'
  | 'abnahme';

export function siaPhaseLabel(phase: SiaPhase): string {
  switch (phase) {
    case 'strategie':
      return 'Strategische Planung (SIA 112 Ph. 1)';
    case 'wettbewerb':
      return 'Wettbewerb/Studie (SIA 4.22)';
    case 'vorprojekt':
      return 'Vorprojekt (SIA 31)';
    case 'bauprojekt':
      return 'Bauprojekt (SIA 32)';
    case 'bewilligung':
      return 'Baueingabe (SIA 33)';
    case 'ausschreibung':
      return 'Ausschreibung (SIA 41)';
    case 'ausfuehrung':
      return 'Ausführungsprojekt/Ausführung (SIA 51/52)';
    case 'abnahme':
      return 'Gebäudeabnahme (unbelegte Arbeitsphase)';
  }
}

/**
 * NUR-Vorschlag (kein Zwang, s. Kommentar bei `BauPhase`): welcher
 * Plan-Detaillierungsgrad zu einer SIA-Teilphase passt. Der Command
 * `design.siaPhaseSetzen` nennt das in seiner Zusammenfassung, koppelt es
 * aber NICHT automatisch in `doc.settings.phase` — Owner-Kontrolle, keine
 * Überraschungen.
 */
export function empfohlenePlanPhase(siaPhase: SiaPhase): BauPhase {
  switch (siaPhase) {
    case 'strategie':
      // Vor dem eigentlichen Wettbewerb entsteht noch kein Plan — dieselbe
      // reduzierte Poché-Empfehlung wie 'wettbewerb' ist der ehrlichste
      // Nächstwert (kein eigener, unbelegter Detaillierungsgrad erfunden).
      return 'wettbewerb';
    case 'wettbewerb':
      return 'wettbewerb';
    case 'vorprojekt':
      return 'vorprojekt';
    case 'bauprojekt':
      return 'bauprojekt';
    case 'bewilligung':
      return 'baueingabe';
    case 'ausschreibung':
    case 'ausfuehrung':
    case 'abnahme':
      return 'werkplan';
  }
}

/**
 * KV-Kennwerte (v0.6.3, `docs/V063-VOLLPROJEKT-KONZEPT.md` Abschnitt 4,
 * Lücken-Batch 3) — Basis für die Kostenvoranschlag-**Grobschätzung**
 * (`derive/kostenschaetzung.ts`). AUSDRÜCKLICH ein Richtwert auf GF-Basis,
 * KEIN Devis: keine CRB/NPK-Positionen, keine eBKP-Feingliederung — das
 * echte Devis-Modul bleibt laut `SUBMISSION-KONZEPT.md` §5.1 Owner-Entscheid.
 * Jeder Zahlenwert unten ist eine **Annahme Owner-Guideline, kein
 * verbindlicher Wert** — Owner-typische CH-Wohnbau-Grössenordnung, kein
 * Norm-/Baukostenindex-Zitat. Additiv zu `DocSettings` (wie `siaPhase`,
 * ROADMAP 233): Altbestand-Docs laden über den Default-Spread in
 * `fromJSON`/`defaultSettings`, kein Kernel-Bruch.
 */
export interface KvKennwerte {
  /** BKP-2-Basiswert in CHF pro m² GF (Geschossfläche aus der Berechnungsliste/
   * den gezeichneten Decken). Annahme Owner-Guideline, kein verbindlicher Wert
   * — grobe CH-Wohnbau-Grössenordnung mittlerer Standard, keine Baukostenindex-
   * Quelle. */
  chfProM2Gf: number;
  /** Anteil Rohbau am BKP-2-Basiswert (0..1). Annahme Owner-Guideline, kein
   * verbindlicher Wert. */
  anteilRohbau: number;
  /** Anteil Ausbau am BKP-2-Basiswert (0..1). Annahme Owner-Guideline, kein
   * verbindlicher Wert. */
  anteilAusbau: number;
  /** Anteil Gebäudetechnik am BKP-2-Basiswert (0..1). Annahme Owner-Guideline,
   * kein verbindlicher Wert. Rohbau+Ausbau+Technik ergeben nicht zwingend
   * genau 1.0 — die Summe wird gerechnet, nicht erzwungen (Owner darf bewusst
   * über/unter 100 % der BKP-2-Basis gewichten). */
  anteilTechnik: number;
  /** Zuschlag BKP 4 (Umgebung) als Anteil der BKP-2-Summe (0..1). Annahme
   * Owner-Guideline, kein verbindlicher Wert. */
  zuschlagUmgebung: number;
  /** Zuschlag BKP 5 (Baunebenkosten) als Anteil der BKP-2-Summe (0..1).
   * Annahme Owner-Guideline, kein verbindlicher Wert. */
  zuschlagBaunebenkosten: number;
  /** Reserve/Unvorhergesehenes als Anteil der Zwischensumme (BKP 2+4+5, 0..1).
   * Annahme Owner-Guideline, kein verbindlicher Wert. */
  reserve: number;
}

/** Default-KV-Kennwerte — s. Kommentar bei `KvKennwerte`: Annahme
 * Owner-Guideline, kein verbindlicher Wert, jederzeit über
 * `design.kvKennwerteSetzen` überschreibbar. */
export const defaultKvKennwerte: KvKennwerte = {
  chfProM2Gf: 1900,
  anteilRohbau: 0.45,
  anteilAusbau: 0.4,
  anteilTechnik: 0.15,
  zuschlagUmgebung: 0.06,
  zuschlagBaunebenkosten: 0.08,
  reserve: 0.1,
};

/**
 * Bauablauf-Kennwerte (v0.6.3, `docs/V063-VOLLPROJEKT-KONZEPT.md` Abschnitt 4,
 * Lücken-Batch 4, Owner-Hauptaufgabe K22) — Leistungswerte (Menge pro Woche)
 * für den Grob-Terminplan (`derive/bauablauf.ts`). Genau wie bei
 * `KvKennwerte`: jeder Zahlenwert ist eine **Annahme Owner-Guideline, kein
 * verbindlicher Wert** — grobe CH-Baustellen-Grössenordnung (kleines MFH,
 * ein Team je Gewerk), keine SIA-/Baumeisterverband-Norm zitiert. Additiv zu
 * `DocSettings` (wie `kvKennwerte`): Altbestand-Docs laden über den
 * Default-Spread in `fromJSON`/`defaultSettings`, kein Kernel-Bruch.
 */
export interface BauablaufKennwerte {
  /** Aushub: m² Baugrube (Grundfläche der untersten Geschossdecke) pro Woche. Annahme. */
  m2AushubProWoche: number;
  /** Rohbau: m³ Wand-/Deckenvolumen (Beton/Mauerwerk) pro Woche — gilt für
   * Fundament/Bodenplatte UND für jedes Rohbau-Geschoss. Annahme. */
  m3RohbauProWoche: number;
  /** Dach: m² Dachfläche (Grundriss, ohne Abwicklung) pro Woche. Annahme. */
  m2DachProWoche: number;
  /** Fenster/Hülle dicht: m² Fenster-/Türfläche pro Woche. Annahme. */
  m2HuelleProWoche: number;
  /** Innenausbau Elektro: m² Geschossfläche (GF) pro Woche. Annahme. */
  m2ElektroProWoche: number;
  /** Innenausbau Sanitär/Heizung: m² GF pro Woche. Annahme. */
  m2SanitaerHeizungProWoche: number;
  /** Innenausbau Trockenbau/Gipser: m² GF pro Woche. Annahme. */
  m2TrockenbauProWoche: number;
  /** Innenausbau Bodenbeläge: m² GF pro Woche. Annahme. */
  m2BodenbelaegeProWoche: number;
  /** Innenausbau Maler: m² GF pro Woche. Annahme. */
  m2MalerProWoche: number;
  /** Umgebung: m² Umgebungsfläche (Parzelle minus Fussabdruck, sonst
   * Fussabdruck selbst) pro Woche. Annahme. */
  m2UmgebungProWoche: number;
  /** Abnahme: feste Dauer in Wochen — ein Termin, kein Bauvolumen, darum kein
   * Mengenbezug. Annahme. */
  abnahmeWochen: number;
  /** Mindestdauer je Phase in Wochen (nie ein 0-Wochen-Balken, auch bei sehr
   * kleiner oder fehlender Menge). Annahme. */
  minDauerWochen: number;
}

/** Default-Bauablauf-Kennwerte — s. Kommentar bei `BauablaufKennwerte`:
 * Annahme Owner-Guideline, kein verbindlicher Wert, jederzeit über
 * `design.bauablaufKennwerteSetzen` überschreibbar. */
export const defaultBauablaufKennwerte: BauablaufKennwerte = {
  m2AushubProWoche: 250,
  m3RohbauProWoche: 60,
  m2DachProWoche: 200,
  m2HuelleProWoche: 150,
  m2ElektroProWoche: 300,
  m2SanitaerHeizungProWoche: 250,
  m2TrockenbauProWoche: 200,
  m2BodenbelaegeProWoche: 350,
  m2MalerProWoche: 400,
  m2UmgebungProWoche: 300,
  abnahmeWochen: 1,
  minDauerWochen: 1,
};

/** Bemassungs-Stil (V2-A5) — projektweit, wirkt in App-Plan, Druck und DXF. */
export interface BemassungsStil {
  /** Aussenketten: beide (Öffnungen + Gesamtmass), nur Gesamtmass, oder keine. */
  aussenKetten: 'beide' | 'gesamt' | 'keine';
  /** Innenketten auf den Achsen der Innenwände (Werkplan). */
  innenKetten: boolean;
  /** Höhenkoten je Geschoss in Schnitt und Ansicht. */
  hoehenKoten: boolean;
  /** Rohkonstruktions-Kette (B1): Kanten der tragenden Schicht als 3. Kette. */
  rohKette?: boolean;
}

/** Projekt-Stammdaten (v0.7.5 A2, Welle 2) — die «langweiligen», aber auf
 * jedem Plankopf/Baueingabeformular verlangten Fakten: Bauherrschaft,
 * Adresse, Parzellennummer, Planverfasser:in, Fristen. Bewusst GETRENNT von
 * `standort` (WGS84/LV95-Koordinaten für Sonnenstudie/Vermessung, V2-V4) und
 * von `parzellenFlaeche` (reine Kennzahl für die AZ-Rechnung) — dieselbe
 * Parzelle kann eine Nummer UND eine Fläche UND einen Standort haben, das
 * sind drei unabhängige, additive Felder, keins ersetzt ein anderes. Nur
 * über `design.projektInfoSetzen` gesetzt (Merge, nie Komplettüberschrieb —
 * s. dortigen Kommentar). EHRLICH: läuft (wie jede DocSettings-Änderung)
 * über Yjs/Undo/`.kosmo`-Paket, ABER `SyncClient` synct heute nur
 * `entities` live, keine SettingsPatches — Stammdaten sind persistent
 * (Vault/IndexedDB, `.kosmo`-Export, Undo), aber NICHT live-kollaborativ
 * zwischen offenen Sitzungen. Das ist vertagte Folgearbeit an `@kosmo/sync`,
 * kein Bug dieser Runde. */
export interface ProjektInfo {
  bauherr?: string;
  adresse?: string;
  parzelleNr?: string;
  /** Verfasser:in/Planbüro — erscheint zusammen mit dem Bauherrn im Plankopf. */
  verfasser?: string;
  /** Fristen/Termine (Baueingabe, Ausschreibung, …) — je Eintrag ein Label +
   * ISO-Datum. Noch ohne eigenes UI-Feld (A2), additiv für spätere
   * Termin-Übersichten/Kosmo-Erinnerungen. */
  fristen?: { label: string; datum: string }[];
  /** Projekt-/Baugesuchs-Nummer (v0.8.0 P2) — freier Code (Büro- oder
   * Behörden-Vergabe), erscheint im Plankopf neben den übrigen Stammdaten.
   * Additiv, wie die übrigen `ProjektInfo`-Felder; nur über
   * `design.projektInfoSetzen` gesetzt (Merge). */
  projektCode?: string;
}

/**
 * Büro-Stammdaten (v0.8.0 P2) — Name, Adresse, Kürzel und Logo fürs
 * Plankopf-Bürofeld. Additiv zu `DocSettings`, nach demselben Muster wie
 * `ProjektInfo`: fehlend (kein `buero`-Feld) = kein Bürofeld im Plankopf,
 * bestehende Docs bleiben unverändert (Goldens-Guard, kein Kernel-Bruch).
 * Nur über `publish.bueroSetzen` gesetzt (Merge, nie Komplettüberschrieb —
 * s. dortigen Kommentar). EHRLICH, wie bei `ProjektInfo` oben: läuft über
 * Yjs/Undo/`.kosmo`-Export wie jede SettingsPatch-Änderung, ABER
 * `SyncClient` synct heute nur `entities` live, keine SettingsPatches —
 * Büro-Stammdaten sind persistent (Vault/IndexedDB, `.kosmo`-Export, Undo),
 * aber NICHT live-kollaborativ zwischen offenen Sitzungen (dieselbe vertagte
 * Folgearbeit an `@kosmo/sync` wie bei `ProjektInfo`).
 */
export interface BueroInfo {
  name?: string;
  adresse?: string;
  kuerzel?: string;
  /** ImageAsset-Id des Büro-Logos — SVG oder JPG (seit v0.8.1 P7; PNG bleibt
   * abgelehnt, s. `publish.bueroSetzen`-Kommentar zum Format-Guard). */
  logoAssetId?: string;
}

/**
 * Render-AUFTRAG (v0.8.4 PC2, `docs/V084-SPEZ.md` E6/C-18) — was `vis.render`
 * bestellt (Node, Kamera-Wahl, Stimmung, Backbone, Auflösung). BEWUSST NUR
 * der Wunsch, nie die Ausführung: Job-Status/Bild/Fehler bleiben Laufzeit
 * (`vis-jobs.ts`/`vis-runtime.ts`, «Laufzeit ≠ Modell» wie bei `NodeLauf`,
 * `entities.ts` Render-Graph-Bilder-Kommentar). Ein Kernel-Command darf nie
 * `Date.now()` in eine Doc-mutierende Nutzlast schreiben (Determinismus/
 * Doppellauf-Test) — dieses Feld trägt darum ABSICHTLICH KEINEN Zeitstempel,
 * die App-seitige Ausführung erkennt einen neuen Auftrag an der Objekt-
 * Referenz (jeder `vis.render`-Lauf liefert ein frisches Literal, auch bei
 * identischen Parametern).
 */
export interface VisRenderWunsch {
  graphId: string;
  nodeId: string;
  kameraWahl: 'auto' | 'saved';
  stimmungPreset?: 'morgen' | 'abend' | 'weiss';
  backbone?: 'z-image-turbo' | 'qwen' | 'flux2-klein' | 'flux-krea' | 'sdxl';
  aufloesung?: readonly [number, number];
}

/**
 * P-GLASNAHT (02.09.2026) — woher die Modellgeometrie stammt.
 *
 * DER ANLASS: Drei Demoläufe hintereinander sind mit einem Modell gefahren,
 * das hinter dem Stand seines Erzeugers zurücklag, und keine Stelle der Kette
 * konnte das merken — weil die ausgeführte Datei nichts über sich selbst
 * aussagte. Der Prüfer auf der Bildseite (`aiimaging.modellstand`) VERGLEICHT:
 * was die Datei über ihren Erzeuger behauptet, gegen das, was an ihr messbar
 * ist. Eine Datei ohne diese Angabe ist konstruktionsbedingt nicht
 * beurteilbar — sein Urteil lautete darum «ungeprueft», und das ist
 * ausdrücklich KEIN Bestehen.
 *
 * Die glb-Ausfuhr kann das nicht aus sich selbst heraus sagen: sie sieht das
 * Dokument, nicht die Datei, aus der es entstand. Darum merkt sich das
 * Dokument es hier — einmal, bei der Übernahme.
 *
 * REGEL 3: `name` ist der DATEINAME ohne Pfad. Ein Pfad enthält den
 * Benutzernamen und hat in nichts zu suchen, was das Haus verlässt.
 */
export interface ModellHerkunft {
  /** Heute nur 'ifc' — der einzige Weg, auf dem Fremdgeometrie hereinkommt. */
  art: 'ifc';
  /** Dateiname OHNE Pfad. */
  name: string;
  bytes: number;
  /**
   * Was die Übernahme aus der Datei ins Dokument gelegt hat, je IFC-Klasse
   * in kanonischer Schreibweise ('IfcWindow', nicht 'IFCWINDOW').
   *
   * Gezählt wird das EINGEFÜGTE, nicht das in der Datei Gefundene: ein
   * Bauteil, das am FreeMesh-Budget oder an fehlender Geschosszuordnung
   * scheitert, steht nicht im Dokument und darf im Herkunftsvermerk nicht
   * behauptet werden.
   */
  ifcKlassen: Record<string, number>;
  /** Tag der Übernahme, ISO (YYYY-MM-DD). */
  stand: string;
}

/**
 * Eine von Hand gesetzte Kamera, aus einer Fremddatei ins Projekt übernommen
 * (12.09.2026, Form 3 «Module anschliessen»).
 *
 * WARUM ES DIESES FELD BRAUCHT — GEMESSEN, NICHT ANGENOMMEN: bis hierher
 * lebte in diesem Dokument KEINE Kamera. Der einzige Kamera-Erzeuger war
 * `derive/kamera.ts` `deriveAutoKameras()`, eine reine Ableitung aus den
 * Szenen-Bounds; der `kameras`-Port des Render-Graphen (`derive/visgraph.ts`)
 * ruft sie live, und `NodeCanvas.tsx` zeigt sie live. Eine Kamera, die
 * NICHT aus der Geometrie folgt, hatte damit keinen Ort — und genau das ist
 * die Kamera, die der Architekt von Hand gesetzt hat. IFC trägt sie nicht,
 * nur 3DS (Graphisoft dokumentiert sie ausdrücklich nur für den 3DS-Export,
 * s. `import/kamera3ds.ts`).
 *
 * EINHEITEN UND ACHSEN: `position`/`target` stehen in METERN in der
 * glTF-Konvention (x, y = oben, z) — Zahl für Zahl dieselbe Konvention wie
 * `AutoKameraStandpunkt.position` (`derive/kamera.ts`) und damit dieselbe
 * wie der tatsächlich gesendete `.glb`-Datenkörper (`derive/gltf.ts`). Die
 * Umrechnung aus der Quelldatei (3DS ist Z-oben) passiert EINMAL beim
 * Import, nicht bei jedem Verbraucher — sonst läuft sie irgendwann an zwei
 * Stellen verschieden, und das ist der Achsenfehler vom 26.08.2026.
 *
 * REGEL 3: `quelle.datei` ist der DATEINAME ohne Pfad — ein Pfad trüge den
 * Benutzernamen, und dieses Feld wandert über den Render-Auftrag aus dem
 * Haus.
 */
export interface UebernommeneKamera {
  /** Name des Kamerablocks in der Quelldatei, z. B. «Cam_0». */
  name: string;
  /** Augpunkt, Meter, glTF-Konvention (x, y = oben, z). */
  position: readonly [number, number, number];
  /** Blickziel, gleiche Einheiten und Achsen. */
  target: readonly [number, number, number];
  /**
   * Horizontaler Bildwinkel in Grad (Kleinbild, Sensor 36 mm) — der ECHTE,
   * nie ein geklemmter. `CameraSpec.fov` (`kosmo-contracts`
   * `render-scene.ts`) ist `min(10).max(120)` und WEIST AB statt zu stutzen;
   * eine Kamera ausserhalb dieser Grenzen wird darum gar nicht erst
   * übernommen, statt hier still zurechtgebogen zu werden.
   */
  fov: number;
  /** Brennweite in mm, wie sie in der Datei steht — die Zahl aus dem
   *  Kamerablatt des Architekten, mitgeführt, damit sie nachprüfbar bleibt. */
  brennweiteMm: number;
  /** Woher sie stammt. `datei` ist der Dateiname OHNE Pfad (REGEL 3). */
  quelle: { art: '3ds'; datei: string; stand: string };
}

export interface DocSettings {
  projectName: string;
  /** P-GLASNAHT: s. `ModellHerkunft`. `null` = das Modell ist hier gezeichnet
   *  worden, nicht übernommen — dann gibt es nichts zu bezeugen. */
  herkunft: ModellHerkunft | null;
  /** Faktor Raumprogramm→anrechenbare Geschossfläche (Owner-Wissen: 1.28 bzw. 1.22 je Büro). */
  agfFactor: number;
  /** Fassadenzuschlag auf aGF für GF-Volumenstudien (Owner: 10% Skelettbau). */
  facadeFactor: number;
  /** Faktor der Berechnungsliste: aGF-Ziel = HNF-Soll × programmFaktor (Owner: 1.22). */
  programmFaktor: number;
  /** Zulässiges aGF-Maximum (m²) für Δ-Max der Berechnungsliste; null = keins gesetzt. */
  maxAgf: number | null;
  /** Wettbewerbs-Raumprogramm (Soll-Flächen je Wohnungstyp). */
  raumprogramm: RaumprogrammPosten[];
  /** Wettbewerbsdossier (Phase 0): Do's, Don'ts, Fakten — fliesst in Kosmos Systemprompt. */
  dossier: DossierEintrag[];
  bemassung: BemassungsStil;
  /** Detaillierungsgrad der Pläne nach SIA-Phase — NICHT der Projektstand, s. `BauPhase`-Kommentar. */
  phase: BauPhase;
  /** Aktuelle SIA-Teilphase des Projekts (v0.6.3) — getrennter Zustand von
   * `phase`, s. `SiaPhase`-Kommentar. Nur über `design.siaPhaseSetzen`
   * gesetzt, koppelt `phase` NICHT automatisch. */
  siaPhase: SiaPhase;
  /** KV-Grobschätzung-Kennwerte (v0.6.3) — s. `KvKennwerte`-Kommentar:
   * Richtwert, kein Devis. Nur über `design.kvKennwerteSetzen` gesetzt. */
  kvKennwerte: KvKennwerte;
  /** Bauablaufplan-Kennwerte (v0.6.3) — s. `BauablaufKennwerte`-Kommentar:
   * Richtwert, ersetzt keine Bauleitung. Nur über
   * `design.bauablaufKennwerteSetzen` gesetzt. */
  bauablaufKennwerte: BauablaufKennwerte;
  /** Aktive Zonenregel (V2-Vorform V1): speist Δ-Max, Höhen-/Geschoss-Checks. */
  zonenRegel: ZonenRegel | null;
  /** Raumtyp-Regeln (V2-F3, Finch Graph-Rules): leer = eingebaute Richtwerte. */
  raumRegeln: RaumRegel[];
  /** Custom-Kennzahlen (V2-F9): Wert × Flächenbasis, z.B. CHF/m² aGF. */
  kennzahlFormeln: KennzahlFormel[];
  /** Zonen-Vorlagen (V2-F7): Layouts, achsweise streckbar wieder absetzbar. */
  vorlagen: ZonenVorlage[];
  /** Projektstandort CH (V2-V4): einmal geholt, im Doc = offline verfügbar. */
  standort: ProjektStandort | null;
  /** Fassadenmodule (Modul-Editor): gezeichnete Module für die Rasterung. */
  fassadenModule: FassadenModul[];
  /** Parzellenfläche in m² (für AZ → zulässige aGF). */
  parzellenFlaeche: number | null;
  /** Rollen-Vorstufe (Vision D2): ordnet die Zentrale und färbt Kosmos Blick.
   * Bewusst KEINE Rechteverwaltung — Ansichts-Filter, mehr nicht. */
  rolle: 'entwurf' | 'ausfuehrung' | 'admin' | null;
  /**
   * Rahmenangaben, ohne die Normregeln nicht angewandt werden duerfen
   * (Stufe 2 der Wissens-Integration, `wissen/anwendbarkeit.ts`).
   *
   * Alle drei sind bewusst NULLBAR und nicht vorbelegt. Eine Vorbelegung
   * waere eine Behauptung ueber das Projekt, die niemand aufgestellt hat —
   * und `gilt()` antwortet auf fehlende Angaben mit «unbestimmt», also mit
   * einer Frage statt einem Fehlalarm. Genau so soll es sein.
   */
  rahmen: {
    /** Kantonskuerzel. Ohne ihn bleibt kantonales Recht unbestimmt. */
    kanton: string | null;
    /**
     * Kategorie des Bereichs nach SIA 500 Ziff. 1.3 — `oeffentlich`,
     * `wohnen` oder `arbeit`. Sie haengt am BEREICH, nicht am Gebaeude.
     */
    kategorie: 'oeffentlich' | 'wohnen' | 'arbeit' | null;
    /**
     * Ist hindernisfreies Bauen vorgeschrieben? SIA 500 Ziff. 0.1.2: die
     * Norm gilt nicht von selbst. `null` heisst «nicht festgestellt».
     */
    hindernisfreiPflicht: boolean | null;
  };
  /** Verschneidungsprioritäten-Overrides je Material (RE-ARCHICAD A1,
   * 0–999); fehlend = Katalog-Default aus MATERIAL_PRIORITAET. */
  materialPrioritaeten?: Record<string, number>;
  /** Publikations-Sets (RE-ARCHICAD A4): benannte Blattauswahl + Namensregel
   * — ein Klick exportiert den ganzen Plansatz («Publisher ohne Baum»). */
  publikationsSets?: PublikationsSet[];
  /** Themenpläne (RE-ARCHICAD A5, grafische Überschreibungen): Regeln
   * Kriterium→Farbe, je Blatt-Platzierung aktivierbar — Brandschutz-,
   * Schallschutz- oder Materialplan aus demselben Modell. */
  themen?: ThemenPlan[];
  /** Keynotes (RE-ARCHICAD A6): zentrale Notizliste nr→Text — Etiketten
   * verweisen mit der Nummer, die Blatt-Legende schreibt den Text aus. */
  keynotes?: { nr: string; text: string }[];
  /** Aktive Schnittlinie (H-9, v0.6.8) — null = kein Schnitt gesetzt. Nur über
   * `design.schnittSetzen` gesetzt. */
  schnitt?: SchnittSpec | null;
  /** Fassadenmodul-Zuweisung auf Wandzügen ohne Volumenkörper (H-35, v0.6.8):
   * additive Erweiterung von `design.fassadenModulZuweisen` — statt einer
   * MassBody-Kante wird die Fassadenseite eines Geschosses direkt benannt,
   * abgeleitet aus den zusammenhängenden Aussenwänden. `derive/
   * fassadenmodule.ts`s `richtungsModule()` liest BEIDE Quellen (Volumenkörper
   * UND diese Liste); der bestehende MassBody-Weg bleibt unverändert. */
  wandFassadenModule?: WandFassadenZuweisung[];
  /** Poché-Modus (v0.7.0, `docs/V070-KONZEPT.md` E2) — steuert, wie stark die
   * SIA-Phase die Grundriss-/Schnitt-Füllung bestimmt: `'phase'` (Default bei
   * Abwesenheit) lässt `phase` entscheiden (Wettbewerb/Vorprojekt = ein
   * schwarzes Poché, Bauprojekt/Baueingabe = Schichten schwarz/grau, Werkplan
   * = heutiges Material-Verhalten); `'schwarz'` erzwingt die Schwarz-Regeln
   * phasenunabhängig; `'material'` erzwingt das heutige Tint-Verhalten
   * phasenunabhängig. Duplikat-Union statt Import aus `derive/poche.ts` —
   * `model/` importiert nicht aus `derive/` (s. `SchnittSpec`-Kommentar). Nur
   * über `design.pocheModusSetzen` gesetzt. */
  pocheModus?: 'phase' | 'schwarz' | 'material';
  /** 3D-Darstellungsmodus (v0.7.0 E3) — `'auto'` (Default bei Abwesenheit)
   * löst über `siaPhase` auf: bis und mit `'bewilligung'` weiss, ab
   * `'ausschreibung'` Material. `'material'/'weiss'/'schwarz'` erzwingen den
   * jeweiligen Modus. Reine Projektsemantik (Yjs/Undo) — der Textur-Toggle
   * bleibt separat in localStorage. Auflösung: `aufgeloesteDarstellung3d()`
   * unten. Nur über `design.darstellung3dSetzen` gesetzt. */
  darstellung3d?: 'auto' | 'material' | 'weiss' | 'schwarz';
  /** H-42: Öffnungsflügel-Bogen bei parametrischen Fenstern zeichnen —
   * Default bei Abwesenheit `true` (Bestandsverhalten). `false` blendet die
   * `fenster-bogen`-Symbolik aus (Owner-Schalter im Projekt-Menü). Nur über
   * `design.fensterBoegenSetzen` gesetzt. */
  fensterBoegen?: boolean;
  /** Projekt-Stammdaten (v0.7.5 A2) — s. `ProjektInfo`-Kommentar oben. Fehlend
   * (oder ein leeres `{}`) = kein Feld gesetzt, Plankopf zeigt keine
   * Bauherr-/Verfasser-Zeile (Golden-Guard). Nur über
   * `design.projektInfoSetzen` gesetzt. */
  projekt?: ProjektInfo;
  /** Büro-Stammdaten (v0.8.0 P2) — s. `BueroInfo`-Kommentar oben. Fehlend =
   * kein Bürofeld im Plankopf (Golden-Guard). Nur über `publish.bueroSetzen`
   * gesetzt. */
  buero?: BueroInfo;
  /** Letzter Render-Wunsch (v0.8.4 PC2) — s. `VisRenderWunsch`-Kommentar
   * oben. Fehlend ODER `null` = kein offener Wunsch (Golden-Guard, Muster
   * `schnitt?: SchnittSpec | null`). Nur über `vis.render` gesetzt. */
  visRenderAuftrag?: VisRenderWunsch | null;
  /** Standort-Persistenz (v0.8.6 PC1, `docs/V086-SPEZ.md` E6/D7) — s.
   * `StandortAdresse`-Kommentar oben. Fehlend ODER `null` = «kein Standort
   * gesetzt» (Golden-Guard, Muster `schnitt?: SchnittSpec | null`). Nur über
   * `design.standortAdresseSetzen` gesetzt. */
  standortAdresse?: StandortAdresse | null;
  /** ÖREB-Auszug light (v0.8.7 PB1, `docs/V087-SPEZ.md` E6/D7/C-11/C-12) — s.
   * `OerebAuszug`-Kommentar unten. Fehlend ODER `null` = «kein Auszug
   * abgerufen» (Golden-Guard, Muster `standortAdresse?: … | null`). Nur über
   * `design.oerebAuszugSetzen` gesetzt. KEIN rechtsgültiger ÖREB-Auszug —
   * der Pflicht-Hinweis dazu lebt im UI (StandortSuche, DesignWorkspace.tsx),
   * nicht im Modell. */
  oerebAuszug?: OerebAuszug | null;
  /**
   * Von Hand gesetzte, aus einer Fremddatei übernommene Kamera-Standpunkte
   * (12.09.2026) — s. `UebernommeneKamera`. Fehlend ODER leer heisst «keine
   * übernommen» (Golden-Guard, Muster `schnitt?: SchnittSpec | null`): ohne
   * das Feld ist jeder abgeleitete Standpunkt und jeder Render-Auftrag Zahl
   * für Zahl derselbe wie vorher. Nur über `design.kamerasUebernehmen`
   * gesetzt.
   */
  /**
   * ═══════════════════════════════════════════════════════════════════════
   *  DIE NORDRICHTUNG — Abnahmezeile 3, erste Haelfte
   * ═══════════════════════════════════════════════════════════════════════
   *
   * «das haus nach norden drehen» — und bis zum 18.09.2026 gab es das
   * schlicht nicht. Der Sonnenstand war stellbar (Datum, Uhrzeit, zwei Wege
   * in der Oberflaeche), die AUSRICHTUNG des Hauses dazu nicht. Damit stand
   * jede Schattenstudie schief, sobald das Projekt nicht zufaellig nach
   * Norden gezeichnet war — und niemand konnte es sehen.
   *
   * DIE KONVENTION, und sie gehoert hierhin und nirgendwo sonst:
   * **In welche Himmelsrichtung zeigt die +Y-Achse des Projekts.**
   * 0 = nach Norden (Vorgabe, der heutige Stand). 90 = nach Osten. Gemessen
   * im Uhrzeigersinn wie jede Kompasspeilung.
   *
   * WARUM SO HERUM: Der Architekt zeichnet zuerst und richtet dann aus. Er
   * dreht nicht den Norden, er sagt, wo sein «oben» hinzeigt. Die
   * Umrechnung in die Sonnenrichtung macht `azimutImProjekt()` weiter unten —
   * an EINER Stelle, damit 3D-Fenster, Nordpfeil und Bildkanal nicht
   * auseinanderlaufen koennen.
   *
   * WAS SIE NICHT DREHT: die gemeldeten Sonnenzahlen. Ein Mittagsazimut von
   * 180 Grad ist eine Aussage ueber die Sonne, nicht ueber das Haus, und
   * bleibt wahr, wie das Haus auch steht. Gedreht wird nur, was eine
   * RICHTUNG IM MODELL ist.
   */
  /** `| undefined` ausdruecklich, und das ist kein Schoenheitsfehler: Nur so
   *  darf ein Rueckgaengig-Schritt das Feld WIEDER ENTFERNEN statt eine
   *  gesetzte Null zu hinterlassen. `KosmoDoc.apply` legt Einstellungen mit
   *  einem Spread zusammen — der kann einen Schluessel nur loeschen, wenn der
   *  neue Wert wirklich `undefined` ist, und `exactOptionalPropertyTypes`
   *  verbietet das ohne diese Angabe. Gemessen: ohne sie war das Dokument
   *  nach Setzen+Rueckgaengig nicht mehr byte-gleich zum Stand davor. */
  nordrichtungGrad?: number | undefined;

  /**
   * ABNAHMEZEILE 46 — WIE STARK DIE SONNE SCHEINT, als Faktor auf den
   * gerechneten Sonnenstand. 1 heisst «wie gemessen», 0.4 gedaempft,
   * 2 scharf. Vorgabe ist NICHT 1, sondern **fehlend**.
   *
   * Zweimal zugerufen:
   *   «vielleicht sonnenlicht noch etwas staerker mit minimal staerkerem
   *    schattenwurf»
   *   «das sonnenlicht ist aktuell nicht mehr im innenraum wirklich
   *    vorhanden also drueckt nicht mehr so rein wie zuvor»
   *
   * WARUM EIN FAKTOR UND KEINE LUX-ZAHL: Die Staerke der Sonne ist an einem
   * Ort und einer Uhrzeit keine freie Groesse — sie steht fest. Was der
   * Owner stellt, ist die BILDWIRKUNG: wie hart das Licht hereindrueckt.
   * Eine Beleuchtungsstaerke in Lux zu behaupten, die niemand gemessen hat,
   * waere eine Zahl ohne Deckung; ein Faktor sagt ehrlich, was er ist.
   *
   * `| undefined` aus demselben Grund wie oben bei `nordrichtungGrad`: nur
   * so nimmt ein Rueckgaengig-Schritt das Feld WIEDER WEG, statt eine
   * gesetzte 1 zu hinterlassen — die naemlich nicht dasselbe ist wie «nie
   * gestellt». Der Bildkanal nennt die Sonne nur, wenn jemand sie gestellt
   * hat; sonst stuende in jedem Prompt ein Satz ueber ein Licht, das
   * niemand angefasst hat.
   */
  sonnenStaerke?: number | undefined;

  uebernommeneKameras?: UebernommeneKamera[];
}

/** Auflösung von `darstellung3d: 'auto'` (v0.7.0 E3) — pure Funktion, testbar
 * ohne Viewport3D. Bis und mit `'bewilligung'` (Wettbewerb…Baueingabe) gilt
 * das Weissmodell als Phasen-Default, ab `'ausschreibung'` Material. */
/**
 * DER SONNEN-AZIMUT, WIE ER IM PROJEKT ERSCHEINT — Abnahmezeile 3.
 *
 * `SunCalc.getPosition()` liefert den Azimut im Bogenmass, gemessen von SUED
 * nach WEST (so steht es auch im Viewport-Kommentar). Diese Funktion dreht ihn
 * um die Nordrichtung des Projekts — und das ist alles, was an der ganzen
 * Zeile Rechnung ist.
 *
 * DIE PROBE IN WORTEN, damit die Richtung nicht zur Glaubensfrage wird:
 * Zeigt die +Y-Achse nach OSTEN (90 Grad) und steht die Sonne im echten
 * Sueden, dann steht sie vom Projekt aus gesehen «rechts» — der Azimut im
 * Projekt ist um 90 Grad kleiner. Darum MINUS.
 *
 * `azimutImProjekt(a, 0) === a` ist der Rueckfall fuer jedes bestehende
 * Dokument: ohne gesetzte Nordrichtung aendert sich nichts, Bit fuer Bit.
 */
export function azimutImProjekt(azimutRad: number, nordrichtungGrad: number | undefined): number {
  if (!nordrichtungGrad) return azimutRad;
  return azimutRad - (nordrichtungGrad * Math.PI) / 180;
}

export function aufgeloesteDarstellung3d(settings: DocSettings): 'material' | 'weiss' | 'schwarz' {
  const modus = settings.darstellung3d ?? 'auto';
  if (modus !== 'auto') return modus;
  // v0.7.2: 'strategie' (SIA 112 Ph. 1, additiv) liegt VOR 'wettbewerb' —
  // zählt aus demselben Grund als «früh» (noch kein Weissmodell-Anlass für
  // Material).
  const fruehePhasen: SiaPhase[] = ['strategie', 'wettbewerb', 'vorprojekt', 'bauprojekt', 'bewilligung'];
  return fruehePhasen.includes(settings.siaPhase) ? 'weiss' : 'material';
}

/** Amtliche 3D-Darstellung (v0.7.3 D5) — NICHT zu verwechseln mit
 * `aufgeloesteDarstellung3d()` oben: jene respektiert eine manuelle
 * `settings.darstellung3d`-Übersteuerung (Arbeitsmodus, frei wählbar,
 * NIE amtlich); diese hier IGNORIERT `settings.darstellung3d` bewusst und
 * leitet den Modus einzig aus der SIA-Phase ab (bzw. aus `zweck`, wenn
 * gegeben). Grund: Beweisbares — «Für Vis aufnehmen», Blatt-Bildslots,
 * Kosmo-Blick-Captures — muss IMMER im offiziellen, phasenbestimmten
 * Modus rendern, unabhängig davon, was der/die Bearbeitende gerade als
 * Arbeitsmodus eingestellt hat.
 *
 * `zweck`:
 * - `'situation'` / `'volumennachweis'` → IMMER `'schwarz'` (Capture-
 *   Kontext für Situationsplan/Volumennachweis, überschreibt die Phase).
 * - abwesend → Phasen-Ableitung analog zu `aufgeloesteDarstellung3d`:
 *   frühe Phasen (Strategie…Bewilligung) → `'weiss'` (Weissmodell),
 *   ab Werkplan (Ausschreibung…Abnahme) → `'material'` (Textur). */
export function offizielleDarstellung3d(
  settings: DocSettings,
  zweck?: 'situation' | 'volumennachweis',
): 'material' | 'weiss' | 'schwarz' {
  if (zweck === 'situation' || zweck === 'volumennachweis') return 'schwarz';
  const fruehePhasen: SiaPhase[] = ['strategie', 'wettbewerb', 'vorprojekt', 'bauprojekt', 'bewilligung'];
  return fruehePhasen.includes(settings.siaPhase) ? 'weiss' : 'material';
}

/** Eine Fassadenseiten-Zuweisung im wand-basierten Baupfad (H-35, v0.6.8).
 * `richtung` dupliziert absichtlich `Fassadenrichtung` aus `derive/
 * fassadenmodule.ts` statt sie zu importieren — `model/` importiert nicht aus
 * `derive/` (siehe `SchnittSpec`-Kommentar). */
export interface WandFassadenZuweisung {
  storeyId: string;
  richtung: 'sued' | 'nord' | 'west' | 'ost';
  modul: string;
}

/** Eine Override-Regel: WAS wird WIE getönt (erste Treffer-Regel gewinnt). */
export interface ThemenRegel {
  /** raumTyp (Zonen), material (Schichten/Stützen) oder klasse (Plan-Klasse
   * wie «treppe», «decke», «stuetze»). */
  kriterium: 'raumTyp' | 'material' | 'klasse';
  wert: string;
  /** Füllfarbe (Hex), im Druck solid mit erhaltenem Stift. */
  farbe: string;
  /** Legenden-Text; fehlt = wert. */
  label?: string;
}

/** Benannter Themenplan (RE-ARCHICAD A5). */
export interface ThemenPlan {
  name: string;
  regeln: ThemenRegel[];
}

/** Benanntes Export-Set (RE-ARCHICAD A4). namensregel-Platzhalter:
 * {nr} (2-stellig), {blatt}, {projekt}, {massstab} (1-50), {format} (A1-quer). */
export interface PublikationsSet {
  name: string;
  sheetIds: string[];
  namensregel?: string;
}

/** Fassadenmodul (Modul-Editor, vorform-Kern): Elemente in Modul-Koordinaten. */
export interface FassadenModul {
  name: string;
  /** Modulmass b × h (mm). */
  breite: number;
  hoehe: number;
  elemente: ModulElement[];
}

export interface ModulElement {
  /** Rechteck in Modul-Koordinaten (mm, Ursprung unten links). */
  x: number;
  y: number;
  b: number;
  h: number;
  typ: 'fenster' | 'paneel';
}

/** Projektstandort (V2-V4): WGS84 für die Sonne, LV95 fürs Vermessen. */
export interface ProjektStandort {
  label: string;
  lat: number;
  lon: number;
  /** LV95 Ost/Nord (m). */
  e: number;
  n: number;
  /** Absolutbezug ±0.00 in m ü.M. (B2: erscheint an der EG-Kote). */
  hoeheM?: number;
}

/**
 * Standort-Adresssuche-Beleg (v0.8.6 PC1, `docs/V086-SPEZ.md` E6/D7/C-17):
 * das amtliche Suchergebnis der StandortSuche (geo.admin.ch SearchServer,
 * `DesignWorkspace.tsx`) — Adresstext, LV95-Koordinaten, Herkunft, Abrufzeit.
 * BEWUSST ein eigenes Feld (`DocSettings.standortAdresse`), NICHT eine
 * Erweiterung von `ProjektStandort`/`standort`: Letzteres trägt WGS84 lat/lon
 * + optional `hoeheM` fürs Sonnenstudien-/Schwarzplan-/Viewport3D-Fundament
 * und wird bereits von `design.standortSetzen` gesetzt (registriert seit V2-
 * V4) — dieselbe Kommando-Kennung für ein neues Setting hätte
 * `registerCommand` bei der doppelten Registrierung werfen lassen
 * (`commands/core.ts`). `standortAdresse` ist rein additiv, fliesst NICHT in
 * `derive/*` ein (Golden-Guard, wie `schnitt`/`visRenderAuftrag`) und dient
 * einzig der Reload-/`.kosmo`-Persistenz + der KosmoData-Anzeige. Nur über
 * `design.standortAdresseSetzen` gesetzt.
 */
export interface StandortAdresse {
  adresse: string;
  /** LV95 Ost/Nord (m). */
  lv95: { e: number; n: number };
  quelle: 'geoadmin';
  /** ISO-Zeitstempel des Abrufs (App-seitig erzeugt, s. Kommentar im Command). */
  abgerufenAm: string;
}

/**
 * ÖREB-Auszug light (v0.8.7 PB1, `docs/V087-SPEZ.md` E6/D7/C-11/C-12): das
 * Ergebnis der Kette LV95 (aus `standortAdresse`) → GetEGRID →
 * ÖREB-Extract, reduziert auf die reine Themencode-Betroffenheitsliste
 * (Thema betroffen ja/nein, OHNE Detailwerte — die Spez erlaubt diese
 * Reduktion ausdrücklich als Reissleine, hier bewusst als Normalform
 * gewählt: der öffentlich dokumentierte ÖREB-Transferstruktur-Extract trennt
 * `ConcernedTheme`/`NotConcernedTheme` ohnehin nur nach Code+Titel, s.
 * Fixture-Vertrag in `DesignWorkspace.tsx` `StandortSuche`/`oerebAbrufen`).
 * BEWUSST kein rechtsgültiger Auszug — nur ein «light»-Abbild fürs Projekt;
 * der Pflicht-Hinweis dazu lebt im UI, nicht im Modell (Sanktion 7).
 * Additiv wie `standortAdresse`, fliesst NICHT in `derive/*` ein
 * (Golden-Guard). Nur über `design.oerebAuszugSetzen` gesetzt. */
export interface OerebAuszug {
  /** Eidgenössischer Grundstücksidentifikator (GetEGRID-Ergebnis). */
  egrid: string;
  /** ISO-Zeitstempel des Abrufs (App-seitig erzeugt). */
  abgerufenAm: string;
  quelle: 'oereb-bund';
  /** Reine Themencode-Betroffenheitsliste — kein Detailwert je Thema. */
  themen: { code: string; titel: string; betroffen: boolean }[];
}

/** Zonen-Vorlage (V2-F7): Zonen relativ zur BBox-Ecke, Grösse fürs Strecken. */
export interface ZonenVorlage {
  name: string;
  /** BBox der Vorlage (mm) — Referenz für den achsweisen Stretch. */
  breite: number;
  hoehe: number;
  zonen: {
    outline: { x: number; y: number }[];
    name: string;
    sia: string;
    raumTyp?: string;
    /** F7-Locks (v0.7.0 E5-ii, Finch «locked/extendable»): Achse dieser
     * Zone bleibt beim achsweisen Stretch (`design.vorlageSetzen`/
     * `design.grundrissGenerieren`) mass-stabil, statt proportional
     * mitzuskalieren (z.B. Nasszelle fest 2.4 m tief, während Diele/Küche
     * die Differenz aufnehmen). Fehlend = `'dehnbar'` — heutiges
     * Verhalten (alles skaliert gleichmässig), Alt-Vorlagen unverändert. */
    dehnungX?: 'fest' | 'dehnbar';
    dehnungY?: 'fest' | 'dehnbar';
  }[];
  /** Möbel relativ zur BBox-Ecke (beim Speichern in der BBox eingesammelt). */
  moebel?: { typ: string; at: { x: number; y: number }; rotationGrad: number }[];
  /** Zonentüren relativ zur BBox-Ecke (Review-Fix 8). */
  tueren?: { at: { x: number; y: number }; breite: number }[];
  /** Regeln-in-Vorlagen (v0.7.0 E5-v, Finch «Graph Rules» je Plan): Ids aus
   * `REGEL_PRESETS` (`regelpresets.ts`). Beim Absetzen/Instanziieren
   * (`design.vorlageSetzen`, Plan-Library-Treffer in
   * `design.grundrissGenerieren`) werden die referenzierten Presets in
   * `DocSettings.raumRegeln` aktiviert — bestehende Projekt-Regeln werden
   * NIE still überschrieben, nur um fehlende Raumtypen ergänzt (Vereinigung,
   * im Command-Summary benannt). Fehlend/leer = keine Regel-Aktivierung. */
  regeln?: string[];
}

/** Custom-Kennzahl (V2-F9): name = «Erstellungskosten», wert 3200, basis 'agf', einheit 'CHF'. */
export interface KennzahlFormel {
  name: string;
  /** Multiplikator pro m² der Basis. */
  wert: number;
  basis: 'gf' | 'agf' | 'hnf' | 'ngf';
  /** Ergebnis-Einheit, z.B. «CHF» oder «kg CO2e». */
  einheit: string;
}

/** Raumtyp-Regel (V2-F3): Grenzwerte je Raumtyp, dreistufig gemeldet. */
export interface RaumRegel {
  raumTyp: string;
  /** Mindestfläche m²; null = keine. */
  minFlaeche: number | null;
  /** Mindest-Lichtbreite mm (BBox-Näherung); null = keine. */
  minBreite: number | null;
  /** Raum braucht ein Fenster (Tageslicht). */
  tageslicht: boolean;
}

/** Schnittlinie (H-9, v0.6.8): früher reiner UI-Laufzeit-State am Schnitt-
 * Werkzeug, jetzt über `design.schnittSetzen` im Doc — damit gelten Undo,
 * Yjs-Sync und Kosmo-Tool automatisch wie bei jedem anderen Command. Die
 * Geometrie deckt sich absichtlich mit `derive/section.ts`s `SectionSpec`
 * (a/b/depth/lookLeft), ist hier aber unabhängig definiert, damit `model/`
 * nicht von `derive/` importiert. */
export interface SchnittSpec {
  a: Pt;
  b: Pt;
  /** Sichttiefe in mm (wie weit hinter der Ebene projiziert wird). */
  depth: number;
  /** Blick zur linken Normalen (true) oder rechten (false). */
  lookLeft: boolean;
}

/** CH-Zonenregel — Richtwerte je Bauzone, editierbar; kein Ersatz fürs Baureglement. */
export interface ZonenRegel {
  name: string;
  /** Ausnützungsziffer aGF/Parzellenfläche; null = keine. */
  az: number | null;
  /** Max. Gebäudehöhe über Projektnull (mm). */
  maxHoehe: number | null;
  maxVollgeschosse: number | null;
  grenzabstandKlein: number | null;
  grenzabstandGross: number | null;
}

export const defaultSettings: DocSettings = {
  projectName: 'Unbenannt',
  herkunft: null,
  agfFactor: 1.28,
  facadeFactor: 1.1,
  programmFaktor: 1.22,
  maxAgf: null,
  raumprogramm: [],
  dossier: [],
  // Grundriss-Default = Bestandsverhalten; Koten an (Schnitt/Ansicht gewinnen)
  bemassung: { aussenKetten: 'beide', innenKetten: false, hoehenKoten: true },
  // Default = volle Detaillierung (Bestandsverhalten); Vorprojekt reduziert
  phase: 'werkplan',
  // Default = Beginn des SIA-Zyklus (neues Projekt startet im Wettbewerb).
  siaPhase: 'wettbewerb',
  kvKennwerte: { ...defaultKvKennwerte },
  bauablaufKennwerte: { ...defaultBauablaufKennwerte },
  zonenRegel: null,
  parzellenFlaeche: null,
  raumRegeln: [],
  kennzahlFormeln: [],
  vorlagen: [],
  standort: null,
  fassadenModule: [],
  rolle: null,
  rahmen: { kanton: null, kategorie: null, hindernisfreiPflicht: null },
};

export interface Patch {
  readonly id: string;
  readonly before: Entity | null;
  readonly after: Entity | null;
}

export interface SettingsPatch {
  readonly settings: true;
  readonly before: Partial<DocSettings>;
  readonly after: Partial<DocSettings>;
}

export type AnyPatch = Patch | SettingsPatch;

export function isSettingsPatch(p: AnyPatch): p is SettingsPatch {
  return 'settings' in p;
}

export function invertPatches(patches: readonly AnyPatch[]): AnyPatch[] {
  return [...patches]
    .reverse()
    .map((p) =>
      isSettingsPatch(p)
        ? { settings: true as const, before: p.after, after: p.before }
        : { id: p.id, before: p.after, after: p.before },
    );
}

export class KosmoDoc {
  readonly entities = new Map<string, Entity>();
  settings: DocSettings = { ...defaultSettings };
  /** Monoton steigende Revisionsnummer — Cache-Invalidierung der Derive-Stufe. */
  revision = 0;

  /**
   * B83 (`docs/AUFTRAG-B83-RUECKGAENGIG-PRUEFT-NICHTS.md`, ROADMAP 1207):
   * Ids, die JE Teil DIESES Dokuments waren — auch nach dem Löschen
   * (Grabstein-Menge, wächst nur, schrumpft nie). `History.undo()`/`redo()`
   * (`commands/core.ts`) brauchen dieses Gedächtnis: der Undo-/Redo-Stapel
   * überlebt einen Dokumentwechsel (Demo laden, Projekt öffnen, Tresor),
   * diese Menge NICHT — ein frisch erzeugtes/geladenes Dokument kennt nur
   * seine eigenen Ids, nie die eines vorherigen Dokuments. Bewusst PRIVAT:
   * die einzige zulässige Frage von aussen ist `warJeTeilDesDokuments(id)`,
   * nicht die Menge selbst — sie ist ein Implementierungsdetail des
   * Dokuments, keine öffentliche Datenstruktur.
   */
  private readonly jeGesehen = new Set<string>();

  /**
   * B83: gehörte diese Id JE zu DIESEM Dokument (auch wenn die Entität
   * inzwischen gelöscht ist)? `false` heisst: diese Id stammt aus einem
   * ANDEREN Dokument — genau das Signal, das `History.undo()`/`redo()`
   * gegen eine verschleppte Fremd-Id prüfen.
   */
  warJeTeilDesDokuments(id: string): boolean {
    return this.jeGesehen.has(id);
  }

  get<T extends Entity = Entity>(id: string): T | undefined {
    return this.entities.get(id) as T | undefined;
  }

  byKind<T extends Entity>(kind: T['kind']): T[] {
    const out: T[] = [];
    for (const e of this.entities.values()) if (e.kind === kind) out.push(e as T);
    return out;
  }

  inStorey(storeyId: string): Entity[] {
    const out: Entity[] = [];
    for (const e of this.entities.values()) {
      if ('storeyId' in e && e.storeyId === storeyId) out.push(e);
    }
    return out;
  }

  openingsOf(wallId: string) {
    const out = [];
    for (const e of this.entities.values()) {
      if (e.kind === 'opening' && e.wallId === wallId) out.push(e);
    }
    return out;
  }

  storeysOrdered() {
    return this.byKind<import('./entities').Storey>('storey').sort((a, b) => a.index - b.index);
  }

  /** Oberkante eines Geschosses = elevation + height (für Wandhöhen 'geschoss'). */
  storeyTop(storeyId: string): Mm | undefined {
    const s = this.get<import('./entities').Storey>(storeyId);
    return s ? s.elevation + s.height : undefined;
  }

  apply(patches: readonly AnyPatch[]): void {
    for (const p of patches) {
      if (isSettingsPatch(p)) {
        this.settings = { ...this.settings, ...p.after };
      } else if (p.after === null) {
        this.entities.delete(p.id);
      } else {
        this.entities.set(p.id, p.after);
        this.jeGesehen.add(p.id); // B83 — Grabstein-Menge, s. Feld-Kommentar oben
      }
    }
    this.revision++;
  }

  toJSON(): DocJson {
    return {
      schema: 'kosmo.model/v1',
      settings: this.settings,
      entities: [...this.entities.values()],
    };
  }

  static fromJSON(json: DocJson): KosmoDoc {
    const doc = new KosmoDoc();
    doc.settings = { ...defaultSettings, ...json.settings };
    for (const e of json.entities) {
      doc.entities.set(e.id, e);
      doc.jeGesehen.add(e.id); // B83 — geladene Startentitäten gehören von Anfang an zum Dokument
    }
    return doc;
  }
}

export interface DocJson {
  schema: 'kosmo.model/v1';
  settings: DocSettings;
  entities: Entity[];
}
