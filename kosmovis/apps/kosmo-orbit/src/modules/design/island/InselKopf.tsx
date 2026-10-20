import { Badge, KButton, KTooltip } from '@kosmo/ui';
import type { SyncStatus } from '../../../state/project-sync';
import { useProject } from '../../../state/project-store';
import { autosaveText } from '../../../state/autosave-text';
import type { AutosaveLage } from '../../../state/project-vault';
import { syncChipText } from '../../../state/kopplung';
import { useVerbindungsWaechter } from '../../../state/verbindungs-waechter';
import './island.css';

/**
 * B76 «Der Inselkopf» — `docs/AUFTRAG-B76-INSELKOPF.md`, `docs/V0954-SPEZ.md`
 * §3 P1 (Abnahme C-2 bis C-4).
 *
 * DER ANLASS, selbst nachgelesen (Messbefehle im Bau-Bericht, nicht aus dem
 * Auftrag abgeschrieben — die dort genannten Zeilennummern lagen um +23
 * daneben, seit P5/B80 `App.tsx` 24 Zeilen laenger ist):
 *
 *   App.tsx:995        {!bodenDockAusgeblendet && screen !== 'home' && (
 *   App.tsx:1002           <header
 *   App.tsx:464-471    const bodenDockAusgeblendet = designIslandAktiv || … ;
 *
 * Der Kopfbalken rendert GENAU DANN, wenn KEINE Insel laeuft — und die Insel
 * ist der ausgelieferte Zustand. Damit traegt das ausgelieferte Produkt seine
 * sechs Grundfunktionen nirgends: `save-project`, `open-project`,
 * `autosave-status`, `sync-toggle`, `starter-guide-start`, `app-version`.
 *
 * DER OWNER-ENTSCHEID vom 28.08.2026 («gemischt», V0954-SPEZ §3 P1, C-1 —
 * nicht neu zu verhandeln): die Insel ist bewusst randfrei, ein voller Balken
 * widerspricht ihr. Also ZWEI Orte statt eines Balkens —
 *
 *   Speichern · Oeffnen · Auto-Save  → `InselGrundstreifen` (unten), ein
 *       schmaler, IMMER sichtbarer Streifen: «Speichern muss man sehen, ohne
 *       zu suchen».
 *   Version · Rundgang · Sync        → `InselZweitgruppe` (unten), die zweite
 *       Gruppe unmittelbar neben dem vorhandenen `island-einstellungen-kreis`.
 *
 * WO DIESE DATEI LIEGT, und warum nicht in `shell/`: sie teilt den Ort mit
 * `StationenOrb.tsx`/`AnsichtsInfo.tsx`/`GeschossPille.tsx` — auch die leben
 * unter `modules/design/island/`, werden aber seit PB3 stationsagnostisch aus
 * `App.tsx` fuer JEDE Insel gerendert. Kein zweites Muster fuer dieselbe Sache.
 *
 * WAS SIE NICHT TUT (Auftrag §4): sie baut den bestehenden Kopfbalken weder um
 * noch zieht sie ihn um — `App.tsx`s `kopfWerkzeuge()` und der
 * `!bodenDockAusgeblendet`-Zweig bleiben Zeichen fuer Zeichen, wie sie waren.
 * Beide Zweige schliessen sich gegenseitig aus (`bodenDockAusgeblendet` ist
 * die eine Bedingung, ihre Negation die andere), darum tragen die Bauteile
 * hier dieselben `data-testid`s wie der Balken: sie stehen NIE gleichzeitig im
 * DOM, und jede Bestands-Spec, die `save-project` klickt, findet in der Insel
 * ab jetzt genau einen Knopf statt keinen.
 */

/**
 * Geometrisches Ausweichen statt eines Ebenen-Entscheids (Auftrag §4:
 * «benannte Konstante, Wert aus dem TSX, Rang unveraendert»).
 *
 * Der Einstellungs-Kreis sitzt auf `right:14px` (`island.css`
 * `.isl-einstellungen-kreis`) und ist 44px breit; die Kopf-Reihe der Insel
 * folgt links einem 52px-Raster (14 · 66 · 118, s. `.isl-buehnenkopf`-
 * Kommentar dort). Die zweite Gruppe nimmt rechts das naechste Feld desselben
 * Rasters — sie beruehrt den Kreis nicht, und der Kreis behaelt Groesse,
 * Position, Klick-Weg und `data-testid` unveraendert (mehrere Bestands-Specs
 * messen seine Box, `e2e/island-ui.spec.ts`).
 */
// Lieferung 12 §2 (30.09.2026): + 44 + 4 fuer den Speicher-Kreis links neben dem Zahnrad.
export const INSEL_ZWEITGRUPPE_RECHTS_PX = 14 + 52 + 48;

export interface InselGrundstreifenProps {
  /** Ruft denselben `downloadProject`-Weg wie der Kopfbalken-Knopf. */
  readonly onSpeichern: () => void;
  /**
   * Ruft denselben `speichereProjektVollstaendig`-Weg wie der
   * Kopfbalken-Knopf «Sichern (.kosmo)».
   *
   * **NACHGETRAGEN AM 22.09.2026, und der Grund ist ein Loch im
   * ausgelieferten Produkt.** Der Knopf kam am 17.09.2026 dazu (P28) und
   * wurde nur in den Kopfbalken gebaut — der rendert genau dann, wenn KEINE
   * Insel laeuft. Auf den sieben Insel-Stationen gab es damit keinen Weg,
   * das Projekt vollstaendig auf die eigene Platte zu sichern. Der Kommentar
   * am Balken-Knopf sagt selbst, warum das zaehlt: «Dem Menschen das Sichern
   * zu nehmen waere schlimmer als das Problem.»
   */
  readonly onSpeichernVollstaendig: () => void;
  /** Ruft denselben `oeffneProjektDatei`-Weg wie der Kopfbalken-Knopf. */
  readonly onOeffnen: () => void;
  /** `App.tsx`s `autosaveLage` — Stand, Zeit des letzten Erfolgs, Grund im
   *  Fehlerfall (Fund F7, 08.09.2026). Vorher nur die ISO-Zeit, und damit
   *  keine Form fuer «hat nicht geklappt». */
  readonly autosaveLage: AutosaveLage;
}

/**
 * ZWILLING, bewusst stehen gelassen: dieselbe Formulierung steht ein zweites
 * Mal im Kopfbalken (`App.tsx`, `data-testid="autosave-status"`). Sie zu
 * vereinen hiesse, den Kopfbalken anzufassen — und genau das verbietet Auftrag
 * §4 («Zubau, kein Umzug»). Der Zwilling ist hier benannt statt verschwiegen;
 * das Zusammenlegen gehoert in das Paket, das den Balken ohnehin anfasst.
 */

/**
 * Der schmale, immer sichtbare Streifen unten links (Owner: «Speichern muss
 * man sehen, ohne zu suchen»).
 *
 * WARUM UNTEN LINKS, und warum das die einzige freie Ecke ist — nachgesehen,
 * nicht angenommen: die Kopf-Reihe der Insel belegt oben links `left:14/66/118`
 * (Logo · Stationen-Orb · Ansichts-Info) und `top:66px` (Geschoss-Pille), oben
 * rechts den Einstellungs-Kreis; unten rechts sitzen der Kosmo-Orb
 * (`right:26px; bottom:24px`) und das Kosmo-Fenster (`kosmo-panel.css`,
 * `bottom:100px`). Die vier Inseln selbst haengen an den Kanten-Mitten
 * (`.isl-rand-links/-oben/-rechts/-unten`, je `50%`). Unten links ist damit
 * die einzige Ecke ohne Bestand.
 *
 * KEIN `z-index` — bewusst, und das ist der geometrische Ausweg statt eines
 * Ebenen-Entscheids (Auftrag §4 verbietet beides: den Entscheid und den
 * Eingriff in `tools/z-ebenen-gate.mjs`). Ohne eigene Stufe kann der Streifen
 * ein Insel-Bedienelement NIE verdecken: die Inseln stehen spaeter im DOM und
 * gewinnen damit die Malreihenfolge (offen zusaetzlich mit `z-index:100`,
 * `.isl-root--offen`). Der Wachhund gegen verdeckte Bedienelemente
 * (`e2e/w5-1-insel-ueberdeckung.spec.ts`) kann hier also keinen Fund
 * bekommen — er misst, ob etwas ueber einem Insel-Element liegt.
 */
export function InselGrundstreifen({
  onSpeichern,
  onSpeichernVollstaendig,
  onOeffnen,
  autosaveLage,
}: InselGrundstreifenProps) {
  return (
    <div className="isl-grundstreifen" data-testid="island-grundstreifen">
      {/* KURZHILFE-GATE (22.09.2026): alle drei Knoepfe dieser Gruppe auf
          `KTooltip` umgestellt, statt nur den neu dazugekommenen
          `save-project-vollstaendig` (`tools/kurzhilfe-gate.mjs` meldete dort
          das Wachstum 5 -> 6). Nur den einen umzubauen haette die Gruppe
          zerrissen — zwei Geschwister mit nativem `title=`, einer mit
          `KTooltip`, ohne erkennbaren Grund fuer den Unterschied. `KTooltip`
          traegt hier keine der beiden bekannten Ausschlussbedingungen
          (`tooltip.tsx`s Kopfkommentar bzw. `kurzhilfe-bestand.json`s
          Eintraege zu `KuratierInspektor.tsx`/`OrbitStart.tsx`): kein
          `flex:1`-Zwang auf den Knopf selbst und kein `width:100%` in einem
          fest bemessenen Kreis — `.isl-grundstreifen` ist ein schlichter
          Flex-Streifen mit `gap`, `.k-tooltip` ist `display:inline-block`
          ohne eigenes Padding/Margin und uebernimmt darum die Breite seines
          Kindes unveraendert (`--isl-grundstreifen-breite: 392px` bleibt
          gueltig, nachgemessen nach dem Umbau — BERICHTIGT 23.09.2026: die
          Zahl galt nur bis zum vierten Knopf «Sichern»; seit `79035fc29`
          steht sie auf 507px, s. `island.css`). Ergebnis: der Deckel sinkt
          (6 -> 3), er steigt nicht — `tools/kurzhilfe-bestand.json`
          nachgezogen. «Sichern» steht VOR «Weitergeben», wie im Kopfbalken —
          und in derselben Reihenfolge aus demselben Grund: das eigene Archiv
          kommt vor dem Weitergeben. Wortlaut und `data-testid` woertlich wie
          dort, nur der Ueberbringer des Hilfetexts wechselt von nativem
          `title=` zu `KTooltip`. */}
      <KTooltip text="Vollständige .kosmo-Datei für das eigene Archiv — nichts fehlt, auch keine Herstellergeometrie">
        <KButton
          size="touch"
          tone="ghost"
          onClick={onSpeichernVollstaendig}
          data-testid="save-project-vollstaendig"
        >
          Sichern<span className="isl-grundstreifen-endung"> (.kosmo)</span>
        </KButton>
      </KTooltip>
      {/* Wortlaut und `data-testid` woertlich wie im Kopfbalken (K6,
          `docs/OWNER-KORREKTUREN-2026-07.md`) — `e2e/k6-projektkontext.spec.ts`
          prueft den Text mit `toContainText`; der Hilfetext selbst kommt
          seit dem Kurzhilfe-Umbau oben aus `KTooltip`, nicht mehr aus einem
          nativen `title=`. */}
      <KTooltip text="Projekt als .kosmo-Datei exportieren — Auto-Save sichert ohnehin jeden Schritt im Tresor">
        <KButton size="touch" tone="ghost" onClick={onSpeichern} data-testid="save-project">
          Weitergeben<span className="isl-grundstreifen-endung"> (.kosmo)</span>
        </KButton>
      </KTooltip>
      <KTooltip text="Ein zuvor exportiertes .kosmo-Projekt laden">
        <KButton size="touch" tone="ghost" onClick={onOeffnen} data-testid="open-project">
          Projekt öffnen
        </KButton>
      </KTooltip>
      <span className="isl-grundstreifen-hinweis" data-testid="autosave-status">
        {autosaveText(autosaveLage)}
      </span>
    </div>
  );
}

export interface InselZweitgruppeProps {
  readonly syncStatus: SyncStatus;
  readonly peers: number;
  /** Ob die Sync-Leiste offen ist — nur fuer `aria-pressed`, kein Layout. */
  readonly syncOffen: boolean;
  /** Anzeige-Version, z.B. «v0.9.53» (`__APP_VERSION__`, gereicht aus `App.tsx`). */
  readonly version: string;
  /** Der DRITTE `setSyncOpen`-Aufrufweg (Auftrag §3.4) — er haengt NICHT am
   *  `!bodenDockAusgeblendet`-Zweig; die beiden bestehenden bleiben unberuehrt. */
  readonly onSyncToggle: () => void;
  /**
   * Nahtstelle fuer einen zweiten Wirt (Visbox-Entscheid 116 (7), 20.10.2026): ohne Rundgang kein
   * «?»-Knopf, statt eines Knopfs ohne Wirkung. KosmoOrbit reicht ihn immer.
   */
  readonly onRundgang?: () => void;
  /**
   * Nahtstelle fuer einen zweiten Wirt (Visbox-Entscheid 116 (5)): an der Stelle des Sync-Chips,
   * in derselben Optik, ein eigener Chip — in Visbox der Heim-PC («Wer rechnet?»). Der Klick geht
   * an `onSyncToggle`. KosmoOrbit setzt ihn nicht; dann steht der Sync-Chip wie bisher.
   */
  readonly chip?: InselChip;
}

/** Ein Chip an der Stelle des Sync-Chips (zweiter Wirt, s. `InselZweitgruppeProps.chip`). */
export interface InselChip {
  readonly text: string;
  /** Farbe wie beim Sync-Chip: «gut» = live, «aus» = still, «warnung» = alles dazwischen. */
  readonly ton: 'gut' | 'aus' | 'warnung';
  /** Vorlesename (ohne `title`: die Kurzhilfe-Wache haelt die Zahl der Browser-Tooltips). */
  readonly label: string;
  readonly testid: string;
}

const CHIP_TON: Record<InselChip['ton'], string> = {
  gut: 'var(--k-success)',
  aus: 'var(--k-ink-faint)',
  warnung: 'var(--k-warning)',
};

/**
 * B82 #4 — der Rueckgaengig-Knopf, s. `InselZweitgruppe`s Kopfkommentar
 * unten fuer die WARUM-HIER-Begruendung (der Fund am echten Chromium, der
 * `InselGrundstreifen` als Ort ausschloss). `history.canUndo` (Getter,
 * `packages/kosmo-kernel/src/commands/core.ts`) deaktiviert den Knopf statt
 * einen stillen No-op zuzulassen — dieselbe Sicherheitslage wie beim
 * manuellen Verlauf-Knopf (`DesignWorkspace.tsx`), nur dort ungeprueft (der
 * dortige Klick ist ohnehin ein No-op ohne Wirkung, s. dort). Eigene
 * Komponente statt Inline-JSX, damit `useProject`-Selector und Klick-Handler
 * an einem Ort stehen wie beim Sync-/Rundgang-Knopf daneben.
 */
function IslandUndoKnopf() {
  const kannRueckgaengig = useProject((s) => s.history.canUndo);
  return (
    <button
      onClick={() => useProject.getState().undo()}
      data-testid="island-undo"
      data-aussenklick-frei=""
      className="k-druck isl-kopf-zweit-knopf"
      disabled={!kannRueckgaengig}
      aria-label="Letzten Schritt rückgängig machen"
      title="Letzten Schritt rückgängig machen — derselbe Weg wie die Zwei-Finger-Doppeltipp-Geste (Einstellungen › Bewegung & Klang)"
    >
      <span className="isl-kopf-zweit-zeichen" aria-hidden="true">
        ↩
      </span>
    </button>
  );
}

/**
 * D2 (Bot-Fund U8, `docs/MESSUNG-UX-BOTLAUF-2026-09-23.md`) — der
 * Wiederholen-Knopf, der bisher NIRGENDS im Insel-Modus sichtbar war: nur
 * `IslandUndoKnopf` direkt daneben stand da, `history.redo()` (`project-
 * store.ts`) hatte im Insel-Modus keinen sichtbaren Aufrufweg. Der
 * manuelle Verlauf-Knopf in `DesignWorkspace.tsx` traegt «Wiederholen»
 * zwar schon — der rendert aber nur im Manuell-Modus, nicht im
 * ausgelieferten Produktions-Default `island`.
 *
 * Dieselbe Sicherheitslage wie beim Rueckgaengig-Knopf daneben:
 * `history.canRedo` (Getter, `packages/kosmo-kernel/src/commands/core.ts`)
 * deaktiviert den Knopf statt eines stillen No-op, wenn nichts zu
 * wiederholen ist.
 *
 * NATIVES `title=` STATT EINES ZWEITEN — bewusst NICHT, wie es
 * `IslandUndoKnopf` daneben tut: `tools/kurzhilfe-gate.mjs` deckelt diese
 * Datei bereits auf drei `title=`-Stellen (`tools/kurzhilfe-bestand.json`,
 * Sync-Knopf, Rundgang-Knopf, Rueckgaengig-Knopf) — ein vierter Wortlaut
 * mit `title=` waere Wachstum ueber den gehaltenen Bestand hinaus und liegt
 * ausserhalb dieses Dateikreises (`tools/**`, «alles andere bleibt
 * byte-gleich», `docs/V016-SPEZ.md` §14). `KTooltip` (bereits importiert,
 * s. `InselGrundstreifen` oben) ersetzt `title=` wortgetreu, ohne den
 * gedeckelten Bestand zu beruehren — und traegt den Hilfetext ausserdem
 * dauerhaft ueber `aria-describedby` in den Zugaenglichkeitsbaum, auch
 * waehrend der Knopf deaktiviert ist (`tooltip.tsx`s
 * P-KURZHILFE-LESBAR-Kommentar).
 *
 * `lage="unten"` STATT DES DEFAULTS `"oben"` — selbst nachgelesen
 * (`aura.css` `.k-tooltip-blase--oben`: `bottom: calc(100% + var(--k-s2))`,
 * oeffnet also NACH OBEN relativ zum Knopf): die Zweitgruppe sitzt auf
 * `top: 14px` (`island.css`), der Knopf darin hat 44px Mindesthoehe — nach
 * oben blieben rechnerisch nur rund 14px Luft vor dem Bildschirmrand, die
 * Blase selbst braucht mehr. `KTooltip` hat keine Kollisionserkennung
 * (selbst gelesen, `tooltip.tsx`), eine falsche Seite waere darum am
 * oberen Rand abgeschnitten — genau der Fehler, den Regel 2 der
 * UI-Regeln («kein Text verlaesst je seine Box») ausschliesst. Unten ist
 * frei (das Planfeld/der Canvas), die Blase oeffnet darum dorthin.
 *
 * NACHBESSERUNG 24.09.2026 (gelöst, s. `island.css`s Kommentar bei
 * `--isl-zweitgruppe-breite` für die volle Rechnung): der vierte Knopf
 * macht die Gruppe ehrlich breiter (243 -> 292px) und schiebt rechts-
 * buendige Stationsinhalte, die sich an `--isl-kopfzone-rechts-frei`
 * orientieren, um denselben Betrag nach LINKS — bei KosmoPrepare @
 * 1024x768 landete «nach Art» dadurch in der mittig verankerten
 * WISSEN-Pille, bei KosmoVis @ 1024x768 die AUSKLAPP-BOX der ANSICHT-
 * Insel auf der Kopfzeile. Rechnerisch bewiesen (voller Beleg dort): mit
 * VIER vollwertigen 44px-Knoepfen NEBENEINANDER gibt es keinen Wert der
 * Konstante, der gleichzeitig `b130-kopfzone-rechts.spec.ts` besteht UND
 * unter der Kollisionsschwelle bleibt — ein echter vierter Knopf braucht
 * mindestens 40px mehr, die Toleranz war nur 10px.
 *
 * ERSTER GELOESTER ANLAUF (verworfen, im Bau-Bericht dokumentiert): ein
 * erzwungener Zeilenumbruch unter 1200px machte die Gruppe zwar wieder
 * schmal (243px, byte-gleich zum Drei-Knopf-Stand), aber dafuer HOEHER
 * (zwei Zeilen statt einer) — und riss damit eine ANDERE Bestandsprobe:
 * `b154-vis-inseln-gegen-das-kosmo-feld.spec.ts` @ 1024x768 «stimmung»
 * (die STIMMUNG-Insel ist auf `--isl-frei-oben` = 74px verankert, die
 * zweizeilige Gruppe reichte bis 112px). Nachgemessen, GENAU DAS war der
 * Fund (Kopf 968px² statt 0) — die Rechnung fuer B154/W5-1 hatte nur die
 * BREITE geprueft, nicht die HOEHE. Verworfen, weil eine Reparatur, die
 * eine neue, vorher gruene Probe reisst, keine Reparatur ist.
 *
 * GEWAEHLTER WEG: unter 1200px weicht NICHT Wiederholen, sondern die
 * Versionsanzeige (`--isl-kopf-zweit-version`, weiter unten in dieser
 * Datei) — `display:none` in derselben Medienregel (`island.css`). Die
 * Gruppe bleibt EINE Zeile, EINE Hoehe (46px real gemessen, byte-gleich
 * zur Hoehe vor D2) — nur die Zusammensetzung wechselt von «drei Knoepfe
 * + Version» auf «vier Knoepfe, keine Version». Gemessen (Build +
 * `getBoundingClientRect`, 1024px): die reale Breite ist 241,75px —
 * SCHMALER als die alten 243px, weil die Versionsanzeige (~54px inkl.
 * Abstand) mehr Platz freigibt, als der vierte Knopf braucht (~52px
 * inkl. Abstand). `--isl-zweitgruppe-breite` faellt in derselben
 * Medienregel auf 242px zurueck (aufgerundet, s. `island.css`s
 * Kommentar dort fuer die volle Zahlenreihe), `--isl-kopfzone-rechts-
 * frei` folgt automatisch. Ab 1200px bleibt alles wie im Bau vom
 * 24.09.2026 (eine Zeile, alle vier Knoepfe UND die Version, 292px,
 * `b130` bleibt dort unveraendert gruen — die Version verschwindet nur
 * unterhalb der Schwelle, die B130 gar nicht prueft).
 */
function IslandRedoKnopf() {
  const kannWiederholen = useProject((s) => s.history.canRedo);
  return (
    <KTooltip text="Zuletzt rückgängig gemachten Schritt wiederholen" lage="unten">
      <button
        onClick={() => useProject.getState().redo()}
        data-testid="island-redo"
        data-aussenklick-frei=""
        className="k-druck isl-kopf-zweit-knopf"
        disabled={!kannWiederholen}
        aria-label="Wiederholen"
      >
        <span className="isl-kopf-zweit-zeichen" aria-hidden="true">
          ↪
        </span>
      </button>
    </KTooltip>
  );
}

/**
 * Die zweite Gruppe, unmittelbar links neben dem vorhandenen
 * `island-einstellungen-kreis` (Owner-Entscheid 28.08.2026).
 *
 * `z-index: 42` in `island.css` ist DERSELBE Rang, den der Einstellungs-Kreis
 * daneben schon traegt (`.isl-einstellungen-kreis`, W0-Ebenentafel
 * INSEL_BUEHNENKOPF) — keine neue Stufe, keine Umordnung, kein Eintrag in der
 * Ebenentafel noetig: `tools/z-ebenen-gate.mjs` prueft die fuenf dort
 * governierten Selektoren, und dieser ist keiner davon (selbst nachgelesen,
 * Abschnitt «WARUM NUR FÜNF GOVERNIERTE ELEMENTE»).
 *
 * B82 #4 (`docs/AUFTRAG-B82-SECHS-VERDRAHTUNGEN.md`) haengt hier den
 * Rueckgaengig-Knopf an — NICHT an `InselGrundstreifen` (erster Entwurf,
 * verworfen). Grund, AM ECHTEN CHROMIUM GEMESSEN statt vermutet:
 * `InselGrundstreifen` traegt (Auftrag §4, s. dortiger Kommentar) bewusst
 * KEIN `z-index` — und `App.tsx` rendert es VOR `<main className="app-main">`
 * (Zeile 1176 vs. 1335). Ein Playwright-Klick auf einen dort platzierten
 * Testknopf lief 90 s in Timeout: `<canvas … data-engine="three.js…">
 * subtree intercepts pointer events` — der 3D-Viewport-Canvas (ebenfalls
 * ohne eigenen `z-index`, aber SPAETER im DOM) gewinnt die Malreihenfolge
 * und deckt den Knopf fuer jeden echten Klick zu. Derselbe Fund gilt damit
 * LATENT auch fuer die BESTEHENDEN `save-project`/`open-project`-Knoepfe in
 * `InselGrundstreifen` — nur hat sie bislang KEIN Test in der design-Station
 * (mit sichtbarem 3D-Viewport) tatsaechlich angeklickt (`k6-projektkontext.
 * spec.ts` prueft `save-project` auf der DATA-Station, ohne Canvas). Ausserhalb
 * des B82-Dateikreises liegt `InselGrundstreifen`s eigener Fix (Auftrag
 * verbietet ausdruecklich jeden `z-index`-Eingriff) — gemeldet statt
 * verschwiegen, nicht selbst repariert.
 *
 * `InselZweitgruppe` hat DAGEGEN LAENGST ein eigenes `z-index:42` (oben,
 * B76-Entscheid) und ist darum vom selben Fund NICHT betroffen — bestehende
 * `sync-toggle`/`starter-guide-start`-Klicks in Bestandsspecs beweisen das
 * bereits. Der Rueckgaengig-Knopf zieht hierher, OHNE dass diese Datei
 * irgendeinen `z-index`-Wert selbst aendert oder neu setzt (Auftrag §NICHT
 * TUN) — er erbt den bestehenden Rang seines neuen Elternteils.
 */
export function InselZweitgruppe({
  syncStatus,
  peers,
  syncOffen,
  version,
  onSyncToggle,
  onRundgang,
  chip,
}: InselZweitgruppeProps) {
  const waechterLage = useVerbindungsWaechter((z) => z.lage);
  return (
    <div
      className="isl-kopf-zweitgruppe"
      style={{ right: `${INSEL_ZWEITGRUPPE_RECHTS_PX}px` }}
      data-testid="island-kopf-zweitgruppe"
    >
      {/* Sync — bis B76 war `setSyncOpen` NUR aus dem Kopfbalken erreichbar
          (genau zwei Aufrufstellen, beide im `!bodenDockAusgeblendet`-Zweig).
          Die Sync-Leiste selbst rendert schon immer ausserhalb dieses Zweigs;
          es fehlte allein der Schalter. */}
      {chip ? (
        <button
          onClick={onSyncToggle}
          data-testid={chip.testid}
          className="k-druck isl-kopf-zweit-knopf"
          aria-pressed={syncOffen}
          aria-label={chip.label}
        >
          <Badge hue={CHIP_TON[chip.ton]}>{chip.text}</Badge>
        </button>
      ) : (
        <button
          onClick={onSyncToggle}
          data-testid="sync-toggle"
          className="k-druck isl-kopf-zweit-knopf"
          aria-pressed={syncOffen}
          aria-label="Sync-/Kopplungs-Leiste öffnen oder schliessen"
          title="Sync-/Kopplungs-Leiste (HomeStation)"
        >
          <Badge
            hue={
              syncStatus === 'live'
                ? 'var(--k-success)'
                : syncStatus === 'aus'
                  ? 'var(--k-ink-faint)'
                  : 'var(--k-warning)'
            }
          >
            {/* Befund 2 am Geraet (erg-20261002-lw-verbinden-nachzug-geraet.md):
                hier stand ein eigener Text — ohne «· bereit» und mit dem rohen
                Zustandsnamen («VERBINDE»). Jetzt derselbe Wortlaut wie der
                Chip im Kopfbalken (`syncChipText`, eine Quelle). */}
            {syncChipText(syncStatus, peers, waechterLage)}
          </Badge>
        </button>
      )}
      {/* Rundgang — Wortlaut/`title`/`aria-label`/`data-testid` woertlich wie
          im Kopfbalken (V1.6 Block E). */}
      {onRundgang && (
        <button
          onClick={onRundgang}
          data-testid="starter-guide-start"
          className="k-druck isl-kopf-zweit-knopf"
          title="Rundgang — Kosmo erklärt das Programm erneut"
          aria-label="Rundgang erneut starten"
        >
          <span className="isl-kopf-zweit-zeichen" aria-hidden="true">
            ?
          </span>
        </button>
      )}
      {/* Rueckgaengig — B82 #4, s. Kopfkommentar oben (warum HIER, nicht
          in `InselGrundstreifen`). ZWEITER, unabhaengiger Aufrufweg
          zu `useProject().undo()` NEBEN der bestehenden Zwei-Finger-
          Doppeltipp-Geste (`IslandShell.tsx`, `state/touch-undo.ts`,
          OWNER-OFFEN markiert und hier unangetastet) — kein Ersatz.
          `history.canUndo` deaktiviert den Knopf statt eines stillen
          No-op, wenn nichts rueckgaengig zu machen ist. Direkter
          Store-Zugriff statt einer neuen Prop: `InselZweitgruppe`
          bekommt ihre uebrigen Aktionen ueber Props aus `App.tsx`
          gereicht, das ausserhalb dieses B82-Dateikreises liegt
          (`modules/design/**`) — `useProject` ist ein Zustand-Store
          ohne Provider und braucht keinen neuen Aufrufer dort, genau
          wie `IslandShell.tsx`s `useZweiFingerUndoGeste()` schon. */}
      <IslandUndoKnopf />
      {/* Wiederholen — D2 (Bot-Fund U8, `docs/MESSUNG-UX-BOTLAUF-
          2026-09-23.md`), s. `IslandRedoKnopf`s Kopfkommentar oben. NEBEN
          Rueckgaengig, derselbe Store-Zugriffsweg. */}
      <IslandRedoKnopf />
      {/* Version — im Kopfbalken haengt `app-version` an der Wortmarke
          (`packages/kosmo-ui/src/Logo.tsx`, `<sup data-testid="app-version">`).
          Die Insel traegt keine Wortmarke (Owner: randfrei), darum hier als
          eigene, kleine Zeile mit demselben Testid-Vertrag. Unter 1200px
          `display:none` (`island.css`, `.isl-kopf-zweit-version`) — s.
          `IslandRedoKnopf`s Kopfkommentar oben fuer das «Warum genau
          dieses Kind weicht». */}
      <span className="isl-kopf-zweit-version" data-testid="app-version">
        {version}
      </span>
    </div>
  );
}
