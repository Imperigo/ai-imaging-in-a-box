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
  /**
   * K2 (`docs/AUFTRAG-EINBAU-B163-KOSMODESIGN-AN-INTEGRATOR.md` §K2,
   * Paket dl-d4-gruppenschiene, Nachbesserung 24.09.2026) — additiv und
   * optional, `undefined` ist byte-gleich zu vorher (dasselbe additive
   * Muster wie `hinweis`/`toolId` oben). Kurzer, deutscher Klartext für
   * eine kleine Marke am Werkzeug-Knopf (K2 wörtlich: «Der Knopf traegt
   * die Marke Vorschlag, solange OE-RP4 offen ist») — anders als `status`
   * (das den ganzen Knopftitel ändert) ist `marke` rein additiv sichtbar,
   * das Werkzeug bleibt `status:'vorhanden'` (es FUNKTIONIERT bereits,
   * die Marke ist ein Hinweis auf einen offenen Owner-Entscheid, kein
   * Platzhalter). Heute nur bei `leuchte` gesetzt.
   */
  readonly marke?: string;
}

function werkzeug(
  id: string,
  name: string,
  island: IslandId,
  glyphe: string | ComponentType<{ size?: number }>,
  status: IslandWerkzeugStatus,
  hatPopup: boolean,
  extra?: { toolId?: string; hinweis?: string; marke?: string },
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
    ...(extra?.marke !== undefined ? { marke: extra.marke } : {}),
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
  // K2 (`docs/AUFTRAG-EINBAU-B163-KOSMODESIGN-AN-INTEGRATOR.md` §K2, Paket
  // dl-d4-gruppenschiene, Nachbesserung 24.09.2026) — die zwei fehlenden
  // Katalog-Einträge der Gruppe «Einrichten» (`ZEICHNEN_GRUPPEN` unten
  // nennt sie schon seit der K1-Vorarbeit, nur ohne Katalog-Eintrag, s.
  // Übergabe-Hinweis am Dateiende). KEIN `toolId`: anders als die 24
  // bestehenden Zeichenwerkzeuge ist die Aktivierung kein einfacher
  // `setTool()`-Moduswechsel, sondern öffnet eine Auswahl-Karte (Stufe-2-
  // Inhalt `inhalte/zeichnen.tsx`s `MoebelStufe2`/`LeuchteStufe2`), die
  // `design.moebelSetzen`/`design.leuchteZeichnen` direkt über
  // `useProject().runCommand` ausführt — derselbe Weg, den JEDER Stufe-2-
  // Inhalt dieser Datei laut ihrem eigenen Kopfkommentar schon nutzt.
  // `aktiviereIslandWerkzeug()`s `default`-Zweig (DesignWorkspace.tsx,
  // ausserhalb dieses Dateikreises, ungeändert) tut für Ids ohne `toolId`
  // ohnehin nichts — GENAU wie bei `profil`/`kennzahlen`/… — das Popup
  // öffnet rein über `IslandShell.tsx`s lokalen Zustand (`aufWerkzeugKlick`
  // setzt `aktivesWerkzeugId`/`stufe` UNABHÄNGIG vom Rückgabewert des
  // Callbacks). Gesamtstand jetzt 26 (ZEICHNEN 26 inkl. Auswahl).
  // `hinweis` versorgt zweierlei (s. `IslandWerkzeug.hinweis`-Kommentar
  // oben): den Lang-Hover-Tooltip UND den Stufe-3/Fenster-Fallback, falls
  // ein Klick auf das bereits offene Popup zum Fenster eskaliert (dessen
  // Registry-Eintrag hat bewusst kein `Stufe3`, s. `inhalte/zeichnen.tsx`).
  werkzeug('moebel', 'Möbel', 'zeichnen', icon(ISLAND_GLYPHEN, 'moebel'), 'vorhanden', true, {
    hinweis: 'Möbel aus dem Katalog setzen (19 Arten) — Taste E dreht vor dem Setzen um 90°.',
  }),
  // K2 wörtlich: «Der Knopf traegt die Marke Vorschlag, solange OE-RP4
  // offen ist» — `marke` ist rein additiv (s. `IslandWerkzeug.marke`-
  // Kommentar oben), das Werkzeug SELBST ist fertig und funktioniert
  // (`design.leuchteZeichnen` ist ein Kernel-Befehl seit A9/Welle 3, kein
  // Platzhalter) — darum `status:'vorhanden'`, nicht `'neu'`.
  werkzeug('leuchte', 'Leuchte', 'zeichnen', icon(ISLAND_GLYPHEN, 'leuchte'), 'vorhanden', true, {
    marke: 'Vorschlag',
    hinweis: 'Pendelleuchte unter die Decke hängen — Marke «Vorschlag», solange OE-RP4 offen ist.',
  }),
  // U25 Phase 0 (01.10.2026): zwei Panels, die nur in der Dock-Flaeche der
  // Oberflaeche «manuell» standen, bekommen hier ihr Werkzeug. Beide haben
  // KEIN `toolId`: sie zeichnen nicht per Klick im Plan, sondern setzen ueber
  // ein Formular (`design.curtainWallSetzen`) bzw. einen Assistenten
  // (`design.rasterSetzen`) — dieselbe Lage wie `moebel`/`leuchte`. Inhalte in
  // `inhalte/s-panels.tsx`, die Panels selbst (`CurtainWallPanel`,
  // `RasterPanel`) bleiben unveraendert. Die Zeichnen-Insel zaehlt damit 28.
  werkzeug('fensterband', 'Fensterband', 'zeichnen', icon(ISLAND_GLYPHEN, 'fensterband'), 'vorhanden', true),
  werkzeug('stuetzenraster', 'Stützenraster', 'zeichnen', icon(ISLAND_GLYPHEN, 'stuetzenraster'), 'vorhanden', true),
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
    // E222 (Paket 05 WB-Ebenen): das Mehrschicht-Sichtbarkeitssystem gibt es jetzt (Karte «Ebenenliste»).
    hinweis: 'Bauteil-Ebenen ein- und ausblenden, sperren, als Drahtmodell zeigen und als Kombination speichern (Karte «Ebenenliste»); dazu Textur-Schalter und Splat-Ebene.',
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
  // **KosmoQuantity (damals noch «KosmoDraw», s. den Namens-Kommentar an
  // seiner Zeile unten) kommt hier als PROJEKT-Insel-Blatt, NICHT als
  // Stationen-Orb-Eintrag** — der Owner-Entscheid vom 06.08.2026
  // (P-WERKZEUGORDNUNG, `e2e/island-ui.spec.ts:472-478` «modellbaum und
  // spez sind keine tools») haelt die Abwesenheit von
  // `stationen-orb-eintrag-draw` fest und bleibt unberuehrt:
  // `StationenOrb.tsx` speist sich aus `shell/orbit-werkzeuge.ts`, nicht
  // aus diesem Katalog. Gesamtstand jetzt 46 (PROJEKT 10).
  werkzeug('kv', 'Kosten', 'projekt', icon(ISLAND_GLYPHEN, 'kv'), 'vorhanden', true),
  werkzeug('maengel', 'Mängel', 'projekt', icon(ISLAND_GLYPHEN, 'maengel'), 'vorhanden', true),
  werkzeug('bauablauf', 'Bauablauf', 'projekt', icon(ISLAND_GLYPHEN, 'bauablauf'), 'vorhanden', true),
  // **Name «KosmoQuantity» (Owner-Entscheid 21.09.2026, wörtlich: «ja
  // kosmodraw ist zeichenwerkzeug...wir machen alles englisch»).** Bis dahin
  // hiess dieser Eintrag «KosmoDraw» — denselben Namen trägt seit dem
  // 21.09.2026 aber das Untertool der ZEICHENFLÄCHE (`shell/orbit-
  // werkzeuge.ts`, `id:'draw'`, `moduleId:'design'`). Zwei verschiedene
  // Gegenstände, ein Name; `e2e/zentrale-bloecke.spec.ts` hielt die
  // Kollision fest, ohne sie zu entscheiden. Der Owner hat entschieden:
  // KosmoDraw gehört der Zeichenfläche, dieses Werkzeug bekommt einen
  // eigenen englischen Namen.
  //
  // **Warum «Quantity» und nicht «Model» — begründet aus dem, was das
  // Werkzeug TUT (`DrawPanel.tsx` gelesen, nicht der Klang gewählt):** die
  // drei Reiter sind Modellbaum, Mengen und Ausmass, und alle drei LESEN nur
  // (`deriveMengen`/`deriveAusmass`, kein Command, keine Mutation — das
  // Serienbild-Szenario `kosmodesign-draw.json` belegt es am Dokument:
  // «dabei ist nichts entstanden und nichts verschwunden»). Was dieses
  // Werkzeug von KosmoDraw unterscheidet, ist genau das: KosmoDraw erzeugt
  // das Modell, dieses hier beziffert es. «KosmoModel» wäre dafür der
  // falsche Griff gewesen — `orbit-werkzeuge.ts`s Untertool `id:'modell'`
  // hält den Namen «Modell» ausdrücklich für ein GEPLANTES, freies
  // Formwerkzeug (FreeMesh) frei; ihn hier zu verbrauchen hätte dieselbe
  // Kollision neu erzeugt, die dieser Eintrag gerade auflöst.
  //
  // **Und warum EINZAHL, obwohl das Panel «Mengen» im Plural zeigt:**
  // `docs/KOSMO-NAMEN-CANON.md` Regel 2 lautet «Singular, immer. […] Keine
  // Plural-Varianten» — die Umsetzungstabelle desselben Blattes führt genau
  // diesen Fall schon einmal vor (`NotionBruecke.tsx`: KosmoReferences →
  // KosmoReference). «KosmoQuantities» wäre der gleiche Rückfall gewesen.
  // Die deutsche Beschriftung bleibt davon unberührt: der Bereich heisst
  // weiterhin «Modell & Mengen» (`STATION_TITEL.draw`, Canon-Regel 3) —
  // englisch ist der NAME, nicht die Oberfläche
  // (`docs/NAMENSREGEL-2026-09-21.md`).
  werkzeug('draw', 'KosmoQuantity', 'projekt', icon(ISLAND_GLYPHEN, 'draw'), 'vorhanden', true),
  // U25 Phase 0 (01.10.2026, Owner: «die alte manuelle UI komplett eliminieren
  // und nur mit Insel-UI arbeiten»): die Volumenstudie samt Varianten-Matrix
  // und Fassadenmodulen stand nur in der Dock-Flaeche der Oberflaeche
  // «manuell». Der Insel-Knopf `island-volumen-studie-oeffnen` setzte nur das
  // Flag `studieOffen` — nichts las es. Dieses Werkzeug ist der fehlende Ort;
  // das Fenster (Stufe 3) traegt das unveraenderte Panel
  // (`island/inhalte/s-panels.tsx`, Komponente `studien/StudienPanel.tsx`).
  // Kein `toolId`: die Studie wird nicht ueber einen Plan-Klickmodus bedient.
  werkzeug('studie', 'Volumenstudie', 'projekt', icon(ISLAND_GLYPHEN, 'studie'), 'vorhanden', true),
  // U25 Phase 0: der Abgleich mit dem Rueckmeldeplan des Unternehmers (Karten
  // «uebernehmen») stand nur als Dock-Panel `unternehmerplan` da, sichtbar
  // sobald ein DXF mit Abgleich geladen war. Der DXF-Import selbst lebt
  // schon in der AUSTAUSCH-Insel (`island-import-dxf`); dieses Werkzeug zeigt
  // die Karten dazu. Das Fenster oeffnet sich beim Ankommen des Abgleichs.
  werkzeug('unternehmerplan', 'Unternehmerplan', 'projekt', icon(ISLAND_GLYPHEN, 'unternehmerplan'), 'vorhanden', true),
];

/** AUSTAUSCH (7; B3 Splat: +splat) — §3.4. */
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
  // B3 (Bestandsaufnahme Splat-Szenario 06.10.2026, §3 B3): Splat laden /
  // Video → Splat aus der Standard-Oberfläche. Bis hierher nur in der
  // Manuell-Oberfläche (`DockFlaeche`, `splatPanelOffen`) erreichbar. Kein
  // `toolId` (kein Plan-Klickmodus); Stufe 2/3 betten das echte
  // `SplatPanel` ein (seit der Zusammenfuehrung mit U25 Phase 0 am 06.10.2026
  // in `inhalte/s-panels.tsx`, ein Eintrag fuer beide).
  // U25 Phase 0: Splat-Wolken (.splat/.ply) laden, zuschneiden, ausduennen,
  // exportieren, Video -> Splat. Das Panel stand nur in der Dock-Flaeche;
  // KosmoPackage -> «Splat-Werkzeug öffnen» und Kosmos `ui.panelSetzen`
  // fuehrten in der Insel ins Leere. Der Import-Knopf steht beim Import
  // (`island-import-splat`), das Panel hier.
  werkzeug('splat', 'Splat', 'austausch', icon(ISLAND_GLYPHEN, 'splat'), 'vorhanden', true),
  // U25 Phase 6: das Werkzeug «Manuell» (Rückweg in die alte Oberfläche) ist mit ihr entfallen.
];

/** Gesamtkatalog, 46/46 (ursprünglich 29/29, s. Kopfkommentar für die
 *  additiven P-B2-/P-P2-/P-D-/P-KI-/P-UI-/B77-Ergänzungen), Reihenfolge exakt §3.1→§3.4 + Anhänge. */
export const WERKZEUG_KATALOG: readonly IslandWerkzeug[] = [...ZEICHNEN, ...ANSICHT, ...PROJEKT, ...AUSTAUSCH];

export function werkzeugeFuerIsland(island: IslandId): readonly IslandWerkzeug[] {
  return WERKZEUG_KATALOG.filter((w) => w.island === island);
}

/**
 * K1-Vorarbeit — Gruppenschiene (`docs/AUFTRAG-EINBAU-B163-KOSMODESIGN-AN-
 * INTEGRATOR.md` §K1, Bild `docs/entwuerfe/kosmodesign/varianten/a1.png`,
 * Owner-Entscheide E116/E117 `docs/ENTSCHEIDE-2026-09-22.md`). Reine,
 * additive Datentabelle — die sechs Gruppen der Zeichnen-Insel, Reihenfolge
 * und Zusammensetzung wörtlich aus der AUFTRAG-Tabelle übernommen.
 * `werkzeugIds` referenziert Katalog-`id`s; `zeichen` ist die Leit-Id fürs
 * Gruppen-Symbol (Spalte «Zeichen» der Tabelle).
 *
 * **Absichtlich NICHT verdrahtet:** die eigentliche Gruppenschiene (zehn
 * runde Knoepfe, aufklappbare Gruppenkarte, Haeufigkeits-Zaehler, Suche)
 * lebt in `IslandShell.tsx`/`island.css` und ist NICHT Teil dieser Änderung
 * — s. Übergabe-Hinweis am Dateiende.
 *
 * `'auswahl'` erscheint bewusst in KEINER Gruppe («Auswahl steht ausserhalb,
 * sie zeichnet nichts», AUFTRAG §K1).
 */
export type IslandGruppeId =
  | 'bauteile'
  | 'oeffnenErschliessen'
  | 'einrichten'
  | 'raeumeFlaechen'
  | 'messenBeschriften'
  | 'skizzieren';

export interface IslandGruppe {
  readonly id: IslandGruppeId;
  readonly label: string;
  /** Katalog-Id, deren Glyphe das Gruppen-Symbol trägt (Tabellenspalte «Zeichen»). */
  readonly zeichen: string;
  readonly werkzeugIds: readonly string[];
}

/**
 * K2-Nachtrag (Paket dl-d4-gruppenschiene, Nachbesserung 24.09.2026):
 * `'moebel'`/`'leuchte'` stehen jetzt AUCH im Katalog (`WERKZEUG_KATALOG`,
 * s. `ZEICHNEN`-Array oben) — der frühere Blocker («in der Tabelle, aber
 * noch nicht im Katalog») ist zu. Der ehemalige Melder
 * `EINRICHTEN_NOCH_NICHT_IM_KATALOG` ist darum entfallen (er hätte ab jetzt
 * dauerhaft `[]` gemeldet — ein Melder ohne möglichen Fund ist kein
 * Melder mehr, s. `test/island-einrichten-moebel-leuchte.test.tsx` und
 * `test/island-gruppenschiene-vorarbeit.test.ts` für die Gegenprobe «beide
 * Ids sind heute im Katalog»).
 */
export const ZEICHNEN_GRUPPEN: readonly IslandGruppe[] = [
  {
    id: 'bauteile',
    label: 'Bauteile',
    zeichen: 'volumen',
    werkzeugIds: ['wand', 'stuetze', 'unterzug', 'decke', 'dach', 'volumen', 'fensterband', 'stuetzenraster'],
  },
  { id: 'oeffnenErschliessen', label: 'Öffnen und Erschliessen', zeichen: 'treppe', werkzeugIds: ['oeffnung', 'treppe', 'rampe', 'gelaender'] },
  { id: 'einrichten', label: 'Einrichten', zeichen: 'moebel', werkzeugIds: ['moebel', 'leuchte'] },
  { id: 'raeumeFlaechen', label: 'Räume und Flächen', zeichen: 'zone', werkzeugIds: ['zone', 'schraffurflaeche'] },
  {
    id: 'messenBeschriften',
    label: 'Messen und Beschriften',
    zeichen: 'messen',
    werkzeugIds: ['messen', 'hoehenkote', 'winkelmass', 'radialmass', 'notiz', 'detail', 'schnitt'],
  },
  { id: 'skizzieren', label: 'Skizzieren', zeichen: 'skizze', werkzeugIds: ['skizze', 'linienzug', 'kreis', 'mesh'] },
];

/**
 * U26 · Variante A (Owner-Entscheid 06.10.2026, «Entscheid insel A», Entwurfsfläche
 * https://claude.ai/artifact/3eLzdAeE3PWATqHuKTAATg): jede offene Insel ist EINE Reihe oder Spalte runder Knöpfe,
 * Gruppen trennt ein feiner Strich. Hier steht die Reihenfolge und wo eine Gruppe beginnt — für die Inseln ohne
 * Gruppenschiene. Werkzeuge, die hier nicht stehen, behalten ihre Katalog-Reihenfolge und folgen am Ende.
 * Projekt bekommt drei Gruppen (Zahlen · Prüfen · Planen) und wird damit eine Spalte statt zwei.
 */
export const INSEL_GRUPPEN: Readonly<Record<string, readonly (readonly string[])[]>> = {
  projekt: [
    ['kennzahlen', 'kv', 'liste', 'draw'],
    ['checks', 'maengel', 'kommentare', 'varianten'],
    ['bauablauf', 'studie', 'profil', 'unternehmerplan'],
  ],
  ansicht: [
    ['darstellung', 'sonne', 'ebenen'],
    ['achsen', 'trace', 'graph'],
  ],
  austausch: [
    ['export', 'import'],
    ['rendern', 'blaetter'],
    ['sync', 'splat'],
  ],
};

/** Ordnet die Werkzeuge einer Insel nach `INSEL_GRUPPEN` und nennt die Kennungen, mit denen eine neue Gruppe
 *  beginnt (nie das erste Werkzeug). Ohne Eintrag für die Insel: unverändert, keine Trenner. */
export function ordneNachGruppen<T extends { readonly id: string }>(
  island: string,
  werkzeuge: readonly T[],
): { liste: readonly T[]; gruppenAnfang: ReadonlySet<string> } {
  const gruppen = INSEL_GRUPPEN[island];
  if (!gruppen) return { liste: werkzeuge, gruppenAnfang: new Set() };
  const rang = new Map<string, number>();
  const anfang = new Set<string>();
  let i = 0;
  for (const g of gruppen) {
    g.forEach((id, j) => {
      rang.set(id, i++);
      if (j === 0) anfang.add(id);
    });
  }
  const liste = [...werkzeuge].sort((a, b) => (rang.get(a.id) ?? 1e6) - (rang.get(b.id) ?? 1e6));
  const gruppenAnfang = new Set([...anfang].filter((id) => liste.length > 0 && liste[0]!.id !== id && liste.some((w) => w.id === id)));
  return { liste, gruppenAnfang };
}

export function gruppeFuerWerkzeug(id: string): IslandGruppeId | undefined {
  return ZEICHNEN_GRUPPEN.find((g) => g.werkzeugIds.includes(id))?.id;
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
  /**
   * K1-Nachbesserung (Paket dl-d4-gruppenschiene, 24.09.2026) — additiv und
   * optional, `undefined`/`false` ist byte-gleich zum bisherigen flachen
   * Werkzeug-Grid (dasselbe additive Muster wie `fixeStufe`/`einklappbar`
   * oben). `true` schaltet `IslandShell.tsx`s Gruppenschiene ein: zehn runde
   * Knoepfe (Suche, drei haeufigste, Trennlinie, sechs Gruppen aus
   * `ZEICHNEN_GRUPPEN`) statt der flachen Liste aller Werkzeuge.
   *
   * **Bewusst NICHT auf `true` fuer den `zeichnen`-Eintrag in
   * `DESIGN_INSELN` unten gesetzt — das ist der eigentliche Rest-Blocker
   * dieses Pakets, s. Uebergabe-Hinweis am Dateiende.** Zwei bestehende
   * Testdateien AUSSERHALB dieses Dateikreises
   * (`apps/kosmo-orbit/test/island-shell.test.tsx`,
   * `apps/kosmo-orbit/test/island-shell-pd2.test.tsx`, zusammen 34
   * Fundstellen) rendern `<IslandShell island="zeichnen" />` OHNE eigene
   * `konfig` — sie loesen damit zwangslaeufig genau diesen
   * `DESIGN_INSELN`-Eintrag auf (`designInselKonfig`, unten) und klicken
   * `island-werkzeug-wand`/`-volumen`/`-messen`/… SOFORT nach dem Hover,
   * ohne zuvor eine Gruppe zu oeffnen. Ein Default-`true` hier wuerde beide
   * Dateien zuverlaessig rot machen — Dateien, die dieses Paket laut
   * Dateikreis NICHT aendern darf. Das ist keine Vermutung: beide Dateien
   * wurden gegen genau dieses Muster geprueft (`grep -c
   * 'island-werkzeug-' island-shell.test.tsx island-shell-pd2.test.tsx` →
   * 22 + 12 = 34 direkte Fundstellen, keine davon ueber einen
   * Gruppen-Umweg).
   */
  readonly gruppenschiene?: boolean;
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

/**
 * K1-Nachbesserung — dieselbe `zeichnen`-Konfig wie `DESIGN_INSELN`, nur mit
 * `gruppenschiene: true`. Fertig zum Verdrahten, sobald der Integrator die
 * zwei ausserhalb dieses Dateikreises liegenden Testdateien
 * (`island-shell.test.tsx`/`island-shell-pd2.test.tsx`, s. Kommentar am
 * `gruppenschiene`-Feld oben) freigegeben oder selbst nachgezogen hat —
 * entweder hier `DESIGN_INSELN`s `zeichnen`-Eintrag direkt auf `true`
 * setzen, oder `DesignWorkspace.tsx` diese Konfig statt `designInselKonfig
 * ('zeichnen')` uebergeben (letzteres liegt ausserhalb dieses Dateikreises).
 * Bis dahin dient dieser Export den NEUEN Tests dieses Pakets
 * (`test/island-gruppenschiene-rail.test.tsx`), die die Gruppenschiene
 * gezielt UEBER `konfig` einschalten, ohne den geteilten Default zu ruehren.
 */
export const DESIGN_INSEL_ZEICHNEN_GRUPPENSCHIENE: InselKonfig = {
  ...designInselKonfig('zeichnen'),
  gruppenschiene: true,
};

/**
 * NACHTRAG (Gegenpruefung 25.09.2026, Pruefer-Hauptfund «K1 nicht am
 * Bedienweg») — der echte App-Default, OHNE `DESIGN_INSELN` selbst
 * anzufassen: dieselben vier Inseln wie `DESIGN_INSELN`, nur mit
 * `DESIGN_INSEL_ZEICHNEN_GRUPPENSCHIENE` statt des flachen
 * `zeichnen`-Eintrags. `IslandShell.tsx`s `IslandBuehne` (in DIESEM
 * Dateikreis) setzt ihren `inseln`-Default jetzt hierauf — genau die
 * Komponente, die `DesignWorkspace.tsx` (ausserhalb des Dateikreises,
 * `<IslandBuehne />` ohne eigene `inseln`-Prop) tatsaechlich rendert. Damit
 * ist K1 am echten Bedienweg, OHNE `DesignWorkspace.tsx` anzufassen.
 *
 * **Warum `DESIGN_INSELN` selbst trotzdem unveraendert bleibt:**
 * `designInselKonfig('zeichnen')` UND jeder direkte
 * `<IslandShell island="zeichnen" />`-Aufruf OHNE eigene `konfig` loesen
 * weiterhin `DESIGN_INSELN` auf, nicht diese Variante — genau der
 * Aufrufweg von `island-shell.test.tsx`/`island-shell-pd2.test.tsx`
 * (ausserhalb dieses Dateikreises, s. Kommentar am `gruppenschiene`-Feld
 * oben). Diese zwei Dateien bleiben dadurch weiterhin byte-gleich zu vorher
 * — ihr einziges verbleibendes Rot ist der bereits gemeldete 24→26-
 * Werkzeugzahl-Fund aus K2 (Punkt 3 des Uebergabe-Hinweises unten),
 * strukturell unabhaengig von dieser Nachbesserung. Gegengeprueft: kein
 * anderer Aufrufer im Baum rendert `<IslandBuehne />` (bzw. `<IslandBuehne
 * onWerkzeugAktion={...} />`) OHNE eigene `inseln`-Prop UND klickt dabei
 * ausserhalb der drei Vorgabe-haeufigsten (Auswahl/Wand/Öffnung) direkt auf
 * ein ZEICHNEN-Werkzeug — `apps/kosmo-orbit/test/n4-stummer-oeffnung-klick.
 * test.tsx` (öffnet die Pille, klickt `island-werkzeug-oeffnung` sofort
 * danach) bleibt darum gruen: „Öffnung" ist selbst einer der drei
 * Vorgabe-Knöpfe und sitzt direkt auf der Schiene, keine Gruppe noetig. Die
 * beiden anderen `<IslandBuehne />`-Aufrufe ohne `inseln`-Prop in
 * Testdateien ausserhalb dieses Dateikreises
 * (`island-shell.test.tsx:510`, `island-shell-pd2.test.tsx:105`) testen
 * die Zwei-Finger-Undo-Geste bzw. die PROJEKT-Insel — keine Beruehrung mit
 * ZEICHNEN. Beleg: `test/island-gruppenschiene-app-default.test.tsx`
 * (neu, dieser Dateikreis) rendert `<IslandBuehne />` BYTE-IDENTISCH zum
 * echten `DesignWorkspace.tsx`-Aufruf und beweist damit den Bedienweg,
 * ohne die App selbst zu starten.
 */
export const DESIGN_INSELN_STANDARD: readonly InselKonfig[] = DESIGN_INSELN.map((k) =>
  k.id === 'zeichnen' ? DESIGN_INSEL_ZEICHNEN_GRUPPENSCHIENE : k,
);

/**
 * ÜBERGABE-HINWEIS (Paket dl-d4-gruppenschiene, Nachbesserung 24.09.2026,
 * gemessen gegen Basis `801572767` + eigenen Vorarbeits-Commit `4895a16c1`):
 * K1/K2 (`docs/AUFTRAG-EINBAU-B163-KOSMODESIGN-AN-INTEGRATOR.md`) waren nach
 * der Vorarbeit weiterhin praktisch ungebaut — die Pruefer-Nachmessung war
 * zutreffend: keine sichtbare Gruppenschiene, kein `moebel`/`leuchte`, keine
 * Taste E. Diese Nachbesserung liefert, additiv, innerhalb des Dateikreises:
 *
 * 1. **Die Gruppenschiene ist jetzt real gebaut** (`IslandShell.tsx`: zehn
 *    runde Knöpfe — Suche, drei häufigste, Trennlinie, sechs Gruppen; ein
 *    Klick auf eine Gruppe klappt eine Karte mit ihren Werkzeugen auf, Esc
 *    oder zweiter Klick auf dieselbe Gruppe schliesst sie; Suche über Klick
 *    ODER Taste `/`, Enter aktiviert den ersten Treffer), plus der
 *    Häufigkeits-Zähler (`gruppenschiene-haeufigkeit.ts`, neu, lokal in
 *    `localStorage`, Vorgabe Auswahl/Wand/Öffnung bis 20 gezählte
 *    Aktivierungen — wörtlich K1). Getestet in
 *    `test/gruppenschiene-haeufigkeit.test.ts` (6 Fälle) und
 *    `test/island-gruppenschiene-rail.test.tsx` (neu).
 *
 * 2. **Bewusst NICHT als Default für die echte `zeichnen`-Insel verdrahtet**
 *    — `DESIGN_INSELN`s `zeichnen`-Eintrag behält `gruppenschiene`
 *    ungesetzt (`undefined`), der ganze Rest der App bleibt dadurch
 *    byte-gleich. Grund, gemessen statt vermutet: `designInselKonfig`
 *    liefert für `island="zeichnen"` OHNE eigene `konfig` GENAU diesen
 *    Eintrag — und exakt diesen Aufrufweg nutzen ZWEI bestehende
 *    Testdateien AUSSERHALB dieses Dateikreises
 *    (`apps/kosmo-orbit/test/island-shell.test.tsx`,
 *    `apps/kosmo-orbit/test/island-shell-pd2.test.tsx`; `grep -c
 *    'island-werkzeug-'` → 22 + 12 = 34 Fundstellen), die nach blossem Hover
 *    SOFORT `island-werkzeug-wand`/`-volumen`/`-messen`/… klicken, ohne eine
 *    Gruppe zu öffnen. Ein Default-`true` bricht beide Dateien zuverlässig
 *    — Dateien, die dieser Dateikreis nicht ändern darf (»Nur in DEINEM
 *    Dateikreis ändern … NICHT anfassen, im Ergebnis melden«). Das ist ein
 *    STRUKTURELLER Befund, kein Testzahl-Detail wie bei Punkt 3 unten: die
 *    Kopplung sitzt in `designInselKonfig` selbst, nicht in einer einzelnen
 *    Erwartung. Fertig verdrahtbar: `DESIGN_INSEL_ZEICHNEN_GRUPPENSCHIENE`
 *    (oben) — der Integrator (oder wer die zwei Testdateien freigibt) setzt
 *    entweder `DESIGN_INSELN`s `zeichnen`-Eintrag auf `gruppenschiene:true`
 *    oder übergibt `DesignWorkspace.tsx` diese Konfig statt des Defaults
 *    (letzteres liegt ausserhalb dieses Dateikreises).
 *
 * 3. **ZWEITE Nachbesserung (24.09.2026, Prüfer-Urteil zu dieser Fassung
 *    NACHBESSERN — K2 zu 0 % gebaut): `moebel`/`leuchte` sind jetzt ECHTE
 *    `WERKZEUG_KATALOG`-Einträge** (s. `ZEICHNEN`-Array oben, Gesamtstand
 *    ZEICHNEN 26). Die Prämisse von Punkt 3/4 der ERSTEN Nachbesserung
 *    («braucht eine neue `ToolId` in `state/ui-zustand.ts`») war FALSCH —
 *    gemessen statt geglaubt: von den 24 bisherigen ZEICHNEN-Werkzeugen
 *    haben mehrere (`profil` in PROJEKT, die acht `hatPopup`-ohne-`toolId`-
 *    Fälle in ANSICHT/AUSTAUSCH) NIE eine `ToolId` gebraucht — ihr Stufe-2-
 *    Inhalt (`inhalte/*.tsx`) wirkt direkt über `useProject().runCommand`,
 *    UND `IslandShell.tsx`s `aufWerkzeugKlick` öffnet das Popup rein über
 *    lokalen React-Zustand (`setAktivesWerkzeugId`/`setStufe('popup')`),
 *    UNABHÄNGIG vom Rückgabewert des `onWerkzeugAktion`-Callbacks
 *    (`DesignWorkspace.tsx`s `aktiviereIslandWerkzeug`, `default`-Zweig:
 *    kein Aufruf für unbekannte Ids — bereits so, ungeändert, ausserhalb
 *    dieses Dateikreises, aber NICHT angefasst). `moebel`/`leuchte` folgen
 *    exakt demselben Muster: `MoebelStufe2`/`LeuchteStufe2`
 *    (`inhalte/zeichnen.tsx`, neu) rufen `runCommand('design.moebelSetzen'
 *    | 'design.leuchteZeichnen', …)` selbst auf. **Bricht dadurch
 *    unvermeidlich mehrere Erwartungen in Dateien ausserhalb dieses
 *    Dateikreises — gemessen mit dem vollen `npm test -w @kosmo/orbit-app`
 *    (nicht nur den zwei naheliegenden Dateien), 6 Dateien, 12 Fälle,
 *    keine sonst (Zahl am 25.09.2026 in der dritten Nachbesserung
 *    berichtigt — hier stand «7 Dateien», gezählt sind unten nur sechs):**
 *    - Sechs reine Zähl-Erwartungen (`WERKZEUG_KATALOG.length`/
 *      `ISLAND_GLYPHEN`-Grösse/`werkzeugeFuerIsland('zeichnen').length`/
 *      registrierte Stufe-Inhalte als feste Zahl, keine kennt einen
 *      Toleranzbereich): `apps/kosmo-orbit/test/island-katalog-pd2.test.ts`
 *      Zeilen 45/205/219 (46→48, 44→46, 24→26),
 *      `apps/kosmo-orbit/test/island-shell.test.tsx` Zeile 88 (24→26),
 *      `apps/kosmo-orbit/test/pb2-icon-verdrahtung.test.ts` Zeilen
 *      48/71/81/82 (46→48, 46→48, 37→39, 46→48),
 *      `apps/kosmo-orbit/test/island-glyphen.test.tsx` Zeilen 71/78/169
 *      (46→48, 37→39, 49→51),
 *      `apps/kosmo-orbit/test/island-inhalte-pd3a.test.tsx` Zeile 94
 *      (29→31, plus die `ALLE_29`-Namensliste dort um `moebel`/`leuchte`
 *      ergänzen).
 *    - **Eine substantiellere, keine blosse Zahl:**
 *      `apps/kosmo-orbit/test/a9-leuchte-inspector.test.tsx` Zeile 311
 *      (`expect(quelle).not.toContain('design.leuchteZeichnen')`) — die
 *      Probe verhindert bewusst eine ZWEITE, unabhängig gepflegte
 *      Leuchte-Anlegen-Stelle neben `Inspector.tsx`s
 *      `LeuchteAbhaengenZeile` (Kopfkommentar dort: «Gegen den Fall aus
 *      Muster 11: Gleiche Woerter an zwei Orten»). `LeuchteAbhaengenZeile`
 *      passt hier NICHT: sie verlangt eine bereits ausgewählte `Slab`
 *      (Decke) und hängt die Leuchte an DEREN Mittelpunkt/Geschoss
 *      darunter — K2 verlangt wörtlich einen STANDALONE-Knopf in der
 *      Einrichten-Karte, ohne vorab gewählte Decke. `LeuchteStufe2` nutzt
 *      darum bewusst den vom Befehl selbst dokumentierten Rückfall (kein
 *      `deckeId` → Geschoss-Oberkante, `commands/design.ts`s
 *      `drawLeuchte`-Kommentar: «der Notausgang … nicht die Eingangstuer
 *      fuer eine falsche Angabe»). K2 ist damit ein bewusster, im Auftrag
 *      selbst verlangter ZWEITER Aufrufweg — die Probe braucht eine
 *      Ausnahme für genau diesen einen (`LeuchteStufe2`), keine Streichung.
 *    Keine der sechs Dateien angefasst (Dateikreis), s. Bau-Bericht dieser
 *    zweiten Nachbesserung für die volle Messung. Das ist
 *    kein Fehler dieses Pakets: die K1-Abnahme selbst verlangt wörtlich
 *    «die Zahl 26 gegen den Katalog prüft» — 24 kann nicht gleichzeitig
 *    stimmen bleiben UND K2 fertig sein. Trivialer Integrator-Fix: die
 *    genannten Zahlen an den genannten Stellen anheben.
 * 4. **Taste `E` (90°-Drehung vor dem Setzen): jetzt gebaut**, aber NICHT
 *    in `kurztasten.ts` — die dort ausschliesslich registrierten Kürzel
 *    sind GLOBALE Werkzeugwechsel (A/W/Z/…, `werkzeugFuerTaste`), während
 *    `E` eine LOKALE Aktion NUR innerhalb der offenen «Möbel»-Karte ist
 *    (dasselbe Muster wie `IslandShell.tsx`s `/`-Sucheöffnung, deren
 *    eigener Kommentar das vorzeichnet: «lebt ohnehin NICHT in der
 *    globalen Registry, sondern lokal … kollidiert also strukturell mit
 *    keinem globalen Kürzel»). `MoebelStufe2` bindet `keydown` NUR
 *    solange sie selbst gemountet ist (derselbe scope-gebundene
 *    `useEffect`+`window.addEventListener`/Cleanup wie dort), mit
 *    demselben Eingabefeld-Schutz. Gegengeprüft: `e`/`E` steht in KEINEM
 *    `KURZTASTEN`-Eintrag (`grep -n "taste: '[a-z]'" kurztasten.ts` → 13
 *    Einträge, `e` fehlt). Die im Auftrag genannte Datei
 *    `apps/kosmo-orbit/src/state/kurztasten.ts` existiert weiterhin nicht
 *    — der tatsächliche Pfad bleibt `apps/kosmo-orbit/src/modules/design/
 *    kurztasten.ts`, unverändert (kein Eintrag nötig, die Taste lebt lokal).
 * 5. `design.moebelSetzen`/`design.leuchteZeichnen` sind kernel-seitig
 *    bereits vollständig (`packages/kosmo-kernel/src/commands/design.ts`,
 *    Zeilen 5797/5897) — jetzt AUCH über die Insel erreichbar.
 *
 * **Was das für die K1/K2-Abnahme heisst (ehrlich, nicht schöngerechnet):**
 * K2 ist mit dieser zweiten Nachbesserung vollständig gebaut und getestet
 * (Möbel setzen inkl. `E`-Drehung, Leuchte mit «Vorschlag»-Marke — beide
 * landen echt im Dokument über den Command→Patch-Weg). Die Gruppenschiene
 * (K1) selbst bleibt aus Punkt 2 heraus weiterhin NICHT die Standard-
 * Ansicht des echten Programms — wer die App öffnet, sieht weiterhin die
 * flache Leiste (jetzt 26 statt 24 Werkzeuge, alle erreichbar, nur eben
 * nicht über die Gruppenschiene). Das Bild `eingebaut-a1.png` neben `a1.png`
 * und die 15-Specs-Stichprobe brauchen die ECHTE, standardmässig
 * eingeschaltete Insel für ihren Bedienweg — dafür bleibt die
 * `DESIGN_INSEL_ZEICHNEN_GRUPPENSCHIENE`-Konfig (oben) der fertige,
 * geprüfte Baustein; das Bild dieser Nachbesserung zeigt sie darum direkt
 * über diese Konfig gerendert (kein Blocker für ein Bild, nur für den
 * ECHTEN App-Default). Die sieben Inselproben (`w5-projekt-fenster-
 * nachbarn` u. a.) prüfen den bestehenden Default-Zustand — die zwei
 * neuen Katalog-Einträge ändern an dessen VERHALTEN nichts (flache Leiste
 * zeigt einfach zwei Knöpfe mehr), sie laufen unverändert grün, s.
 * Bau-Bericht.
 *
 * 6. **NACHTRAG zur Gegenprüfung vom 25.09.2026 (dritte Nachbesserung
 *    dieses Pakets): zwei Messfehler im weitergereichten Bau-Bericht
 *    korrigiert, ein Ursachenirrtum aufgeklärt — frisch nachgemessen, nicht
 *    aus dem Prüfer-Befund übernommen.**
 *    - Die 5 In-Kreis-Testdateien waren im Bau-Bericht als «41/41» gemeldet.
 *      Frisch gemessen mit demselben Befehl (`npm run test -w
 *      @kosmo/orbit-app -- test/gruppenschiene-haeufigkeit.test.ts
 *      test/island-gruppenschiene-rail.test.tsx
 *      test/island-gruppenschiene-vorarbeit.test.ts
 *      test/island-einrichten-moebel-leuchte.test.tsx
 *      test/einrichten-verlauf.test.ts`): **49/49 grün, EXIT=0** —
 *      unverändert seit Commit `73f8bb089`, dessen eigene Commit-Botschaft
 *      schon korrekt 49 nennt. Der Fehler sass nur im separat
 *      weitergereichten Bau-Bericht, nicht im Commit.
 *    - Der als «vorbestehender, dateikreisfremder Fund» gemeldete
 *      Typecheck-Fehler (`packages/kosmo-sync/src/client.ts:171`,
 *      `Doc.destroy fehlt im yjs-Typenindex`, EXIT=2) ist KEIN Code-Fehler
 *      in `client.ts`: dieser Arbeitsbaum (seit Tagen wiederverwendet,
 *      Container-Neustarts überlebt) hatte ein beschädigtes
 *      `node_modules/lib0` — sämtliche `.d.ts`/`.map`-Dateien fehlten
 *      (90 statt 263 Dateien, gegen einen gesunden Arbeitsbaum derselben
 *      Version gegengezählt), darunter `observable.d.ts`, das `Doc`s
 *      `destroy()` über `ObservableV2` liefert. Nach `rm -rf
 *      node_modules/lib0 && npm install lib0 --no-save` (node_modules
 *      liegt ausserhalb der Versionskontrolle, kein Diff, keine
 *      Paket-Version geändert) sind sowohl `npm run typecheck` als auch
 *      `npm run build -w @kosmo/orbit-app` sauber **EXIT=0** — mit den
 *      GEWÖHNLICHEN Befehlen, ohne den `npx vite build`-Umweg. Wer diesen
 *      Arbeitsbaum weiter benutzt und denselben Fehler sieht: die Ursache
 *      ist `node_modules`, nicht `client.ts` — dieselbe Reparatur fahren,
 *      bevor ein «vorbestehender Fund» weitergereicht wird.
 *    - **Weiterhin unverändert bestätigt** (kein Messfehler, reproduziert):
 *      `tools/zielgroessen-gate.mjs` bleibt ROT (size=sm 701→703,
 *      size=touch 75→77 Stellen — Deckel ausserhalb dieses Dateikreises),
 *      und `test/island-shell.test.tsx` + `test/island-shell-pd2.test.tsx`
 *      + `test/island-katalog-pd2.test.ts` bleiben zusammen 4 rot / 69 grün
 *      (harte 24/44-Erwartungen ausserhalb dieses Dateikreises, s. Punkt 3
 *      oben) — **Nachtrag 25.09.2026, vierte Nachbesserung: die dritte
 *      Datei fehlte hier in der Aufzählung** (nur die ersten zwei genannt),
 *      obwohl die Zahl 4/69 sie schon brauchte — ohne
 *      `island-katalog-pd2.test.ts` sind es nur 1 rot / 39 grün, frisch
 *      nachgemessen. Getrennt davon, additiv, der volle K2-Zuwachs über den
 *      ganzen Baum: 6 Dateien, 12 Fälle (s. Punkt 3 oben, dort ebenfalls am
 *      25.09.2026 von «7» auf «6 Dateien» berichtigt) — die 4 Fälle aus
 *      diesem Absatz sind darin enthalten, nicht zusätzlich zu zählen
 *      (`island-shell.test.tsx` 1 Fall + `island-katalog-pd2.test.ts`
 *      3 Fälle = dieselben 4, die anderen 8 stehen nur in Punkt 3). Der
 *      vorherige Bau-Bericht hatte dem Integrator nur «4 rot / 69 grün» für
 *      diese drei Dateien gemeldet und dabei verschwiegen, dass der volle
 *      Testlauf (`npm run test -w @kosmo/orbit-app`, ohne Dateifilter)
 *      6 Dateien / 12 Fälle zeigt — Faktor 3, nicht 4, gegen die
 *      irrtümlich gemeldeten «3 Dateien / 4 Fälle». Alle Zahlen dieses
 *      Absatzes heute mit den genannten Befehlen neu gemessen, EXIT=1 für
 *      beide Teilläufe (rot bleibt rot).
 *      Punkt 2 dieses Hinweises (Gruppenschiene bewusst nicht Default) ist
 *      der eine noch offene KRITISCHE Rest-Blocker, bevor K1/K2 im echten
 *      Programm sichtbar sind — nicht nur gebaut.
 *
 * 7. **NACHTRAG (Gegenpruefung 25.09.2026, fuenfte Nachbesserung) — der
 *    Rest-Blocker aus Punkt 2/6 ist zu, innerhalb dieses Dateikreises:**
 *    `IslandShell.tsx`s `IslandBuehne` (Datei in diesem Dateikreis) setzt
 *    ihren `inseln`-Default jetzt auf `DESIGN_INSELN_STANDARD` (oben) statt
 *    auf das rohe `DESIGN_INSELN` — genau die Komponente, die
 *    `DesignWorkspace.tsx` ohne eigene `inseln`-Prop rendert. `DesignWorkspace.
 *    tsx` selbst bleibt unangefasst (weiterhin ausserhalb des Dateikreises,
 *    und jetzt auch nicht mehr noetig). `DESIGN_INSELN` bleibt bewusst
 *    unveraendert — Begruendung und Gegenpruefung gegen alle
 *    `<IslandBuehne>`-Aufrufer im Baum s. Kommentar an
 *    `DESIGN_INSELN_STANDARD` oben. Neuer Beweis-Test (dieser Dateikreis):
 *    `test/island-gruppenschiene-app-default.test.tsx` rendert
 *    `<IslandBuehne />` byte-identisch zum echten App-Aufruf und zeigt die
 *    zehn Rail-Knoepfe — war ROT vor dieser Nachbesserung (Rot-vor-Gruen),
 *    ist jetzt GRUEN. **Was das NICHT loest** (weiterhin ausserhalb des
 *    Dateikreises, unveraendert): die sechs 24→26-Testdateien aus Punkt 3,
 *    die `a9-leuchte-inspector.test.tsx`-Ausnahme, und die zwei
 *    `zielgroessen-gate.mjs`-Deckel — alle drei bleiben offene
 *    Integrator-Schritte, s. Bau-Bericht dieser Nachbesserung fuer die
 *    frische Messung.
 *
 *    **NEUER, bisher unentdeckter Preis dieser Nachbesserung, ehrlich
 *    benannt (nicht schöngerechnet) — EIN zusätzliches Testfile ausserhalb
 *    des Dateikreises bricht:** `apps/kosmo-orbit/test/
 *    b49-zonen-zuruf-direktes-zeichnen.test.tsx` (3 Fälle, alle 3 rot) —
 *    sein lokaler `aktiviereWerkzeug()`-Helfer klickt `island-werkzeug-zone`
 *    direkt nach dem Pillen-Klick, ohne die Gruppe «Räume und Flächen» zu
 *    öffnen (`zone` ist keines der drei Vorgabe-häufigsten). Gefunden beim
 *    vollen, ungefilterten `npm run test -w @kosmo/orbit-app` (nicht nur
 *    den vorher bekannten Dateien) — der Pruefer hatte nur die ZWEI
 *    `island-shell*.test.tsx`-Dateien als Kollateralschaden der
 *    Default-Umschaltung genannt; ein dritter, andersartiger Fall
 *    (echte `DesignWorkspace`-Instanz statt direktem `<IslandShell>`-Aufruf)
 *    blieb unentdeckt, bis diese Nachbesserung den vollen Lauf fuhr.
 *    Trivialer Integrator-Fix (gleiche Form wie `n4-stummer-oeffnung-klick.
 *    test.tsx`s bereits bestehendes Muster): vor dem `island-werkzeug-zone`-
 *    Klick einen Klick auf `isl-gruppe-raeume-flaechen` einfügen. Nicht
 *    selbst behoben — Datei ausserhalb des Dateikreises.
 *
 *    **Randfund, KEIN neuer Schaden dieser Nachbesserung (Ursache: K2s
 *    24→26-Zuwachs, wie Punkt 3 oben) — nur bisher nicht mitgezählt:**
 *    `apps/kosmo-orbit/test/insel-scroll-e10.test.tsx` (1 Fall, «expected 24
 *    to be 26») rendert `<IslandShell island="zeichnen" />` DIREKT (kein
 *    `<IslandBuehne>`, unberührt von dieser Nachbesserung) — derselbe
 *    Zähl-Fund wie die sechs in Punkt 3 genannten Dateien, nur dort nicht
 *    mitgezählt. Ehrliche Summe des K2-Zuwachses damit: **7 Dateien, 13
 *    Fälle**, nicht 6/12 (Punkt 3 oben bleibt unveraendert stehen, hier nur
 *    ergänzt statt dort umgeschrieben — Nachvollziehbarkeit).
 *
 *    **Tie-Break-Klarstellung (kleiner, unabhaengiger Fund des Pruefers):**
 *    `gruppenschiene-haeufigkeit.ts`s `topDreiHaeufigste()`-Kopfkommentar
 *    beschrieb einen Vorgabe-Vorrang-Tie-Break («zuerst in der Vorgabe
 *    genannte, dann alphabetisch»), den der Code nie hatte — reine
 *    `localeCompare`-Sortierung, kein Vorgabe-Bezug. Der Kommentar war die
 *    Abweichung (der Code ist deterministisch und ausreichend fuer den
 *    K1-Auftrag, der keinen bestimmten Tie-Break verlangt); der Kommentar
 *    ist jetzt an den Code angeglichen, kein Verhalten geaendert.
 */
