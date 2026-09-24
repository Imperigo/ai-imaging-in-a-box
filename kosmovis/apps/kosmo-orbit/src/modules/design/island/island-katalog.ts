/**
 * Island-Werkzeug-Katalog (PD1 Fundament + PD2 Verdrahtung, `docs/ISLAND-UI-
 * SPEZ.md` §2/§3).
 *
 * Statischer, reiner Datensatz — die ursprüngliche 29-Werkzeug-Zuordnung auf
 * die vier Islands (ZEICHNEN 11 / ANSICHT 6 / PROJEKT 6 / AUSTAUSCH 6),
 * Reihenfolge und Zählung 1:1 aus der Mapping-Tabelle §3.1–§3.4 übernommen.
 * v0.9.1 P-B2 (`docs/V091-SPEZ.md` §P-B2) hängt additiv zwei weitere
 * ZEICHNEN-Werkzeuge ans Ende der Insel (`gelaender`/`rampe`) — Gesamtstand
 * jetzt 31 (ZEICHNEN 13 / ANSICHT 6 / PROJEKT 6 / AUSTAUSCH 6), s. dortigen
 * Kommentar.
 *
 * v0.9.2 P-P2 (`docs/V092-SPEZ.md` §P-P2) hängt additiv EIN weiteres
 * PROJEKT-Werkzeug an (`profil` — Profil-Manager, Typenkatalog-Verwaltung
 * für Stützen-/Unterzugprofile, `inhalte/profile.tsx`) — Gesamtstand jetzt 32
 * (ZEICHNEN 13 / ANSICHT 6 / PROJEKT 7 / AUSTAUSCH 6). Kein `toolId` (wie
 * `kennzahlen`/`liste`): das Werkzeug ist ein reiner Katalog-Manager ohne
 * Plan-Klickmodus, dieselbe Begründung wie bei den übrigen `toolId`-losen
 * PROJEKT-Werkzeugen.
 *
 * **PD2 (diese Fassung): `toolId` echt gesetzt**, wo eine Insel-Id 1:1 einer
 * bestehenden `ui-zustand.ts`-`ToolId` entspricht (die neun Zeichenwerkzeuge
 * mit direktem `setTool`-Weg). Für die übrigen «Vorhanden»/«Teilweise»-
 * Werkzeuge, deren echte Aktion KEIN `ToolId`-Setzen ist (z. B. Sonne →
 * `sonneOffen`, Varianten → `variantenPanelOffen`), bleibt `toolId` leer —
 * ihre Verdrahtung lebt als benannter Fall in `DesignWorkspace.tsx`s
 * `aktiviereIslandWerkzeug()` (Integrationspunkt, dateidisjunkt von diesem
 * reinen Datensatz). `glyphe` trägt seit PB2 (v0.8.4, s. Icon-Verdrahtungs-
 * Kommentar weiter unten) echte Icon-Components statt Text-Kürzeln — seit
 * PE2 (Bauauftrag Punkt 2) auch `skizze` (21. Icon, `island-glyphen.tsx`),
 * damit sind alle 29 Katalog-Werkzeuge SVG-vollständig.
 *
 * **`hinweis` (PD2):** ehrlicher Kurztext fürs (weiterhin leere PD1-)
 * Popup-/Fenster-Rahmen jener Werkzeuge, die PD2 NICHT verdrahtet — die
 * echte Aktion liegt aus Datei-Kreis-Gründen anderswo (PlanView.tsx/andere
 * Station, ausserhalb PD2s Dateikreis) bzw. ist mangels Toggle (Kennzahlen/
 * Checks: «immer sichtbar», kein Flag) nicht erreichbar. Nur Werkzeuge MIT
 * Popup (`hatPopup===true`) können einen Hinweis zeigen — Achsen/Manuell
 * (die zwei `hatPopup===false`-Fälle) bleiben beim PD1-Toast.
 *
 * **v0.8.3 E1/E2/E3 (`docs/V083-SPEZ.md` §1/§2/§3.3):** die drei einstigen
 * «kein heutige Entsprechung»-Fälle (Öffnung/Messen/Kommentare, §3 Status
 * NEU/teilweise) haben jetzt echte Kernel-Entitäten+Commands UND einen
 * eigenen `ToolId` (§8-5/§8-6/§8-7 Owner-entschieden) — alle drei Zeilen
 * unten tragen seither `toolId`+`status:'vorhanden'` statt `hinweis`.
 *
 * `hatPopup` bildet den Prototyp-Datensatz `t.pop` nach (§4.2: «Werkzeuge
 * ohne Popup quittieren die Aktivierung mit einem Toast») — `false` NUR dort,
 * wo §4.4 wörtlich «kein Popup nötig» vermerkt (Achsen: reiner Toggle;
 * Manuell: Sofort-Umschaltung ohne Popup). Alle übrigen 27 Werkzeuge bekommen
 * `true`, auch wenn ihr Stufe-2-Inhalt laut §4.4 schlicht ist (z. B. Graph
 * «An/Aus») — die Spec markiert dort kein «kein Popup nötig», anders als bei
 * Achsen.
 *
 * **PE2 (v0.8.4, C-27 — «8 Rahmen-Werkzeuge»):** die toolId-lose 8er-Gruppe
 * aus `island-katalog-pd2.test.ts` (Achsen/Trace/Graph/Kennzahlen/Checks/
 * Rendern/Blätter/Sync) war der Ursprung der Owner-Mängelliste «8
 * Rahmen-Werkzeuge» (`docs/V084-SPEZ.md` §1.1). Geprüft gegen den Code:
 * 7 der 8 (alle ausser Achsen) tragen seit P3/PD3a/PD3b (v0.8.3) längst
 * echten Registry-Inhalt (`inhalte/{ansicht,projekt,austausch}.tsx`,
 * `registrierteWerkzeugIds()` listet alle 27 Popup-Werkzeuge, keine Lücke).
 * Nur die `hinweis`-Metadaten hier hinkten hinterher — Kennzahlen/Checks
 * trugen einen inzwischen toten Text (Stufe 3 zeigt das echte, eingebettete
 * Panel), Rendern/Blätter/Sync behaupteten «Weg offen (§8-4)», obwohl §8-4
 * seit PD3c entschieden UND real verdrahtet ist (`docs/ISLAND-UI-SPEZ.md`
 * §8 Punkt 4 Nachtrag) — derselbe «Leiche»-Fund wie beim Trace/Graph-Hinweis
 * (P10 v0.8.3). PE2 entfernt alle fünf toten `hinweis`-Felder ersatzlos
 * (dasselbe Muster). Achsen bleibt der einzige echte Rest — Owner-sauber
 * geschlossen durch die §4.4-Ausnahme (kein Popup, kein Rahmen).
 *
 * **v0.9.4 P-KI (Folgepaket zu 653/661, «Koten-Werkzeuge in Insel und
 * Inspector»):** + 3 weitere ZEICHNEN-Werkzeuge (`hoehenkote`/`winkelmass`/
 * `radialmass`) — Gesamtstand jetzt 36 (ZEICHNEN 17 / ANSICHT 6 / PROJEKT 7
 * / AUSTAUSCH 6). Die Klickkette (P-PB, 661) ist bereits fertig; dieses
 * Paket liefert NUR den Insel-Knopf (`toolId`, s. unten) + die Stufe-2/3-
 * Inhalte (`inhalte/zeichnen.tsx`) + Inspector-Zeilen — s. dortige
 * Kopfkommentare für den genauen Zuschnitt.
 *
 * **B77 (`docs/AUFTRAG-B77-VIER-PANELS.md`, Abnahme `docs/V0954-SPEZ.md`
 * C-5 bis C-8):** + 4 weitere PROJEKT-Werkzeuge (`kv`/`maengel`/
 * `bauablauf`/`draw`) — Gesamtstand jetzt 46 (ZEICHNEN 24 / ANSICHT 6 /
 * PROJEKT 10 / AUSTAUSCH 6). Begründung s. bei den vier Zeilen selbst.
 *
 * **P3 (Fundregister `docs/inventur/funde-2026-09-07.tsv`, PLH-STATUS-2 +
 * PLH-HINWEIS-5):** zwei zusammenhängende Funde. Erstens: die einzige
 * Lesestelle von `status` war bis hierhin `SpezWorkspace.tsx:143` — der
 * Design-Renderer (`IslandShell.tsx`) las das Feld gar nicht, acht Design-
 * Werkzeuge mit `status !== 'vorhanden'` sahen darum ununterscheidbar aus
 * wie die übrigen 38. Zweitens: `hinweis` hatte einen gebauten Renderer
 * (Tooltip + Fenster-Fallback, `IslandShell.tsx`), aber KEIN einziger
 * Katalog-Eintrag übergab ihn — eine Datenquelle, die niemand fütterte, für
 * einen Verbraucher, den niemand fütterte. `IslandShell.tsx` liest `status`
 * jetzt (Suffix «(Platzhalter)» am Werkzeugtitel, Muster `SpezWorkspace.
 * tsx:143`s «Öffnen (Platzhalter)» — keine neue Bauart).
 *
 * **Die Messung, gegen den Code statt gegen den Katalog-Kommentar:** von
 * den acht Kandidaten (gelaender/rampe/detail/ebenen/rendern/blaetter/sync/
 * manuell) waren SIEBEN veraltet, nicht platzhalterisch —
 * `test/island-katalog-pd2.test.ts:119-122` hatte den Verdacht für
 * rendern/blaetter/sync bereits vorweggenommen. gelaender/rampe/detail
 * tragen seit v0.9.1 P-B1 bzw. dem P-D-Nachzug (s. deren Zeilen-Kommentare
 * oben) die VOLLSTÄNDIGE Klickkette (`DesignWorkspace.tsx`s
 * `punktSetzen()`/`mehrpunktAbschliessen()` → `design.gelaenderZeichnen`/
 * `-rampeZeichnen`/`-detailErstellen`, editierbar im Inspector) — der
 * P-B2-Kommentar «NICHT Teil dieses Pakets, das liefert P-B1» beschrieb
 * einen offenen Punkt, der beim Schreiben DIESES Kommentars längst
 * geschlossen war. rendern/blaetter/sync zeigen echte Laufzeitdaten
 * (`useVisRuntime`/`useProject`/`syncActive()`, `inhalte/austausch.tsx`)
 * UND einen echten Weiterweg (`ZurStationKnopf`) — dieselbe «voll
 * verdrahtet»-Schwelle wie jedes andere `vorhanden`-Werkzeug, das auf ein
 * Cross-Station-Panel verweist (z. B. `darstellung`). manuell schaltet mit
 * `setDesignOberflaeche('manuell')` vollständig und unbedingt auf die
 * komplette klassische Oberfläche um — dieselbe Mechanik (toolId-los,
 * `hatPopup:false`, ein Store-Flip in `aktiviereIslandWerkzeug()`) wie
 * `achsen`, das längst `status:'vorhanden'` trägt. Alle sieben wechseln
 * hier auf `'vorhanden'`.
 *
 * **Der einzige echte Rest: `ebenen`.** Das Werkzeug heisst «Ebenen»
 * (Mehrzahl, Mehrschicht-Anspruch), liefert aber nur EINEN generischen
 * Textur-Schalter (`viewport-chrome-runtime.ts`) — kein unabhängiges
 * Ein-/Ausblenden einzelner Ebenen (Achsen/Bemassung/Text/…). Das ist
 * dieselbe Lücke, die `inhalte/ansicht.tsx`s `EbenenStufe3` bereits selbst
 * einräumt (`island-ebenen-hinweis-neu`) — ein wirklich unfertiges
 * Werkzeug, kein «Leiche»-Fund. Bleibt `status:'teilweise'` UND bekommt
 * jetzt den katalogseitigen `hinweis` (bislang war das Feld an dieser
 * Stelle schlicht nie gesetzt worden — genau die in PLH-HINWEIS-5
 * gemessene leere Datenquelle).
 */

import type { ComponentType } from 'react';
import {
  IconAuswahl,
  IconWand,
  IconVolumen,
  IconZone,
  IconDach,
  IconTreppe,
  IconStuetze,
  IconMesh,
  IconSchnitt,
} from '../werkzeug-icons';
import { ISLAND_GLYPHEN } from './island-glyphen';

/**
 * PB2 (`docs/V084-SPEZ.md` §3 E8 + Bauauftrag «Werkzeug-Chrome») —
 * Icon-Verdrahtung: `glyphe` trägt ab hier ECHTE Icon-Components statt
 * Text-Kürzeln, wo eines existiert. Acht der elf ZEICHNEN-Werkzeuge
 * bekommen ihre bereits bestehenden `werkzeug-icons.tsx`-SVGs (Auswahl/
 * Wand/Volumen/Zone/Dach/Treppe/Stütze/Mesh — `schnitt`, das neunte Icon
 * dieser Datei, war bis W-4 (`docs/BERICHT-FABLE-UI-2026-08-18.md`) KEIN
 * Katalog-Werkzeug; W-4 gibt ihm seinen Katalog-Eintrag, s. dort). Die
 * übrigen 20 Werkzeuge (inkl. Öffnung/Messen aus ZEICHNEN) bekommen ihr
 * `ISLAND_GLYPHEN`-Icon. PE2 (v0.8.4, Bauauftrag Punkt 2) schliesst die
 * letzte Lücke: `skizze` bekommt jetzt ebenfalls ihr `ISLAND_GLYPHEN`-Icon
 * (das 21., dort namensgleich `skizze`) statt des früheren Text-Kürzels
 * `'SK'` — der `string`-Zweig von `glyphe` bleibt ein echter Typ-Fallback
 * (`IslandWerkzeug.glyphe: string | ComponentType<...>`, E8), aber ab jetzt
 * ohne aktiven Katalog-Konsumenten.
 */
function icon(rec: Record<string, ComponentType<{ size?: number }>>, id: string): ComponentType<{ size?: number }> {
  const c = rec[id];
  if (!c) throw new Error(`island-katalog: kein ISLAND_GLYPHEN-Icon für "${id}"`);
  return c;
}

export type IslandId = 'zeichnen' | 'ansicht' | 'projekt' | 'austausch';

/** Reihenfolge der vier Islands (Bühnenordnung §1/§2: links·oben·rechts·unten). */
export const ISLAND_REIHENFOLGE: readonly IslandId[] = ['zeichnen', 'ansicht', 'projekt', 'austausch'];

export const ISLAND_LABEL: Readonly<Record<IslandId, string>> = {
  zeichnen: 'ZEICHNEN',
  ansicht: 'ANSICHT',
  projekt: 'PROJEKT',
  austausch: 'AUSTAUSCH',
};

/** Pill-Orientierung je Island (§2-Tabelle: 34×104 vertikal / 104×34 horizontal). */
export type IslandOrientierung = 'vertikal' | 'horizontal';

export const ISLAND_ORIENTIERUNG: Readonly<Record<IslandId, IslandOrientierung>> = {
  zeichnen: 'vertikal',
  ansicht: 'horizontal',
  projekt: 'vertikal',
  austausch: 'horizontal',
};

export type IslandWerkzeugStatus = 'vorhanden' | 'teilweise' | 'neu';

export interface IslandWerkzeug {
  /** Kebab-Case-Id, wo möglich 1:1 aus bestehenden `ToolId`s/Command-Namen (§3-Fundstellen). */
  readonly id: string;
  /** Deutscher Anzeigename (Leiste/Popup/Fenster-Titel, Toast-Text). */
  readonly name: string;
  /** PC0 v0.8.4: `string` statt `IslandId` — andere Stationen bringen eigene
   *  Insel-Ids mit (`docs/V084-SPEZ.md` E1); für design bleibt es faktisch
   *  die Vierer-Union (alle Aufrufer unten übergeben `IslandId`). */
  readonly island: string;
  /** PB2 E8: echtes Icon (SVG-Component) ODER Text-Kürzel-Fallback (`skizze`,
   *  s. Datei-Kopfkommentar). String bleibt gültig — Fallback, kein totes Bein. */
  readonly glyphe: string | ComponentType<{ size?: number }>;
  readonly status: IslandWerkzeugStatus;
  /** `false` nur bei den zwei §4.4-Ausnahmen (Achsen, Manuell) — s. Kopfkommentar. */
  readonly hatPopup: boolean;
  /** Echte `ui-zustand.ts`-`ToolId` (PD2) — nur gesetzt, wo die Aktivierung
   *  1:1 `setTool(toolId)` ist (die neun Zeichenwerkzeuge). */
  readonly toolId?: string;
  /** PD2: ehrlicher Hinweistext fürs Popup, wenn KEINE Aktion verdrahtet ist
   *  (s. Kopfkommentar) — undefined bei allen verdrahteten Werkzeugen.
   *  P3 (PLH-HINWEIS-5): der einzige tatsächliche Verbraucher ist der
   *  Lang-Hover-Tooltip in `IslandShell.tsx` (unbedingt, sobald gesetzt)
   *  plus der Fenster-Fallback (nur ohne registrierten Stufe-3-Inhalt) —
   *  bis P3 hatte KEIN Katalog-Eintrag das Feld je gesetzt; `ebenen` ist
   *  der erste echte Fall. */
  readonly hinweis?: string;
}

function werkzeug(
  id: string,
  name: string,
  island: IslandId,
  glyphe: string | ComponentType<{ size?: number }>,
  status: IslandWerkzeugStatus,
  hatPopup: boolean,
  extra?: { toolId?: string; hinweis?: string },
): IslandWerkzeug {
  return {
    id,
    name,
    island,
    glyphe,
    status,
    hatPopup,
    ...(extra?.toolId !== undefined ? { toolId: extra.toolId } : {}),
    ...(extra?.hinweis !== undefined ? { hinweis: extra.hinweis } : {}),
  };
}

/** ZEICHNEN (11) — §3.1. */
const ZEICHNEN: readonly IslandWerkzeug[] = [
  werkzeug('auswahl', 'Auswahl', 'zeichnen', IconAuswahl, 'vorhanden', true, { toolId: 'auswahl' }),
  werkzeug('wand', 'Wand', 'zeichnen', IconWand, 'vorhanden', true, { toolId: 'wand' }),
  // v0.8.3 E3 (§3.3, docs/V083-SPEZ.md, §8-5 jetzt entschieden): echter
  // ToolId statt Hinweis — `aktiviereIslandWerkzeug()` (DesignWorkspace.tsx)
  // setzt `setTool('oeffnung')` automatisch (`w.toolId`-Zweig).
  werkzeug('oeffnung', 'Öffnung', 'zeichnen', icon(ISLAND_GLYPHEN, 'oeffnung'), 'vorhanden', true, { toolId: 'oeffnung' }),
  werkzeug('volumen', 'Volumen', 'zeichnen', IconVolumen, 'vorhanden', true, { toolId: 'volumen' }),
  werkzeug('zone', 'Zone', 'zeichnen', IconZone, 'vorhanden', true, { toolId: 'zone' }),
  werkzeug('dach', 'Dach', 'zeichnen', IconDach, 'vorhanden', true, { toolId: 'dach' }),
  werkzeug('treppe', 'Treppe', 'zeichnen', IconTreppe, 'vorhanden', true, { toolId: 'treppe' }),
  werkzeug('stuetze', 'Stütze', 'zeichnen', IconStuetze, 'vorhanden', true, { toolId: 'stuetze' }),
  // PE2 (v0.8.4, Bauauftrag Punkt 2): `skizze` bekommt jetzt ihr echtes
  // SVG (`island-glyphen.tsx`s 21. Icon) — der frühere Text-Fallback `'SK'`
  // ist raus, alle 29 Katalog-Werkzeuge sind damit SVG-vollständig.
  werkzeug('skizze', 'Skizze', 'zeichnen', icon(ISLAND_GLYPHEN, 'skizze'), 'vorhanden', true, { toolId: 'skizze' }),
  werkzeug('mesh', 'Mesh', 'zeichnen', IconMesh, 'vorhanden', true, { toolId: 'mesh' }),
  // v0.8.3 E2/E3 (§2/§3.3, §8-7 jetzt entschieden): echter ToolId.
  werkzeug('messen', 'Messen', 'zeichnen', icon(ISLAND_GLYPHEN, 'messen'), 'vorhanden', true, { toolId: 'messen' }),
  // v0.9.1 P-B2 (`docs/V091-SPEZ.md` §P-B2): zwei NEUE ZEICHNEN-Werkzeuge —
  // die Kernel-Seite (Entity + Command, P-A1/P-A2) ist fertig gelandet,
  // `toolId` aktiviert echt denselben generischen `setTool`-Weg wie jedes
  // andere Zeichenwerkzeug (`aktiviereIslandWerkzeug()`,
  // `DesignWorkspace.tsx`, unverändert — kein Sonderfall nötig).
  // **P3-Korrektur (PLH-STATUS-2):** stand hier mit `status:'teilweise'`,
  // weil die Zwei-Punkt-Klickkette «NICHT Teil dieses Pakets» war und erst
  // P-B1 (Fable) sie liefern sollte. P-B1 ist seither gelandet
  // (`DesignWorkspace.tsx`s `punktSetzen()`/`gelaenderAbschliessen()` →
  // `design.gelaenderZeichnen`, editierbar im Inspector) — der Katalog
  // wurde dabei nie nachgezogen. Gemessen statt vermutet: `status:'vorhanden'`.
  werkzeug('gelaender', 'Geländer', 'zeichnen', icon(ISLAND_GLYPHEN, 'gelaender'), 'vorhanden', true, { toolId: 'gelaender' }),
  // **P3-Korrektur (PLH-STATUS-2):** dieselbe Nachziehlücke wie Geländer —
  // `design.rampeZeichnen` (Zwei-Punkt-Kette, eigenes Steigungs-Gate im
  // Kernel) ist seit P-B1 vollständig verdrahtet.
  werkzeug('rampe', 'Rampe', 'zeichnen', icon(ISLAND_GLYPHEN, 'rampe'), 'vorhanden', true, { toolId: 'rampe' }),
  // v0.9.2 P-D-Nachzug (Fable, docs/V092-SPEZ.md §P-D): Detail-Marker als
  // Zwei-Punkt-Zeichenwerkzeug (echte ToolId, Klickkette in
  // DesignWorkspace.tsx) — Gesamtstand 33 (ZEICHNEN 14).
  // **P3-Korrektur (PLH-STATUS-2):** dieselbe Nachziehlücke — die Kette war
  // laut eigenem Kommentar hier bereits beim P-D-Nachzug fertig
  // (`design.detailErstellen`), der `status` blieb trotzdem auf
  // `'teilweise'` stehen.
  werkzeug('detail', 'Detail', 'zeichnen', icon(ISLAND_GLYPHEN, 'detail'), 'vorhanden', true, { toolId: 'detail' }),
  // v0.9.4 P-KI (Folgepaket zu 653/661, «Koten-Werkzeuge in Insel und
  // Inspector»): drei NEUE ZEICHNEN-Werkzeuge für die P-KW-Mass-Entitäten
  // (`Hoehenkote`/`Winkelmass`/`Radialmass`, `model/entities.ts`) — anders
  // als `gelaender`/`rampe`/`detail` oben ist die Klickkette hier BEREITS
  // vollständig gebaut (P-PB, `DesignWorkspace.tsx`s `tool==='hoehenkote'|
  // 'winkelmass'|'radialmass'`-Zweige, `ui-zustand.ts`s `ToolId`-Union bereits
  // 16→19 erweitert) — Status darum `vorhanden` statt `teilweise`. `toolId`
  // aktiviert denselben generischen `setTool`-Weg wie jedes andere
  // Zeichenwerkzeug (`aktiviereIslandWerkzeug()`, DesignWorkspace.tsx,
  // unverändert). Gesamtstand 36 (ZEICHNEN 17).
  werkzeug('hoehenkote', 'Höhenkote', 'zeichnen', icon(ISLAND_GLYPHEN, 'hoehenkote'), 'vorhanden', true, {
    toolId: 'hoehenkote',
  }),
  werkzeug('winkelmass', 'Winkelmass', 'zeichnen', icon(ISLAND_GLYPHEN, 'winkelmass'), 'vorhanden', true, {
    toolId: 'winkelmass',
  }),
  werkzeug('radialmass', 'Radialmass', 'zeichnen', icon(ISLAND_GLYPHEN, 'radialmass'), 'vorhanden', true, {
    toolId: 'radialmass',
  }),
  // v0.9.7 P-UI (`docs/V097-SPEZ.md` §2 P-UI): sechs NEUE ZEICHNEN-Werkzeuge —
  // vier bedienen P-2Ds EINE `annotation`-Entität (Text/Linienzug/Kreis/
  // Fläche, `commands/design.ts` `design.annotationTextSetzen`/
  // `-LinienzugSetzen`/`-KreisSetzen`/`-FlaecheSetzen`), zwei schliessen die
  // reine UI-Lücke von Träger («Unterzug», `design.unterzugZeichnen`) und
  // Decke (`design.deckeZeichnen`) — beide Commands sind seit v0.8.x
  // vollständig, nur ohne Insel-Werkzeug. Alle sechs `toolId===id`, echte
  // `ui-zustand.ts`-ToolIds (19→25) — Klickinteraktion in
  // `DesignWorkspace.tsx`s `punktSetzen()`/`mehrpunktAbschliessen()`.
  // Status `vorhanden`: die Klickkette ist in DIESEM Paket bereits fertig
  // gebaut (kein `gelaender`/`rampe`-Zwischenschritt nötig). Gesamtstand
  // jetzt 42 (ZEICHNEN 23).
  werkzeug('notiz', 'Notiz', 'zeichnen', icon(ISLAND_GLYPHEN, 'notiz'), 'vorhanden', true, { toolId: 'notiz' }),
  werkzeug('linienzug', 'Linienzug', 'zeichnen', icon(ISLAND_GLYPHEN, 'linienzug'), 'vorhanden', true, {
    toolId: 'linienzug',
  }),
  werkzeug('kreis', 'Kreis', 'zeichnen', icon(ISLAND_GLYPHEN, 'kreis'), 'vorhanden', true, { toolId: 'kreis' }),
  werkzeug('schraffurflaeche', 'Fläche', 'zeichnen', icon(ISLAND_GLYPHEN, 'schraffurflaeche'), 'vorhanden', true, {
    toolId: 'schraffurflaeche',
  }),
  werkzeug('unterzug', 'Unterzug', 'zeichnen', icon(ISLAND_GLYPHEN, 'unterzug'), 'vorhanden', true, {
    toolId: 'unterzug',
  }),
  werkzeug('decke', 'Decke', 'zeichnen', icon(ISLAND_GLYPHEN, 'decke'), 'vorhanden', true, { toolId: 'decke' }),
  // W-4 (Fable-Bericht 18.08.2026, Fables eigener Gestaltungsentscheid):
  // «Schnitt ist ein Fachwerkzeug ohne Konvention — er bekommt einen Knopf
  // in der ZEICHNEN-Leiste», anders als Undo (dokumentiert unsichtbar, OS-
  // Konvention). Vorher: NUR über die Taste S erreichbar (`kurztasten.ts`),
  // derselbe generische `setTool('schnitt')`-Weg wie jedes andere
  // Zeichenwerkzeug (`aktiviereIslandWerkzeug()`, `DesignWorkspace.tsx`,
  // unverändert — `toolId` genügt). `IconSchnitt` (`werkzeug-icons.tsx`) war
  // bis hierhin ein Icon ohne Katalog-Konsument, s. Datei-Kopfkommentar.
  // `hatPopup:true` (Stufe-2/3-Inhalt: `inhalte/zeichnen.tsx`) — konsistent
  // mit allen 23 übrigen ZEICHNEN-Werkzeugen, keine neue Ausnahme.
  werkzeug('schnitt', 'Schnitt', 'zeichnen', IconSchnitt, 'vorhanden', true, { toolId: 'schnitt' }),
];

/** ANSICHT (6) — §3.2. */
const ANSICHT: readonly IslandWerkzeug[] = [
  // Darstellung/Phase teilen sich die echte Aktion (Projekt-Menü öffnen,
  // `setProjektMenuOffen(true)`) — beide Selects leben im selben,
  // bestehenden Block (`DesignWorkspace.tsx:2764-2784`).
  werkzeug('darstellung', 'Darstellung', 'ansicht', icon(ISLAND_GLYPHEN, 'darstellung'), 'vorhanden', true),
  werkzeug('sonne', 'Sonne', 'ansicht', icon(ISLAND_GLYPHEN, 'sonne'), 'vorhanden', true),
  // P3 (PLH-STATUS-2/PLH-HINWEIS-5): der einzige der acht gemessenen Fälle,
  // der wirklich nur teilweise verdrahtet ist — «Ebenen» liefert heute
  // GENAU einen generischen Textur-Schalter, kein unabhängiges Ein-/
  // Ausblenden einzelner Ebenen (dieselbe Lücke, die `inhalte/ansicht.tsx`s
  // `EbenenStufe3` selbst schon einräumt, `island-ebenen-hinweis-neu`).
  // `status:'teilweise'` bleibt richtig; `hinweis` war bislang schlicht nie
  // gesetzt (PLH-HINWEIS-5s leere Datenquelle) — jetzt gesetzt, tooltip-
  // sichtbar über `IslandShell.tsx`.
  werkzeug('ebenen', 'Ebenen', 'ansicht', icon(ISLAND_GLYPHEN, 'ebenen'), 'teilweise', true, {
    hinweis: 'Nur ein Textur-Schalter — ein echtes Mehrschicht-Sichtbarkeitssystem (einzelne Ebenen unabhängig ein-/ausblenden) gibt es noch nicht.',
  }),
  werkzeug('achsen', 'Achsen', 'ansicht', icon(ISLAND_GLYPHEN, 'achsen'), 'vorhanden', false),
  // P10 v0.8.3 (Matrix-Abnahme): die PD2-Zwischenstand-Hinweise «dort noch
  // nicht verdrahtet» waren seit PD3a toter Text — `inhalte/ansicht.tsx`
  // registriert Trace/Graph mit echten Stufe-2/3-Inhalten, der Fallback-
  // `hinweis` rendert dann nie (IslandShell zeigt ihn nur OHNE Registry-
  // Inhalt). Ersatzlos entfernt statt stehen gelassen: ein Hinweis, der das
  // Gegenteil der gebauten Realität behauptet, ist auch als Leiche falsch.
  werkzeug('trace', 'Trace', 'ansicht', icon(ISLAND_GLYPHEN, 'trace'), 'vorhanden', true),
  werkzeug('graph', 'Graph', 'ansicht', icon(ISLAND_GLYPHEN, 'graph'), 'vorhanden', true),
];

/** PROJEKT (10) — §3.3 + B77-Anhang. */
const PROJEKT: readonly IslandWerkzeug[] = [
  // PE2 (v0.8.4, C-27): der frühere «Panel ist immer aktiv»-Hinweis ist raus —
  // toter Text seit `inhalte/projekt.tsx` das echte, eingebettete
  // `KennzahlenPanel`/`SubmissionsCheckPanel` in Stufe 3 zeigt (IslandShell
  // rendert `hinweis` nur, wenn KEIN Stufe-3-Inhalt registriert ist).
  werkzeug('kennzahlen', 'Kennzahlen', 'projekt', icon(ISLAND_GLYPHEN, 'kennzahlen'), 'vorhanden', true),
  werkzeug('checks', 'Checks', 'projekt', icon(ISLAND_GLYPHEN, 'checks'), 'vorhanden', true),
  werkzeug('varianten', 'Varianten', 'projekt', icon(ISLAND_GLYPHEN, 'varianten'), 'vorhanden', true),
  // P-WERKZEUGLEISTE Teil 2 (O-T8): 'phase' ist ausgezogen — der
  // Phasenwechsel lebt NUR in den Einstellungen (state/phasen-wechsel.ts).
  werkzeug('liste', 'Liste', 'projekt', icon(ISLAND_GLYPHEN, 'liste'), 'vorhanden', true),
  // v0.8.3 E1/E3 (§1/§3.3, §8-6 jetzt entschieden): echter ToolId — der
  // Insel-Katalog-Id bleibt `kommentare` (Plural, Bestandstext), der ToolId
  // dahinter ist `kommentar` (Singular, `ui-zustand.ts`s `ToolId`-Union) —
  // beide Namen sind unabhängig, `werkzeug()`s `extra.toolId` verknüpft sie.
  werkzeug('kommentare', 'Kommentare', 'projekt', icon(ISLAND_GLYPHEN, 'kommentare'), 'vorhanden', true, {
    toolId: 'kommentar',
  }),
  // v0.9.2 P-P2 (`docs/V092-SPEZ.md` §P-P2): additives 7. PROJEKT-Werkzeug —
  // Profil-Manager (Typenkatalog für Stützen-/Unterzugprofile, projektglobal
  // wie Assembly). Kein `toolId`: Profile werden NICHT durch einen
  // Plan-Klickmodus erzeugt (anders als Wand/Stütze/Zone), sondern reine
  // Katalogpflege im Einstellungsfenster (`inhalte/profile.tsx`) — dieselbe
  // Begründung wie bei `kennzahlen`/`liste` oben (kein `ui-zustand.ts`-Tool
  // nötig). Status `vorhanden`: P-P1 (Kernel: Entity+Commands+Referenz-
  // Schutz) ist bereits vollständig gelandet.
  werkzeug('profil', 'Profile', 'projekt', icon(ISLAND_GLYPHEN, 'profil'), 'vorhanden', true),
  // B77 (`docs/AUFTRAG-B77-VIER-PANELS.md`, Abnahme `docs/V0954-SPEZ.md`
  // C-5 bis C-8): vier NEUE PROJEKT-Werkzeuge fuer die vier verwaisten
  // Panels. Gemessener Anlass: `KvPanel`/`MaengelPanel`/`BauablaufPanel`/
  // `DrawPanel` haben je GENAU EINE JSX-Verwendungsstelle, alle in
  // `DesignWorkspace.tsx` unter `DockFlaeche` — und die haengt an
  // `designOberflaeche === 'manuell'`. Laeuft eine Insel, gibt es KEINEN
  // Ort, an dem eines der vier erscheinen koennte; die Store-Flags
  // (`setKvOffen`/`setMaengelOffen`/`setBauablaufOffen`/`setDrawOffen`)
  // kippen, aber niemand liest sie. Diese vier Zeilen sind der fehlende
  // Ort — Stufe-2/3-Inhalte in `inhalte/projekt.tsx` betten die
  // BESTANDS-Panels unveraendert ein (Muster `KennzahlenStufe3`).
  // Kein `toolId`: keines der vier wird ueber einen Plan-Klickmodus
  // erzeugt — dieselbe Begruendung wie bei `kennzahlen`/`liste`/`profil`.
  // `aktiviereIslandWerkzeug()` (`DesignWorkspace.tsx`) braucht dafuer
  // KEINEN neuen Fall: sein `default:`-Zweig laesst genau solche
  // Werkzeuge bewusst durch, ihre Wirkung lebt im Stufe-2/3-Inhalt.
  //
  // **KosmoDraw kommt hier als PROJEKT-Insel-Blatt, NICHT als
  // Stationen-Orb-Eintrag** — der Owner-Entscheid vom 06.08.2026
  // (P-WERKZEUGORDNUNG, `e2e/island-ui.spec.ts:472-478` «modellbaum und
  // spez sind keine tools») haelt die Abwesenheit von
  // `stationen-orb-eintrag-draw` fest und bleibt unberuehrt:
  // `StationenOrb.tsx` speist sich aus `shell/orbit-werkzeuge.ts`, nicht
  // aus diesem Katalog. Gesamtstand jetzt 46 (PROJEKT 10).
  werkzeug('kv', 'Kosten', 'projekt', icon(ISLAND_GLYPHEN, 'kv'), 'vorhanden', true),
  werkzeug('maengel', 'Mängel', 'projekt', icon(ISLAND_GLYPHEN, 'maengel'), 'vorhanden', true),
  werkzeug('bauablauf', 'Bauablauf', 'projekt', icon(ISLAND_GLYPHEN, 'bauablauf'), 'vorhanden', true),
  werkzeug('draw', 'KosmoDraw', 'projekt', icon(ISLAND_GLYPHEN, 'draw'), 'vorhanden', true),
];

/** AUSTAUSCH (6) — §3.4. */
// PE2 (v0.8.4, C-27): der frühere `ANDERE_STATION_HINWEIS` («Weg offen,
// §8-4») ist raus — §8-4 ist seit PD3c entschieden UND real verdrahtet
// (`docs/ISLAND-UI-SPEZ.md` §8 Punkt 4 Nachtrag: `registriereStationsWeg`,
// echte Navigation über `ZurStationKnopf`), der Hinweis behauptete das
// Gegenteil der gebauten Realität UND war zusätzlich toter Text (Stufe 3
// ist für alle drei registriert, `inhalte/austausch.tsx`) — dieselbe
// «Leiche», die P10 (v0.8.3) schon bei Trace/Graph fand und entfernte.
const AUSTAUSCH: readonly IslandWerkzeug[] = [
  werkzeug('export', 'Export', 'austausch', icon(ISLAND_GLYPHEN, 'export'), 'vorhanden', true),
  werkzeug('import', 'Import', 'austausch', icon(ISLAND_GLYPHEN, 'import'), 'vorhanden', true),
  // **P3-Korrektur (PLH-STATUS-2):** alle drei standen auf `'teilweise'`,
  // obwohl der PE2-Kommentar oben (v0.8.4) selbst schon festhält, dass sie
  // «längst echten Registry-Inhalt» tragen — `test/island-katalog-pd2.
  // test.ts:119-122` hatte den Verdacht vorweggenommen. Gemessen: alle drei
  // zeigen echte Laufzeitdaten (`useVisRuntime`/`useProject`/`syncActive()`,
  // `inhalte/austausch.tsx`) UND einen echten Weiterweg (`ZurStationKnopf`
  // zu KosmoVis/KosmoPublish; Sync hat bewusst kein Insel-Ziel, s. dortigen
  // Kommentar) — dieselbe Schwelle wie jedes andere Cross-Station-Werkzeug
  // (z. B. `darstellung`). `status:'vorhanden'`.
  werkzeug('rendern', 'Rendern', 'austausch', icon(ISLAND_GLYPHEN, 'rendern'), 'vorhanden', true),
  werkzeug('blaetter', 'Blätter', 'austausch', icon(ISLAND_GLYPHEN, 'blaetter'), 'vorhanden', true),
  werkzeug('sync', 'Sync', 'austausch', icon(ISLAND_GLYPHEN, 'sync'), 'vorhanden', true),
  // **P3-Korrektur (PLH-STATUS-2):** stand auf `'neu'`, obwohl
  // `aktiviereIslandWerkzeug()`s `case 'manuell'` unbedingt und vollständig
  // `setDesignOberflaeche('manuell')` ausführt — dieselbe Mechanik
  // (toolId-los, `hatPopup:false`, ein Store-Flip) wie `achsen` oben, das
  // längst `status:'vorhanden'` trägt. Kein Feature fehlt hier; `status:'neu'`
  // beschrieb nie einen echten Zustand.
  werkzeug('manuell', 'Manuell', 'austausch', icon(ISLAND_GLYPHEN, 'manuell'), 'vorhanden', false),
];

/** Gesamtkatalog, 46/46 (ursprünglich 29/29, s. Kopfkommentar für die
 *  additiven P-B2-/P-P2-/P-D-/P-KI-/P-UI-/B77-Ergänzungen), Reihenfolge exakt §3.1→§3.4 + Anhänge. */
export const WERKZEUG_KATALOG: readonly IslandWerkzeug[] = [...ZEICHNEN, ...ANSICHT, ...PROJEKT, ...AUSTAUSCH];

export function werkzeugeFuerIsland(island: IslandId): readonly IslandWerkzeug[] {
  return WERKZEUG_KATALOG.filter((w) => w.island === island);
}

/**
 * PC0 v0.8.4 (`docs/V084-SPEZ.md` E1): Konfig-Objekt je Insel — die
 * generische Schnittstelle, über die JEDE Station die IslandShell bespielt.
 * Die fünf bisher hartkodierten design-Records (IslandId-Union,
 * ISLAND_REIHENFOLGE/-LABEL/-ORIENTIERUNG + ISLAND_RAND_KLASSE in
 * IslandShell.tsx) bleiben als design-Wahrheit bestehen und werden hier nur
 * EINMAL in die Konfig-Form gegossen — Verhalten byte-gleich, kein
 * testid/keine Klasse ändert sich (Sanktion 1 der V084-SPEZ).
 */
export interface InselKonfig {
  readonly id: string;
  readonly label: string;
  readonly orientierung: IslandOrientierung;
  /** CSS-Randklasse (`isl-rand-links|-oben|-rechts|-unten`) — Position an der Bühne. */
  readonly randKlasse: string;
  readonly werkzeuge: readonly IslandWerkzeug[];
  /**
   * P-TRENNUNG (v0.9.35, O-T29 «sammlungsisland oben dauerhaft einblenden
   * als grosse fixe pille»): haelt die Insel DAUERHAFT auf dieser Stufe —
   * sie startet dort, und Ruhe/Rueckklapp fallen nie darunter (Popups
   * klappen auf die fixe Stufe zurueck statt auf die Pille). Additiv und
   * optional: ohne das Feld ist das Verhalten byte-gleich zu vorher —
   * die Shell ist stationsuebergreifend geteilt.
   */
  readonly fixeStufe?: 'leiste';
  /**
   * B140 (11.09.2026, Owner-Entscheid «Leiste einklappbar»): der Kopf dieser
   * Leiste ist ein Schalter, der sie weglegt, ohne das Werkzeug zu schliessen.
   *
   * **Ausdrueckliche Zustimmung statt stiller Voreinstellung, und das ist
   * gemessen begruendet.** Gebaut war es zuerst fuer JEDE Insel ohne feste
   * Stufe — dasselbe Problem, derselbe Mechanismus. Der
   * Ueberdeckungs-Waechter hat das widerlegt: in KosmoVis steht die
   * STIMMUNG-Insel bei offenem Kosmo-Panel ausweichend oben rechts
   * (`vis-island.css`, ROADMAP-1000-Nachlauf), und dort ist der Leistenkopf
   * **nicht erreichbar** — gemessen 32x32 Bildpunkte unter dem
   * Einstellungs-Kreis, `elementFromPoint` auf der Kopfmitte trifft den
   * Kreis. 12 unentschuldigte Funde (vier Fenstergroessen x drei Zustaende).
   *
   * Dass der Kopf dort schon vorher verdeckt war, hat niemand gemerkt: eine
   * BESCHRIFTUNG klickt keiner, und der Waechter fragt nach Bedienelementen.
   * Ein freier Platz daneben gibt es nicht — die Luecke zwischen der
   * Kopf-Zweitgruppe und dem Kreis ist an ALLEN vier Groessen **11 px**, die
   * Leiste braucht 82. Das Ausweichen selbst neu zu legen ist eine Frage an
   * KosmoVis, nicht an einen Einklappschalter.
   *
   * Darum traegt das Feld nur, wer geprueft ist. Heute sind das die vier
   * design-Inseln; wer es ergaenzt, faehrt
   * `e2e/w5-1-insel-ueberdeckung.spec.ts` und zeigt 0 neue Funde.
   */
  readonly einklappbar?: boolean;
}

/** Rand-Position je design-Island (§1/§2) — bis PC0 in `IslandShell.tsx:49-54`. */
const DESIGN_RAND_KLASSE: Readonly<Record<IslandId, string>> = {
  zeichnen: 'isl-rand-links',
  ansicht: 'isl-rand-oben',
  projekt: 'isl-rand-rechts',
  austausch: 'isl-rand-unten',
};

/** Die vier design-Inseln in Bühnenordnung — Default der `IslandBuehne`. */
export const DESIGN_INSELN: readonly InselKonfig[] = ISLAND_REIHENFOLGE.map((id) => ({
  id,
  label: ISLAND_LABEL[id],
  orientierung: ISLAND_ORIENTIERUNG[id],
  randKlasse: DESIGN_RAND_KLASSE[id],
  werkzeuge: werkzeugeFuerIsland(id),
  // B140: der Zeichentisch ist die Station, fuer die der Owner entschieden
  // hat, und die einzige, deren Leistenkopf in JEDEM gefahrenen Zustand
  // erreichbar gemessen ist (`e2e/w5-1-insel-ueberdeckung.spec.ts`, 40 Faelle
  // ueber vier Fenstergroessen). Begruendung am Feld oben.
  einklappbar: true,
}));

export function designInselKonfig(id: IslandId): InselKonfig {
  const konfig = DESIGN_INSELN.find((k) => k.id === id);
  if (!konfig) throw new Error(`Unbekannte design-Insel: ${id}`);
  return konfig;
}
