import { z } from 'zod';
import {
  evaluiereGraph,
  exportGlb,
  exportIfc,
  istHimmelArt,
  isVisPresetId,
  pruefeGlasnaht,
  pruefeKamerahoehen,
  visPresetById,
  type AutoKameraStandpunkt,
  type HimmelArt,
  type KosmoDoc,
  type Sheet,
  type VisGraph,
} from '@kosmo/kernel';
import { STANDARD_BRIDGE_URL } from '@kosmo/ai';
import {
  RenderJob,
  BlenderSimJob,
  BakeJob,
  bridgeRoutes,
  unbekannteFelder,
  type BlenderSimArt,
} from '@kosmo/contracts';
import { melde, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { researchProfilAktiv } from '../../state/research-profil';
import { memoKey, useVisRuntime, type NodeLaufStatus } from './vis-runtime';
// P-BESCHEID (v0.9.33, B43 Teil 2 §10): der Urteilsspruch selbst ist eine
// reine Funktion in `bridge-bescheid.ts` — hier laeuft nur die Messung, die
// ihn fuettert. `pruefeBridge` ist die bestehende `/health`-Probe aus dem
// Heimserver-Modul; sie ist tokenfrei erreichbar und darum genau die
// Gegenprobe, die «laeuft die Bridge ueberhaupt?» beantworten kann.
import { bridgeBescheid, type BescheidLage } from './bridge-bescheid';
import { BRIDGE_TOKEN_KEY, pruefeBridge } from '../../state/home-server';

/**
 * Bridge-Jobs für KosmoVis (P2/HS3) — ein Weg für Graph UND Einfach-Ansicht:
 * Modell als GLB an /jobs (render-scene/v1), Status holen, Bild aufs Blatt.
 * Alle Antworten laufen durch den `@kosmo/contracts`-Vertrag (`safeParse` statt
 * blindem `as`-Cast); jeder Bridge-Fetch trägt den Token konditional.
 */

export type JobQa = NonNullable<RenderJob['result']>['qa'];
/** Der validierte Job-Record — der Vertrag ist die EINE Wahrheit (HS1). */
export type JobRecord = RenderJob;

/**
 * Typisierter HTTP-Fehler der Bridge (KLEIN 8). Ein blankes `new Error(status)`
 * verschluckt die Ursache: der Poll fängt es still weg und ein falscher Token
 * (401/403) tauchte früher NUR als 10-Minuten-Timeout auf. Mit dem `status`-Feld
 * kann der Aufrufer einen Auth-Fehler sofort von einem transienten Netzfehler
 * trennen und ehrlich anzeigen.
 */
export class BridgeHttpError extends Error {
  readonly status: number;
  constructor(status: number, kontext: string) {
    super(`${kontext}: ${status}`);
    this.name = 'BridgeHttpError';
    this.status = status;
  }
}

/** True, wenn der Fehler eine Ablehnung wegen Token/Rechten ist (401/403). */
export function istAuthFehler(err: unknown): err is BridgeHttpError {
  return err instanceof BridgeHttpError && (err.status === 401 || err.status === 403);
}

/**
 * True, wenn die konfigurierte Bridge-URL VERMUTLICH von der CSP
 * (`connect-src`) geblockt wird (KLEIN 9) — eine ehrliche VERMUTUNG, kein
 * Beleg (die App kann die CSP-Entscheidung selbst nicht beobachten, nur die
 * CSP-Regeln kennen und dagegen mustern). Seit v0.9.0 (Owner-Live-Befund
 * 22.07.2026) sind die HomeServer-Dienst-Ports 8600/8700/11434 host-offen
 * freigegeben (`index.html` + `tauri.conf.json`) — aber NUR über `http`
 * (`http://*:8600 http://*:8700 http://*:11434`, KEIN `https://*:8600`).
 * Die CSP kennt keine CIDR-Wildcards, darum Port-genau statt `http://*:*`
 * weit aufzureissen.
 *
 * v0.9.21 P-E (`docs/V0921-SPEZ.md` §3 P-E, `docs/BEFUND-FERNRENDER.md`
 * §2.3 Punkt 3): bis hierher prüfte diese Funktion NUR IPv4-Hostnamen auf
 * einem fremden Port — ein Azure-DNS-Name (z.B. eine
 * `*.cloudapp.azure.com`-Adresse) rutschte auf JEDEM Port unbemerkt durch
 * (der IPv4-Regex griff nie, die Funktion meldete "nicht geblockt"), und ein
 * `https`-Ziel wurde selbst auf Port 8600 fälschlich als "gedeckt" gemeldet,
 * weil der Port-Vergleich das Protokoll ignorierte. Beides hätte
 * `sendeGraphRenderAuftrag`s «Bridge nicht erreichbar»-Meldung (unten) an
 * der falschen Stelle suchen lassen — genau die Owner-Regel, die dieses
 * Paket behebt. Jetzt gilt für JEDEN Host (IPv4 oder DNS-Name): gedeckt ist
 * AUSSCHLIESSLICH `http` auf genau 8600/8700/11434 (plus `localhost`/
 * `127.0.0.1` auf jedem Port, wie bisher) — alles andere gilt als vermutlich
 * geblockt. **Nicht** geändert: die CSP selbst (Owner-Freigabe nötig,
 * `docs/AUSSENVERBINDUNGEN.md`) — nur die Diagnose, die an ihr misst.
 */
export function bridgeVermutlichCspGeblockt(): boolean {
  return urlVermutlichCspGeblockt(bridgeBase());
}

/**
 * Dieselbe Regel für eine BELIEBIGE URL — die eine Quelle, an der die
 * CSP-Vermutung im Code steht.
 *
 * Nachtrag 09.08.2026 (Matrix-Abnahme v0.9.21, Zelle C-9): P-E hat die Regel
 * oben repariert, aber die zweite, seit v0.9.0 ausdrücklich als
 * Schwesterfunktion dokumentierte Kopie in `shell/Diagnose.tsx`
 * (`istWahrscheinlichCspGeblockt`, ROADMAP 606) übersehen — sie trug beide
 * Fehler weiter (kein Protokoll-Vergleich, DNS-Namen blind durchgewunken)
 * und speiste damit eine nutzersichtbare Meldung im Selbstdiagnose-Panel.
 * Statt die Reparatur ein zweites Mal von Hand zu wiederholen, ist die
 * Handkopie hier aufgelöst: Diagnose importiert diese Funktion. Eine
 * Handkopie driftet still (Lehre 5 dieser Version) — zwei Kopien derselben
 * CSP-Regel sind der Beleg dafür.
 */
export function urlVermutlichCspGeblockt(url: string): boolean {
  try {
    const u = new URL(url);
    if (u.hostname === 'localhost' || u.hostname === '127.0.0.1') return false;
    const portHostOffenGedeckt = u.port === '8600' || u.port === '8700' || u.port === '11434';
    if (u.protocol === 'http:' && portHostOffenGedeckt) return false;
    return true;
  } catch {
    return false;
  }
}

export function bridgeBase(): string {
  return (localStorage.getItem('kosmo.bridge') ?? STANDARD_BRIDGE_URL).replace(/\/$/, '');
}

/**
 * Bridge-Token aus dem lokalen Speicher (`kosmo.bridge.token`). Ist die Bridge
 * token-geschützt und der Client sendet keinen Header, sperrt sie die eigene
 * App aus (HS1-Befund) — darum hängt `bridgeFetch` ihn an JEDEN Aufruf.
 */
export function bridgeToken(): string {
  return (localStorage.getItem('kosmo.bridge.token') ?? '').trim();
}

/**
 * V015-SPEZ P10, Fund VIS-U8-ZEITGRENZE: «die einzige Naht zur HomeStation
 * hat keine Zeitgrenze — 16 Aufrufer koennen unbegrenzt haengen.» Nachgemessen
 * (17.09.2026): `bridgeFetch` rief nacktes `fetch` ohne `signal`, alle 16
 * Aufrufer (`vis-jobs.ts` × 14, `state/auftragsbuch.ts` × 2) teilen sich diese
 * EINE Funktion. Das Muster existiert im Haus bereits (`App.tsx`s
 * `AbortSignal.timeout(2500)` fuer die `/raeume`-Sonde) — hier ist die
 * Sonde aber kein leichter Healthcheck, sondern traegt teils ein GLB-Modell
 * als Multipart-Upload (`jobs`-Erstellung, koennen mehrere MB sein). 30
 * Sekunden sind grosszuegig genug fuer einen Upload im LAN und trotzdem
 * ENDLICH — der Unterschied, um den es hier geht, ist «haengt kurz» gegen
 * «haengt fuer immer, bis der Tab geschlossen wird».
 */
const BRIDGE_ZEITGRENZE_MS = 30_000;

/** Ein Fetch mit konditionalem `X-Kosmo-Token`-Header — die einzige Naht.
 *  Traegt seit VIS-U8-ZEITGRENZE eine Zeitgrenze (`BRIDGE_ZEITGRENZE_MS`),
 *  ausser ein Aufrufer liefert selbst ein `signal` (kein heutiger Aufrufer
 *  tut das — Repo-Grep `grep -rn "signal" vis-jobs.ts auftragsbuch.ts` liefert
 *  0 Treffer ausserhalb dieser Stelle —, die Naht bleibt aber fuer einen
 *  kuenftigen eigenen AbortController offen, statt ihn zu ueberschreiben). */
export function bridgeFetch(pfad: string, init?: RequestInit): Promise<Response> {
  const token = bridgeToken();
  const headers = new Headers(init?.headers);
  if (token) headers.set('X-Kosmo-Token', token);
  return fetch(`${bridgeBase()}${pfad}`, {
    ...init,
    headers,
    signal: init?.signal ?? AbortSignal.timeout(BRIDGE_ZEITGRENZE_MS),
  });
}

/**
 * EIN gemeinsamer Status-Mapper (HS3) für beide Poll-Stellen — die frühere
 * Doppelung in NodeCanvas und VisWorkspace stirbt hier. Übersetzt den
 * Bridge-Job-Zustand ehrlich in den Client-Lebenszyklus.
 */
export function mappeJobStatus(record: { status: string; result?: unknown }): NodeLaufStatus {
  if (record.result) return 'fertig';
  switch (record.status) {
    case 'awaiting_approval':
      return 'wartetFreigabe';
    case 'queued':
      return 'wartetGpu';
    case 'running':
      return 'rendert';
    case 'done':
      return 'fertig';
    case 'error':
      return 'fehler';
    case 'cancelled':
      return 'abgebrochen';
    case 'kein-render-worker':
      // Matrix-C-1-Fund (v0.9.0): der ehrliche Worker-Status erreicht jetzt
      // die App (Vertrag erweitert) — als Fehler anzeigen, nie als Warten.
      return 'fehler';
    default:
      // Unbekannter/neuer Bridge-Status: ein Wartezustand ist ehrlicher als
      // «rendert» — wir behaupten keine laufende Rechnung (Fable-Auflage 7).
      return 'wartetGpu';
  }
}

/**
 * Backbones, die im Produktprofil gesperrt sind und nur im research-Profil
 * bestellt werden dürfen — EINE Liste für BEIDE Stellen, die sie brauchen:
 * das Gate in `postRenderJob` (wirft) und die Profil-Naht in
 * `sendeGraphRenderAuftrag` (setzt das Flag). Vorher stand `'flux-krea'` nur
 * als Literal im Gate; ein zweites Vorkommen wäre die Sorte Doppelwahrheit,
 * bei der eines Tages eines von beiden nachgeführt wird und das andere nicht.
 *
 * Inhalt = die Non-Commercial-Wahl aus der Lizenz-Sanierung 11.08.2026:
 * FLUX.1-Krea-dev (BFL-Lizenz, auch als GGUF). `flux2-klein` steht bewusst
 * NICHT hier — für das Modell gibt es überhaupt keinen Lizenz-Beleg im Repo
 * («vor Download klären», `docs/MODEL_DOWNLOAD_MANIFEST.md`), und ein
 * research-Schalter wäre dort eine Zusage, die niemand geprüft hat.
 */
const NUR_RESEARCH_BACKBONES = ['flux-krea'] as const;

function istNurResearchBackbone(backbone: string | undefined): boolean {
  return backbone !== undefined && (NUR_RESEARCH_BACKBONES as readonly string[]).includes(backbone);
}

/**
 * P-LEERSZENE (auftraege/von-homestation/auf-orbit-20260825-07.md Punkt 2,
 * `docs/MESSUNG-LEERSZENE-2026-08-25.md`) — Anzahl der GLB-tragenden
 * Bauteile im aktuellen Projekt. Dieselbe Summe, die `NodeCanvas.tsx` am
 * Modell-Node anzeigt («Szene: N Bauteile») — EINE Quelle statt einer
 * zweiten Handrechnung an jeder Sperr-Stelle, sonst laufen Anzeige und
 * Sperren-Begründung irgendwann auseinander (dieselbe Krankheit wie
 * `KosmoPanel.tsx`s zwei Effekte 20 Zeilen auseinander, ROADMAP 1093).
 *
 * Bewusst NICHT dasselbe wie `VisRenderAuftrag.hatSzene`
 * (`derive/visgraph.ts`): das prüft nur, ob eine Kante vom Modell-Node zum
 * `szene`-Port des Render-Nodes führt — reine Graph-Konnektivität,
 * unabhängig davon, ob das Projekt überhaupt Geometrie enthält. Gemessen
 * (MESSUNG 2 im obigen Bericht): ein verbundener Modell-Node bei 0
 * Bauteilen lässt `hatSzene` `true` werden UND schickt `exportGlb` eine
 * geometrielose GLB an die Bridge — die Sperre unten schliesst genau diese
 * Lücke, ohne `hatSzene` selbst anzufassen (der bestehende Kernel-Test
 * `kernel.test.ts:7043` bleibt damit unberührt gültig).
 *
 * P-GEOMETRIEZAEHLUNG (`docs/MESSUNG-FIXTUREGEOMETRIE-2026-08-25.md`,
 * `docs/MESSUNG-GEOMETRIEZAEHLUNG-2026-08-25.md`) — der Riegel zählte bis
 * hierher AUSSCHLIESSLICH `wall`/`slab`/`roof` und blockte damit legitime,
 * nicht-leere Szenen: ein `mass`-Volumenkörper («Massenstudien in der
 * Wettbewerbsphase», `design.volumenErstellen`s eigene Beschreibung) landet
 * genauso im GLB (`derive/scene.ts` `deriveEntity`/`deriveAll`,
 * `derive/gltf.ts` `KIND_LABEL['mass']`), wurde aber als «0 Bauteile»
 * gemeldet. Dieselbe Lücke traf `stair`/`ramp`/`column`/`beam`/`freemesh`/
 * `gelaender` — jede reine Treppen-/Rampen-/Stützen-/Unterzugs-/FreeMesh-/
 * Geländer-Szene ohne Wand/Decke/Dach.
 *
 * Die Liste unten ist jetzt VOLLSTÄNDIG deckungsgleich mit dem kind-Dispatch
 * von `deriveEntity` (`@kosmo/kernel`, `derive/scene.ts`) — den ELF
 * Entity-Arten, die dort je ein `GeometryArtifact` liefern (können).
 * `test/p-geometriezaehlung.test.ts` hält das PRO ART fest (ein Fixture je
 * Kind, `szeneBauteileAnzahl` UND `deriveAll` gegeneinander geprüft) — driftet
 * `deriveEntity` künftig um eine elfte Art, ohne dass diese Liste mitzieht,
 * reisst der Test, statt still zu driften (das Muster, an dem dieses Repo
 * schon dreimal verbrannt ist: ROADMAP 1015/1016/1017, alle drei
 * Zwillingslisten ohne Wache).
 *
 * NACHGEFUEHRT 11.09.2026 — die Deckungsgleichheit gilt ab sofort nur noch
 * FUER DIE ARTEN, nicht mehr fuer jedes einzelne Bauteil. Seit `meta.nurBild`
 * (model/entities.ts) ueberspringt `deriveAll` markierte Bauteile; diese
 * Zaehlung sieht sie weiterhin. Ein Haus mit 1642 als «nur Bild» markierten
 * Brettern zaehlt hier 1647 und in `deriveAll` 5.
 *
 * FUNKTIONAL BRICHT DAS NICHTS, und das ist der Grund, warum es so bleibt:
 * die GLB-Ausfuhr nimmt `deriveAllMitBilddetails` und traegt die markierten
 * Koerper mit — der Riegel «es ist etwas zum Rendern da» bleibt also richtig.
 * Falsch waere nur der Satz gewesen, dass die Zahlen gleich SIND. Er stand
 * hier, und er steht jetzt berichtigt hier. Genau dieses Muster ist gemeint,
 * wenn oben von den drei Zwillingslisten die Rede ist: nicht der Zahlenwert
 * hat gefehlt, sondern die Aussage darueber war stehengeblieben.
 *
 * WARUM NICHT EINFACH `deriveAll(doc).length` (der naheliegende, 100 % nicht-
 * driftende Weg — `deriveAll` IST die Menge, die `exportGlb` exportiert)?
 * GEMESSEN, nicht angenommen (`docs/MESSUNG-GEOMETRIEZAEHLUNG-2026-08-25.md`):
 * `doc.revision` ist EIN globaler Zähler (`model/doc.ts`) — JEDER Befehl
 * IRGENDWO in der App (auch ein verschobener Vis-Graph-Node, eine
 * Material-Auswahl) macht `deriveEntity`s Pro-Entity-Cache für JEDE Entity im
 * Doc ungültig. Diese Funktion läuft aber bei JEDEM React-Rendern von
 * `NodeCanvas.tsx`/`austausch.tsx` (beide abonnieren `revision`, laufen also
 * bei JEDEM Befehl irgendwo in der App neu, solange KosmoVis offen ist) UND
 * ein zweites Mal bei jedem `laeufe`-Poll-Tick, OHNE dass sich die Geometrie
 * geändert hätte. Gemessen am mitgelieferten Referenzprojekt «Testobjekt Lichthof» (7
 * Geschosse, 32 Wände, 139 Entities): `deriveAll` kostet dort **~18 ms
 * MEDIAN** je invalidiertem Aufruf (Wand-Gehrung `miterWallEnds` scannt für
 * JEDE Wand ALLE anderen Wände des Docs — O(Wandzahl) je Wand). An einem
 * synthetisch grösseren Modell (432 Wände) steigt das auf **~255 ms
 * MEDIAN** — eine Reparatur, die den Render-Riegel korrigiert und dabei
 * JEDEN Befehl in einem grösseren Projekt spürbar bremst, sobald KosmoVis
 * offen ist, wäre keine Reparatur, sondern eine neue, versteckte Bremse
 * (Auflage: «Eine Reparatur, die die Oberfläche zäh macht, ist keine»). Die
 * Kind-Zählung unten bleibt dagegen bei **< 0.02 ms** selbst am
 * Referenzprojekt «Testobjekt Lichthof» (reines `Map`-Durchlaufen, keine Extrusion, keine
 * Gehrungsrechnung) — kein Memo-Cache nötig, die billige Zählung ist schon
 * schnell genug, dass ein zusätzlicher Cache nur Komplexität ohne
 * messbaren Nutzen wäre.
 *
 * TERRAIN ZÄHLT BEWUSST NICHT MIT: `derive/scene.ts` liefert auch für
 * `terrain`-Entities ein `GeometryArtifact` (`deriveTerrainBaender`,
 * materialKey `'terrain'`) — eine reine Geländeszene (via
 * `design.terrainSetzen`, projektglobal, OHNE dass je eine Wand/Decke/o.ä.
 * existiert) exportiert also tatsächlich eine nicht-leere GLB. Terrain läuft
 * aber NICHT durch `deriveEntity`s kind-Dispatch (dort fehlt der `terrain`-
 * Zweig ganz — `deriveTerrainBaender` ist eine SEPARATE, projektglobale
 * Ableitung, kein Pro-Entity-Artefakt) und ist darum aus DIESER Zählung von
 * selbst aussen vor, ohne einen eigenen Ausschluss-Code. Bewusste
 * Produktentscheidung: der Meldungstext unten spricht von «Bauteilen», und
 * ein Geländeprofil ist architektonisch kein Bauteil, sondern der
 * Baugrund-Kontext dazu — wer nur Terrain gesetzt, aber noch nichts gebaut
 * hat, bekommt darum weiterhin «0 Bauteile», auch wenn die GLB technisch
 * nicht leer wäre. `test/p-geometriezaehlung.test.ts` belegt beide Seiten:
 * eine Nur-Terrain-Szene bleibt gesperrt UND `deriveAll` liefert für sie
 * trotzdem ein Artefakt (dokumentierte, keine stillschweigende Entscheidung).
 */
const GEOMETRIE_ARTEN_ANZAHL = (doc: KosmoDoc): number =>
  doc.byKind('wall').length +
  doc.byKind('slab').length +
  doc.byKind('mass').length +
  doc.byKind('roof').length +
  doc.byKind('stair').length +
  doc.byKind('ramp').length +
  doc.byKind('column').length +
  doc.byKind('beam').length +
  doc.byKind('freemesh').length +
  doc.byKind('gelaender').length +
  // ELFTE ART, 11.09.2026. Der Kommentar oben sagte woertlich voraus: «driftet
  // deriveEntity kuenftig um eine elfte Art, ohne dass diese Liste mitzieht,
  // reisst der Test, statt still zu driften.» Die elfte Art kam — und der Test
  // riss NICHT. Er ist eine handgepflegte Liste derselben zehn Arten und kann
  // eine elfte konstruktionsbedingt nicht sehen. Die Wache war blind gegen
  // genau den Fall, fuer den sie gebaut wurde.
  //
  // Gemessene Folge, bevor diese Zeile stand: ein Dokument mit NUR Moebeln
  // meldete «0 Bauteile» und sperrte den Renderknopf, waehrend deriveAll ein
  // Artefakt lieferte und die GLB-Ausfuhr nicht leer gewesen waere.
  doc.byKind('furniture').length;

export function szeneBauteileAnzahl(doc: KosmoDoc): number {
  return GEOMETRIE_ARTEN_ANZAHL(doc);
}

/**
 * EINE Textquelle für Sperre (Button-`disabled`/`title`) UND Melde-Toast
 * (Klick-Guard in `sendeGraphRenderAuftrag` unten) — dieselbe Begründung wie
 * `szeneBauteileAnzahl` oben: eine zweite Abschrift dieses Satzes würde
 * irgendwann von der ersten abweichen. Form folgt dem Muster, das der
 * Home-PC-Worker an `bridge-bescheid.ts` ausdrücklich gelobt hat (P-BESCHEID,
 * v0.9.33): Ursache benennen, Ort nennen, UND vor der falschen Reparatur
 * warnen (hier: nicht am Render-Node oder an der Bridge suchen).
 *
 * P-GEOMETRIEZAEHLUNG: die Aufzählung in Klammern spiegelt jetzt die elf
 * Arten aus `GEOMETRIE_ARTEN_ANZAHL` oben (nicht mehr nur Wände/Decken/
 * Dächer) — Terrain bewusst NICHT genannt, s. Kommentar dort. «Möbel» kam
 * am 11.09.2026 als elftes dazu: der Satz zählte die Arten auf, die der
 * Nutzer bauen kann, und liess ausgerechnet die Art weg, wegen der ein
 * Nur-Möbel-Dokument fälschlich «0 Bauteile» meldete. Ein Aufzählungstext,
 * der hinter der gezählten Menge zurückbleibt, schickt den Leser an die
 * falsche Stelle.
 */
export const KEINE_GEOMETRIE_HINWEIS =
  'Kein Render ohne Geometrie — die Szene hat 0 Bauteile (Wände/Decken/Dächer/' +
  'Volumenkörper/Treppen/Rampen/Stützen/Unterzüge/Geländer/FreeMesh/Möbel). ' +
  'Ursache: In KosmoDesign wurde noch nichts gebaut oder geladen. Befehlspalette ' +
  '(⌘K/Ctrl+K) → «Beispielprojekt Demohaus laden», danach zurück zu KosmoVis. ' +
  'Nicht am Render-Node oder an der Bridge suchen — Verbindung und Graph sind in ' +
  'Ordnung, es fehlt nur das Modell selbst.';

/**
 * Render-Job senden — Szene kommt aus dem Graphen (Prompt, Treue, Samples).
 * K20/A10: `presetId`/`resolution`/`sun`/`komposition` kommen NUR mit, wenn
 * der Render-Node ein Cycles-Preset trägt; `kameras` NUR, wenn ein
 * Auto-Kamera-Node verbunden ist — sonst bleibt der Job byte-identisch zum
 * bisherigen Stand (1600×1000, `cameras: 'auto'`, keine Sonne).
 */
/**
 * Faehrt der `interior`/IFC-Transport fuer DIESES Dokument? — die EINE
 * Bedingung, an beiden Stellen benutzt, die sie kennen muessen
 * (`postRenderJob` unten UND `istUeberDiesenWegBestellbar`s Aufrufer in
 * `NodeCanvas.tsx`), damit sie nie zwei verschiedene Antworten geben koennen
 * (dieselbe Begruendung wie am Kommentar unten — Zwillingslisten sind in
 * diesem Repo dreimal auseinandergelaufen, ROADMAP 1015/1016/1017).
 *
 * B117 SCHRITT 2 (Owner-Entscheid E57, 07.09.2026,
 * `docs/AUFTRAG-B117-DREI-PERSPEKTIVEN-EINE-GELIEFERT.md` Abschnitt 3a):
 * genau dann wahr, wenn das Dokument mindestens eine Zone traegt. Eine
 * Innenansicht ohne Zone waere eine Leitung ohne Ladung (Abschnitt 3a,
 * woertlich) — und `exportIfc` (`ifc/export.ts`) traegt Raeume als
 * `IfcSpace` nur, wenn Zonen im Dokument stehen (gemessen an der
 * Demohaus-Probe: 26 `IFCSPACE`, weil 26 Zonen uebernommen wurden,
 * `test/p-erg117-e2e-raeume-zu-zonen.test.tsx`, der Schritt-1-Beleg dieses
 * Pakets).
 */
export function interiorFaehrt(doc: KosmoDoc): boolean {
  return doc.byKind('zone').length > 0;
}

/**
 * Ist ein abgeleiteter Auto-Kamera-Standpunkt ueber DIESEN Render-Weg
 * bestellbar? — die EINE Wahrheit fuer Auftrag und Anzeige.
 *
 * P-DREISTANDPUNKTE (v0.9.46, ROADMAP 1074): «Innenraum» wird von
 * `deriveAutoKameras` zu Recht abgeleitet, war ueber diesen Weg aber nicht
 * bestellbar — er sendete immer `geometry.format:'glb'` und nie ein
 * `interior`-Feld, und Innenansichten haengen seit P-INTERIOR (1071) hart an
 * beidem. Ein mitgeschickter Innenraum-Standpunkt waere also eine Zusage
 * ohne den Riegel, der sie erlaubt.
 *
 * **B117 SCHRITT 2 (Owner-Entscheid E57):** der zweite Parameter
 * `interiorFaehrtHier` ist PFLICHT, KEIN Default — dasselbe Mittel wie
 * `UEBERNEHMBARE_SORTEN` in `ifc-import.ts:177`: der Typcheck zwingt jede
 * Aufrufstelle, sich BEWUSST zu entscheiden, statt sich auf einen stillen
 * Vorgabewert zu verlassen, der irgendwann falsch waere. «Innenraum» ist
 * bestellbar GENAU DANN, wenn `interiorFaehrtHier` wahr ist (aufgeloest
 * ueber `interiorFaehrt(doc)` oben) — «Eingang»/«Übersicht» bleiben immer
 * bestellbar, unabhaengig davon.
 *
 * **Warum das eine EXPORTIERTE Funktion ist und keine zwei gleichlautenden
 * Filter:** die Auftragsseite (`postRenderJob` unten) und die Anzeigeseite
 * (`NodeCanvas.tsx`, Kamera-Panel) muessen dieselbe Antwort geben, sonst
 * verspricht die Oberflaeche wieder etwas, das die Leitung nicht traegt —
 * genau der Befund, der dieses Paket ausgeloest hat. Handgepflegte
 * Zwillingslisten sind in diesem Repo dreimal auseinandergelaufen
 * (ROADMAP 1015, 1016, 1017), und jedes Mal war die wahre Zahl eine andere
 * als die gemeldete.
 */
export function istUeberDiesenWegBestellbar(standpunktName: string, interiorFaehrtHier: boolean): boolean {
  return standpunktName !== 'Innenraum' || interiorFaehrtHier;
}

/* ------------------------------------------------------------------ *
 * A2 · Vis-Bedienung, 16.09.2026 — Zeilen 50a und 51 der Abnahmeliste
 * ------------------------------------------------------------------ */

/**
 * ZEILE 50a — waehlbare Auflösungen. Die Liste ist bewusst kurz und jede
 * Zeile hat einen Grund; eine frei tippbare Zahl waere hier schlechter, weil
 * der ferne Renderer die Breite ohnehin auf ein Vielfaches von acht abrundet
 * (`kosmo_worker_comfyui.py`) und eine krumme Eingabe still etwas anderes
 * ergaebe als das Eingetippte.
 *
 * `[4000, 2667]` ist die Auflösung, in der das vom Owner angenommene Bild
 * gerechnet wurde (00-CHRONIK.md §6) — sie ist kein runder Wunsch, sondern
 * ein Messpunkt, und genau darum steht sie hier.
 */
export const AUFLOESUNGEN: readonly { readonly wert: readonly [number, number]; readonly text: string }[] = [
  { wert: [1600, 1000], text: '1600 × 1000 — bisherige Vorgabe' },
  { wert: [1920, 1200], text: '1920 × 1200 — Präsentation' },
  { wert: [2560, 1707], text: '2560 × 1707 — halbe Kante der vollen' },
  { wert: [4000, 2667], text: '4000 × 2667 — volle Auflösung des angenommenen Bildes' },
];

/**
 * ZEILE 51 — «brich ab und mach mir einer der in 10min durch ist, schreib
 * qualitaet runter». Die Zeile ist ohne Zahlen nicht bedienbar: «hohe
 * Qualität» gegen «schnell» zu stellen, ohne zu sagen, was das in Sekunden
 * heisst, ist eine Behauptung und keine Wahl.
 *
 * ES GIBT GENAU ZWEI GEMESSENE PUNKTE (00-CHRONIK.md §6, beide bei
 * 4000 × 2667 auf OPTIX):
 *   2048 Abtastungen → 775 Sekunden
 *    128 Abtastungen →  83 Sekunden
 *
 * Aus zwei Punkten folgt eine Gerade, mehr nicht. Sie lautet
 *   Zeit = 36,8667 s + 0,3604167 s je Abtastung
 * und trifft beide Messpunkte auf die Sekunde genau. Das feste Glied ist NICHT
 * erfunden, sondern die Folge davon, dass die Messpunkte nicht durch den
 * Ursprung gehen: rein proportional gerechnet kaeme fuer 128 Abtastungen
 * 48 Sekunden heraus statt der gemessenen 83. Wer hier proportional rechnet,
 * verspricht ein Drittel zu wenig Zeit.
 *
 * WAS DIESE RECHNUNG NICHT WEISS: sie ist an EINER Szene auf EINER Karte
 * gemessen. Eine andere Szene rechnet anders. Jede Zahl, die diese Funktion
 * ausser bei genau 128 und 2048 auf 4000×2667 liefert, ist eine SCHAETZUNG —
 * die Oberflaeche schreibt das auch so hin.
 */
const ZEIT_MESSPUNKTE = { klein: { s: 128, t: 83 }, gross: { s: 2048, t: 775 } } as const;
const ZEIT_REFERENZ_PIXEL = 4000 * 2667;
const ZEIT_JE_ABTASTUNG =
  (ZEIT_MESSPUNKTE.gross.t - ZEIT_MESSPUNKTE.klein.t) / (ZEIT_MESSPUNKTE.gross.s - ZEIT_MESSPUNKTE.klein.s);
const ZEIT_GRUNDLAST = ZEIT_MESSPUNKTE.klein.t - ZEIT_MESSPUNKTE.klein.s * ZEIT_JE_ABTASTUNG;

/**
 * Geschaetzte Rechenzeit in Sekunden. Die Grundlast (Szene aufbauen, BVH) wird
 * NICHT mit der Bildflaeche skaliert — nur der abtastungsabhaengige Teil, denn
 * nur der faellt je Bildpunkt an. Bei genau 4000 × 2667 und 128 bzw. 2048
 * Abtastungen kommen die beiden gemessenen Zahlen heraus, sonst eine Schaetzung.
 */
export function zeitschaetzungSekunden(abtastungen: number, aufloesung: readonly [number, number]): number {
  const flaechenfaktor = (aufloesung[0] * aufloesung[1]) / ZEIT_REFERENZ_PIXEL;
  return Math.round(ZEIT_GRUNDLAST + ZEIT_JE_ABTASTUNG * abtastungen * flaechenfaktor);
}

/** «775 s» als «12 min 55 s» — eine Minutenangabe liest sich, eine Sekundenzahl nicht. */
export function zeitText(sekunden: number): string {
  if (sekunden < 90) return `${sekunden} s`;
  const min = Math.floor(sekunden / 60);
  const rest = sekunden % 60;
  return rest === 0 ? `${min} min` : `${min} min ${rest} s`;
}

/**
 * Die waehlbaren Qualitaetsstufen. `gemessen: true` heisst: diese Zahl steht
 * so in der Chronik. Alles andere ist auf der Geraden oben hochgerechnet und
 * wird in der Oberflaeche als Schaetzung ausgewiesen — die Unterscheidung ist
 * der ganze Zweck dieser Zeile.
 */
export const QUALITAETSSTUFEN: readonly {
  readonly abtastungen: number;
  readonly name: string;
  readonly gemessen: boolean;
}[] = [
  { abtastungen: 128, name: 'schnell', gemessen: true },
  { abtastungen: 512, name: 'mittel', gemessen: false },
  { abtastungen: 1024, name: 'hoch', gemessen: false },
  { abtastungen: 2048, name: 'voll — wie das angenommene Bild', gemessen: true },
];

/**
 * ZEILE 56 — die Bildwerkzeuge zur Auswahl.
 *
 * ABGELEITET, NICHT ABGESCHRIEBEN. Die erste Fassung dieser Liste schrieb die
 * fünf Namen noch einmal aus — und `test/backbone-eine-liste.test.ts` hat
 * genau das gemeldet: «Ist eine sechste Handschrift entstanden, oder wurden
 * sie abgeleitet? Beides gehört angesehen — diese Zahl bitte bewusst
 * nachführen, nicht reflexhaft.» Die Zahl wurde NICHT nachgeführt. Statt
 * dessen:
 *
 * 1. `Bildwerkzeug` fällt aus der Parameterliste von `postRenderJob` — eine
 *    der bereits gezählten zwei Aufzählungen dieser Datei, keine neue.
 * 2. Die Texte liegen in einem `Record<Bildwerkzeug, …>`. Ein Record ist
 *    VOLLSTÄNDIG: kommt im Vertrag ein Backbone dazu, bricht hier die
 *    Typprüfung, bis er einen Namen bekommt. Eine Liste hätte dazu
 *    geschwiegen — genau die Drift, gegen die die Wache gebaut wurde.
 *
 * Die Lizenzangaben stammen aus `00-CHRONIK.md` §7 und dem Vertragskommentar
 * in `render-scene.ts`, nicht aus dem Gedächtnis.
 */
export type Bildwerkzeug = NonNullable<Parameters<typeof postRenderJob>[0]['backbone']>;

export const BILDWERKZEUG_TEXTE: Record<Bildwerkzeug, { readonly name: string; readonly hinweis: string }> = {
  'z-image-turbo': {
    name: 'Z-Image Turbo',
    hinweis: 'Vorgabe · Apache-2.0 · Tiefenkonditionierung am Gerät belegt',
  },
  sdxl: { name: 'SDXL / Juggernaut', hinweis: 'CreativeML Open RAIL++-M' },
  'flux2-klein': { name: 'FLUX.2 [klein]', hinweis: 'Apache-2.0' },
  qwen: {
    name: 'Qwen-Image-Edit',
    hinweis: 'Apache-2.0 · KEIN ControlNet — bearbeitet das Bild, statt der Geometrie zu folgen',
  },
  'flux-krea': {
    name: 'FLUX.1-Krea-dev',
    hinweis: 'NICHT kommerziell — nur im Forschungsprofil bestellbar, sonst weist der Auftrag ab',
  },
};

/** Die Werkzeuge in Anzeigereihenfolge — Schlüssel des Records, nichts Eigenes. */
export const BILDWERKZEUG_IDS = Object.keys(BILDWERKZEUG_TEXTE) as Bildwerkzeug[];

export function istBildwerkzeug(v: unknown): v is Bildwerkzeug {
  return typeof v === 'string' && Object.prototype.hasOwnProperty.call(BILDWERKZEUG_TEXTE, v);
}

/**
 * Liest die sechs Bedienwerte aus den persistenten Render-Node-Parametern.
 * REIN, damit sie prüfbar ist, und an EINER Stelle, damit Anzeige und Auftrag
 * nie auseinanderlaufen können (derselbe Grund wie bei
 * `istUeberDiesenWegBestellbar` oben — handgepflegte Zwillinge sind in diesem
 * Repo dreimal auseinandergelaufen).
 *
 * Jeder Wert ist EINZELN optional: wer nur die Auflösung stellt, ändert am
 * Rest nichts. Unsinnige gespeicherte Werte (Hand-Edit, alter Stand, fremder
 * Import) fallen still auf «nicht gesetzt» zurück, statt eine kaputte
 * Bestellung zu bauen — die gleiche Haltung wie `params ?? {}` bei Bug T4a.
 */
export function renderBedienungAusParams(params: Record<string, string | number | boolean>): {
  samples?: number;
  resolution?: readonly [number, number];
  sunDetails?: { staerke?: number; kelvin?: number; winkelGrad?: number };
  himmel?: { modell: HimmelArt; staerke: number; luftdichte: number; aerosoldichte: number; drehungGrad?: number };
  belichtung?: { belichtung: number; farbraum: 'AgX' | 'Filmic' | 'Standard' | 'Raw'; anmutung?: string };
  rauschschwelle?: number;
  backbone?: Bildwerkzeug;
} {
  const erg: ReturnType<typeof renderBedienungAusParams> = {};

  // ZEILE 51 — Abtastungen.
  const abt = params['abtastungen'];
  if (typeof abt === 'number' && Number.isFinite(abt) && abt >= 1) erg.samples = Math.round(abt);

  // ZEILE 50a — Auflösung, gespeichert als «BREITExHOEHE», weil ein
  // Node-Parameter nur Zahl/Text/Wahrheitswert trägt (`ParamWert`), kein Paar.
  const auf = params['aufloesung'];
  if (typeof auf === 'string') {
    const treffer = AUFLOESUNGEN.find((a) => `${a.wert[0]}x${a.wert[1]}` === auf);
    if (treffer) erg.resolution = treffer.wert;
  }

  // ZEILE 4 — Licht- und Bildwerte kommen als GANZES aus dem Preset, nie
  // einzeln von Hand: die vier Zahlen des angenommenen Bildes gehören
  // zusammen, und eine halb übernommene Belichtung wäre schlechter als keine.
  const presetRoh = params['preset'];
  if (isVisPresetId(presetRoh)) {
    const p = visPresetById(presetRoh);
    const { staerke, kelvin, winkelGrad } = p.render.sun;
    if (staerke !== undefined || kelvin !== undefined || winkelGrad !== undefined) {
      erg.sunDetails = {
        ...(staerke !== undefined ? { staerke } : {}),
        ...(kelvin !== undefined ? { kelvin } : {}),
        ...(winkelGrad !== undefined ? { winkelGrad } : {}),
      };
    }
    if (p.render.himmel) erg.himmel = { ...p.render.himmel };
    if (p.bild) erg.belichtung = { ...p.bild };
    if (p.render.rauschschwelle !== undefined) erg.rauschschwelle = p.render.rauschschwelle;
  }

  // ZEILE 47 — eine ausdrücklich gewählte Himmelsart schlägt die des Presets.
  const himmelArt = params['himmel'];
  if (istHimmelArt(himmelArt)) {
    const basis = erg.himmel ?? { modell: himmelArt, staerke: 1, luftdichte: 0.4, aerosoldichte: 3 };
    erg.himmel = { ...basis, modell: himmelArt };
  }

  // ZEILE 48 — Drehung wirkt NUR auf einen vorhandenen Himmel. Ohne Himmel
  // wird sie nicht mitgeschickt: eine Drehung von nichts ist keine Bestellung,
  // und ein Feld, das nichts bewirkt, ist schlechter als kein Feld
  // (`render-scene.ts`, Rückzug von `style.refs`).
  const drehung = params['umgebungDrehungGrad'];
  if (erg.himmel && typeof drehung === 'number' && Number.isFinite(drehung)) {
    erg.himmel = { ...erg.himmel, drehungGrad: Math.max(0, Math.min(360, drehung)) };
  }

  // ZEILE 56 — Bildwerkzeug.
  const bw = params['backbone'];
  if (istBildwerkzeug(bw)) erg.backbone = bw;

  return erg;
}

/* ------------------------------------------------------------------ *
 * A15 · Die Fremdnaht Bild, 17.09.2026 — was die Gegenseite WIRKLICH liest
 * ------------------------------------------------------------------ */

/**
 * Der gemessene Stand EINES Vertragsfeldes an der Naht zur Bildseite.
 *
 * - `gelesen` — die Gegenseite wertet das Feld aus. Am fremden Code oder an
 *   der abgehenden Befehlszeile nachgewiesen, nicht an einer Beschreibung.
 * - `nicht-gelesen` — das Feld reist mit und aendert am Bild nichts. Das ist
 *   die teuerste Lage, weil sie im Vertrag wie eine Faehigkeit aussieht
 *   («Die Attrappe», Muster 11).
 * - `ungeprueft` — niemand hat nachgesehen. Steht hier nur, solange die
 *   Messung wirklich aussteht; «ungeprueft» ist eine Auskunft, «vermutlich»
 *   waere keine.
 */
export type Fremdstand = 'gelesen' | 'nicht-gelesen' | 'ungeprueft';

export interface FremdnahtBefund {
  /** Pfad im Vertrag, wie er in `render-scene.ts` steht. */
  readonly feld: string;
  /** Wie das Feld an der Oberflaeche heisst. Der Architekt bestellt eine
   *  «Sonnenstaerke», keinen `render.sun.staerke` — und ein Hinweistext, der
   *  Vertragspfade aufzaehlt, wird nach dem zweiten Mal nicht mehr gelesen. */
  readonly titel: string;
  /** Zeile der 60-ABNAHMELISTE.md, die an diesem Feld haengt. */
  readonly zeile: string;
  readonly stand: Fremdstand;
  /** Tag der Messung — ein Befund ohne Datum altert unbemerkt. */
  readonly gemessenAm: string;
  /** WORAN gemessen wurde. Eine Stelle, die man nachlaufen kann. */
  readonly beleg: string;
}

/**
 * DIE MESSUNG VOM 17.09.2026 — wer auf der Bildseite welches Feld auswertet.
 *
 * **Warum diese Tabelle existiert und nicht bloss ein Satz im Hinweistext:**
 * Bis heute stand am Render-Knoten «ob der Cycles-Schritt auf der HomeStation
 * sie schon auswertet, ist von hier aus nicht zu pruefen». Das war 16.09.
 * ehrlich und ist es seit der Messung nicht mehr. Ein Satz altert still, eine
 * Tabelle mit Datum und Beleg nicht — und die Probe
 * `a15-fremdnaht-bild.test.ts` zaehlt nach, dass JEDES Feld, das
 * `renderBedienungAusParams` erzeugen kann, hier einen Eintrag hat. Wer ein
 * siebtes Bedienelement baut und die Messung vergisst, bekommt Rot statt
 * einer stillen Bestellung.
 *
 * **WIE gemessen wurde** (der Weg ist wiederholbar, darum steht er hier):
 * Die Nutzlast, die `postRenderJob` heute baut, wurde durch den echten Leser
 * der Gegenseite geschickt — `aiimaging.kosmo_szene.lies_szene` im Repo
 * `ai-imaging-in-a-box` — und von dort weiter durch
 * `aiimaging.seams._multipass_argumente`, die Funktion, die die Befehlszeile
 * fuer Blender baut. Gezaehlt wurde dann, welcher bestellte Wert in dieser
 * Befehlszeile vorkommt. Die Probe kann widersprechen: `azimuth` (200.0) und
 * `elevation` (32.0) stehen dort, `staerke` (6.0), `kelvin` (4900) und
 * `winkelGrad` (0.62) stehen nicht.
 *
 * **ES GIBT ZWEI GEGENSEITEN, und das ist der eigentliche Befund.**
 *  1. Der KosmoVis-Worker (`ai-imaging-in-a-box`) liest unseren Vertrag —
 *     und kennt von `render` nur `resolution`, `samples`, `faithful` und den
 *     Sonnen-STAND. Seine eigene Tabelle `DURCHGEREICHT`/`STEHENGEBLIEBEN`
 *     sagt das selbst, und die Messung bestaetigt sie.
 *  2. Das Cycles-Werkzeug der HomeStation (`~/kosmo-render/werkzeug/
 *     render_lauf.py`, das Werkzeug des Renderprojekts vom 10.09.) HAT die
 *     Schalter `--sonne-staerke` und `--sonne-farbe` und rechnet die Ebenen
 *     standardmaessig mit (`--ohne-passes` schaltet sie ab). Es liest aber
 *     **keinen Vertrag**: `grep -rl 'render-scene'` ueber jenen Ordner
 *     findet null Treffer, und `grep -rl 'render_lauf'` ueber beide Repos
 *     und den Ordner selbst findet ausser der Datei, ihrer Anleitung und
 *     vier Laufprotokollen **keinen Aufrufer**. Es wird von Hand gestartet.
 *
 * Daraus folgt der Satz, der diese Welle traegt: **der Empfaenger fehlt nicht,
 * er ist nicht angeschlossen.** Ein neues Vertragsfeld wuerde daran nichts
 * aendern — es waere die vierte stille Bestellung (Muster 15).
 */
export const FREMDNAHT: readonly FremdnahtBefund[] = [
  {
    feld: 'render.resolution',
    titel: 'Auflösung',
    zeile: '50a',
    stand: 'gelesen',
    gemessenAm: '17.09.2026',
    beleg:
      'lies_szene liefert «aufloesung»/«hoehe»; beides steht in der Blender-Zeile ' +
      '(--aufloesung 4000, --hoehe 2656 — auf ein Vielfaches von 16 abgerundet, und das meldet die Gegenseite).',
  },
  {
    feld: 'render.samples',
    titel: 'Abtastungen',
    zeile: '51',
    stand: 'gelesen',
    gemessenAm: '17.09.2026',
    beleg: 'lies_szene liefert «samples»; steht als --samples 2048 in der Blender-Zeile.',
  },
  {
    feld: 'render.sun.azimuth',
    titel: 'Sonnenrichtung',
    zeile: '46',
    stand: 'gelesen',
    gemessenAm: '17.09.2026',
    beleg: 'steht als --sonne-azimut=200.0 in der Blender-Zeile (seams._multipass_argumente).',
  },
  {
    feld: 'render.sun.elevation',
    titel: 'Sonnenhöhe',
    zeile: '46',
    stand: 'gelesen',
    gemessenAm: '17.09.2026',
    beleg: 'steht als --sonne-hoehe=32.0 in der Blender-Zeile (seams._multipass_argumente).',
  },
  {
    feld: 'render.sun.staerke',
    titel: 'Sonnenstärke',
    zeile: '46',
    stand: 'nicht-gelesen',
    gemessenAm: '17.09.2026',
    beleg:
      'kommt bei lies_szene im Block «sonne» an und geht dort nicht weiter: seams._multipass_argumente ' +
      'reicht aus dem Sonnenblock NUR elevation/azimuth/konvention durch, und blender_depth_stage.py hat ' +
      'keinen Schalter dafuer. Das Cycles-Werkzeug der HomeStation hat einen (--sonne-staerke), liest aber keinen Vertrag.',
  },
  {
    feld: 'render.sun.kelvin',
    titel: 'Farbtemperatur',
    zeile: '46',
    stand: 'nicht-gelesen',
    gemessenAm: '17.09.2026',
    beleg:
      'wie staerke. Gegenstueck auf der HomeStation waere --sonne-farbe (Planck-Naeherung in render_lauf.py), unverbunden.',
  },
  {
    feld: 'render.sun.winkelGrad',
    titel: 'Sonnenwinkel',
    zeile: '46',
    stand: 'nicht-gelesen',
    gemessenAm: '17.09.2026',
    beleg:
      'wie staerke — und hier gibt es nicht einmal drueben einen Schalter: render_lauf.py setzt den ' +
      'Sonnenwinkel FEST auf 0.62 Grad (daten.angle = math.radians(0.62)). Von den drei Sonnenzahlen ist ' +
      'diese die einzige, die auch bei angeschlossener Naht noch Arbeit drueben braeuchte.',
  },
  {
    feld: 'render.himmel',
    titel: 'Himmel',
    zeile: '47/48',
    stand: 'nicht-gelesen',
    gemessenAm: '17.09.2026',
    beleg:
      'taucht in lies_szene gar nicht erst auf — die Gegenseite liest render feldweise mit .get() und ' +
      'beanstandet Unbekanntes nicht. render_lauf.py haette --himmel-staerke/--luft/--staub, ist aber unverbunden.',
  },
  {
    feld: 'render.belichtung',
    titel: 'Belichtung',
    zeile: '4',
    stand: 'nicht-gelesen',
    gemessenAm: '17.09.2026',
    beleg:
      'wie himmel: nicht in lies_szene. Gegenstueck auf der HomeStation waere --belichtung/--look/--farbraum, unverbunden.',
  },
  {
    feld: 'render.rauschschwelle',
    titel: 'Rauschschwelle',
    zeile: '51',
    stand: 'nicht-gelesen',
    gemessenAm: '17.09.2026',
    beleg:
      'wie himmel: nicht in lies_szene. Drueben steckt die Rauschschwelle in den Profilen DRAFT/PREVIEW/' +
      'PRODUCTION/FINAL von render_lauf.py, nicht in einem eigenen Schalter.',
  },
  {
    feld: 'vis.backbone',
    titel: 'Bildwerkzeug',
    zeile: '56',
    stand: 'gelesen',
    gemessenAm: '17.09.2026',
    beleg: 'lies_szene liefert «backbone» und die Gegenseite weist unbekannte Werte als Mangel ab (backbone_von_fremd).',
  },
];

/** Nachschlagen, gemessen — `undefined` heisst «steht nicht in der Tabelle». */
export function fremdnahtBefund(feld: string): FremdnahtBefund | undefined {
  return FREMDNAHT.find((f) => f.feld === feld);
}

/**
 * Die Felder, die mitreisen und drueben nichts bewegen — in Vertragsschreibweise.
 * Gezaehlt aus der Tabelle, nie von Hand gepflegt: eine zweite Liste waere
 * genau der Zwilling, der in diesem Repo dreimal auseinandergelaufen ist.
 */
export function fremdnahtNichtGelesen(): readonly string[] {
  return FREMDNAHT.filter((f) => f.stand === 'nicht-gelesen').map((f) => f.feld);
}

/**
 * Der Satz, der am Render-Knoten steht. Er wird GERECHNET, nicht getippt —
 * wer die Tabelle aendert, aendert die Oberflaeche mit, und andersherum kann
 * die Oberflaeche nichts behaupten, was nicht gemessen ist.
 *
 * DIE LAENGE IST EINE BEDINGUNG, KEINE GESCHMACKSFRAGE: dieser Text steht in
 * der Zeile `zusatz-ehrlichkeit`, und das Zeilenregister in `NodeCanvas.tsx`
 * gibt ihr 106 px. Der Satz, der bis zum 17.09.2026 dort stand, war 275
 * Zeichen lang; dieser bleibt darunter. Waere er laenger, saehe der Knoten
 * unveraendert tadellos aus und schnitte den Schluss ab — genau der Befund
 * vom 17.09. (93 px ausserhalb des gezeichneten Rahmens, von niemandem
 * gemeldet). Darum die Anzeigenamen und nicht die Vertragspfade.
 */
export function fremdnahtSatz(): string {
  const gelesen = FREMDNAHT.filter((f) => f.stand === 'gelesen').length;
  const offen = FREMDNAHT.filter((f) => f.stand === 'nicht-gelesen');
  const tag = FREMDNAHT[0]?.gemessenAm ?? '';
  return (
    `Gemessen ${tag}: die Bildseite wertet ${gelesen} von ${FREMDNAHT.length} Auftragsfeldern aus. ` +
    `${offen.length} reisen mit und ändern am Bild nichts — ${offen.map((f) => f.titel).join(', ')}.`
  );
}

/**
 * Was am fertigen Bild verlangt wurde und heute keinen Empfaenger hat —
 * Zeilen 50b/53/57/58/59 der Abnahmeliste. Hier stehen KEINE Bedienelemente,
 * und das ist der Punkt: ein Knopf mit dem Wort «Maske» daneben waere die
 * Attrappe, vor der Muster 11 warnt. Ein Satz, der sagt was fehlt und warum,
 * ist keine.
 */
export interface BildwegOffen {
  readonly zeile: string;
  readonly was: string;
  readonly warum: string;
}

export const BILDWEG_OFFEN: readonly BildwegOffen[] = [
  {
    zeile: '50b',
    was: 'Alle Ebenen (Passes) mit ausgeben',
    warum:
      'Der Vertrag hat kein Feld dafuer, und der Rueckweg traegt es nicht: die Gegenseite legt je Kamera ' +
      'genau EIN Bild in «images» (das KI-Bild). Tiefe, Schoenbild und Material-ID rechnet sie, behaelt sie aber.',
  },
  {
    zeile: '53',
    was: 'Stil aus Referenzbildern uebernehmen',
    warum:
      'Beide Seiten warten aufeinander: unser Feld style.refs wurde am 04.09.2026 zurueckgezogen, weil es ' +
      'niemand las — drueben steht es bis heute in der Liste «stehengeblieben», samt der Frage, auf welchem ' +
      'Weg fremde Referenzbilder ueberhaupt ankommen sollen. Die Frage ist an uns gestellt und unbeantwortet.',
  },
  {
    zeile: '57',
    was: 'Etwas nachtraeglich ins fertige Bild setzen (Inpainting)',
    warum:
      'UNSERE HAELFTE STEHT SEIT DEM 21.09.2026 (`bild/bereich.ts`): der Bearbeitungsbereich samt weicher ' +
      'Kante, als PNG-Maske weitergebbar. Was fehlt, ist DRUEBEN und nur dort — im ganzen Repo der ' +
      'Bildseite gibt es das Wort «inpaint» nicht ein einziges Mal, und ihr Bildauftrag (RenderAuftrag) ' +
      'hat kein Feld fuer Maske oder Ausbesserung. Wir koennen es nicht von uns aus hinzufuegen: sie ' +
      'weisen seit auf-20260911-103 jede Bestellung mit unbekannten Feldern ab, und das zu Recht. ' +
      'Bestellt als auf-orbit-20260921-01.',
  },
  {
    zeile: '58',
    was: 'Einen Bereich vorgeben, ausserhalb dessen nichts angefasst wird',
    warum:
      'Dieselbe Lage wie 57, und dieselbe Vorlage: Der Bereich ist gebaut (Rechteck, Bauteil oder ganzes ' +
      'Bild, mit Uebergang), er hat eine Maske, und sie ist ein echtes PNG. Die Bildseite hat zwar ein ' +
      'Maskenmodul — es trennt aber Bauwerk von Gelaende, um die Geometrie zu MESSEN, und fuehrt nirgends ' +
      'in den Bildschritt hinein.',
  },
  {
    zeile: '59',
    was: 'Im Bild die Flaeche eines bestimmten Bauteils finden',
    warum:
      'ERLEDIGT AM 21.09.2026, und zwar OHNE die Bildseite: `derive/bauteilmaske.ts` rechnet die Flaeche ' +
      'aus der eigenen Geometrie. Der aeltere Eintrag hier sagte, es fehle der Rueckweg zum Material-ID-Pass ' +
      'des Workers — das stimmte und war der teurere Weg. Wer die Zugehoerigkeit selbst rechnen kann, ' +
      'braucht sie nicht zurueckgeschickt.',
  },
];

export async function postRenderJob(params: {
  prompt: string;
  faithful: number;
  samples: number;
  nurCycles?: boolean;
  resolution?: readonly [number, number];
  sun?: { azimuth: number; elevation: number; staerke?: number; kelvin?: number; winkelGrad?: number };
  komposition?: { seitenverhaeltnis: number; brennweiteMm: number; horizontlinie: number };
  /**
   * ZEILE 47/48 (60-ABNAHMELISTE.md) — gerechneter Himmel als Hintergrund UND
   * Lichtquelle, samt Drehung um die Hochachse. Spiegelt `RenderScene.render.
   * himmel` eins zu eins. Kommt NUR mit, wenn ein Himmel gewaehlt ist — ohne
   * Wahl bleibt die Nutzlast Zeichen fuer Zeichen wie bisher.
   */
  himmel?: {
    modell: HimmelArt;
    staerke: number;
    luftdichte: number;
    aerosoldichte: number;
    drehungGrad?: number;
  };
  /**
   * ZEILE 4 — Belichtung/Farbraum/Anmutung (Farbverwaltung, wirkt NACH dem
   * Rechnen). Spiegelt `RenderScene.render.belichtung`.
   */
  belichtung?: { belichtung: number; farbraum: 'AgX' | 'Filmic' | 'Standard' | 'Raw'; anmutung?: string };
  /** ZEILE 51 — Cycles-Rauschschwelle, spiegelt `RenderScene.render.rauschschwelle`. */
  rauschschwelle?: number;
  kameras?: AutoKameraStandpunkt[];
  /**
   * PC1 (`docs/V084-SPEZ.md` §5 W2, C-17) — additiv, spiegelt den seit W0
   * erweiterten `render-scene/v1`-Vertrag (`kosmo-contracts` `render.
   * environment`, E4). Kommt NUR mit, wenn die STIMMUNG-Insel einen Preset
   * gewählt hat — ohne Auswahl bleibt der Job byte-identisch zum bisherigen
   * Stand (kein `environment`-Feld, wie vor v0.8.4).
   */
  environment?: { preset: 'morgen' | 'abend' | 'weiss' };
  /**
   * v0.8.4 PC2 (`docs/V084-SPEZ.md` E6/C-18) — additiv, spiegelt
   * `kosmo-contracts` `RenderScene.cameras`s Literal-Modi. Kommt NUR zum
   * Tragen, wenn KEIN `kameras`-Array vorliegt (ein Auto-Kamera-Node am
   * Render-Node gewinnt weiterhin, wie bisher) UND explizit `'saved'`
   * gewählt ist — ohne diesen Parameter bleibt der Job byte-identisch zum
   * bisherigen Stand (`cameras: 'auto'`).
   */
  kameraWahl?: 'auto' | 'saved';
  /**
   * v0.8.4 PC2 — additiv, spiegelt `RenderScene.vis.backbone`.
   *
   * Modell-Lizenz-Sanierung 11.08.2026 (Advisor-Auftrag Phase 2): `'flux-krea'`
   * (FLUX.1-Krea-dev, BFL-Lizenz NON-COMMERCIAL, auch als GGUF) ist nur noch
   * mit explizitem `researchOnly: true` bestellbar — sonst wirft dieser Weg
   * einen sprechenden Fehler, der als ehrlicher Node-Fehlerzustand sichtbar
   * wird (kein stilles Umbiegen auf ein anderes Modell).
   * Profile: `docs/MODEL_DOWNLOAD_MANIFEST.md`.
   *
   * HOMESTATION-BEFUND 12 (19.08.2026): die Vorgabe war `'qwen'` — ein
   * Backbone, der die Tiefenkonditionierung am Geraet gemessen gar nicht
   * kann. Sie ist jetzt `'z-image-turbo'`, ausgeschrieben unten am
   * `??`-Rueckfall. **Der Job ist damit NICHT mehr byte-identisch zum Stand
   * davor**, und das ist der Zweck: der alte Wert erzeugte Bildbearbeitung
   * statt tiefenkonditioniertem Rendern. Alle bisherigen Werte bleiben
   * gueltig, keiner entfaellt.
   */
  backbone?: 'z-image-turbo' | 'qwen' | 'flux2-klein' | 'flux-krea' | 'sdxl';
  /**
   * Explizites research-Flag (Lizenz-Sanierung 11.08.2026): erforderlich für
   * Non-Commercial-Backbones (`'flux-krea'`), landet als `vis.research_only`
   * im Vertrag (`RenderScene`). Nie Default — eine bewusste Forschungs-
   * Entscheidung je Auftrag, kein Produktpfad.
   */
  researchOnly?: boolean;
  /**
   * v0.8.9 §9 E9/E10 (Line-Art, `docs/V089-SPEZ.md`) — additiv, spiegelt
   * `RenderScene.style.mode`s neuen Wert `'lineart'`. Ohne Parameter bleibt
   * der Job byte-identisch zum bisherigen Stand (`mode: 'none'`, wie vor
   * v0.8.9). Der Vertragskommentar (`render-scene.ts`) ist hier bindend:
   * «jeder Client, der `mode:'lineart'` sendet, MUSS zugleich `vis.skip:true`
   * setzen — eine Strichzeichnung wartet nie auf einen KI-Veredelungs-
   * Schritt.» Darum HART erzwungen (nicht optional/überschreibbar durch
   * `nurCycles`): eine Strichzeichnung ist Cycles/Freestyle-Rendering, kein
   * KI-Stil-Transfer, egal was `nurCycles` sagt.
   *
   * v0.8.11 Z4: `sendeGraphRenderAuftrag` leitet diesen Wert seither aus dem
   * persistenten `node.params.lineart` ab (statt einem transienten
   * `opts.mode`) — dieser Parameter hier bleibt unverändert die einzige Naht
   * zur Bridge, nur die Quelle beim EINEN Aufrufer hat sich verschoben.
   */
  mode?: 'none' | 'lineart';
}): Promise<JobRecord> {
  // Lizenz-Gate (Sanierung 11.08.2026): der Non-Commercial-Backbone ist ohne
  // explizites research-Flag NICHT bestellbar. Der Fehler wandert über den
  // bestehenden catch-Weg als ehrlicher Node-Fehlertext in die UI.
  if (istNurResearchBackbone(params.backbone) && params.researchOnly !== true) {
    // v0.9.28 P-AUF Posten 3: der Text nennt jetzt auch den WEG. Vorher sagte
    // er nur, dass es das research-Profil braucht — nicht, dass es in dieser
    // App einen Schalter dafür gibt; wer den Auftrag gestellt hat, blieb mit
    // einer Sackgasse zurück.
    throw new Error(
      `Backbone «${params.backbone}» (FLUX.1-Krea-dev) ist non-commercial und nur im research-Profil ` +
        '(research_only) bestellbar — Produkt-Wahl ist «z-image-turbo». Einschalten: Einstellungen → ' +
        'Modell-Lizenzen → «research-Profil». Zusätzlich muss der HomeStation-Worker mit ' +
        '--research-only laufen — er erzwingt das Laden, nicht diese App. ' +
        'Siehe docs/MODEL_DOWNLOAD_MANIFEST.md.',
    );
  }
  const { doc } = useProject.getState();
  // B117 SCHRITT 2 (Owner-Entscheid E57): die EINE Bedingung, ob dieser
  // Auftrag als IFC/`interior` geht oder byte-identisch zum Stand vor
  // Schritt 2 bleibt (glb, kein `interior`, «Innenraum» gefiltert).
  const interiorMoeglich = interiorFaehrt(doc);
  // P-GLASNAHT: DER LETZTE PUNKT IN DIESER LANE, an dem die Datei noch in
  // der Hand ist — danach ist sie ein Auftrag an die Bridge und kostet
  // GPU-Zeit. Gemessen an der ausgeführten glb des Demolaufs vom
  // 02.09.2026: 700 Fenster in der Quelle, 3 Materialien, ausnahmslos
  // OPAQUE — vier Läufe lang hat das niemand bemerkt, weil an keiner Stelle
  // jemand gefragt hat, ob die Scheibe angekommen ist.
  //
  // GEMELDET, NICHT ABGEBROCHEN: dieselbe Linie wie beim Massstabs- und
  // beim Modellstands-Befund der Bildseite. Wie oft dieser Riegel an echten
  // Projekten anschlägt, ist ungemessen; ein Riegel ohne bekannte
  // Fehlalarmrate lehnt Aufträge ab, und niemand weiss welche. Der Befund
  // steht damit im Protokoll — wer ihn zum Abbruch machen will, hat dann
  // Zahlen dafür.
  //
  // B117 SCHRITT 2, GEMELDETE LUECKE (nicht entschieden, s. Bericht): faehrt
  // `interior`, geht das Modell als IFC — `pruefeGlasnaht` misst aber auf
  // GLB-Bytes (`derive/gltf.ts`), die dieser Zweig nicht mehr erzeugt. Der
  // Riegel wird HIER NICHT still uebersprungen: er meldet sich im Protokoll
  // mit Grund, im selben `console.warn`-Stil wie sein eigener Fehlschlag
  // unten, bis der Owner zwischen den im Bericht genannten Optionen
  // entschieden hat (zusaetzlicher GLB-Export NUR fuer die Pruefung, oder
  // Auslassen mit protokolliertem Grund — genau das, was hier bis dahin
  // passiert).
  // Y3 P-IFC-BESTELLUNG-Muster (`bake-auftrag.ts:103/116`, woertlich
  // uebernommen): `modell` traegt entweder die glb-Bytes oder den IFC-Text,
  // `dateiname`/`mimeTyp` (unten am `form.append`) folgen derselben Wahl.
  // ENTSCHEID 19.09.2026 (B117 Schritt 2) — DER RIEGEL LAEUFT AUF BEIDEN WEGEN.
  // `pruefeGlasnaht` misst auf GLB-Bytes; der IFC-Weg erzeugt keine. Ein
  // Formatwechsel haette den Riegel also lautlos mitgenommen — und genau
  // diese Klasse hat auf dem GLB-Weg schon einmal vier Laeufe lang eine
  // fehlende Verglasung durchgelassen (s. P-GLASNAHT oben). Darum wird fuer
  // die PRUEFUNG auch im IFC-Fall zusaetzlich glb exportiert, gesendet wird
  // trotzdem der IFC-Text.
  //
  // Der Preis ist benannt und angenommen: ein zweiter Export je
  // Innenraum-Auftrag, also feste Rechenzeit und waehrend des Exports
  // doppelter Speicher — spuerbar bei grossen Modellen. Dagegen steht ein
  // unbekanntes Loch genau der Art, gegen die dieser Riegel gebaut wurde,
  // neben einem Renderlauf, der auf der Gegenseite 775 Sekunden kostet. Eine
  // bekannte Rechenzeit schlaegt ein unbekanntes Loch.
  let modell: ArrayBuffer | string;
  {
    const glb = exportGlb(doc, doc.settings.projectName);
    const glasnaht = pruefeGlasnaht(glb);
    if (glasnaht.urteil !== 'traegt') {
      console.warn(
        `[Glasnaht ${glasnaht.urteil}] ${glasnaht.grund} ` +
          `(gemessen: ${glasnaht.gemessen.nMaterialien} Materialien, ` +
          // V7 «Materialweg»: der Riegel misst seit dem Durchlass ZWEI Wege
          // (Alpha-Mischung und `KHR_materials_transmission`). Stünde hier
          // weiter nur die BLEND-Zahl, meldete das Protokoll bei einem
          // «zurueck» die halbe Messung — und die zweite Zahl wäre genau die,
          // die dann fehlt.
          `${glasnaht.gemessen.nBlend} durchsichtig, ${glasnaht.gemessen.nDurchlass} lichtdurchlaessig, ` +
          `Quelle-Fenster: ${glasnaht.gemessen.ifcFenster ?? 'unbekannt'})`,
      );
    }
    // Gesendet wird je nach Weg — geprueft wurde in beiden Faellen dasselbe
    // Modell, nur in der Darstellung, die der Riegel lesen kann.
    modell = interiorMoeglich ? exportIfc(doc) : glb;
  }
  // P-DREISTANDPUNKTE (HomeStation-Befund, auftraege/von-homestation/
  // auf-orbit-20260821-01.md, Auftrag 3) — SEIT B117 SCHRITT 2 FALLABHAENGIG:
  // `deriveAutoKameras` liefert «Innenraum» (bei vorhandenen Zonen) als
  // Standpunkt INNERHALB des Gebäudes. Innenansichten sind seit P-INTERIOR
  // (ROADMAP 1071) an `interior`/IFC gebunden (superRefine, `kosmo-contracts`
  // `render-scene.ts`: ohne `geometry.format:'ifc'` wird eine Innenansicht-
  // Bestellung hart abgewiesen). Der Filter selbst bleibt bestehen — er
  // faellt nicht durch Entfernen weg, sondern dadurch, dass `interiorMoeglich`
  // (oben) jetzt wahr sein KANN: `istUeberDiesenWegBestellbar` laesst
  // «Innenraum» GENAU DANN durch. Eingang/Übersicht sind Aussenstandpunkte
  // und bleiben unberührt.
  const kamerasOhneInnenraum = params.kameras?.filter((k) => istUeberDiesenWegBestellbar(k.name, interiorMoeglich));
  const kameras = kamerasOhneInnenraum && kamerasOhneInnenraum.length > 0 ? kamerasOhneInnenraum : undefined;
  // B117 Weg B — Uebergangs-Sichtbarkeit (Owner-Entscheid E57, docs/AUFTRAG-
  // B117-DREI-PERSPEKTIVEN-EINE-GELIEFERT.md Abschnitt 3a Schritt 3; Anatomie
  // docs/UI-UX-2026-09-06-B117-DREI-PERSPEKTIVEN.md §4). BEFUND VIS-B117-
  // INNENRAUM: die Zeile oben liess die Kameraliste bisher STUMM schrumpfen —
  // kein `melde(...)`, keine Zahl. EIN Hinweis, MIT Zahl, MIT Grund, und er
  // erscheint nur, wenn wirklich etwas gefiltert wurde (sonst bliebe eine
  // Dauerwarnung stehen, die nach drei Tagen niemand mehr liest —
  // UI-Worker-Anatomie Punkt 4). Kein Aufklapper, kein `<title>`: der Satz
  // steht direkt im Toast.
  //
  // B117 SCHRITT 2 nachgezogen: dieser Toast erscheint jetzt SELTENER, nicht
  // per Sonderfall — er ist die Bedingung `kamerasOhneInnenraum.length <
  // params.kameras.length` von oben unveraendert, und die ist nur noch wahr,
  // wenn `interiorMoeglich` FALSCH ist (dann filtert `istUeberDiesenWegBe
  // stellbar` «Innenraum» weiterhin heraus). Faehrt `interior`, filtert der
  // Aufruf nichts mehr heraus, und dieser Block bleibt darum stumm — kein
  // Sonderfall-Code noetig, die bestehende Zaehlung regelt es von selbst.
  if (params.kameras && kamerasOhneInnenraum && kamerasOhneInnenraum.length < params.kameras.length) {
    const gesamt = params.kameras.length;
    const gesendet = kamerasOhneInnenraum.length;
    melde(
      `${gesendet} von ${gesamt} Standpunkten gesendet — «Innenraum» ist ueber diesen Weg ohne Zonen im ` +
        'Dokument nicht bestellbar (er sendet die Szene dann als glb, nicht als IFC-Raeume).',
      { ton: 'info' },
    );
  }
  const lineArt = params.mode === 'lineart';
  const scene = {
    schema: 'kosmovis.render-scene/v1',
    // P-ACHSENRIEGEL (26.08.2026, kosmo-contracts render-scene.ts): `up_axis`
    // ist seit dem Vorfall PFLICHT — diese App sendet durchgehend `'y'`, weil
    // das ihre bewiesene, reale Konvention ist (s. Kommentar an `kamera.ts`
    // Kopf: `toGlb` ist Zeile für Zeile dieselbe Formel wie der tatsächlich
    // gesendete `.glb`-Export in `derive/gltf.ts:143-145`).
    // N1 (ROADMAP 1331, `auf-20260901-68` R2): `derive/kamera.ts` weiss seit
    // N1 bereits, welchen Bodenbezug es für einen Standpunkt benutzt hat
    // (`AutoKameraStandpunkt.referenzpunkt`, optional) — der Job trägt das
    // additiv mit, statt es hier stillschweigend fallen zu lassen. KEIN
    // Vorgabewert: fehlt `k.referenzpunkt` (z.B. «Übersicht», die bewusst
    // nicht ab einem Bodenbezug rechnet), bleibt die CameraSpec byte-
    // identisch zum Stand vor N1 — ein stiller Default wäre genau die
    // Festlegung, gegen die `CameraSpec.referenzpunkt` gebaut wurde
    // (`kosmo-contracts` `render-scene.ts:52-54`).
    cameras: kameras
      ? kameras.map((k) => ({
          name: k.name,
          position: k.position,
          target: k.target,
          fov: k.fov,
          up_axis: 'y' as const,
          ...(k.referenzpunkt ? { referenzpunkt: k.referenzpunkt } : {}),
        }))
      : (params.kameraWahl ?? 'auto'),
    render: {
      resolution: params.resolution ?? [1600, 1000],
      samples: params.samples,
      faithful: params.faithful,
      ...(params.sun ? { sun: params.sun } : {}),
      ...(params.environment ? { environment: params.environment } : {}),
      // A2/16.09.2026 (Zeilen 4, 47, 48, 51): jedes der drei Felder kommt NUR
      // mit, wenn es bestellt wurde. Ein leeres Objekt statt Weglassen waere
      // hier das Gegenteil von additiv — der Vertrag unterscheidet «nicht
      // bestellt» von «auf null bestellt».
      ...(params.himmel ? { himmel: params.himmel } : {}),
      ...(params.belichtung ? { belichtung: params.belichtung } : {}),
      ...(params.rauschschwelle !== undefined ? { rauschschwelle: params.rauschschwelle } : {}),
    },
    // `refs` ZURUECKGEZOGEN 04.09.2026 (Owner-Entscheid, B97 Posten A) — der
    // einzige Erzeuger im Baum war genau diese Zeile, und sie schrieb eine
    // leere Liste, die niemand las. Begruendung im Vertrag (`render-scene.ts`).
    style: { mode: lineArt ? 'lineart' : 'none', prompt: params.prompt },
    // HS5: «Nur Cycles» → vis.skip: true (reines Cycles, keine KI-Veredelung).
    // Die Bridge leitet das in requested_engine "cycles" ab (HS2). E10:
    // `lineArt` gewinnt HART über `nurCycles` — s. Kommentar an `mode` oben.
    vis: {
      skip: lineArt || params.nurCycles === true,
      backbone: params.backbone ?? 'z-image-turbo',
      upscale: false,
      // research_only nur bei explizitem Flag mitschicken — Produkt-Jobs
      // bleiben byte-identisch zum Stand vor der Lizenz-Sanierung.
      ...(params.researchOnly === true ? { research_only: true } : {}),
    },
    ...(params.komposition ? { komposition: params.komposition } : {}),
    // B117 SCHRITT 2 (Owner-Entscheid E57): `interior`/IFC kommen NUR, wenn
    // `interiorMoeglich` wahr ist — ohne Zonen bleibt dieser Teil der Szene
    // Zeichen fuer Zeichen wie vor Schritt 2 (kein `interior`-Feld,
    // `format:'glb'`, s. Zusicherung A im Bericht).
    ...(interiorMoeglich ? { interior: { rooms: 'auto' as const } } : {}),
    out: '',
    geometry: { path: '', format: interiorMoeglich ? ('ifc' as const) : ('glb' as const) },
  };
  const form = new FormData();
  form.append('scene', JSON.stringify(scene));
  // Y3 P-IFC-BESTELLUNG-Muster (`bake-auftrag.ts:116`, woertlich uebernommen).
  const dateiname = interiorMoeglich ? 'model.ifc' : 'model.glb';
  const mimeTyp = interiorMoeglich ? 'application/x-step' : 'model/gltf-binary';
  form.append('model', new Blob([modell], { type: mimeTyp }), dateiname);
  const res = await bridgeFetch(bridgeRoutes.jobs, { method: 'POST', body: form });
  if (!res.ok) throw new BridgeHttpError(res.status, 'Bridge antwortet mit');
  return parseJob(await res.json());
}

/**
 * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15) — Extraktion von `NodeCanvas.tsx`s
 * bisherigem `ausfuehren()`-Closure (unverändertes Verhalten, nur ortsneutral
 * gemacht): der Render-Node-«Ausführen»-Weg braucht NICHTS NodeCanvas-
 * Lokales (nur `doc`/`runCommand`-freie Werte + `evaluiereGraph`, beides pur/
 * exportiert) — darum jetzt hier, aufrufbar SOWOHL vom Node selbst
 * (unverändert) ALS AUCH von der neuen AUSTAUSCH-Insel («Render senden»,
 * `island/inhalte/austausch.tsx`), ohne die Logik zweimal zu schreiben.
 * `environment` kommt aus der STIMMUNG-Insel (`vis-runtime.ts`
 * `renderStimmungPreset`) — der Aufrufer entscheidet, ob er ihn mitgibt.
 *
 * `opts` (v0.8.4 PC2, `docs/V084-SPEZ.md` E6/C-18) — additiv: der
 * `vis.render`-Kernel-Command-Executor (`VisWorkspace.tsx`) reicht
 * `kameraWahl`/`backbone`/`aufloesung` aus dem im Doc gespeicherten
 * Render-Wunsch (`doc.settings.visRenderAuftrag`) durch. Beide bestehenden
 * Aufrufer (`NodeCanvas.tsx`s Ausführen-Knopf, `island/inhalte/
 * austausch.tsx`) lassen `opts` weg — der Job bleibt für sie byte-identisch
 * zum bisherigen Stand.
 *
 * Line-Art (v0.8.11, `docs/V0810-SPEZ.md` §5 Z4, Ein-Quellen-Entscheid): KEIN
 * `opts.mode`-Feld mehr — der frühere transiente Weg (Insel-`useState`,
 * gefallen mit `island/inhalte/austausch.tsx`) ist ersatzlos weg. `mode`
 * kommt jetzt AUSSCHLIESSLICH aus dem PERSISTENTEN Render-Node-Parameter
 * `node.params.lineart` (boolean, gesetzt über `vis.nodeParametrieren` —
 * NodeCanvas-Checkbox UND der AUSTAUSCH-Insel-Switch schreiben beide
 * dorthin). Damit ist Line-Art undo-bar, überlebt Insel-Remounts und hat
 * genau EINE Quelle der Wahrheit, egal über welchen Weg der Job ausgelöst
 * wird (Knopf am Node, Insel-Knopf, `vis.render`-Kosmo-Tool).
 */
export function sendeGraphRenderAuftrag(
  graphId: string,
  nodeId: string,
  environment?: { preset: 'morgen' | 'abend' | 'weiss' },
  opts?: {
    kameraWahl?: 'auto' | 'saved';
    backbone?: 'z-image-turbo' | 'qwen' | 'flux2-klein' | 'flux-krea' | 'sdxl';
    aufloesung?: readonly [number, number];
  },
): void {
  const { doc } = useProject.getState();
  const graph = doc.get<VisGraph>(graphId);
  if (!graph) return;
  const auswertung = evaluiereGraph(doc, graph);
  const roh = auswertung.renderAuftraege.get(nodeId);
  if (!roh) return;
  if (!roh.hatSzene) {
    melde('Der Render-Node braucht eine Szene — verbinde den Modell-Node.', { ton: 'fehler' });
    return;
  }
  // P-LEERSZENE: `hatSzene` allein beweist nur die Kante, nicht die
  // Geometrie dahinter (Kommentar an `szeneBauteileAnzahl` oben) — dieser
  // Schutz greift auch dann, wenn ein Aufrufer (Kosmo-Tool `vis.render` in
  // `VisWorkspace.tsx`, oder ein künftiger Weg) den UI-Button umgeht und
  // direkt hier landet. Die Buttons selbst sind zusätzlich gesperrt
  // (NodeCanvas.tsx/austausch.tsx) — diese Zeile ist die zweite, tiefere
  // Naht, nicht der einzige Riegel.
  if (szeneBauteileAnzahl(doc) === 0) {
    melde(KEINE_GEOMETRIE_HINWEIS, { ton: 'fehler' });
    return;
  }
  // P-ACHSENRIEGEL (26.08.2026): Selbstprüfung der Auto-Kamera-Standpunkte
  // gegen die Bauwerkshöhe (`kamera.ts` `pruefeKamerahoehen`, reine
  // Ableitung, kein Klemmen). MELDET statt still zu korrigieren oder den
  // Auftrag stumm zu blocken — dieselbe Meldebahn wie jeder andere Fehler
  // hier (`meldeFehler`), damit es keine zweite Wahrheit gibt. Bewusst NICHT
  // blockierend (kein `return`): eine unplausible Kamerahöhe ist ein
  // Hinweis, den der Architekt einordnen kann (z. B. ein ungewöhnliches
  // Terrain-Nullniveau) — kein harter Vertragsbruch wie die leere Szene
  // oben, die keinen Job je ergäbe.
  for (const befund of pruefeKamerahoehen(doc)) {
    meldeFehler(befund.text);
  }
  const node = graph.nodes.find((n) => n.id === nodeId);
  const zusatz = formularZusatz(node?.params ?? {});
  // A2/16.09.2026 (Zeilen 4, 47, 48, 50a, 51, 56): die sechs neuen
  // Bedienelemente schreiben PERSISTENTE Node-Parameter — dasselbe Muster wie
  // `nurCycles` und `lineart` oben, damit die Wahl undo-faehig ist, ein
  // Remount ueberlebt und ueber JEDEN Ausloeser gilt (Knopf am Node, Insel,
  // Kosmo-Tool). Gelesen wird sie hier, an EINER Stelle.
  const bedienung = renderBedienungAusParams(node?.params ?? {});
  // Der SonnenSTAND kommt weiterhin allein aus `visgraph.ts` (Preset oder gar
  // nichts) — die Bedienung steuert nur die LichtDETAILS. Ohne Stand gibt es
  // darum auch kein `sun`-Feld: Staerke und Farbtemperatur ohne Stand waeren
  // eine halbe Sonne, und der Vertrag verlangt Azimut und Elevation.
  const sun = roh.sun ? { ...roh.sun, ...bedienung.sunDetails } : undefined;
  const auftrag = {
    ...roh,
    prompt: kombiniertePrompt(roh.prompt, zusatz),
    // Reihenfolge ist Absicht: was der Bediener ausdruecklich gewaehlt hat,
    // schlaegt den Preset-Wert aus `visgraph.ts`. Hat er nichts gewaehlt,
    // bleibt `roh` unangetastet — und damit alles wie bisher.
    ...(bedienung.samples !== undefined ? { samples: bedienung.samples } : {}),
    ...(bedienung.resolution ? { resolution: bedienung.resolution } : {}),
    ...(sun ? { sun } : {}),
    ...(bedienung.himmel ? { himmel: bedienung.himmel } : {}),
    ...(bedienung.belichtung ? { belichtung: bedienung.belichtung } : {}),
    ...(bedienung.rauschschwelle !== undefined ? { rauschschwelle: bedienung.rauschschwelle } : {}),
  };
  // v0.8.11 Z4: Line-Art liest DIREKT den persistenten Node-Parameter — EIN
  // Quellen-Ort, s. Kommentar oben.
  const mode: 'none' | 'lineart' = node?.params?.['lineart'] === true ? 'lineart' : 'none';
  // v0.9.28 P-AUF Posten 3 — die EINZIGE Naht, an der diese App ein
  // research-Flag setzt. Bewusst HIER und nicht als `opts`-Feld: kein
  // Aufrufer (auch nicht der `vis.render`-Executor in `VisWorkspace.tsx`,
  // also auch kein Modell-Wunsch) kann das Flag hereinreichen — es entsteht
  // ausschliesslich aus dem ausdrücklich gesetzten Geräte-Schalter
  // (`state/research-profil.ts`, dortiger Kopfkommentar begründet, warum das
  // Produkt-Gate dadurch nicht weicher wird).
  //
  // Angehängt wird es NUR beim gesperrten Backbone: ein Produkt-Job (qwen/
  // sdxl) bleibt byte-identisch, egal wie der Schalter steht — genau wie das
  // Worker-Flag `--research-only` nichts an einem erlaubten Checkpoint
  // ändert, sondern nur einen gesperrten aufsperrt.
  //
  // A2/16.09.2026, ZEILE 56: das Bildwerkzeug kann jetzt aus zwei Quellen
  // kommen — aus `opts` (der `vis.render`-Kosmo-Weg, ein einmaliger Wunsch je
  // Aufruf) und aus dem persistenten Node-Parameter (das neue Bedienelement
  // am Render-Node). `opts` GEWINNT: ein ausdrücklicher Aufruf mit
  // Werkzeugwunsch soll nicht stumm vom gespeicherten Wert überschrieben
  // werden. Das research-Gate gilt für beide Quellen gleichermassen — sonst
  // wäre der neue Weg ein Loch im Lizenz-Riegel.
  const backbone = opts?.backbone ?? bedienung.backbone;
  const researchOnly = istNurResearchBackbone(backbone) && researchProfilAktiv();
  const key = memoKey(auftrag);
  const { setzeLauf, patchLauf } = useVisRuntime.getState();
  setzeLauf(nodeId, { status: 'gesendet', memoKey: key, gestartetUm: Date.now() });
  void postRenderJob({
    ...auftrag,
    ...(environment ? { environment } : {}),
    ...(opts?.kameraWahl !== undefined ? { kameraWahl: opts.kameraWahl } : {}),
    ...(backbone !== undefined ? { backbone } : {}),
    ...(researchOnly ? { researchOnly: true } : {}),
    // `aufloesung` spiegelt denselben Job-Parameter wie das bestehende
    // `resolution` (K20/A10-Presets nutzen ihn schon) — kein Zweitfeld.
    ...(opts?.aufloesung !== undefined ? { resolution: opts.aufloesung } : {}),
    mode,
  })
    .then((j) =>
      patchLauf(nodeId, {
        jobId: j.job_id,
        status: mappeJobStatus(j),
        ...(j.approval_token !== undefined ? { approvalToken: j.approval_token } : {}),
      }),
    )
    .catch(async (err) => {
      // TypeError = fetch-Netzfehler → ehrliche Offline-Meldung (§2.1.5),
      // nicht der kryptische «Failed to fetch»-Rohtext. KLEIN 9 / v0.9.21
      // P-E: liegt die Bridge-URL ausserhalb der host-offenen CSP-Freigabe
      // (IP ODER DNS-Name, nur http auf 8600/8700/11434), ist der
      // «Netzfehler» VERMUTLICH in Wahrheit die CSP — «vermutlich» bleibt
      // im Text, weil die App das nicht beweisen kann (nur die eigene CSP
      // kennt und dagegen mustern), aber der Hinweis benennt die
      // wahrscheinlichste Ursache, damit niemand vergeblich woanders sucht.
      // P-BESCHEID (B43 Teil 2 §10): ein 401 ist kein Offline — und die App
      // sah den 401 bisher gar nicht. Verwirft der Browser eine abgelehnte
      // Antwort mangels CORS-Freigabe, kommt kein Status an, sondern ein
      // TypeError «Failed to fetch»: von einem toten Server nicht zu
      // unterscheiden. Darum wird jetzt GEMESSEN statt geurteilt — `/health`
      // ist tokenfrei; antwortet es, laeuft die Bridge, und die alte Meldung
      // haette den Owner die Bridge neustarten lassen statt den Token pruefen.
      // P5b (v0.9.56): derselbe Bescheid geht jetzt AUCH in den Toast — bis
      // hierhin stand im Node-Status der Bescheid, im Toast aber weiterhin
      // `err.message` («Failed to fetch»), weil `meldeFehler(err)` den
      // Rohtext zeigt. EIN Bescheid, zwei Anzeigen — kein zweiter
      // `/health`-Ruf (der wäre teuer und könnte ein anderes Urteil liefern
      // als der, den `patchLauf` gerade gesetzt hat).
      const bescheid = await bescheidFuerBridgeFehler(err);
      patchLauf(nodeId, { status: 'fehler', fehler: bescheid });
      melde(bescheid, { ton: 'fehler' });
    });
}

export async function holeJob(jobId: string): Promise<JobRecord> {
  const res = await bridgeFetch(bridgeRoutes.job(jobId));
  if (!res.ok) throw new BridgeHttpError(res.status, `Job ${jobId}`);
  return parseJob(await res.json());
}

/** Wartenden Job freigeben (nur bei aktiver Freigabe-Pflicht) — braucht den
 * approval_token aus dem Create-Response. */
export async function freigebenJob(jobId: string, approvalToken: string): Promise<JobRecord> {
  const res = await bridgeFetch(bridgeRoutes.jobApprove(jobId), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approval_token: approvalToken }),
  });
  if (!res.ok) throw new BridgeHttpError(res.status, `Freigabe ${jobId}`);
  return parseJob(await res.json());
}

/** Kooperativer Abbruch — awaiting_approval/queued/running → cancelled. */
export async function abbrechenJob(jobId: string): Promise<JobRecord> {
  const res = await bridgeFetch(bridgeRoutes.jobCancel(jobId), { method: 'POST' });
  if (!res.ok) throw new BridgeHttpError(res.status, `Abbruch ${jobId}`);
  return parseJob(await res.json());
}

/**
 * Validiert eine Bridge-Antwort gegen den Vertrag; `safeParse` statt `as`.
 *
 * P-DONE (`auftraege/von-homestation/auf-orbit-20260821-01.md` AUFTRAG 1):
 * die Meldung trug bis hierhin NUR den festen Satz «Bridge-Antwort passt
 * nicht zum Render-Job-Vertrag» — OHNE zu sagen, WELCHES Feld. Genau das
 * hat den echten `paarurteil.kante`-Fund (ROADMAP 1068) zu einer eigenen
 * Nachmessung gezwungen, statt dass die Fehlermeldung selbst den Weg zeigt.
 * Jetzt trägt sie dieselben `path: message`-Paare wie
 * `postBlenderSimJob`s `SonnenstundenParams`-Fehler oben — EIN Muster für
 * «Vertrag lehnt ab» in dieser Datei.
 *
 * E76 (Owner-Entscheid 19.09.2026, `auftraege/ergebnisse/
 * erg-20260919-104-unbekannte-felder-in-der-bestellung.md` Abschnitt V3):
 * unser Vertrag traegt bewusst KEIN `.strict()` — ein unbekanntes Feld der
 * Gegenseite wird von zod still abgestreift, das bleibt GEWOLLT (ein
 * `.strict()` wuerde jede kuenftige Feld-Ergaenzung der Gegenseite unsere
 * Seite anhalten lassen). Das mildere Mittel, das der Owner stattdessen
 * gewaehlt hat: bei ERFOLG wird zusaetzlich GEMESSEN (`unbekannteFelder()`,
 * `@kosmo/contracts`), und ein Fund wird GEMELDET, ohne den Lauf
 * anzuhalten — `geprueft.data` geht unveraendert weiter. Genau diese Klasse
 * Fehler stand schon bei `RenderJob.result` selbst («Ohne dieses Feld würde
 * `RenderJob.parse()` es stumm strippen (Fable-Review-1)») und wurde damals
 * von Hand gefunden.
 *
 * `console.warn` statt `melde(...)`: derselbe Stil wie die Glasnaht-Wache
 * oben (`pruefeGlasnaht`-Aufruf, `postRenderJob`) — ein Protokoll-Befund
 * fuer die Werkstatt (Zahl + Grund + Fundstellen), kein Architekten-Toast.
 * `melde(...)` traegt in dieser Datei durchgehend Saetze, die der Owner
 * SELBST etwas angehen (z. B. «X von Y Standpunkten gesendet») — ein
 * abgestreiftes Fremdfeld der Bridge-Antwort ist dagegen eine
 * Vertragsbeobachtung, auf die niemand am Bildschirm reagieren kann. KEINE
 * Dauerwarnung: die Meldung erscheint nur, wenn wirklich etwas Unbekanntes
 * da war.
 */
function parseJob(raw: unknown): JobRecord {
  const geprueft = RenderJob.safeParse(raw);
  if (!geprueft.success) {
    const details = geprueft.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join('; ');
    throw new Error(`Bridge-Antwort passt nicht zum Render-Job-Vertrag — ${details}`);
  }
  const unbekannt = unbekannteFelder(raw, geprueft.data);
  if (unbekannt.length > 0) {
    console.warn(
      `[E76] ${unbekannt.length} Feld(er) in der Bridge-Antwort waren dem Vertrag unbekannt und wurden von ` +
        `zod abgestreift (Owner-Entscheid 19.09.2026, auf-20260919-104): ${unbekannt.join(', ')}`,
    );
  }
  return geprueft.data;
}

// ─────────────────────────────────────────────────────────────────────────
// Blender-Sim-/Bake-Jobs (v0.8.9 §9 E9/E11, PBL2) — EIGENE Verträge
// (`BlenderSimJob`/`BakeJob`, NICHT `RenderJob`), eigene Präfixe (`bsim-`/
// `bake-`) und eigene Endpoints (`bridgeRoutes.jobsBlenderSim`/`jobsBake`).
// Physik/Geometrie-Optimierung werden NIE gefakt — der Fake-Betrieb endet
// beweisbar auf `kein-blender-worker` (s. `blender-sim.ts`/`bake-job.ts`-
// Kopfkommentare, Sanktion 12).
// ─────────────────────────────────────────────────────────────────────────

/**
 * Client-seitiges Shape der `art:'sonnenstunden'`-Params (v0.8.9 §9 E11) —
 * die Bridge selbst erzwingt hier NICHTS (`BlenderSimScene.params` ist ein
 * offenes `z.record(z.string(), z.unknown())`, s. `blender-sim.ts`
 * Kopfkommentar); ein Tippfehler (z.B. `lng` statt `lon`) fiele sonst erst
 * am echten Blender-Worker auf der HomeStation auf, nicht am Client. Prüft
 * NUR den Sonnenstunden-Shape — `wind`/`gebaeude-energie` haben eigene
 * Params, die diese Version clientseitig (noch) nicht validiert (kein
 * Client dafür in 0.8.9).
 */
export const SonnenstundenParams = z.object({
  lat: z.number(),
  lon: z.number(),
  datum: z.string().min(1),
  kriteriumStunden: z.number().optional(),
});
export type SonnenstundenParams = z.infer<typeof SonnenstundenParams>;

/** Validiert eine Bridge-Antwort gegen den Blender-Sim-Job-Vertrag. */
function parseBlenderSimJob(raw: unknown): BlenderSimJob {
  const geprueft = BlenderSimJob.safeParse(raw);
  if (!geprueft.success) {
    throw new Error('Bridge-Antwort passt nicht zum Blender-Sim-Job-Vertrag');
  }
  return geprueft.data;
}

/** Validiert eine Bridge-Antwort gegen den Bake-Job-Vertrag. */
function parseBakeJob(raw: unknown): BakeJob {
  const geprueft = BakeJob.safeParse(raw);
  if (!geprueft.success) {
    throw new Error('Bridge-Antwort passt nicht zum Bake-Job-Vertrag');
  }
  return geprueft.data;
}

/**
 * Blender-Simulation senden (Wind/Sonnenstunden/Gebäude-Energie) — multipart
 * an `bridgeRoutes.jobsBlenderSim`, Antwort gegen `BlenderSimJob.safeParse`
 * (NICHT `RenderJob`). Für `art:'sonnenstunden'` wird `params` VOR dem Senden
 * gegen `SonnenstundenParams` geprüft — ein ungültiges Shape wirft, BEVOR
 * überhaupt ein Netzwerk-Request losgeht.
 */
export async function postBlenderSimJob(
  art: BlenderSimArt,
  params: Record<string, unknown>,
  glbBytes: BlobPart,
): Promise<BlenderSimJob> {
  if (art === 'sonnenstunden') {
    const geprueft = SonnenstundenParams.safeParse(params);
    if (!geprueft.success) {
      throw new Error(
        `Sonnenstunden-Parameter ungültig: ${geprueft.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join('; ')}`,
      );
    }
  }
  const scene = {
    schema: 'kosmo.blender-sim/v1',
    art,
    geometry: { path: '', format: 'glb' },
    params,
    out: '',
  };
  const form = new FormData();
  // WICHTIG: die Bridge erwartet hier das Feld `szene` (deutsch), NICHT
  // `scene` wie beim generischen Render-Endpoint `/jobs` (main.py
  // `create_job(scene: str = Form(...))` vs. `create_blender_sim_job(szene:
  // str = Form(...))`) — unterschiedliche Feldnamen an zwei Endpoints
  // desselben Servers, wörtlich gegen main.py verifiziert.
  form.append('szene', JSON.stringify(scene));
  form.append('model', new Blob([glbBytes], { type: 'model/gltf-binary' }), 'model.glb');
  const res = await bridgeFetch(bridgeRoutes.jobsBlenderSim, { method: 'POST', body: form });
  if (!res.ok) throw new BridgeHttpError(res.status, 'Bridge antwortet mit');
  return parseBlenderSimJob(await res.json());
}

export async function holeBlenderSimJob(jobId: string): Promise<BlenderSimJob> {
  const res = await bridgeFetch(bridgeRoutes.job(jobId));
  if (!res.ok) throw new BridgeHttpError(res.status, `Job ${jobId}`);
  return parseBlenderSimJob(await res.json());
}

/** Wartenden Blender-Sim-Job freigeben (nur bei aktiver Freigabe-Pflicht). */
export async function freigebenBlenderSimJob(jobId: string, approvalToken: string): Promise<BlenderSimJob> {
  const res = await bridgeFetch(bridgeRoutes.jobApprove(jobId), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approval_token: approvalToken }),
  });
  if (!res.ok) throw new BridgeHttpError(res.status, `Freigabe ${jobId}`);
  return parseBlenderSimJob(await res.json());
}

/** Kooperativer Abbruch — awaiting_approval/queued/running → cancelled. */
export async function abbrechenBlenderSimJob(jobId: string): Promise<BlenderSimJob> {
  const res = await bridgeFetch(bridgeRoutes.jobCancel(jobId), { method: 'POST' });
  if (!res.ok) throw new BridgeHttpError(res.status, `Abbruch ${jobId}`);
  return parseBlenderSimJob(await res.json());
}

/**
 * Textur-Bake senden (Smart-UV-Unwrap + AO-Bake) — multipart an
 * `bridgeRoutes.jobsBake`, Antwort gegen `BakeJob.safeParse`. Endet im
 * Fake-/Container-Betrieb IMMER auf `kein-blender-worker` (Sanktion 12) —
 * dieser Client-Helfer täuscht nichts vor, er reicht nur ehrlich durch.
 */
export async function postBakeJob(
  glbBytes: BlobPart,
  params: { textureSize?: number; unwrap?: 'smart-uv'; decimateRatio?: number },
): Promise<BakeJob> {
  const scene = {
    schema: 'kosmo.bake-job/v1',
    geometry: { path: '', format: 'glb' },
    params: { unwrap: 'smart-uv' as const, ...params },
    out: '',
  };
  const form = new FormData();
  // Dasselbe Feldnamen-Detail wie bei `postBlenderSimJob` (s. dortigen
  // Kommentar): `/jobs/bake` erwartet `szene` (main.py `create_bake_job`).
  form.append('szene', JSON.stringify(scene));
  form.append('model', new Blob([glbBytes], { type: 'model/gltf-binary' }), 'model.glb');
  const res = await bridgeFetch(bridgeRoutes.jobsBake, { method: 'POST', body: form });
  if (!res.ok) throw new BridgeHttpError(res.status, 'Bridge antwortet mit');
  return parseBakeJob(await res.json());
}

export async function holeBakeJob(jobId: string): Promise<BakeJob> {
  const res = await bridgeFetch(bridgeRoutes.job(jobId));
  if (!res.ok) throw new BridgeHttpError(res.status, `Job ${jobId}`);
  return parseBakeJob(await res.json());
}

/** Wartenden Bake-Job freigeben (nur bei aktiver Freigabe-Pflicht). */
export async function freigebenBakeJob(jobId: string, approvalToken: string): Promise<BakeJob> {
  const res = await bridgeFetch(bridgeRoutes.jobApprove(jobId), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approval_token: approvalToken }),
  });
  if (!res.ok) throw new BridgeHttpError(res.status, `Freigabe ${jobId}`);
  return parseBakeJob(await res.json());
}

/** Kooperativer Abbruch — awaiting_approval/queued/running → cancelled. */
export async function abbrechenBakeJob(jobId: string): Promise<BakeJob> {
  const res = await bridgeFetch(bridgeRoutes.jobCancel(jobId), { method: 'POST' });
  if (!res.ok) throw new BridgeHttpError(res.status, `Abbruch ${jobId}`);
  return parseBakeJob(await res.json());
}

/**
 * V-H4 (W1, UI-KONZEPT-065 §5) — semantisches Render-Formular: Fassade / Szene
 * / Jahreszeit / Personen / Freitext sind flache Render-Node-`params` (wie
 * `nurCycles`/`preset`), gesetzt über das bestehende `vis.nodeParametrieren`.
 * Diese zwei Funktionen sind die EINE Naht, die den Formular-Zusatz an den
 * eingehenden Prompt hängt — dieselbe Zusammenführung speist sowohl die
 * sichtbare Anzeige (`render-final-prompt`) als auch den tatsächlichen
 * Bridge-Auftrag (Ehrlichkeit/V8: kein stiller Unterschied zwischen Anzeige
 * und Job). KEINE Änderung am render-scene/v1-Vertrag — nur Prompt-Inhalt.
 */
const RENDER_FORMULAR_FELDER = ['formFassade', 'formSzene', 'formJahreszeit', 'formPersonen', 'formFreitext'] as const;

/**
 * H-30 (`docs/SIM-BEFUNDE.md`, 0.6.8) — Szene/Jahreszeit/Personen trugen als
 * Options-`value` bislang die deutschen Prompt-Langtexte selbst (fragil für
 * Automatisierung/Übersetzung, jede Value-Änderung war ein stiller
 * Vertragsbruch). Jetzt: stabile Schlüssel als `value` (NodeCanvas.tsx
 * Render-Formular), diese Anzeige-Map übersetzt zurück in den Prompt-Text —
 * `formFassade` (modellabgeleitet) und `formFreitext` (frei) bleiben
 * unübersetzt. Unbekannte/alte Werte (z.B. aus einem vor H-30 gespeicherten
 * Projekt) fallen ehrlich auf den rohen gespeicherten Text zurück, statt
 * einen kryptischen Schlüssel zu senden.
 */
const RENDER_FORMULAR_UEBERSETZUNG: Partial<Record<(typeof RENDER_FORMULAR_FELDER)[number], Record<string, string>>> = {
  formSzene: {
    strasse: 'Aussenansicht von der Strasse',
    hof: 'Aussenansicht vom Hof',
    vogel: 'Vogelperspektive',
    innen: 'Innenraumansicht',
  },
  formJahreszeit: {
    sommer: 'Sommer',
    winter: 'Winter',
    herbst: 'Herbst',
  },
  formPersonen: {
    keine: 'keine Personen',
    wenige: 'wenige Personen',
    belebt: 'belebte Szene, viele Personen',
  },
};

/** Übersetzt EINEN Formular-Wert (Schlüssel → Prompt-Text) — auch für Stellen
 * ausserhalb von `formularZusatz`, die einen einzelnen Feldwert anzeigen
 * (z.B. die Kuratier-Karten-Bildunterschrift, NodeCanvas.tsx). */
export function formularFeldText(feld: string, wert: string): string {
  return RENDER_FORMULAR_UEBERSETZUNG[feld as (typeof RENDER_FORMULAR_FELDER)[number]]?.[wert] ?? wert;
}

export function formularZusatz(params: Record<string, string | number | boolean>): string {
  return RENDER_FORMULAR_FELDER.map((f) => {
    const roh = String(params[f] ?? '').trim();
    return roh ? formularFeldText(f, roh) : '';
  })
    .filter((t) => t.length > 0)
    .join(', ');
}

/** Eingehender Prompt (aus der bestehenden Prompt-Leitung) + Formular-Zusatz. */
export function kombiniertePrompt(eingang: string, zusatz: string): string {
  return [eingang, zusatz].filter((t) => t.trim().length > 0).join(', ');
}

export function bildUrl(jobId: string, imageName: string): string {
  return `${bridgeBase()}${bridgeRoutes.jobArtifact(jobId, imageName)}`;
}

/**
 * Artefakt-Bild als Blob holen — über `bridgeFetch` (trägt den Token, liegt im
 * connect-src der CSP). Ein direktes `<img src="http://…">` scheitert doppelt:
 * es kann keinen Token-Header tragen UND wird von `img-src` der CSP geblockt
 * (HS3-Nachbesserung/Fable-Auflage 1). Der Aufrufer macht daraus eine
 * `blob:`-URL (img-src erlaubt `blob:`) oder eine dataURL.
 */
export async function bildBlob(jobId: string, imageName: string): Promise<Blob> {
  const res = await bridgeFetch(bridgeRoutes.jobArtifact(jobId, imageName), { cache: 'no-store' });
  if (!res.ok) throw new BridgeHttpError(res.status, `Bild ${imageName}`);
  return res.blob();
}

/**
 * **Der Bilddeckel ist ZURUECKGEZOGEN (Owner-Entscheid 04.09.2026).**
 *
 * Von V088-SPEZ §3 E7 bis zum 04.09.2026 stand hier ein Tor: Base64-Text
 * einer aufs Blatt gelegten dataURL ueber 1 048 576 Zeichen wurde
 * ABGEWIESEN, mit einer Fehlerzone statt eines Doc-Schreibens.
 *
 * **Warum er faellt.** Fuer die Zahl gab es keinen auffindbaren technischen
 * Grund — sie war ein gesetzter «~1 MB», kein gemessener Engpass. Und die
 * Meldung mischte zwei Einheiten in einem Satz: verglichen wurden
 * Base64-ZEICHEN, angezeigt wurden MEGABYTE, und beide Zahlen standen
 * nebeneinander, als waeren sie dasselbe.
 *
 * **Was jetzt die Grenze ist — gemessen, nicht angenommen.** Der Weg ist
 * nicht grenzenlos, die naechste Grenze liegt nur weiter oben und ist eine
 * echte: der Yjs-Sync-Server deckelt die EINZELNE Nachricht auf
 * `KOSMO_SYNC_MAX_BYTES`, Vorgabe **8 MiB**
 * (`tools/sync-server/src/server.mjs:49`, dort als `maxPayload` an die
 * ws-Bibliothek gereicht, Zeile 143). Ueber dieser Grenze bricht die
 * Verbindung, statt eine Meldung zu geben — sie ist also haerter als das
 * Tor, das hier stand, und liegt rund achtmal hoeher.
 *
 * **Die Messung bleibt.** Wie gross ein Bild ist, darf die Kette weiterhin
 * wissen und sagen — sie weist es nur nicht mehr ab.
 */

/**
 * Base64-Zeichen → Bytes. Vier Base64-Zeichen kodieren drei Bytes; die
 * `=`-Auffuellung am Ende zaehlt nicht mit.
 */
function base64Bytes(b64: string): number {
  const fuellung = b64.endsWith('==') ? 2 : b64.endsWith('=') ? 1 : 0;
  return Math.max(0, Math.floor((b64.length * 3) / 4) - fuellung);
}

function mb(bytes: number): string {
  return (bytes / 1_048_576).toFixed(1);
}

/**
 * Wie gross ist dieses Bild? — eine Auskunft, kein Tor.
 *
 * Exportiert, damit die Messung pruefbar bleibt: ein Deckel, den man
 * entfernt, hinterlaesst sonst Tests, die still gruen bleiben, weil sie
 * nichts mehr pruefen.
 */
export function messeBildGroesse(dataUrl: string): {
  base64Zeichen: number;
  bytes: number;
  mbText: string;
} {
  const komma = dataUrl.indexOf(',');
  const b64 = komma >= 0 ? dataUrl.slice(komma + 1) : dataUrl;
  const bytes = base64Bytes(b64);
  return { base64Zeichen: b64.length, bytes, mbText: mb(bytes) };
}

/**
 * E13 (`docs/V089-SPEZ.md` §9, PBL2) — Herkunfts-Label eines Bildes, das aufs
 * Blatt kommt. Ersetzt die frühere feste `BILD_LABEL_FAKE_RENDER`-Konstante
 * (E7/V088-SPEZ) durch eine echte Herkunftsprüfung:
 *  - `worker` fehlt ODER ist `'fake-worker'` → «Vorschau (Fake-Render)»
 *    (Sanktion 8/V088: Fake-Bild ohne Kennzeichnung = ungültig — bleibt die
 *    Default-Antwort, damit JEDER Aufrufer ohne Herkunftsangabe weiter
 *    ehrlich als Fake gekennzeichnet wird).
 *  - `requestedStyle === 'lineart'` (und ein ECHTER Worker) → «Strichzeichnung
 *    (Line-Art)» (E10).
 *  - sonst (echter Worker, kein Line-Art) → «Render (Cycles)».
 *
 * WICHTIG (Container-Grenze, wörtlich): der `worker`-Wert kommt IMMER von der
 * Fake-Bridge (`tools/homestation-bridge/kosmo_bridge/main.py`
 * `_fake_worker_step`, setzt `record["worker"] = "fake-worker"`) — der
 * `'Render (Cycles)'`-Zweig dieser Funktion ist im Container-Betrieb NIE
 * erreichbar, weil hier nie ein anderer `worker`-String ankommt. Er wird
 * AUSSCHLIESSLICH per Unit-Test mit einem künstlichen `JobRecord` bewiesen
 * (`apps/kosmo-orbit/test/blender-label.test.ts`) und bleibt bis zu einer
 * echten HomeStation-Abnahme (0.8.10+, Owner-Termin) ein unbewiesener
 * Live-Pfad — genau so dokumentiert, nicht stillschweigend als «getestet»
 * behauptet.
 */
export function bildLabel(h: { worker?: string; requestedStyle?: string }): string {
  if (!h.worker || h.worker === 'fake-worker') return 'Vorschau (Fake-Render)';
  if (h.requestedStyle === 'lineart') return 'Strichzeichnung (Line-Art)';
  return 'Render (Cycles)';
}

/**
 * Gemeinsamer Kern von `bildAufsBlatt`/`aufnahmeAufsBlatt` — leerer Bild-Slot
 * zuerst, sonst neuer Slot; ohne Blatt entsteht eines. Alles EIN Undo-Schritt.
 * Gibt den Blattnamen zurück. Nimmt eine FERTIGE dataURL: der Bridge-Weg
 * (`bildAufsBlatt`) holt sie erst per Fetch, der Aufnahme-Weg
 * (`aufnahmeAufsBlatt`) hat sie schon (Viewport-Screenshot, kein Bridge-Job).
 *
 * `titel` bleibt als Parameter erhalten (Aufrufer in KuratierFlaeche.tsx/
 * island/inhalte/austausch.tsx ausserhalb dieses Pakets bleiben unverändert),
 * bestimmt aber NICHT das Slot-Label.
 *
 * `label` ist NEU (E13) und OPTIONAL: `bildAufsBlatt` berechnet ihn aus dem
 * Job-Record (`bildLabel`), `aufnahmeAufsBlatt` erzwingt sein eigenes Label
 * fest. Fehlt `label` (jeder Aufrufer AUSSERHALB dieses Pakets, s.o.), bleibt
 * das Verhalten byte-identisch zum bisherigen Stand: `bildLabel({})` liefert
 * ohne Herkunftsangabe immer «Vorschau (Fake-Render)» (Sanktion 8 bleibt
 * scharf, auch ohne den neuen Parameter).
 */
export function platziereBildAufsBlatt(dataUrl: string, _titel: string, label?: string): string {
  // Owner-Entscheid 04.09.2026: hier stand ein Tor, das ueber 1 MiB
  // Base64-Zeichen abgewiesen hat. Es ist weg — die MESSUNG bleibt und wird
  // gemeldet, damit ein grosses Bild nachvollziehbar bleibt, statt still zu
  // sein. Die naechste echte Grenze liegt beim Sync-Server (8 MiB je
  // Nachricht, s. `messeBildGroesse` oben).
  const bildGroesse = messeBildGroesse(dataUrl);
  console.info(`[Blattbild] ${bildGroesse.mbText} MB (${bildGroesse.base64Zeichen} Base64-Zeichen)`);
  const slotLabel = label ?? bildLabel({});
  const { doc, runCommand, history } = useProject.getState();
  history.beginGroup();
  try {
    const sheets = doc.byKind<Sheet>('sheet').sort((a, b) => a.index - b.index);
    let sheet = sheets.find((s) => (s.bilder ?? []).some((b) => !b.assetId)) ?? sheets[0];
    if (!sheet) {
      const res = runCommand('publish.blattErstellen', { name: 'Renderblatt', format: 'A1', orientation: 'quer' });
      sheet = doc.get<Sheet>((res.patches[0] as { id: string }).id)!;
    }
    const leer = (sheet.bilder ?? []).find((b) => !b.assetId);
    if (leer) {
      runCommand('publish.bildFuellen', { sheetId: sheet.id, bildId: leer.id, dataUrl });
      // `bildFuellen` kennt kein `title`-Param (Kernel-Vertrag bleibt
      // unverändert) — das Pflicht-Label kommt über den bestehenden
      // `bildAnpassen`-Command, in DERSELBEN Undo-Gruppe.
      runCommand('publish.bildAnpassen', { sheetId: sheet.id, bildId: leer.id, title: slotLabel });
    } else {
      runCommand('publish.bildPlatzieren', {
        sheetId: sheet.id,
        x: 40,
        y: 40,
        w: 160,
        dataUrl,
        title: slotLabel,
      });
    }
    return sheet.name;
  } finally {
    history.endGroup();
  }
}

/**
 * Bild als Blatt-Bürger nach KosmoPublish (C1) — Bridge-Artefakt (Render-Job).
 * Gibt den Blattnamen zurück.
 *
 * E13: holt `worker`/`requested_style` aus dem echten Job-Record
 * (`holeJob`) und berechnet daraus das Label — dieselbe Quelle, die den Job
 * auch sonst beschreibt, keine zweite Wahrheit. Schlägt der Zusatz-Fetch
 * fehl (Netz-Aussetzer o.ä.), fällt das Label ehrlich auf `bildLabel({})`
 * zurück («Vorschau (Fake-Render)») — NIE ein erfundenes «Render (Cycles)».
 */
export async function bildAufsBlatt(jobId: string, imageName: string, titel: string): Promise<string> {
  // Über bridgeFetch (Token-Header + connect-src) statt rohem fetch — sonst
  // sperrt eine token-geschützte Bridge das Blatt-Einbetten aus (Fable-Auflage 1).
  const blob = await bildBlob(jobId, imageName);
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result));
    r.onerror = () => reject(r.error ?? new Error('Bild nicht lesbar'));
    r.readAsDataURL(blob);
  });
  let label = bildLabel({});
  try {
    const job = await holeJob(jobId);
    label = bildLabel({
      ...(job.worker !== undefined ? { worker: job.worker } : {}),
      ...(job.requested_style !== undefined ? { requestedStyle: job.requested_style } : {}),
    });
  } catch {
    // Ehrlicher Rückfall auf das Fake-Render-Label (s. Kommentar oben) —
    // ein gescheiterter Zusatz-Fetch darf das Platzieren selbst nicht kippen.
  }
  return platziereBildAufsBlatt(dataUrl, titel, label);
}

/**
 * v0.6.7 P0: Viewport-Aufnahme als Blatt-Bürger — dieselbe Ablage wie
 * `bildAufsBlatt`, aber OHNE Bridge-Fetch (die dataURL liegt schon lokal vor,
 * `vis-runtime.Aufnahme.dataUrl`). Async wie `bildAufsBlatt` (einheitlicher
 * Aufrufer-Weg, `.then().catch()`), auch wenn hier nichts zu awaiten ist.
 * Gibt den Blattnamen zurück.
 *
 * E13: EIGENES, ehrliches Label «Aufnahme (Viewport)» — unabhängig von
 * `bildLabel()`/jedem Job-Record (ein Viewport-Screenshot hat keinen Bridge-
 * Job und war NIE ein Fake-Render, das «Vorschau (Fake-Render)»-Label wäre
 * hier selbst eine Falschbehauptung).
 */
export async function aufnahmeAufsBlatt(dataUrl: string, titel: string): Promise<string> {
  return platziereBildAufsBlatt(dataUrl, titel, 'Aufnahme (Viewport)');
}

/**
 * P-EINEWAHRHEIT (v0.9.35, O-T32) — die EINE Uebersetzung von Bridge-Fehler
 * zu Bescheid, fuer JEDEN Aufrufer. Vorher stand die Messung nur hier in
 * KosmoVis; die KosmoDev-Freigabe schloss aus demselben TypeError blind auf
 * «Offline», waehrend die Einstellungen per /health zu Recht «Verbindung»
 * zeigten — zwei Wahrheiten ueber denselben Zustand. Die Regel steht jetzt
 * einmal (P-VORZEICHEN-Lehre): Lage erheben, im Netzfehler-Fall die
 * tokenfreie /health-Gegenprobe fahren (scheitert sie, bleibt der alte,
 * vorsichtigere Wortlaut — eine misslungene Messung darf keine neue
 * Behauptung erzeugen), Bescheid formulieren.
 */
export async function bescheidFuerBridgeFehler(err: unknown): Promise<string> {
  const netzfehler = err instanceof TypeError;
  const rohtext = err instanceof Error ? err.message : String(err);
  const lage: BescheidLage = {
    netzfehler,
    ...(err instanceof BridgeHttpError ? { status: err.status } : {}),
    tokenGesetzt: (localStorage.getItem(BRIDGE_TOKEN_KEY) ?? '').trim().length > 0,
    cspVerdacht: netzfehler && bridgeVermutlichCspGeblockt(),
  };
  const gegenprobe = netzfehler && !lage.cspVerdacht
    ? await pruefeBridge(bridgeBase()).then((s) => s === 'verbunden').catch(() => undefined)
    : undefined;
  if (gegenprobe !== undefined) lage.healthErreichbar = gegenprobe;
  return bridgeBescheid(lage, rohtext).text;
}

/**
 * P5b (v0.9.56, wissen/fehlerberichte/eingang.jsonl 28.08.2026): kleiner
 * Toast-Helfer NEBEN `bescheidFuerBridgeFehler`, EIGENER Name statt einer
 * `meldeFehler`-Verwechslung — jeder Aufrufer eines Bridge-Catch-Zweigs, der
 * NUR den Toast braucht (kein `patchLauf`/kein zweiter Verbrauch des
 * Bescheids), schreibt `.catch(bescheideBridgeCatch)` statt jedes Mal
 * `melde(await bescheidFuerBridgeFehler(err), { ton: 'fehler' })`
 * auszuschreiben. KEIN zweiter Übersetzer — ruft `bescheidFuerBridgeFehler`
 * (und damit dessen `/health`-Gegenprobe) EINMAL auf und zeigt das Ergebnis.
 * Wer den Bescheid zusätzlich woanders braucht (z. B. `patchLauf`s
 * `fehler`-Feld), ruft `bescheidFuerBridgeFehler` selbst auf und meldet mit
 * `melde(bescheid, { ton: 'fehler' })` — sonst liefe die /health-Probe
 * zweimal für denselben Fehler.
 */
export async function bescheideBridgeCatch(err: unknown): Promise<void> {
  melde(await bescheidFuerBridgeFehler(err), { ton: 'fehler' });
}
