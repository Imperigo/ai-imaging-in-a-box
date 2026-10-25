import { z } from 'zod';
import {
  evaluiereGraph,
  exportGlb,
  exportIfc,
  istHimmelArt,
  isVisPresetId,
  pruefeGlasnaht,
  pruefeKamerahoehen,
  BESTELLFORMAT_VORGABE,
  fovImVertrag,
  kamerasFuerBestellformat,
  KAMERA_AUS_3D_NAME,
  getCommand,
  sheetPaperSize,
  visPresetById,
  docFuerEbenen,
  finalerRenderPrompt,
  type AutoKameraStandpunkt,
  type EbenenKombination,
  type HimmelArt,
  type ImageAsset,
  type KosmoDoc,
  type Sheet,
  type SheetImage,
  type KameraAutoWahl,
  type MaterialWahlAuftrag,
  type UmfeldWahl,
  type VisGraph,
  type VisRenderAuftrag,
  type VisStimmungId,
} from '@kosmo/kernel';
import { STANDARD_BRIDGE_URL } from '@kosmo/ai';
import {
  RenderJob,
  RenderScene,
  BlenderSimJob,
  BakeJob,
  bridgeRoutes,
  renderResultMaengel,
  unbekannteFelder,
  type BlenderSimArt,
} from '@kosmo/contracts';
import { melde, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { useSplatEbene } from '../../state/splat-ebene';
import { splatRenderKontext, szeneMitSplatKontext } from '../design/splat-render-kontext';
import { researchProfilAktiv } from '../../state/research-profil';
import { memoKey, useVisRuntime, type NodeLaufStatus } from './vis-runtime';
// P-BESCHEID (v0.9.33, B43 Teil 2 §10): der Urteilsspruch selbst ist eine
// reine Funktion in `bridge-bescheid.ts` — hier laeuft nur die Messung, die
// ihn fuettert. `pruefeBridge` ist die bestehende `/health`-Probe aus dem
// Heimserver-Modul; sie ist tokenfrei erreichbar und darum genau die
// Gegenprobe, die «laeuft die Bridge ueberhaupt?» beantworten kann.
import { BRIDGE_TOKEN_FEHLT_ODER_FALSCH_SATZ, bridgeBescheid, tokenSatz, type BescheidLage } from './bridge-bescheid';
import { meldeBrueckenFehler } from '../../shell/homeserver-knopf';
import { BRIDGE_TOKEN_KEY, pruefeBridge } from '../../state/home-server';
import { kuerzel } from '../../shell/tastennamen';
// Nur der Typ: `varianten-diff.ts` holt Werte aus dieser Datei, ein
// Wert-Import zurueck waere ein Kreis.
import type { LizenzAngabe } from './varianten-diff';
import {
  SKIZZE_NUR_IN_VISBOX_SATZ,
  anweisungDerBestellung,
  skizzeZurBestellung,
  type LaufAnweisung,
  type SkizzeDerBestellung,
} from './skizze-quelle';
import { gueteAmKnoten, type Guete } from './guete';
import { freiesBildAmKnoten } from './freies-bild';
import { heimStandpunkte } from './heim-standpunkte';
import { mitGrundbild } from './nebeneinander';
import { ABLAGE_GRENZE_BYTES, ablegenDa, druckWarnung, istBlattDa, mbText, projektBild, sichereImProjekt } from './bild-ablage-kern';
import { KAMERA_BLICK_FEHLT_HINWEIS } from './blick-quelle';
import {
  GRUNDLAGE_VERALTET_SATZ,
  KEINE_GRUNDLAGE_SATZ,
  SKIZZE_OHNE_GRUNDLAGE_SATZ,
  STRICHZEICHNUNG_OHNE_VARIANTE_SATZ,
  grundlageAmKnoten,
  grundlageFuerStand,
  grundlageSchonDaSatz,
  grundlageStand,
  kamerasSindTeilmenge,
  type GrundlageAmKnoten,
} from './grundlage';

/**
 * Bridge-Jobs für KosmoVis (P2/HS3) — ein Weg für Graph UND Einfach-Ansicht:
 * Modell als GLB an /jobs (render-scene/v1), Status holen, Bild aufs Blatt.
 * Alle Antworten laufen durch den `@kosmo/contracts`-Vertrag (`safeParse` statt
 * blindem `as`-Cast); jeder Bridge-Fetch trägt den Token konditional.
 */

export type JobQa = NonNullable<RenderJob['result']>['qa'];
/** kv-lieferstatus-null (L1): der Lieferstatus des Ergebnisses, `null` heisst
 *  «nicht festgestellt» (ein Vorbehalt, kein Fehler). */
export type JobLieferstatus = NonNullable<RenderJob['result']>['lieferstatus'];
/**
 * Nachgang 3 (auf-20261006-248; Bruecke `claude/lw-bruecke-worker-feld` bei
 * `5f59fd40e`, beim Integrator zum Einbau): die Bruecke sagt am Job, WER ihn
 * rechnet — `worker`, dazu `worker_seit` (Zeitpunkt der Uebernahme, ISO-8601
 * UTC) und, nur wenn sie den Worker selbst ableitet, `worker_quelle:
 * 'abgeleitet'`. `worker` steht schon im Vertrag (`@kosmo/contracts`
 * `RenderJob`), die beiden neuen Felder nicht; zod wuerde sie still
 * abstreifen. Sie werden darum HIER, nur beim Lesen in der Vis-Station,
 * optional dazugenommen — der gemeinsame Vertrag bleibt unberuehrt. Fehlen
 * sie (aeltere Bruecke), ist der Record wortgleich gueltig wie bisher.
 */
const RenderJobVis = RenderJob.extend({
  worker_seit: z.string().optional(),
  worker_quelle: z.string().optional(),
});
/** Der validierte Job-Record — der Vertrag ist die EINE Wahrheit (HS1),
 *  in der Vis-Station um die zwei Herkunftsfelder der Bruecke erweitert. */
export type JobRecord = z.infer<typeof RenderJobVis>;

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
 * C3 (Splat-Abnahme 06.10.2026): der Satz zu einem gesehenen 401/403 — aus
 * `bridge-bescheid.ts`, mit dem Token-Stand dieses Geräts («fehlt» oder
 * «passt nicht»), und immer mit dem Verweis auf Einstellungen ▸ HomeServer.
 */
export function authFehlerSatz(err: BridgeHttpError): string {
  return `${tokenSatz({ netzfehler: false, status: err.status, tokenGesetzt: bridgeToken() !== '' }) ?? BRIDGE_TOKEN_FEHLT_ODER_FALSCH_SATZ}.`;
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

/**
 * Fehler-Nachgang 20.10.2026 (Owner am Mac, «Variante erzeugen» → «Der Heim-PC ist nicht
 * erreicht: Er hat nicht rechtzeitig geantwortet.»): die ANLAGE eines Render-Auftrags
 * (`POST /jobs`) traegt das ganze Modell als Multipart, und die Gegenseite nimmt es unter einer
 * Sperre an. Mit grossen Modellen und einem beschaeftigten Heim-PC reichten 30 s nicht — der
 * Auftrag war oft schon angelegt, die Seite meldete trotzdem «nicht erreicht». Nur dieser eine
 * Aufruf bekommt die laengere Grenze; alle Abfragen bleiben bei `BRIDGE_ZEITGRENZE_MS`.
 */
export const BRIDGE_AUFTRAG_ZEITGRENZE_MS = 300_000;

/**
 * Antworten auf eine Variante OHNE Modell, nach denen sie einmal MIT Modell hinausgeht:
 * 422 (eine Bruecke, bei der `model` noch Pflicht ist — FastAPI-Pruefung), 400/404/409 (die
 * Gegenseite lehnt laut ab, z. B. weil die Grundlage dort fehlt). 401/403 (Anmeldung) und 5xx
 * nicht: dort hilft ein Modell nichts.
 */
const MODELL_NACHREICHEN_BEI: ReadonlySet<number> = new Set([400, 404, 409, 422]);

/** Satz, wenn eine Variante ohne Modell abgewiesen wurde und mit Modell noch einmal hinausgeht. */
export const MODELL_NACHGEREICHT_SATZ =
  'Der Heim-PC nahm die Variante ohne Modell nicht an — sie geht einmal mit dem Modell hinaus (das dauert länger).';

/**
 * Ob eine Bestellung ohne Modell hinausgeht: genau mit `vis.grundlage` («Variante erzeugen»).
 * Die Gegenseite rechnet dann nur den KI-Schritt auf Kameras und Passes der Grundlage; das
 * Modell (bis hierhin bei JEDER Variante neu exportiert und hochgeladen) braeuchte sie nicht.
 */
export function modellBleibtDaheim(params: { grundlage?: string }): boolean {
  return params.grundlage !== undefined;
}

/** Ein Fetch mit konditionalem `X-Kosmo-Token`-Header — die einzige Naht.
 *  Traegt seit VIS-U8-ZEITGRENZE eine Zeitgrenze (`BRIDGE_ZEITGRENZE_MS`),
 *  ausser ein Aufrufer liefert selbst ein `signal`. Seit dem Fehler-Nachgang
 *  20.10.2026 tut das genau einer: die Auftragsanlage in `postRenderJob`
 *  (`BRIDGE_AUFTRAG_ZEITGRENZE_MS`). */
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
 *
 * P11/B7 (V016-SPEZ) — Befund: ein eingebettetes `result` hiess BISHER immer
 * «fertig», auch mit leerem `images`-Array (`RenderResult.images:
 * z.array(z.string())` erlaubt `[]` — vertragskonform, aber nichts zum
 * Zeigen). «fertig» ohne Bild ist eine falsche Erfolgsmeldung. Jetzt: nur
 * MIT mindestens einem Bild «fertig», sonst ehrlich «fehler» — dieselbe
 * NodeLaufStatus-Vokabel wie jeder andere Fehlschlag (bewusst KEIN neuer
 * Status-Wert: `NodeLaufStatus`/`CompanionKartenStatus` sind über
 * `apps/kosmo-orbit/src/shell/companion-daten.ts`s `STATUS_LABEL`/
 * `STATUS_TON` — ausserhalb dieses Pakets — als ERSCHÖPFENDE `Record<...>`
 * verdrahtet; ein zusätzlicher Wert würde dort nicht kompilieren).
 */
export function mappeJobStatus(record: { status: string; result?: unknown }): NodeLaufStatus {
  if (record.result) {
    // `unknown` bleibt bewusst der Parametertyp (wie vor B7): unter
    // `exactOptionalPropertyTypes: true` lehnt TS ein enger getyptes
    // `result?: { images?: unknown }` an mehreren realen `RenderJob`-Aufrufern
    // ab (Viewport3D.tsx/Companion.tsx, ausserhalb dieses Pakets). Die
    // Bild-Prüfung selbst bleibt darum ein Laufzeit-Check, keine Typannahme.
    const bilder = (record.result as { images?: unknown }).images;
    return Array.isArray(bilder) && bilder.length > 0 ? 'fertig' : 'fehler';
  }
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
 * `qwen-image-2.1` steht ebenso bewusst NICHT hier: Owner-Entscheid E128
 * nimmt es ohne Schalter ins Produkt, die Lizenz wird vor der
 * Veröffentlichung gelöst (Hinweis in `BILDWERKZEUG_TEXTE`).
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
 * geändert hätte. Gemessen am damals mitgelieferten Lichthof-Referenzprojekt
 * (seit W6 · P-LICHTHOF-UMZUG das Demohaus, 7 Geschosse, 32 Wände,
 * 139 Entities): `deriveAll` kostet dort **~18 ms
 * MEDIAN** je invalidiertem Aufruf (Wand-Gehrung `miterWallEnds` scannt für
 * JEDE Wand ALLE anderen Wände des Docs — O(Wandzahl) je Wand). An einem
 * synthetisch grösseren Modell (432 Wände) steigt das auf **~255 ms
 * MEDIAN** — eine Reparatur, die den Render-Riegel korrigiert und dabei
 * JEDEN Befehl in einem grösseren Projekt spürbar bremst, sobald KosmoVis
 * offen ist, wäre keine Reparatur, sondern eine neue, versteckte Bremse
 * (Auflage: «Eine Reparatur, die die Oberfläche zäh macht, ist keine»). Die
 * Kind-Zählung unten bleibt dagegen bei **< 0.02 ms** selbst am damaligen
 * Lichthof-Referenzprojekt (reines `Map`-Durchlaufen, keine Extrusion, keine
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
/**
 * B2 (Nachprobe auf-20261001-230, Auftrag `auf-vis-20261001-01`): ein frischer
 * Graph hat keinen Prompt, und die KI-Veredelung von KosmoVis lehnt einen
 * leeren Prompt ab («Prompt ist leer»: die Tiefenkarte gibt die Kubatur vor,
 * Material, Licht und Stimmung stehen nur im Prompt). Bisher ging der Auftrag
 * trotzdem ab, und die Ablehnung kam erst danach.
 *
 * WAHL: ein Hinweis VOR dem Senden, KEIN Anfangs-Prompt. Ein vorgegebener
 * Text wuerde Material, Licht und Stimmung still fuer den Architekten
 * festlegen, und das Bild saehe nach einer Entscheidung aus, die niemand
 * getroffen hat. Der Hinweis steht am Render-Knoten in der Prompt-Zeile (in
 * der Warnfarbe) und am Knopf, BEVOR jemand sendet.
 *
 * BEWUSST NICHT GESPERRT: eine Sperre an der Naht wurde gebaut und gemessen;
 * sie machte 18 bestehende Proben rot, die einen Auftrag ohne Prompt an die
 * Attrappen-Bruecke schicken (u. a. PC2, P-LEERSZENE, P-DREISTANDPUNKTE,
 * K1). Ob ein leerer Prompt gesperrt wird, ist eine Entscheidung ueber
 * fremde Proben und wird im Meldeblatt vorgelegt, nicht hier vorweggenommen.
 *
 * Gilt nur, wenn ein KI-Schritt bestellt ist: «Nur Cycles» und die
 * Strichzeichnung brauchen keinen Prompt.
 */
export const LEERER_PROMPT_HINWEIS =
  'Kein Prompt: die KI-Veredelung lehnt einen leeren Auftrag ab. ' +
  'Verbinde einen Stimmungs- oder Stil-Knoten oder fülle das Auftrags-Formular am Render-Knoten ' +
  '(«… mehr»). Ohne KI-Schritt («Nur Cycles» oder Strichzeichnung) geht es auch ohne Prompt.';

/** B2: fehlt der Prompt fuer einen bestellten KI-Schritt? Reine Funktion. */
export function promptFehltFuerKi(prompt: string, opts: { nurCycles?: boolean; lineart?: boolean }): boolean {
  const kiSchritt = !(opts.nurCycles === true || opts.lineart === true);
  return kiSchritt && prompt.trim() === '';
}

/**
 * B4 (Nachprobe auf-20261001-230): ohne Bruecken-Token lehnt eine Bruecke im
 * Netz jeden Auftrag mit 401 ab (sie verlangt den Token, sobald sie nicht nur
 * auf diesem Rechner lauscht). Der Hinweis kommt darum VOR dem Senden. Er
 * sperrt nichts: eine Bruecke kann bewusst ohne Token offen laufen, und auf
 * diesem Rechner (`localhost`) braucht sie keinen. Reine Funktion.
 */
export const TOKEN_FEHLT_HINWEIS =
  'Kein Brücken-Token gesetzt: eine Brücke im Netz lehnt den Auftrag ohne Token ab. ' +
  'Token in den KosmoVis-Einstellungen eintragen.';

export function tokenHinweisVorDemSenden(basis: string, token: string): string | undefined {
  if (token.trim() !== '') return undefined;
  try {
    const adresse = new URL(basis);
    // Visbox-Mac-Demolauf 0.3.34 (Fund D, 22.10.2026): ein eigenes Adressschema (die Mac-App laedt die
    // Knotenansicht unter `visbox://app/`, die Bruecke ist `visbox://app/bruecke`) ist keine Bruecke im
    // Netz — die App reicht jeden Auftrag selbst weiter, mit ihrer Anmeldung. Der Satz war dort falsch.
    if (adresse.protocol !== 'http:' && adresse.protocol !== 'https:') return undefined;
    const host = adresse.hostname;
    if (host === 'localhost' || host === '127.0.0.1' || host === '[::1]') return undefined;
  } catch {
    return undefined;
  }
  return TOKEN_FEHLT_HINWEIS;
}

export const KEINE_GEOMETRIE_HINWEIS =
  'Kein Render ohne Geometrie — die Szene hat 0 Bauteile (Wände/Decken/Dächer/' +
  'Volumenkörper/Treppen/Rampen/Stützen/Unterzüge/Geländer/FreeMesh/Möbel). ' +
  'Ursache: In KosmoDesign wurde noch nichts gebaut oder geladen. Befehlspalette ' +
  `(${kuerzel('mod+k')}) → «Beispielprojekt Demohaus laden», danach zurück zu KosmoVis. ` +
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
  // E128 (ENTSCHEIDE-2026-09-22): kommt ins Produkt, die Lizenz wird vor der
  // Veroeffentlichung geloest. Darum KEIN Eintrag in NUR_RESEARCH_BACKBONES
  // (E128 ohne Schalter). Am Geraet gemessen (ROADMAP 1632): keine
  // Tiefenfuehrung — Stil und Einsetzen auf einem gerechneten Bild, die
  // formtreue Strecke bleibt bei der Vorgabe.
  'qwen-image-2.1': {
    name: 'Qwen-Image 2.1',
    // L4-18 = A (21.10.2026): derselbe Satz wie am Bild — Wettbewerbsbilder mit Z-Image Turbo.
    hinweis: 'Lizenz offen — nicht für Wettbewerb oder Veröffentlichung · keine Tiefenführung',
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
 * - `nicht-vorgesehen` — seit K1 (29.09.2026, E75): das Feld reist NICHT mehr
 *   mit. Die Gegenseite nimmt es nicht an und weist Bestellungen mit
 *   unbekannten Feldern ab; wir senden es darum nicht (`NICHT_GESENDET`). Es
 *   bleibt im Vertragstext und in der Bedienung, das Bild aendert es nicht.
 * - `ungeprueft` — niemand hat nachgesehen. Steht hier nur, solange die
 *   Messung wirklich aussteht; «ungeprueft» ist eine Auskunft, «vermutlich»
 *   waere keine.
 */
export type Fremdstand = 'gelesen' | 'nicht-gelesen' | 'nicht-vorgesehen' | 'ungeprueft';

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
    stand: 'gelesen',
    gemessenAm: '29.09.2026',
    beleg:
      'Angabe der Gegenseite im Blatt -01 (gebaut am 24.09.2026), hier NICHT nachgemessen: der Wert geht ' +
      'in die Cycles-Rechnung ein. Vorbehalt: er wirkt auf das Cycles-Bild, nicht auf das gelieferte KI-Bild. ' +
      'Die Messung vom 17.09.2026 (nicht gelesen) ist damit ueberholt.',
  },
  {
    feld: 'render.sun.kelvin',
    titel: 'Farbtemperatur',
    zeile: '46',
    stand: 'gelesen',
    gemessenAm: '29.09.2026',
    beleg:
      'Angabe der Gegenseite im Blatt -01 (gebaut am 24.09.2026), hier NICHT nachgemessen: der Wert geht ' +
      'in die Cycles-Rechnung ein. Vorbehalt: er wirkt auf das Cycles-Bild, nicht auf das gelieferte KI-Bild. ' +
      'Die Messung vom 17.09.2026 (nicht gelesen) ist damit ueberholt.',
  },
  {
    feld: 'render.sun.winkelGrad',
    titel: 'Sonnenwinkel',
    zeile: '46',
    stand: 'gelesen',
    gemessenAm: '29.09.2026',
    beleg:
      'Angabe der Gegenseite im Blatt -01 (gebaut am 24.09.2026), hier NICHT nachgemessen: der Wert geht ' +
      'in die Cycles-Rechnung ein. Vorbehalt: er wirkt auf das Cycles-Bild, nicht auf das gelieferte KI-Bild. ' +
      'Die Messung vom 17.09.2026 (nicht gelesen) ist damit ueberholt.',
  },
  {
    feld: 'render.himmel',
    titel: 'Himmel',
    zeile: '47/48',
    stand: 'nicht-vorgesehen',
    gemessenAm: '29.09.2026',
    beleg:
      'Die Gegenseite nimmt das Feld nicht an (E75, auf-20260924-171 K1); wir senden es seit dem 29.09.2026 ' +
      'nicht mehr (NICHT_GESENDET in vis-jobs.ts). Bedienelement und Preset bleiben, das Bild aendert es nicht.',
  },
  {
    feld: 'render.belichtung',
    titel: 'Belichtung',
    zeile: '4',
    stand: 'nicht-vorgesehen',
    gemessenAm: '29.09.2026',
    beleg:
      'Die Gegenseite nimmt das Feld nicht an (E75, auf-20260924-171 K1); wir senden es seit dem 29.09.2026 ' +
      'nicht mehr (NICHT_GESENDET in vis-jobs.ts). Bedienelement und Preset bleiben, das Bild aendert es nicht.',
  },
  {
    feld: 'render.rauschschwelle',
    titel: 'Rauschschwelle',
    zeile: '51',
    stand: 'nicht-vorgesehen',
    gemessenAm: '29.09.2026',
    beleg:
      'Die Gegenseite nimmt das Feld nicht an (E75, auf-20260924-171 K1); wir senden es seit dem 29.09.2026 ' +
      'nicht mehr (NICHT_GESENDET in vis-jobs.ts). Bedienelement und Preset bleiben, das Bild aendert es nicht.',
  },
  {
    feld: 'render.environment',
    titel: 'Stimmung',
    zeile: '—',
    // Bauplan «Neue Knoten» F3 (Visbox-Entscheide 110/113): seit Visbox 0.3.5 liest der Heim-PC
    // `render.environment` (Himmelsbild als Welt in Blender, acht Stimmungen; Protokoll 74 §153,
    // Fixtures `kv-stimmung-*.json`) und nennt im Ergebnis, womit er gerechnet hat
    // (`angewandt.environment`). Bis dahin: nicht vorgesehen (E75, auf-20260924-171 K1).
    stand: 'gelesen',
    gemessenAm: '20.10.2026',
    beleg:
      'Der Heim-PC rechnet die Stimmung mit Himmelsbild in Blender und meldet sie in angewandt.environment ' +
      '(Visbox 0.3.5, Fixtures kv-stimmung-*.json). Seit dem Knoten «Stimmung» wieder gesendet.',
  },
  {
    feld: 'komposition',
    titel: 'Komposition',
    zeile: '—',
    stand: 'nicht-vorgesehen',
    gemessenAm: '29.09.2026',
    beleg:
      'Die Gegenseite nimmt das Feld nicht an und es widerspricht unseren Kameras (E75, auf-20260924-171 K1); ' +
      'der Inhalt steht in cameras[].fov und render.resolution. Gesendet wird es nicht (NICHT_GESENDET).',
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

/** K1: die Felder, die NICHT mehr mitreisen — gezaehlt aus der Tabelle. */
export function fremdnahtNichtGesendet(): readonly string[] {
  return FREMDNAHT.filter((f) => f.stand === 'nicht-vorgesehen').map((f) => f.feld);
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
  const aus = FREMDNAHT.filter((f) => f.stand === 'nicht-vorgesehen' || f.stand === 'nicht-gelesen');
  // Der jüngste Messtag, nicht der erste Eintrag: die Tabelle wird zeilenweise
  // nachgezogen, und ein Datum, das älter ist als seine Zeilen, wäre falsch.
  const tag =
    FREMDNAHT.map((f) => f.gemessenAm)
      .sort((a, b) => a.split('.').reverse().join('').localeCompare(b.split('.').reverse().join('')))
      .at(-1) ?? '';
  return (
    `Gemessen ${tag}: die Bildseite wertet ${gelesen} von ${FREMDNAHT.length} Auftragsfeldern aus. ` +
    `${aus.length} sind nicht bedient und gehen nicht mehr mit — ${aus.map((f) => f.titel).join(', ')}.`
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

/**
 * P11 (V016-SPEZ, «Szene vor dem Versand pruefen») — validiert den
 * AUSGEHENDEN `scene`-Block gegen `RenderScene` (kosmovis.render-scene/v1,
 * `@kosmo/contracts`), bevor `postRenderJob` ihn absendet. Derselbe
 * `path: message`-Stil wie `parseJob` unten (dort für eingehende
 * Bridge-Antworten) — hier für die ausgehende Bestellung gespiegelt: WELCHES
 * Feld den Vertrag verletzt, nicht nur DASS er verletzt ist. Wirft, sendet
 * nichts.
 */
function pruefeSzeneVorVersand(scene: unknown): void {
  const geprueft = RenderScene.safeParse(scene);
  if (!geprueft.success) {
    const details = geprueft.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join('; ');
    throw new Error(`Szene verletzt den Vertrag (render-scene/v1) — nicht gesendet: ${details}`);
  }
}

/**
 * K1 (auf-20260924-171, Owner-Entscheid E75 «nur Felder senden, die die
 * Gegenseite annimmt»): diese fuenf Felder stehen im Vertragstext
 * (`render-scene.ts`), gehen aber NICHT mehr an /jobs. Die Bildseite weist
 * Bestellungen mit Feldern ab, die sie nicht kennt — ein Demohaus mit Preset
 * blieb dort liegen. EINE Liste, EINE Stelle (`ohneAbgewieseneFelder`): ein
 * sechstes Feld gehoert hierher und nirgends sonst hin. Bedienelemente,
 * Presets und gespeicherte Parameter bleiben unveraendert; der Inhalt steht
 * schon in `cameras[].fov` und `render.resolution`.
 */
export const NICHT_GESENDET = {
  /** Oberste Ebene der Szene. */
  szene: ['komposition'],
  /** Unterfelder von `render`. */
  render: ['himmel', 'belichtung', 'rauschschwelle'],
} as const;

function ohneAbgewieseneFelder<T extends { render: Record<string, unknown> }>(scene: T): T {
  const kopie: Record<string, unknown> = { ...scene, render: { ...scene.render } };
  for (const feld of NICHT_GESENDET.szene) delete kopie[feld];
  for (const feld of NICHT_GESENDET.render) delete (kopie['render'] as Record<string, unknown>)[feld];
  return kopie as T;
}

/**
 * Der angelegte Job plus, was die App beim Senden weiss und der Vertrag nicht
 * traegt: `umgebungFehlt` (Runde 29) — der Grund, warum der sichtbare Splat
 * nicht als Umgebung mitging. Die Aufrufer legen ihn an den Lauf.
 */
export type GesendeterJob = JobRecord & { umgebungFehlt?: string };

/**
 * Geraeteprobe R59: Eine gewoehnliche Punktwolke (.ply mit Lage und Farbe, ohne
 * die Felder eines Gaussian Splat: Deckkraft `opacity`, Groesse `scale_*`, Farbe `f_dc_*`) ging
 * als Splat-Umgebung in die Bestellung, und der Heim-PC brach den ganzen Auftrag ab («kein
 * 3DGS-Splat»). Sie geht darum nicht mit; der Grund steht wie jeder andere Grund ohne Umgebung
 * an der Karte.
 *
 * WORAN ERKANNT, ohne die Datei noch einmal zu lesen: Der Import legt eine PLY ohne `scale_*`
 * mit EINER Punktgroesse fuer alle Punkte an (`splat-import.ts`, `hatGroessen` →
 * `PUNKT_GROESSE_STANDARD`); ein Splat traegt eine Groesse je Punkt. `sizes` als Zahl heisst
 * also: die Quelle hat keine Gauss-Felder. Fehlt nur `opacity` oder `f_dc_*`, faengt es der
 * Heim-PC am PLY-Kopf (laesst die Umgebung mit Satz weg, statt abzubrechen).
 *
 * `cloud` ist optional, damit ein Zustand ohne Wolke (Visbox: keine Splat-Ebene) nichts aendert.
 */
export function punktwolkeOhneSplatFelder(zustand: {
  ebene: { readonly name: string } | null;
  cloud?: { readonly sizes: Float32Array | number } | null;
}): string | null {
  if (!zustand.ebene || !zustand.cloud || typeof zustand.cloud.sizes !== 'number') return null;
  return (
    `Punktwolke «${zustand.ebene.name}» ist kein Splat (ohne Deckkraft und Grösse je Punkt) — ` +
    'sie geht nicht als Umgebung mit, der Render läuft ohne sie'
  );
}

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
  environment?: { preset: VisStimmungId; rotationGrad?: number };
  /**
   * Bauplan «Neue Knoten» F2 (Entscheide 109/113 (3)): die Einstellungen der Auto-Kamera
   * (`RenderScene.cameras_auto`, Vorschlag V). Nur ohne Kameraliste und ohne Skizze; dann geht
   * auch keine Innenansicht mit (der Vertrag weist beides zusammen ab).
   */
  kamerasAuto?: KameraAutoWahl;
  /** F2: Perspektive der von Hand gestellten Standpunkte (`CameraSpec.perspektive`). */
  kamerasPerspektive?: 'senkrecht' | 'frei';
  /** F4 (Entscheid 111): Materialien je Bauteil-Art (`render.materialien`, Vorschlag V). */
  materialien?: Partial<Record<string, MaterialWahlAuftrag>>;
  /**
   * Knoten «Umfeld» (Visbox-Owner-Wunsch 24.10.2026): der Wunsch (`vis.umfeld`). Nur mit Blender-Grundlage
   * — nicht mit Skizze oder Strichzeichnung; ohne Knoten bleibt der Auftrag Zeichen fuer Zeichen wie bisher.
   */
  umfeld?: UmfeldWahl;
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
  backbone?: 'z-image-turbo' | 'qwen' | 'flux2-klein' | 'flux-krea' | 'sdxl' | 'qwen-image-2.1';
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
  /**
   * Owner-Entscheid 96 (Visbox, 15.10.2026) — DIE SKIZZE FUEHRT DAS BILD.
   * Spiegelt `RenderScene.skizze` (`quelle: 'mappe'`, der Name schon
   * aufgeloest, s. `skizzeZurBestellung`). Mit Skizze entsteht EIN Bild —
   * vom Standpunkt des Bildes, auf das gezeichnet wurde, sonst dem der Mappe
   * (Entscheid 96b, die Bildseite waehlt ihn): keine Kameraliste, keine Innenansicht, keine
   * Umgebung — so verlangt es der Vertrag, und so rechnet die Visbox-Seite.
   * Ohne Parameter bleibt der Job Zeichen fuer Zeichen wie bisher.
   */
  skizze?: SkizzeDerBestellung;
  /**
   * L24 Bildweg Varianten (E246): der Entwurf als Ebenenkombination (E222). Gesendet wird dann
   * nur, was in ihr sichtbar ist (`docFuerEbenen`) — so liegen Volumenvarianten im selben
   * Dokument und werden je fuer sich gerechnet. Ohne Parameter Zeichen fuer Zeichen wie bisher.
   */
  entwurf?: EbenenKombination;
  /**
   * Nr. 85 Paket 2 (Entscheid 98, Schritt 1 «Grundlage rendern»): welche Ebenen je Kamera
   * zurueckkommen (`RenderScene.render.passes`). Ohne Parameter kein Feld, wie bisher.
   */
  passes?: 'alle' | readonly ('schoenbild' | 'tiefe' | 'material-id')[];
  /** Nr. 85 (Schritt 2 «Variante erzeugen»): die Grundlage (`vis.grundlage`). Nie mit `nurCycles`. */
  grundlage?: string;
  /** Nr. 85/84 (Entscheid 98a): fester Startwert des KI-Schritts (`vis.seed`). */
  seed?: number;
  /** Entscheid 104: Guete des KI-Schritts (`vis.guete`). Ohne Parameter kein Feld — dann voll, wie bisher. */
  guete?: 'vorschau' | 'voll';
  /** Visbox-Entscheid 149: ein bewusst freies Bild (`vis.freies_bild: true`). Ohne Parameter kein Feld. */
  freiesBild?: boolean;
  /**
   * Visbox-Mac-Probe 0.3.66: der Auftrag ist eine Variante (`vis.variante: true`) — die Gegenseite rechnet sie
   * ohne eigene Staerke mit 0,7, auch ohne `grundlage`. Ohne Parameter kein Feld.
   */
  istVariante?: boolean;
}): Promise<GesendeterJob> {
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
  // L24 Bildweg Varianten (E246): das Modell der Bestellung — ohne Entwurf das ganze Dokument.
  const szene = params.entwurf ? docFuerEbenen(doc, params.entwurf) : doc;
  // B117 SCHRITT 2 (Owner-Entscheid E57): die EINE Bedingung, ob dieser
  // Auftrag als IFC/`interior` geht oder byte-identisch zum Stand vor
  // Schritt 2 bleibt (glb, kein `interior`, «Innenraum» gefiltert).
  // Entscheid 96: eine Skizze ist EIN Bild — mit ihr geht keine Innenansicht (Vertrag, superRefine).
  // F2: mit `cameras_auto` rechnet die Bildseite ihre Standpunkte selbst — eine Innenansicht geht
  // dazu nicht (Vertrag); ohne Auto-Kamera-Einstellungen bleibt es wie bisher.
  const mitKamerasAuto = params.kamerasAuto !== undefined && params.skizze === undefined && !(params.kameras && params.kameras.length > 0);
  const interiorMoeglich = interiorFaehrt(doc) && params.skizze === undefined && !mitKamerasAuto;
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
  //
  // Fehler-Nachgang 20.10.2026 (Owner am Mac: «Variante erzeugen» → «Der Heim-PC ist nicht
  // erreicht: Er hat nicht rechtzeitig geantwortet.»): das Modell wird erst gebaut, wenn es
  // auch hinausgeht (`baueModell`, unten). Mit `vis.grundlage` geht es nicht hinaus — die
  // Gegenseite nimmt Kameras und Passes der Grundlage und rechnet kein Blender.
  const baueModell = (): ArrayBuffer | string => {
    const glb = exportGlb(szene, doc.settings.projectName);
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
    return interiorMoeglich ? exportIfc(szene) : glb;
  };
  const ohneModell = modellBleibtDaheim(params);
  let modell: ArrayBuffer | string | undefined = ohneModell ? undefined : baueModell();
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
  // «Kamera aus 3D-Ansicht» (14.10.2026): hier steht das Bestellformat fest — wer einen
  // vertikalen Winkel mitbringt, bekommt `fov` horizontal fuer GENAU dieses Format
  // (`kamerasFuerBestellformat`, Kern). Alle anderen Standpunkte bleiben Zahl fuer Zahl.
  const bestellformat = params.resolution ?? BESTELLFORMAT_VORGABE;
  const kamerasImFormat = params.kameras ? kamerasFuerBestellformat(params.kameras, bestellformat) : undefined;
  // Entscheid 96: mit Skizze keine Kameraliste — den Standpunkt waehlt die Bildseite (96b: der des
  // Bildes unter der Skizze, sonst der der Mappe; Vertrag).
  const kamerasOhneInnenraum =
    params.skizze !== undefined
      ? undefined
      : kamerasImFormat?.filter((k) => istUeberDiesenWegBestellbar(k.name, interiorMoeglich));
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
          ...(params.kamerasPerspektive ? { perspektive: params.kamerasPerspektive } : {}),
        }))
      : params.skizze !== undefined
        ? ('auto' as const)
        : (params.kameraWahl ?? 'auto'),
    render: {
      resolution: bestellformat,
      samples: params.samples,
      faithful: params.faithful,
      ...(params.sun ? { sun: params.sun } : {}),
      ...(params.environment ? { environment: params.environment } : {}),
      // F4: nur mit mindestens einer Bauteil-Art (ein leeres Objekt weist der Vertrag ab).
      ...(params.materialien && Object.keys(params.materialien).length > 0 ? { materialien: params.materialien } : {}),
      // A2/16.09.2026 (Zeilen 4, 47, 48, 51): jedes der drei Felder kommt NUR
      // mit, wenn es bestellt wurde. Ein leeres Objekt statt Weglassen waere
      // hier das Gegenteil von additiv — der Vertrag unterscheidet «nicht
      // bestellt» von «auf null bestellt».
      ...(params.himmel ? { himmel: params.himmel } : {}),
      ...(params.belichtung ? { belichtung: params.belichtung } : {}),
      ...(params.rauschschwelle !== undefined ? { rauschschwelle: params.rauschschwelle } : {}),
      // Nr. 85 Paket 2: nur «Grundlage rendern» bestellt die Ebenen — sonst kein Feld.
      ...(params.passes !== undefined ? { passes: params.passes === 'alle' ? ('alle' as const) : [...params.passes] } : {}),
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
      // Nr. 85 Paket 2: Grundlage und Startwert nur, wenn bestellt — sonst Zeichen fuer Zeichen
      // wie bisher. Der Vertrag weist `grundlage` zusammen mit `skip` ab (superRefine).
      ...(params.grundlage !== undefined ? { grundlage: params.grundlage } : {}),
      ...(params.seed !== undefined ? { seed: params.seed } : {}),
      // Guete nur fuer den KI-Schritt: mit skip (Strich/nur Cycles) faellt sie weg,
      // sonst wiese der Vertrag den Auftrag ab.
      ...(params.guete !== undefined && !(lineArt || params.nurCycles === true) ? { guete: params.guete } : {}),
      // Knoten «Umfeld»: nur mit Blender-Grundlage (eine Skizze und die Strichzeichnung rechnen keine).
      ...(params.umfeld && !lineArt && params.skizze === undefined ? { umfeld: params.umfeld } : {}),
      // Visbox-Entscheid 149: das freie Bild nur mit KI-Schritt und ohne Skizze (die Skizze fuehrt ihr
      // eigenes Bild; mit skip wiese der Vertrag ab). Sonst kein Feld — Zeichen fuer Zeichen wie bisher.
      ...(params.freiesBild === true && !(lineArt || params.nurCycles === true) && params.skizze === undefined
        ? { freies_bild: true }
        : {}),
      // Visbox-Mac-Probe 0.3.66: die Variante als solche — nur mit KI-Schritt und ohne Skizze (wie das freie Bild).
      ...(params.istVariante === true && !(lineArt || params.nurCycles === true) && params.skizze === undefined
        ? { variante: true }
        : {}),
    },
    ...(params.komposition ? { komposition: params.komposition } : {}),
    // F2: neben `cameras: 'auto'` — sonst Zeichen fuer Zeichen wie bisher.
    ...(mitKamerasAuto ? { cameras_auto: params.kamerasAuto } : {}),
    // B117 SCHRITT 2 (Owner-Entscheid E57): `interior`/IFC kommen NUR, wenn
    // `interiorMoeglich` wahr ist — ohne Zonen bleibt dieser Teil der Szene
    // Zeichen fuer Zeichen wie vor Schritt 2 (kein `interior`-Feld,
    // `format:'glb'`, s. Zusicherung A im Bericht).
    ...(interiorMoeglich ? { interior: { rooms: 'auto' as const } } : {}),
    out: '',
    geometry: { path: '', format: interiorMoeglich ? ('ifc' as const) : ('glb' as const) },
    // Entscheid 96: NUR mit Skizze — ohne bleibt die Szene Zeichen fuer Zeichen wie bisher.
    ...(params.skizze !== undefined
      ? {
          skizze: {
            quelle: 'mappe' as const,
            name: params.skizze.name,
            ...(params.skizze.anweisung ? { anweisung: params.skizze.anweisung } : {}),
          },
        }
      : {}),
  };
  // P11 (V016-SPEZ, «Szene vor dem Versand pruefen») — DER LETZTE PUNKT, an
  // dem noch nichts gesendet ist: die Szene lief bis hierhin UNGEPRUEFT an
  // die Bridge — kein `RenderScene.safeParse` sah die ausgehende Bestellung
  // je, nur eingehende Antworten liefen durch `parseJob`. Ein Verstoss wäre
  // entweder als kryptischer Bridge-Fehler zurückgekommen oder,
  // schlimmer, als eine Bestellung, die die Gegenseite anders interpretiert
  // als gemeint. Wirft VOR `bridgeFetch` — kein Byte geht raus, wenn die
  // Szene den eigenen Vertrag verletzt.
  // lw-splat-context (08.10.2026): die sichtbare Splat-Ebene reist als
  // Umgebung mit (`RenderScene.context`) — aber nur, wenn der Vertrag das
  // Feld kennt (`SPLAT_CONTEXT_IM_VERTRAG`, die eine Stelle in
  // `splat-render-kontext.ts`). Geht sie nicht mit, steht der Grund
  // sichtbar da, statt dass der Splat still im Bild fehlt.
  const splat = useSplatEbene.getState();
  // Entscheid 96: mit Skizze keine Umgebung — die Skizze rechnet auf ihrer Unterlage.
  const splatRoh =
    splat.ebene && params.skizze === undefined
      ? splatRenderKontext({ ebene: splat.ebene, handLage: splat.handLage })
      : null;
  // Geraeteprobe R59: eine Punktwolke ohne Splat-Felder geht nicht als Umgebung mit — der Grund
  // steht in der Meldung und an der Karte («Ohne Umgebung: …»), der Render laeuft ohne sie.
  const ohneSplatFelder = splatRoh?.ok ? punktwolkeOhneSplatFelder(splat) : null;
  const splatTeil = szeneMitSplatKontext(
    scene,
    ohneSplatFelder !== null ? { ok: false, grund: ohneSplatFelder } : splatRoh,
  );
  if (splatTeil.hinweis) melde(`Ohne Umgebung bestellt: ${splatTeil.hinweis}`, { ton: 'info' });
  // K1: gepruefte UND gesendete Szene ist dieselbe — die fuenf abgewiesenen
  // Felder sind vorher raus.
  const gesendet = ohneAbgewieseneFelder(splatTeil.szene);
  pruefeSzeneVorVersand(gesendet);
  // Y3 P-IFC-BESTELLUNG-Muster (`bake-auftrag.ts:116`, woertlich uebernommen).
  const dateiname = interiorMoeglich ? 'model.ifc' : 'model.glb';
  const mimeTyp = interiorMoeglich ? 'application/x-step' : 'model/gltf-binary';
  const sende = (mitModell: boolean): Promise<Response> => {
    const form = new FormData();
    form.append('scene', JSON.stringify(gesendet));
    if (mitModell) {
      modell ??= baueModell();
      form.append('model', new Blob([modell], { type: mimeTyp }), dateiname);
    }
    // Fehler-Nachgang 20.10.2026: die Anlage traegt das Modell (mehrere MB) und die Gegenseite
    // nimmt es unter einer Sperre an — sie bekommt ihre eigene, laengere Zeitgrenze.
    return bridgeFetch(bridgeRoutes.jobs, { method: 'POST', body: form, signal: AbortSignal.timeout(BRIDGE_AUFTRAG_ZEITGRENZE_MS) });
  };
  let res = await sende(!ohneModell);
  if (ohneModell && !res.ok && MODELL_NACHREICHEN_BEI.has(res.status)) {
    // Die Gegenseite nimmt die Variante ohne Modell nicht an (eine Bruecke ohne den Vorschlag
    // «model optional mit Grundlage» antwortet 422, der Heim-PC ohne die Grundlage laut mit
    // einem Mangel). Einmal MIT Modell — danach gilt ihre Antwort, wie sie ist.
    melde(MODELL_NACHGEREICHT_SATZ, { ton: 'info' });
    res = await sende(true);
  }
  if (!res.ok) throw new BridgeHttpError(res.status, 'Bridge antwortet mit');
  const job = parseJob(await res.json());
  return splatTeil.hinweis ? { ...job, umgebungFehlt: splatTeil.hinweis } : job;
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
/** Satz, wenn «Kamera aus 3D-Ansicht» am Render-Knoten haengt und noch keine Kamera traegt. */
export const KAMERA_AUS_3D_FEHLT_HINWEIS =
  'Der Knoten «Kamera aus 3D-Ansicht» trägt noch keine Kamera — erst die 3D-Ansicht öffnen, dann «Kamera übernehmen».';

/**
 * Satz, wenn das Blickfeld der Kamera aus der 3D-Ansicht fuer dieses Format ausserhalb des
 * Vertrags liegt (`CameraSpec.fov` 10–120°) — sonst `null`. Andere Standpunkte prueft das hier
 * nicht (sie kommen mit ihrem eigenen, schon geprueften Winkel).
 */
export function blickfeldAusserhalbHinweis(
  kameras: readonly AutoKameraStandpunkt[] | undefined,
  aufloesung: readonly [number, number] | undefined,
): string | null {
  if (!kameras) return null;
  const format = aufloesung ?? BESTELLFORMAT_VORGABE;
  for (const k of kamerasFuerBestellformat(kameras, format)) {
    if (k.fovVertikalGrad === undefined || fovImVertrag(k.fov)) continue;
    const grad = Number.isFinite(k.fov) ? `${Math.round(k.fov)}°` : 'nicht bestimmbar';
    return (
      `«${KAMERA_AUS_3D_NAME}»: das Blickfeld waagrecht (${grad} bei ${format[0]} × ${format[1]}) liegt ausserhalb ` +
      'von 10–120° — in der 3D-Ansicht enger einstellen oder ein anderes Format wählen, dann «Kamera übernehmen».'
    );
  }
  return null;
}

/**
 * L24 Bildweg Varianten (E246, `varianten.ts`): EINE Zelle-Gruppe der Varianten — derselbe Weg
 * wie «Ausführen» am Render-Knoten, mit vier Ersetzungen. Ausgewertet wird `graph` (die Kopie
 * mit der gewaehlten Stimmung, `graphMitStimmung`), bestellt werden `kameras` statt der am
 * Knoten verbundenen, `promptVorsatz` steht vor dem Prompt (nur wenn keine Stimmung in den
 * Render-Knoten floss), und `entwurf` waehlt das Modell. Der Lauf steht unter `laufId`, nicht
 * unter dem Render-Knoten — dessen eigenes Bild bleibt, wie es war.
 */
export interface VarianteDesAuftrags {
  graph: VisGraph;
  laufId: string;
  kameras?: AutoKameraStandpunkt[];
  /**
   * Visbox-Mac-Probe 0.3.66: nur diese Richtungen der Auto-Kamera (Kuerzel des Heim-PCs, z. B. `['sSE']`) —
   * `cameras_auto.richtungen` statt aller Richtungen. Nur ohne `kameras` (Visbox: der Kern kennt keine Standpunkte).
   */
  richtungen?: string[];
  promptVorsatz?: string;
  entwurf?: EbenenKombination;
}

/**
 * Nr. 85 Paket 2 (98b): der Stand, mit dem eine Grundlage JETZT gerechnet wuerde — dieselbe
 * Zusammenfuehrung wie beim Senden (Bedienung schlaegt Preset, `sunDetails` nur mit Stand).
 * EINE Stelle fuer Knopf, Anzeige und Versand, damit «veraltet» am Knoten und die Sperre im
 * Versand nie auseinanderlaufen.
 */
export function grundlageStandFuerKnoten(
  doc: KosmoDoc,
  roh: Pick<VisRenderAuftrag, 'samples' | 'resolution' | 'sun' | 'kameras'> &
    Partial<Pick<VisRenderAuftrag, 'umgebung' | 'kamerasAuto' | 'kamerasPerspektive' | 'materialien' | 'umfeld'>>,
  params: Record<string, string | number | boolean>,
  opts?: { aufloesung?: readonly [number, number]; kameraWahl?: 'auto' | 'saved' },
): string {
  const bedienung = renderBedienungAusParams(params);
  const sun = roh.sun ? { ...roh.sun, ...bedienung.sunDetails } : undefined;
  return grundlageStand(doc, {
    samples: bedienung.samples ?? roh.samples,
    resolution: opts?.aufloesung ?? bedienung.resolution ?? roh.resolution,
    sun,
    himmel: bedienung.himmel,
    kameras: roh.kameras,
    kameraWahl: opts?.kameraWahl,
    // Neue Knoten: Stimmung (Licht in Blender), Auto-Kamera und Materialien legen die Grundlage
    // mit fest — jede Stimmung hat ihre eigene (Entscheid 110 A, Nr. 85).
    ...(roh.umgebung !== undefined ? { umgebung: roh.umgebung } : {}),
    ...(roh.kamerasAuto !== undefined ? { kamerasAuto: roh.kamerasAuto } : {}),
    ...(roh.kamerasPerspektive !== undefined ? { kamerasPerspektive: roh.kamerasPerspektive } : {}),
    ...(roh.materialien !== undefined ? { materialien: roh.materialien } : {}),
    // Knoten «Umfeld»: Baeume und Autos stehen im Cycles-Bild — eine eigene Grundlage.
    ...(roh.umfeld !== undefined ? { umfeld: roh.umfeld } : {}),
  });
}

/**
 * Visbox-Gegenprobe 328 (S6/S7) und 330 (B2): die EINE Regel, ob eine Variante auf der Grundlage des
 * Render-Knotens rechnet — dann gehen `vis.grundlage` und ihr EINER Startwert (`vis.seed`) mit, kein
 * Blender-Lauf und keine Auswahl aus drei Startwerten. Nur ohne eigenen Entwurf (eine
 * Ebenenkombination ist ein anderes Modell, das der Stand nicht sieht), ohne Skizze, Strichzeichnung
 * oder «nur Cycles», und nur, wenn am Knoten eine Grundlage GENAU dieses Stands liegt (auch eine
 * gemerkte). `sendeGraphRenderAuftrag` sendet danach, die Zeitschaetzung des Varianten-Knotens
 * (`varianten.ts`) rechnet danach — beide fragen hier, damit Anzeige und Bestellung nicht
 * auseinanderlaufen.
 */
export function grundlageDerVariante(
  params: Record<string, string | number | boolean> | undefined,
  standJetzt: string,
  lage: { entwurf: boolean; ohneKi: boolean },
): GrundlageAmKnoten | null {
  if (lage.entwurf || lage.ohneKi) return null;
  const g = grundlageAmKnoten(params, standJetzt);
  return g && g.stand === standJetzt ? g : null;
}

/**
 * Geraeteprobe R56 (HomeStation, 23.10.2026): der Stand, unter dem die Grundlage einer Variante am
 * Render-Knoten liegt. Zuerst der Stand der Variante selbst (`standVariante`, ihre Kameras). Liegt
 * dafuer keine Grundlage, aber bestellt die Variante nur einen TEIL der Kameras des Render-Knotens
 * (gleiche Kennung, gleiche Pose — `kamerasSindTeilmenge`), dann der Stand mit ALLEN Kameras des
 * Knotens: Die Grundlage dieses Stands enthaelt die bestellten Kameras schon fertig. Bis hierhin
 * rechnete eine Variante mit Eingang und Übersicht von drei Kameras die Grundlage neu (148 s statt
 * rund 60 s). Eine neue oder verschobene Kamera bleibt nicht passend.
 *
 * Visbox-Mac-Probe 0.3.66: dasselbe fuer einen Teil der RICHTUNGEN der Auto-Kamera (`varianteRichtungen`,
 * `vis_varianten` mit `standpunkte`): Sind alle bestellten Richtungen unter denen, die die Grundlage des
 * Render-Knotens rechnete (die des Knotens «Kamera», sonst die des Heim-PCs), gilt deren Stand — sonst rechnete
 * eine Variante mit einer von vier Richtungen das Grundbild neu.
 */
export function standDerGrundlageFuerVariante(
  doc: KosmoDoc,
  rohKnoten: Parameters<typeof grundlageStandFuerKnoten>[1],
  varianteKameras: readonly AutoKameraStandpunkt[] | undefined,
  params: Record<string, string | number | boolean>,
  standVariante: string,
  opts?: { aufloesung?: readonly [number, number]; kameraWahl?: 'auto' | 'saved' },
  varianteRichtungen?: readonly string[],
): string {
  const g = grundlageAmKnoten(params, standVariante);
  if (g && g.stand === standVariante) return standVariante;
  if (varianteRichtungen && varianteRichtungen.length > 0 && !varianteKameras) {
    const da = rohKnoten.kamerasAuto?.richtungen ?? heimStandpunkte()?.standpunkte.map((h) => h.kuerzel);
    const teil = !!da && (rohKnoten.kameras ?? []).length === 0 && varianteRichtungen.every((r) => da.includes(r));
    return teil ? grundlageStandFuerKnoten(doc, rohKnoten, params, opts) : standVariante;
  }
  if (!varianteKameras || !kamerasSindTeilmenge(varianteKameras, rohKnoten.kameras)) return standVariante;
  return grundlageStandFuerKnoten(doc, rohKnoten, params, opts);
}

/** Visbox-Mac-Probe 0.3.66: der Stand des Render-Knotens im Graph des Dokuments (ohne die Stimmung einer Variante). */
function standDesRenderKnotens(
  doc: KosmoDoc,
  graphId: string,
  nodeId: string,
  opts?: { aufloesung?: readonly [number, number]; kameraWahl?: 'auto' | 'saved' },
): string | undefined {
  const g = doc.get<VisGraph>(graphId);
  const roh = g ? evaluiereGraph(doc, g).renderAuftraege.get(nodeId) : undefined;
  const node = g?.nodes.find((n) => n.id === nodeId);
  return roh && node ? grundlageStandFuerKnoten(doc, roh, node.params ?? {}, opts) : undefined;
}

/** Visbox-Mac-Probe 0.3.66: der Auftrag mit nur den bestellten Richtungen der Auto-Kamera (`cameras_auto`). */
function mitRichtungen<T extends { kamerasAuto?: KameraAutoWahl }>(roh: T, richtungen: readonly string[] | undefined): T {
  if (!richtungen || richtungen.length === 0) return roh;
  return { ...roh, kamerasAuto: { ...(roh.kamerasAuto ?? {}), richtungen: [...richtungen] } };
}

/**
 * Gegenprobe 330 (B2): Rechnet die Variante dieses Graphen (mit der Stimmung der Zelle) auf der
 * Grundlage des Render-Knotens? Derselbe Weg wie beim Senden: Auswertung des Graphen, die eigenen
 * Kameras statt des Eingangs, der Stand mit den Zahlen der Bedienung — dann `grundlageDerVariante`.
 */
export function varianteAufGrundlage(
  doc: KosmoDoc,
  graph: VisGraph,
  renderId: string,
  variante?: { kameras?: AutoKameraStandpunkt[]; entwurf?: EbenenKombination; richtungen?: string[] },
): boolean {
  const rohKnoten = evaluiereGraph(doc, graph).renderAuftraege.get(renderId);
  const node = graph.nodes.find((n) => n.id === renderId);
  if (!rohKnoten || !node) return false;
  const roh = variante?.kameras ? { ...rohKnoten, kameras: variante.kameras } : mitRichtungen(rohKnoten, variante?.richtungen);
  const params = node.params ?? {};
  const ohneKi = params['lineart'] === true || roh.nurCycles === true || !!roh.skizze;
  // R56: auch eine Teilmenge der Kameras des Knotens rechnet auf dessen Grundlage.
  const stand = standDerGrundlageFuerVariante(doc, rohKnoten, variante?.kameras, params, grundlageStandFuerKnoten(doc, roh, params), undefined, variante?.richtungen);
  return grundlageDerVariante(params, stand, { entwurf: !!variante?.entwurf, ohneKi }) !== null;
}

/**
 * «Grundlage je Stand» (Bauplan «Neue Knoten», Entscheid 110 A): nach einer Aenderung an einem
 * Knoten, der die Grundlage mitbestimmt (Stimmung, Kamera, Oberflaeche …), wird an jedem
 * nachgeschalteten Render-Knoten die schon gerechnete Grundlage DIESES Stands wieder die gezeigte —
 * zurueck zur vorigen Stimmung heisst dann: Variante sofort, ohne neue Grundlage. Gibt die Zahl der
 * umgestellten Render-Knoten zurueck.
 */
export function grundlagenNachfuehren(graphId: string): number {
  const { doc, runCommand } = useProject.getState();
  const graph = doc.get<VisGraph>(graphId);
  if (!graph) return 0;
  const auswertung = evaluiereGraph(doc, graph);
  let n = 0;
  for (const node of graph.nodes) {
    if (node.typ !== 'render') continue;
    const roh = auswertung.renderAuftraege.get(node.id);
    if (!roh) continue;
    const stand = grundlageStandFuerKnoten(doc, roh, node.params ?? {});
    const neu = grundlageFuerStand(node.params, stand);
    if (!neu) continue;
    try {
      runCommand('vis.nodeParametrieren', { graphId, nodeId: node.id, params: neu });
      n++;
    } catch (err) {
      meldeFehler(err);
    }
  }
  return n;
}

/**
 * Ist dieser Render-Auftrag aus dem Dokument FRISCH — noch nie gesehen? (Visbox-Entscheid 146,
 * 24.10.2026.) Der Ausfuehrer (`VisWorkspace.tsx`) sendet nur einen frischen Auftrag. Bis dahin hiess
 * «frisch» nur «eine andere Objekt-Referenz als zuletzt» — nahm Rueckgaengig (Strg+Z, oder «Claudes
 * letzten Schritt zurücknehmen») einen zweiten Auftrag zurueck, kam der ERSTE als andere Referenz
 * zurueck und wurde noch einmal gesendet: ein Zuruecknehmen startete die Grafikkarte. Jetzt merkt sich
 * der Ausfuehrer jeden gesehenen Auftrag (`gesehen`), und ein zurueckgeholter startet nichts.
 * Merkt den Auftrag zugleich als gesehen.
 */
export function istFrischerAuftrag(gesehen: WeakSet<object>, auftrag: object | null | undefined): boolean {
  if (!auftrag || gesehen.has(auftrag)) return false;
  gesehen.add(auftrag);
  return true;
}

export function sendeGraphRenderAuftrag(
  graphId: string,
  nodeId: string,
  environment?: { preset: VisStimmungId; rotationGrad?: number },
  opts?: {
    kameraWahl?: 'auto' | 'saved';
    backbone?: 'z-image-turbo' | 'qwen' | 'flux2-klein' | 'flux-krea' | 'sdxl' | 'qwen-image-2.1';
    aufloesung?: readonly [number, number];
    variante?: VarianteDesAuftrags;
    /**
     * Nr. 85 Paket 2 (Entscheid 98): die zwei Knoepfe am Render-Knoten. `'grundlage'` bestellt
     * nur Blender (`vis.skip`, `render.passes: 'alle'`); `'variante'` den KI-Schritt auf der
     * Grundlage des Knotens mit ihrem Startwert — und sendet NICHT, wenn keine da ist oder sie
     * veraltet ist (98b). Ohne `stufe` ein gewoehnlicher Auftrag wie bisher (Kosmo, Insel).
     */
    stufe?: 'grundlage' | 'variante';
    /**
     * Befund B1 (306): nur der Knopf «Grundlage rendern» der Knotenansicht setzt das. Dann — und nur
     * bei einer reinen Grundlage-Bestellung (keine Variante, keine Guete) fuer genau denselben Stand —
     * wird die bestehende Grundlage genannt statt neu gesendet. Alle anderen Wege senden wie bisher.
     */
    wiederverwenden?: boolean;
    /** `vis.render` ueber Kosmo: ausdruecklich bestellte Grundlage/Startwert (ohne `stufe`). */
    grundlage?: string;
    seed?: number;
    /** `vis.render` ueber Kosmo (Entscheid 104): ausdruecklich bestellte Guete (ohne `stufe`). */
    guete?: Guete;
    /**
     * Visbox-Entscheid 149: ein bewusst freies Bild (ohne Grundbild als Start). Der Varianten-Knoten und
     * `vis.render`/`vis.varianten` reichen es herein; ohne Angabe gilt die Wahl am Render-Knoten
     * (`freiesBildAmKnoten`). Nie Vorgabe.
     */
    freiesBild?: boolean;
  },
): void {
  const { doc } = useProject.getState();
  const variante = opts?.variante;
  const graph = variante?.graph ?? doc.get<VisGraph>(graphId);
  if (!graph) return;
  const auswertung = evaluiereGraph(doc, graph);
  const rohKnoten = auswertung.renderAuftraege.get(nodeId);
  if (!rohKnoten) return;
  // Mit eigenen Kameras zaehlt eine leere «Kamera aus 3D-Ansicht» am Render-Knoten nicht: bestellt
  // wird die gewaehlte Liste, nicht der Eingang.
  const { kameraAus3dFehlt: _ohneKamera3d, kameraBlickFehlt: _ohneBlick, ...rohOhneKamera3d } = rohKnoten;
  const roh = variante
    ? {
        ...(variante.kameras ? { ...rohOhneKamera3d, kameras: variante.kameras } : mitRichtungen(rohKnoten, variante.richtungen)),
        ...(variante.promptVorsatz ? { prompt: finalerRenderPrompt(variante.promptVorsatz, rohKnoten.prompt, []) } : {}),
      }
    : rohKnoten;
  const laufId = variante?.laufId ?? nodeId;
  if (!roh.hatSzene) {
    melde('Der Render-Node braucht eine Szene — verbinde den Modell-Node.', { ton: 'fehler' });
    return;
  }
  // «Kamera aus 3D-Ansicht» haengt am Eingang, traegt aber keine Kamera: NICHT senden. Sonst
  // bestellte der Auftrag `cameras: 'auto'`, und die Gegenseite rechnete still ihre eigenen
  // Standpunkte — ein anderes Bild als das, was der Knoten verspricht.
  if (roh.kameraAus3dFehlt) {
    melde(KAMERA_AUS_3D_FEHLT_HINWEIS, { ton: 'fehler' });
    return;
  }
  // L4-4: dasselbe für den Knoten «Kamera» auf «Blick» ohne gewählten Blick.
  if (roh.kameraBlickFehlt) {
    melde(KAMERA_BLICK_FEHLT_HINWEIS, { ton: 'fehler' });
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
  // B4: Hinweis vor dem Senden, sperrt nicht (s. `tokenHinweisVorDemSenden`).
  const tokenHinweis = tokenHinweisVorDemSenden(bridgeBase(), bridgeToken());
  if (tokenHinweis) melde(tokenHinweis, { ton: 'info' });
  // «Kamera aus 3D-Ansicht»: das Blickfeld fuer das endgueltige Format vor dem Senden pruefen —
  // ausserhalb von 10–120° weist der Vertrag die Bestellung ab (`pruefeSzeneVorVersand`), und
  // das kaeme sonst als Brueckenfehler an, der keiner ist.
  const kameraFov = blickfeldAusserhalbHinweis(auftrag.kameras, opts?.aufloesung ?? auftrag.resolution);
  if (kameraFov) {
    melde(kameraFov, { ton: 'fehler' });
    return;
  }
  // Nr. 85 Paket 2 (Entscheide 98/98a/98b): der Stand der Eingaben, die eine Grundlage
  // festlegen — mit genau den Zahlen, die gleich gesendet werden.
  // Fund B (Visbox-Mac 0.3.34): mit Skizze ist der zweite Knopf «Bild aus Skizze erzeugen» — er bestellt
  // wie `vis_render` mit Skizze (keine Grundlage, die Skizze ist der Eingang), nicht eine Variante.
  const bildAusSkizze = opts?.stufe === 'variante' && !!auftrag.skizze && mode !== 'lineart';
  const stufe = bildAusSkizze ? undefined : opts?.stufe;
  const standJetzt = grundlageStandFuerKnoten(doc, roh, node?.params ?? {}, opts);
  // Befund B1 (306): «Grundlage rendern» ein zweites Mal fuer denselben Stand legte am Heim-PC eine neue
  // Grundlage an. Der Knoten nennt jetzt die bestehende (auch eine gemerkte desselben Stands) und sendet
  // nichts; neu gerechnet wird nur bei einer Aenderung.
  if (stufe === 'grundlage' && opts?.wiederverwenden === true && !variante && opts.guete === undefined) {
    const da = grundlageAmKnoten(node?.params, standJetzt);
    if (da && da.stand === standJetzt) {
      const zurueck = grundlageFuerStand(node?.params, standJetzt);
      if (zurueck) {
        try {
          useProject.getState().runCommand('vis.nodeParametrieren', { graphId, nodeId, params: zurueck });
        } catch (err) {
          meldeFehler(err);
        }
      }
      melde(grundlageSchonDaSatz(da.id), { ton: 'info' });
      return;
    }
  }
  let kiFest: { grundlage?: string; seed?: number; guete?: Guete } = {};
  // Visbox-Entscheid 149: das freie Bild — ausdruecklich aus dem Aufruf, sonst die Wahl am Render-Knoten.
  // Nur mit KI-Schritt: nicht «Grundlage rendern», nicht die Strichzeichnung, nicht mit Skizze
  // (`postRenderJob` laesst das Feld dort und bei «nur Cycles» weg).
  const freiesBild =
    (opts?.freiesBild ?? freiesBildAmKnoten(node?.params)) === true &&
    stufe !== 'grundlage' &&
    mode !== 'lineart' &&
    !auftrag.skizze;
  if (stufe === 'variante') {
    // Zweite, tiefere Naht neben dem gesperrten Knopf: ohne aktuelle Grundlage geht nichts raus.
    // «Grundlage je Stand»: auch eine gemerkte Grundlage desselben Stands gilt.
    const g = grundlageAmKnoten(node?.params, standJetzt);
    const sperre =
      mode === 'lineart'
        ? STRICHZEICHNUNG_OHNE_VARIANTE_SATZ
        : auftrag.skizze
          ? SKIZZE_OHNE_GRUNDLAGE_SATZ
          : !g
            ? KEINE_GRUNDLAGE_SATZ
            : g.stand !== standJetzt
              ? GRUNDLAGE_VERALTET_SATZ
              : null;
    if (sperre || !g) {
      melde(sperre ?? KEINE_GRUNDLAGE_SATZ, { ton: 'fehler' });
      return;
    }
    // Entscheid 143: «Variante erzeugen» ist eine Variante — ohne Wahl am Schalter Voll (vom Grundbild,
    // Bildeingang 0,7 nach Visbox-Entscheid 149); eine ausdruecklich gewaehlte Vorschau bleibt Vorschau.
    kiFest = { grundlage: g.id, seed: g.seed, guete: gueteAmKnoten(node?.params, 'variante') };
  } else if (stufe === undefined) {
    if (opts?.grundlage !== undefined && mode === 'lineart') {
      melde(STRICHZEICHNUNG_OHNE_VARIANTE_SATZ, { ton: 'fehler' });
      return;
    }
    // Entscheid 104: eine ueber Kosmo bestellte Guete nur MIT KI-Schritt — «nur Cycles» und die
    // Strichzeichnung rechnen keinen, und der Vertrag weist `vis.guete` mit `vis.skip` ab.
    // Vorerst auch nicht mit Skizze: der Skizzen-Weg des Heim-PCs kennt die Guete nicht (GUETE_OHNE_SKIZZE_SATZ).
    const ohneKi = mode === 'lineart' || (auftrag.nurCycles === true && opts?.grundlage === undefined) || !!auftrag.skizze;
    kiFest = {
      ...(opts?.grundlage !== undefined ? { grundlage: opts.grundlage } : {}),
      ...(opts?.seed !== undefined ? { seed: opts.seed } : {}),
      ...(opts?.guete !== undefined && !ohneKi ? { guete: opts.guete } : {}),
    };
    // Visbox-Gegenprobe 328 (S6/S7, 22.10.2026): der Varianten-Knoten bestellte ohne `vis.grundlage` — jede
    // Bestellung rechnete am Heim-PC eine NEUE Grundlage (Blender) und waehlte aus drei Startwerten, obwohl am
    // Render-Knoten die Grundlage genau dieses Stands lag. Jetzt wie «Variante erzeugen» (98/98a): liegt fuer
    // den Stand DIESER Bestellung (Modell, Kameras, Stimmung, Material, Format) eine Grundlage am Render-Knoten
    // (auch eine gemerkte), geht ihre Kennung und ihr EINER Startwert mit. Nur ohne eigenen Entwurf (eine
    // Ebenenkombination ist ein anderes Modell, das der Stand nicht sieht), ohne Skizze, Strichzeichnung oder
    // «nur Cycles». Sonst wie bisher. Die Guete kommt seit Entscheid 143 vom Varianten-Knoten
    // (`sendeVarianten`, Vorgabe Voll) und geht nur mit KI-Schritt hinaus (`ohneKi` oben).
    if (variante && opts?.grundlage === undefined) {
      // Geraeteprobe R56: eine Teilmenge der Kameras des Render-Knotens rechnet auf dessen Grundlage
      // (Stand mit allen Kameras); bestellt werden weiter nur die gewaehlten (`cameras`).
      const standGrundlage = standDerGrundlageFuerVariante(doc, rohKnoten, variante.kameras, node?.params ?? {}, standJetzt, opts, variante.richtungen);
      const g = grundlageDerVariante(node?.params, standGrundlage, { entwurf: !!variante.entwurf, ohneKi });
      if (g) kiFest = { ...kiFest, grundlage: g.id, seed: g.seed };
    }
  }
  // Visbox-Mac-Befund 0.3.35 (22.10.2026): ein VOLLER Auftrag (Blender und KI in einem, Entscheid 98c — ohne
  // mitgesandte Grundlage) rechnet am Heim-PC ebenfalls eine neue Grundlage und meldet sie
  // (`result.grundlage`, `wiederverwendet: false`). Bis hierhin merkte sich der Knoten nur die Grundlage von
  // «Grundlage rendern» — nach einem vollen Lauf blieb die alte (oder keine) stehen, und der Knoten sagte
  // weiter «Grundlage veraltet — erst neu rendern», obwohl eben alles neu gerechnet war. Jetzt traegt auch
  // der volle Lauf seinen Stand, und `grundlageNachErgebnis` legt die gemeldete Grundlage ab. Nicht bei
  // einem Varianten-Knoten (anderer Knoten, eigener Stand), Skizze (keine Grundlage) oder Strichzeichnung.
  const vollerLaufMerkt =
    stufe === undefined && !variante && !auftrag.skizze && mode !== 'lineart' && kiFest.grundlage === undefined;
  // Visbox-Mac-Probe 0.3.66 (Mappe am Hang): eine Variante ohne passende Grundlage rechnet am Heim-PC Blender neu
  // und meldet die neue Grundlage — sie fiel weg, weil ihr Lauf an keinem Knoten steht. Danach rechnete
  // `vis_grundlage` bei unveraendertem Stand Blender noch einmal (ein Lauf der fuenf je Stunde). Jetzt legt der
  // Poll sie am Render-Knoten ab: unter ihrem Stand, und gezeigt nur, wenn es der Stand des Render-Knotens ist.
  // Nicht mit eigenem Entwurf (ein anderes Modell, das der Stand nicht sieht).
  const varianteMerkt =
    !!variante && stufe === undefined && !variante.entwurf && !auftrag.skizze && mode !== 'lineart' && kiFest.grundlage === undefined;
  const standDesKnotens = varianteMerkt ? standDesRenderKnotens(doc, graphId, nodeId, opts) : undefined;
  const key = memoKey(auftrag);
  const { setzeLauf, patchLauf } = useVisRuntime.getState();
  setzeLauf(laufId, {
    status: 'gesendet',
    memoKey: key,
    gestartetUm: Date.now(),
    graphId,
    ...(stufe !== undefined ? { stufe } : {}),
    ...(stufe === 'grundlage' || vollerLaufMerkt || varianteMerkt ? { grundlageStand: standJetzt } : {}),
    ...(varianteMerkt ? { grundlageKnoten: nodeId, ...(standDesKnotens !== standJetzt ? { grundlageNurJeStand: true } : {}) } : {}),
    ...(kiFest.grundlage !== undefined ? { grundlageId: kiFest.grundlage } : {}),
    ...(kiFest.seed !== undefined ? { seed: kiFest.seed } : {}),
    // Bitte UI (20.10.2026): die BESTELLTE Guete steht ab dem Absenden am Lauf, damit der Warteplatz
    // nicht umspringt, wenn jemand waehrend des Laufs den Schalter umstellt. Das Ergebnis setzt dann
    // die gemeldete (`gueteAusErgebnis`, Poll) — fehlt sie dort, gilt voll.
    ...(kiFest.guete !== undefined ? { guete: kiFest.guete } : {}),
    // Befund F4 (Visbox-Demolauf 24.10.2026, Punkt d): das BESTELLTE Bildwerkzeug steht am Lauf — der
    // Knoten zeigte sonst die Wahl an seinem Waehler (leer = Z-Image Turbo), auch wenn Kosmo mit
    // `vis.render` ein anderes bestellt hatte.
    ...(backbone !== undefined ? { backbone } : {}),
    // Visbox-Entscheid 149: das BESTELLTE freie Bild steht ab dem Absenden am Lauf; nach dem Ergebnis
    // gilt, was es meldet (`freiesBildAusErgebnis`).
    ...(freiesBild ? { freiesBild: true } : {}),
  });
  // Entscheid 117a (W-4): das Grundbild nur, wenn ein KI-Bild entsteht — «Grundlage rendern», «nur Cycles» und die
  // Strichzeichnung liefern selbst das Blender-Bild; der Varianten-Knoten zeigt nur das KI-Bild.
  const grundbildMit =
    stufe !== 'grundlage' &&
    variante === undefined &&
    mode !== 'lineart' &&
    !(auftrag.nurCycles === true && kiFest.grundlage === undefined);
  // Entscheid 96: `skizze` ist die Wahl am Skizzen-Knoten (Kernel), keine Job-Angabe — sie geht
  // nicht durch `...auftrag` an `postRenderJob`, sondern aufgeloest als `skizze` (unten).
  // Neue Knoten: `umgebung` und `stimmungen` sind Kernel-Angaben, keine Job-Parameter. Die Stimmung
  // aus dem Knoten gewinnt vor der aus der Insel bzw. aus Kosmo (`environment`) — eine Quelle am
  // Graphen; ohne Stimmung-Knoten gilt der Parameter wie bisher.
  const { skizze: skizzenWahl, umgebung, stimmungen: _stimmungen, ...auftragOhneSkizze } = auftrag;
  const umgebungDesAuftrags = umgebung ?? environment;
  // K-2 (Visbox-Demolauf 24.10.2026): mit Skizze geht KEINE Grundlage mit — die Skizze fuehrt ihr Bild
  // selbst und rechnet keine Blender-Grundlage; der Vertrag wiese die Szene sonst ab
  // («Szene verletzt den Vertrag (render-scene/v1) — vis.grundlage»). Eine ueber Kosmo (`vis.render`)
  // mitgegebene Grundlage bleibt darum liegen, und das wird gesagt. Ohne Wirt (KosmoOrbit) kommt keine
  // Skizze an, und die Grundlage gilt wie bisher.
  const senden = (skizze?: SkizzeDerBestellung) => {
    const grundlageMit = kiFest.grundlage !== undefined && !skizze;
    if (skizze && kiFest.grundlage !== undefined) melde(SKIZZE_OHNE_GRUNDLAGE_BESTELLT_SATZ, { ton: 'info' });
    return postRenderJob({
      ...auftragOhneSkizze,
      ...(umgebungDesAuftrags ? { environment: umgebungDesAuftrags } : {}),
      ...(opts?.kameraWahl !== undefined ? { kameraWahl: opts.kameraWahl } : {}),
      ...(backbone !== undefined ? { backbone } : {}),
      ...(researchOnly ? { researchOnly: true } : {}),
      // `aufloesung` spiegelt denselben Job-Parameter wie das bestehende
      // `resolution` (K20/A10-Presets nutzen ihn schon) — kein Zweitfeld.
      ...(opts?.aufloesung !== undefined ? { resolution: opts.aufloesung } : {}),
      mode,
      ...(skizze ? { skizze } : {}),
      ...(variante?.entwurf ? { entwurf: variante.entwurf } : {}),
      // Schritt 1: nur Blender, mit allen Ebenen — das alte Haekchen «nur Cycles» als Knopf.
      ...(stufe === 'grundlage' ? { nurCycles: true, passes: 'alle' as const } : {}),
      // Entscheid 117a (W-4): mit KI-Schritt bestellt der Render-Knoten das Grundbild von sich aus mit
      // (`passes` enthaelt `schoenbild`) — es steht nach dem Lauf neben dem KI-Bild. Nicht der Varianten-Knoten
      // (dort nur das KI-Bild, Blatt 35 C) und nicht die Skizze (sie rechnet ohne Blender-Bild).
      ...(grundbildMit && !skizze ? { passes: mitGrundbild() } : {}),
      // Schritt 2 (oder Kosmo mit Grundlage): KI-Schritt auf der Grundlage. Ein altes
      // `nurCycles: true` am Knoten darf ihn nicht abbestellen — der Vertrag wiese ab.
      ...(grundlageMit ? { nurCycles: false, grundlage: kiFest.grundlage } : {}),
      ...(kiFest.seed !== undefined ? { seed: kiFest.seed } : {}),
      // Entscheid 104/143: die Guete der Variante, wie am Knoten gewaehlt (Vorgabe fuer Varianten: Voll).
      ...(kiFest.guete !== undefined ? { guete: kiFest.guete } : {}),
      // Visbox-Entscheid 149: das freie Bild (nie Vorgabe).
      ...(freiesBild ? { freiesBild: true } : {}),
      // Visbox-Mac-Probe 0.3.66: Varianten-Knoten und «Variante erzeugen» sind Varianten — die Gegenseite rechnet
      // sie mit der Staerke der Variante (0,7), auch wenn keine Grundlage mitgeht.
      ...(variante || stufe === 'variante' ? { istVariante: true } : {}),
    });
  };
  // Befund F4 (Punkt c): welche Anweisung mit dem Bild geht — steht vor der Freigabe am Knoten.
  const mitKi = stufe !== 'grundlage' && mode !== 'lineart' && !(auftrag.nurCycles === true && kiFest.grundlage === undefined);
  let anweisung: LaufAnweisung | undefined;
  // OHNE SKIZZE GENAU DER BISHERIGE AUFRUF, im selben Takt. MIT Skizze erst die Liste der Mappe
  // lesen und «neueste» aufloesen (`skizzeZurBestellung`); kennt der Wirt sie nicht oder hat sie
  // keine Bemerkung, wirft das mit Satz, und der Satz steht am Knoten wie jeder andere Fehler
  // dieses Wegs. Ohne Wirt (KosmoOrbit, ein in Visbox gebauter Graph) geht das Bild aus dem
  // Modell — und das wird gesagt. Entscheid 96a: der Prompt wird NICHT zur Anweisung — es gilt die
  // Bemerkung der Skizze (`style.prompt` reist wie immer mit; die Bildseite rechnet eine Skizze
  // nur mit der Bemerkung).
  // Eine Grundlage rechnet aus dem Modell, nie aus einer Skizze (der Vertrag kennt beides nicht
  // zusammen) — «Grundlage rendern» laesst die Skizze darum liegen.
  const versand: Promise<GesendeterJob> = skizzenWahl && stufe !== 'grundlage'
    ? skizzeZurBestellung(skizzenWahl.wahl, auftrag.prompt ?? '').then((skizze) => {
        if (!skizze) melde(SKIZZE_NUR_IN_VISBOX_SATZ, { ton: 'info' });
        anweisung = mitKi ? anweisungDerBestellung(skizze, auftrag.prompt ?? '') : undefined;
        if (skizze && kiFest.grundlage !== undefined) patchLauf(laufId, { grundlageId: undefined });
        return senden(skizze);
      })
    : (() => {
        anweisung = mitKi ? anweisungDerBestellung(undefined, auftrag.prompt ?? '') : undefined;
        return senden();
      })();
  void versand
    .then((j) =>
      patchLauf(laufId, {
        ...(anweisung !== undefined ? { anweisung } : {}),
        jobId: j.job_id,
        status: mappeJobStatus(j),
        ...(j.approval_token !== undefined ? { approvalToken: j.approval_token } : {}),
        ...(j.umgebungFehlt !== undefined ? { umgebungFehlt: j.umgebungFehlt } : {}),
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
      const bescheid = await bescheidFuerBridgeFehler(err, { schreibRuf: true });
      patchLauf(laufId, { status: 'fehler', fehler: bescheid });
      meldeBrueckenFehler(bescheid);
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

/**
 * Mac-Demolauf 0.3.33 (22.10.2026, Mappe ohne Grundlage): ein Auftrag stand auf «wartet auf
 * Freigabe», ein Klick auf «Freigeben» tat nichts — keine Meldung, Status unveraendert. Der Weg am
 * Knoten hatte drei stumme Ausgaenge: Lauf ohne Kennung oder Freigabe (`return` ohne Wort), eine
 * Antwort, die weiter «wartet» sagt (nur der Status wurde neu gesetzt, also gleich), und ein
 * Fehler der Gegenseite, der nur als fluechtige Meldung oben erschien. Jetzt steht in jedem der
 * drei Faelle ein Satz AM KNOTEN (`freigabeHinweis`), der sagt, warum und was zu tun ist.
 */
/** K-2: mit Skizze bleibt eine mitgegebene Grundlage liegen (der Vertrag kennt beides nicht zusammen). */
export const SKIZZE_OHNE_GRUNDLAGE_BESTELLT_SATZ =
  'Die Skizze führt ihr Bild selbst und rechnet keine Grundlage — die mitgegebene Grundlage bleibt liegen, bestellt ist das Bild aus der Skizze.';

export const FREIGABE_OHNE_KENNUNG_SATZ =
  'Freigeben geht hier nicht: Dieser Auftrag trägt keine Freigabe aus dieser Ansicht. «Abbrechen» und neu bestellen — oder gleich «Grundlage rendern».';
export const FREIGABE_OHNE_WIRKUNG_SATZ =
  'Die Freigabe kam an, der Auftrag wartet aber weiter. «Abbrechen» und neu bestellen — oder gleich «Grundlage rendern».';

/** Der Satz am Knoten, wenn die Gegenseite die Freigabe abweist oder nicht erreichbar ist. */
export function freigabeGescheitertSatz(err: unknown, bescheid: string): string {
  const grund =
    err instanceof BridgeHttpError && err.status === 403
      ? 'die Freigabe passt nicht zu diesem Auftrag'
      : err instanceof BridgeHttpError && err.status === 404
        ? 'diesen Auftrag kennt der Heim-PC nicht mehr'
        : bescheid.trim().replace(/[.\s]+$/, '');
  return `Freigeben hat nicht geklappt — ${grund}. «Abbrechen» und neu bestellen — oder gleich «Grundlage rendern».`;
}

/**
 * «Freigeben» am Render-Knoten: gibt den wartenden Lauf frei und sagt am Knoten, wenn das nicht
 * geht. Gibt den Satz zurueck, der am Knoten steht (oder `null`, wenn die Freigabe gewirkt hat) —
 * fuer die Probe; der Knopf wertet ihn nicht aus.
 */
export async function freigebenAmKnoten(laufId: string): Promise<string | null> {
  const { laeufe, patchLauf } = useVisRuntime.getState();
  const lauf = laeufe[laufId];
  if (!lauf) return null;
  if (!lauf.jobId || !lauf.approvalToken) {
    patchLauf(laufId, { freigabeHinweis: FREIGABE_OHNE_KENNUNG_SATZ });
    melde(FREIGABE_OHNE_KENNUNG_SATZ, { ton: 'fehler' });
    return FREIGABE_OHNE_KENNUNG_SATZ;
  }
  try {
    const j = await freigebenJob(lauf.jobId, lauf.approvalToken);
    const status = mappeJobStatus(j);
    const hinweis = status === 'wartetFreigabe' ? FREIGABE_OHNE_WIRKUNG_SATZ : undefined;
    patchLauf(laufId, { status, wartetGrund: j.message, freigabeHinweis: hinweis });
    if (hinweis) melde(hinweis, { ton: 'fehler' });
    return hinweis ?? null;
  } catch (err) {
    const bescheid = await bescheidFuerBridgeFehler(err, { schreibRuf: true });
    const satz = freigabeGescheitertSatz(err, bescheid);
    patchLauf(laufId, { freigabeHinweis: satz });
    // Die Meldung oben wie bisher (bei einem Token-Bescheid mit dem Knopf zum HomeServer).
    meldeBrueckenFehler(bescheid);
    return satz;
  }
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
  const geprueft = RenderJobVis.safeParse(raw);
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
  // kv-vertrag (E123, Regel B): ein `null` der Gegenseite wird angenommen und
  // als benannter Mangel gemeldet, nicht still als «leer» weitergereicht.
  const maengel = geprueft.data.result ? renderResultMaengel(geprueft.data.result) : [];
  if (maengel.length > 0) {
    console.warn(`[E123] Ergebnis angenommen, ${maengel.length} benannte(r) Mangel: ${maengel.join('; ')}`);
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
 * (E7/V088-SPEZ) durch eine echte Herkunftsprüfung.
 *
 * P11/B5 (V016-SPEZ) NACHGEZOGEN, 23.09.2026 — zwei falsche Behauptungen
 * korrigiert:
 *  - `worker` fehlt GANZ (keine Angabe, z. B. ein fehlgeschlagener
 *    Zusatz-Fetch) → «Herkunft unbekannt». VORHER hiess das «Vorschau
 *    (Fake-Render)» — eine GERATENE Behauptung: ein Bild ohne `worker`-Feld
 *    könnte ebenso ein echter Render gewesen sein, dessen Feld nur nicht
 *    mitkam. Ehrlich ist «unbekannt», nicht «fake».
 *  - `worker === 'fake-worker'` (die Fake-Bridge nennt sich selbst so) →
 *    weiterhin «Vorschau (Fake-Render)», UNVERÄNDERT (Sanktion 8/V088:
 *    Fake-Bild ohne Kennzeichnung = ungültig; E2E `blender-bridge.
 *    spec.ts:247`/`vis-publish-bild.spec.ts` hängen am Wortlaut, ausserhalb
 *    dieses Pakets, nicht angefasst).
 *  - `requestedStyle === 'lineart'` (und ein ECHTER Worker) → «Strichzeichnung
 *    (Line-Art)» (E10) — Cycles/Freestyle-Rendering, kein KI-Stiltransfer,
 *    unverändert.
 *  - `requestedStyle` ist `'redux'`/`'ipadapter'`/`'lora'` (und ein ECHTER
 *    Worker) → «KI-Bild». VORHER hiess das ebenfalls «Render (Cycles)» —
 *    Cycles ist nur der Render-KERN, die KI-Veredelung danach ein
 *    zusätzlicher Schritt (`RenderScene.style.mode`, `kosmo-contracts`); ein
 *    KI-veredeltes Bild als «Cycles» zu zeigen verschleiert genau die
 *    Unterscheidung, die dieses Label dem Nutzer geben soll.
 *  - sonst (echter Worker, kein Line-Art, keine KI-Veredelung) → «echter
 *    Render».
 *
 * NACHGANG 3, 07.10.2026 (Befund des lokalen Workers, auf-20261006-248):
 *  - `worker` fehlt, das Ergebnis nennt aber `engine_used` → «Gerechnet mit
 *    <Modell>» statt «Herkunft unbekannt» (die echte Bruecke vor `5f59fd40e`
 *    traegt kein `worker`). Ohne beides bleibt «Herkunft unbekannt».
 *  - `worker` ist da UND die Bruecke sagt mehr (`worker_quelle`,
 *    `worker_seit`) → hinter dem Label Worker, «(abgeleitet)» und der
 *    Uebernahmezeitpunkt, z. B. «echter Render · Abholer (abgeleitet)».
 *    `worker` hat Vorrang vor `engine_used`.
 *
 * WICHTIG (Container-Grenze, wörtlich): der `worker`-Wert kommt IMMER von der
 * Fake-Bridge (`tools/homestation-bridge/kosmo_bridge/main.py`
 * `_fake_worker_step`, setzt `record["worker"] = "fake-worker"`) — die
 * Zweige «echter Render»/«KI-Bild» dieser Funktion sind im Container-Betrieb
 * NIE erreichbar, weil hier nie ein anderer `worker`-String ankommt. Sie
 * werden AUSSCHLIESSLICH per Unit-Test mit einem künstlichen `JobRecord`
 * bewiesen (`apps/kosmo-orbit/test/blender-label.test.ts`) und bleiben bis
 * zu einer echten HomeStation-Abnahme (0.8.10+, Owner-Termin) ein
 * unbewiesener Live-Pfad — genau so dokumentiert, nicht stillschweigend als
 * «getestet» behauptet.
 */
export function bildLabel(h: {
  worker?: string;
  requestedStyle?: string;
  workerSeit?: string;
  workerQuelle?: string;
  engineUsed?: string;
}): string {
  if (h.worker === undefined) {
    // Nachgang 3 (auf-20261006-248): die Bruecke vor `5f59fd40e` traegt in den
    // Job-Eintrag kein `worker` (nur `requested_engine`), das Ergebnis nennt
    // aber das gerechnete Modell. Das ist eine Angabe der Gegenseite, keine
    // Vermutung — sie steht da, statt «unbekannt». Ohne beides bleibt es
    // «Herkunft unbekannt»; geraten wird nichts.
    const modell = h.engineUsed?.trim();
    return modell ? `Gerechnet mit ${modell}` : 'Herkunft unbekannt';
  }
  if (h.worker === 'fake-worker') return 'Vorschau (Fake-Render)';
  const art =
    h.requestedStyle === 'lineart'
      ? 'Strichzeichnung (Line-Art)'
      : h.requestedStyle === 'redux' || h.requestedStyle === 'ipadapter' || h.requestedStyle === 'lora'
        ? 'KI-Bild'
        : 'echter Render';
  return art + herkunftZusatz(h.worker, h.workerQuelle, h.workerSeit);
}

/** Bekannte Worker-Kennungen der Bruecke in Lesefassung; jede andere steht
 *  wortgleich da. */
const WORKER_NAME: Readonly<Record<string, string>> = {
  abholer: 'Abholer',
  'comfyui-worker': 'ComfyUI-Worker',
  'splat-worker': 'Splat-Worker',
};

/** `2026-10-07T14:03:09Z` → `07.10.2026 14:03 UTC`; Unlesbares faellt weg. */
function uebernahmeZeit(iso: string | undefined): string | undefined {
  if (!iso) return undefined;
  const t = new Date(iso);
  if (Number.isNaN(t.getTime())) return undefined;
  const zwei = (n: number) => String(n).padStart(2, '0');
  return (
    `${zwei(t.getUTCDate())}.${zwei(t.getUTCMonth() + 1)}.${t.getUTCFullYear()} ` +
    `${zwei(t.getUTCHours())}:${zwei(t.getUTCMinutes())} UTC`
  );
}

/**
 * Nachgang 3 — was die Bruecke seit `5f59fd40e` zusaetzlich sagt: hinter dem
 * Label der Worker, «(abgeleitet)», wenn die Bruecke ihn nur erschlossen hat
 * (`worker_quelle`), und der Zeitpunkt der Uebernahme (`worker_seit`). Traegt
 * der Record keines der beiden neuen Felder (aeltere Bruecke), bleibt das
 * Label wie bisher. Die Attrappe (`fake-worker`) behaelt ihr Pflicht-Label
 * unveraendert (oben, vor diesem Zusatz).
 */
function herkunftZusatz(worker: string, quelle: string | undefined, seit: string | undefined): string {
  const abgeleitet = quelle === 'abgeleitet';
  const zeit = uebernahmeZeit(seit);
  if (!abgeleitet && zeit === undefined) return '';
  const name = WORKER_NAME[worker] ?? worker;
  return ` · ${name}${abgeleitet ? ' (abgeleitet)' : ''}${zeit !== undefined ? `, seit ${zeit}` : ''}`;
}

/**
 * P-LIZENZMARKE Schritt 2, Publish-Teil 2 (E154 (4) «Anzeigen, nicht
 * sperren»; Kernel seit ROADMAP 1691: `SheetImage.lizenzOffen?: { modell?,
 * lizenz? }`, angenommen von `publish.bildPlatzieren`/`bildFuellen`): die
 * Angabe fuer den Bild-Slot — oder `undefined`, wenn das Bild keine offene
 * Lizenz meldet. Wie `lizenzOffenGrund` zaehlt nur ein ausdrueckliches
 * `true`; leere Namen fallen weg, statt als leere Felder auf das Blatt zu
 * gehen. Reine Funktion; sie sperrt nichts.
 */
export function lizenzFuersBlatt(
  angabe: LizenzAngabe | null | undefined,
): { modell?: string; lizenz?: string } | undefined {
  if (angabe?.lizenzOffen !== true) return undefined;
  const modell = angabe.engineUsed?.trim();
  const lizenz = angabe.engineLicense?.trim();
  return { ...(modell ? { modell } : {}), ...(lizenz ? { lizenz } : {}) };
}

/** Breite eines neuen Bild-Slots auf dem Blatt (mm Papier) — wie bisher. */
export const BLATTBILD_BREITE = 160;
/** Rand und Abstand zwischen Bildern (mm). */
const BLATTBILD_RAND = 40;
const BLATTBILD_ABSTAND = 20;
/**
 * Angenommene Hoehe eines Bild-Slots je Breite. Der Slot kennt nur `w`; die Bilder
 * der Vis-Station sind 1600x992 bis 1600x1000 (0,62). 0,75 laesst Luft, damit auch
 * ein hoeheres Bild nicht in den naechsten Slot ragt.
 */
const BLATTBILD_HOEHE_JE_BREITE = 0.75;

/**
 * Der erste freie Platz fuer ein neues Bild auf dem Blatt — zeilenweise von oben
 * links, im Raster Breite + Abstand, innerhalb des Papiers.
 *
 * **Anlass (lokaler Worker, auf-20261007-250):** Bis hierher kam jedes neue Bild fest
 * auf (40, 40). Ein zweites «Aufs Blatt» lag GENAU auf dem ersten, die beiden
 * Herkunftszeilen uebereinander — lesbar erst nach Rueckgaengig. Belegt zaehlt jeder
 * vorhandene Bild-Slot mit seiner angenommenen Hoehe. Ist das Raster voll, rueckt das
 * Bild schraeg versetzt neben das letzte — sichtbar daneben, nie deckungsgleich.
 * Reine Funktion.
 */
export function freierBildPlatz(
  bilder: readonly Pick<SheetImage, 'x' | 'y' | 'w'>[],
  papier: { width: number; height: number },
  breite: number = BLATTBILD_BREITE,
): { x: number; y: number } {
  const hoehe = breite * BLATTBILD_HOEHE_JE_BREITE;
  const belegt = bilder.map((b) => ({ x: b.x, y: b.y, w: b.w, h: b.w * BLATTBILD_HOEHE_JE_BREITE }));
  const frei = (x: number, y: number) =>
    belegt.every((b) => x + breite + BLATTBILD_ABSTAND / 2 <= b.x || b.x + b.w + BLATTBILD_ABSTAND / 2 <= x
      || y + hoehe + BLATTBILD_ABSTAND / 2 <= b.y || b.y + b.h + BLATTBILD_ABSTAND / 2 <= y);
  for (let y = BLATTBILD_RAND; y + hoehe <= papier.height - BLATTBILD_RAND; y += hoehe + BLATTBILD_ABSTAND) {
    for (let x = BLATTBILD_RAND; x + breite <= papier.width - BLATTBILD_RAND; x += breite + BLATTBILD_ABSTAND) {
      if (frei(x, y)) return { x, y };
    }
  }
  const n = belegt.length;
  return { x: BLATTBILD_RAND + 12 * n, y: BLATTBILD_RAND + 12 * n };
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
 * fest. Fehlt `label` (jeder Aufrufer AUSSERHALB dieses Pakets, s.o.), fällt
 * es auf `bildLabel({})` zurück. P11/B5 NACHGEZOGEN: das ist seit
 * 23.09.2026 NICHT mehr «Vorschau (Fake-Render)», sondern «Herkunft
 * unbekannt» (s. `bildLabel`-Kommentar) — ein Aufrufer ohne jede
 * Herkunftsangabe behauptet keine geratene Fake-Kennzeichnung mehr, bleibt
 * aber weiterhin PFLICHT-beschriftet (Sanktion 8 bleibt scharf: ein Bild
 * ohne JEDE Kennzeichnung ist ungültig, «unbekannt» ist eine Kennzeichnung).
 */
export function platziereBildAufsBlatt(dataUrl: string, _titel: string, label?: string, lizenz?: LizenzAngabe): string {
  // Owner-Entscheid 04.09.2026: hier stand ein Tor, das ueber 1 MiB
  // Base64-Zeichen abgewiesen hat. Es ist weg — die MESSUNG bleibt und wird
  // gemeldet, damit ein grosses Bild nachvollziehbar bleibt, statt still zu
  // sein. Die naechste echte Grenze liegt beim Sync-Server (8 MiB je
  // Nachricht, s. `messeBildGroesse` oben).
  const bildGroesse = messeBildGroesse(dataUrl);
  console.info(`[Blattbild] ${bildGroesse.mbText} MB (${bildGroesse.base64Zeichen} Base64-Zeichen)`);
  // Abgleich-Grenze (Integrator/Prepare 21.10.2026): ueber 5 MB Rohbild brach die Verbindung still (1009). Dieser Weg
  // (Aufnahme, Skizze, ohne Ablegen) setzt die dataURL direkt — darum hier mit Satz abgelehnt statt still verloren.
  if (bildGroesse.bytes > ABLAGE_GRENZE_BYTES) {
    throw new Error(
      `Nicht aufs Blatt gelegt: ${mbText(bildGroesse.bytes)} MB — über der Grenze von ${mbText(ABLAGE_GRENZE_BYTES)} MB, die der Abgleich trägt.`,
    );
  }
  const slotLabel = label ?? bildLabel({});
  // P-LIZENZMARKE Schritt 2, Publish-Teil 2 (E154 (4), ROADMAP 1691): die
  // Marke geht mit dem Bild auf das Blatt. Ohne Marke bleibt das Feld weg —
  // dann nimmt `bildFuellen` eine alte Marke des Slots mit (Kernel-Regel).
  const marke = lizenzFuersBlatt(lizenz);
  const lizenzFeld = marke ? { lizenzOffen: marke } : {};
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
    const vorher = new Set((sheet.bilder ?? []).filter((b) => b.assetId).map((b) => b.id));
    if (leer) {
      runCommand('publish.bildFuellen', { sheetId: sheet.id, bildId: leer.id, dataUrl, ...lizenzFeld });
      // `bildFuellen` kennt kein `title`-Param (Kernel-Vertrag bleibt
      // unverändert) — das Pflicht-Label kommt über den bestehenden
      // `bildAnpassen`-Command, in DERSELBEN Undo-Gruppe.
      runCommand('publish.bildAnpassen', { sheetId: sheet.id, bildId: leer.id, title: slotLabel });
    } else {
      const platz = freierBildPlatz(sheet.bilder ?? [], sheetPaperSize(sheet));
      runCommand('publish.bildPlatzieren', {
        sheetId: sheet.id,
        x: platz.x,
        y: platz.y,
        w: BLATTBILD_BREITE,
        dataUrl,
        title: slotLabel,
        ...lizenzFeld,
      });
    }
    // L3-A5 (Demolauf 16.10.): die Druckaufloesung am Platz — gewarnt, nicht gesperrt (Rechnung von Publish).
    meldeDruckAmFeld(sheet.id, leer?.id, vorher);
    return sheet.name;
  } finally {
    history.endGroup();
  }
}

/**
 * L3-A5 (Demolauf 16.10.2026): der Bildschirmausschnitt 369 × 228 px ging ohne ein Wort aufs A0.
 * Reicht die Aufloesung am Platz nicht, sagt es eine eigene Meldung NACH der Ablage-Meldung des
 * Aufrufers (darum im naechsten Takt) — gesperrt wird nichts. Gerechnet wie Publish
 * (`druckaufloesung`, `bildFeldRechteck`) am gefuellten Feld.
 */
export const DRUCK_MELDUNG_MS = 10_000;
function meldeDruckAmFeld(sheetId: string, feldId: string | undefined, vorher: ReadonlySet<string>): void {
  const doc = useProject.getState().doc;
  const sheet = doc.get<Sheet>(sheetId);
  const feld = (sheet?.bilder ?? []).find((b) => (feldId ? b.id === feldId : !vorher.has(b.id) && b.assetId));
  if (!feld?.assetId) return;
  const satz = druckWarnung(doc.get<ImageAsset>(feld.assetId), feld);
  if (satz) setTimeout(() => melde(satz, { ton: 'info', dauerMs: DRUCK_MELDUNG_MS }), 0);
}

/** Kennt `publish.bildPlatzieren` schon `assetId` (Prepare, bild-ablegen)? Dann setzt EIN Befehl das neue Feld. */
function platzierenMitAsset(): boolean {
  const params = getCommand('publish.bildPlatzieren')?.params as { shape?: Record<string, unknown> } | undefined;
  return !!params?.shape && 'assetId' in params.shape;
}

/**
 * Video-Befunde L4-16/L3-A4 — ein Bild, das schon im Projekt liegt (`publish.bildAblegen`), aufs
 * Blatt: per `assetId`, nicht ein zweites Mal als Text. Erst ein leeres Feld
 * (`publish.bildFuellen({ sheetId, bildId, assetId })`), sonst ein neues am ersten freien Platz —
 * mit `publish.bildPlatzieren({ …, assetId })` in EINEM Befehl, wo Publish das kann, sonst leer
 * platziert und gefuellt. Ohne Blatt entsteht eines. Alles ein Rueckgaengig-Schritt.
 */
export function platziereProjektBildAufsBlatt(assetId: string, label?: string, lizenz?: LizenzAngabe): string {
  const slotLabel = label ?? bildLabel({});
  const marke = lizenzFuersBlatt(lizenz);
  const lizenzFeld = marke ? { lizenzOffen: marke } : {};
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
    const vorher = new Set((sheet.bilder ?? []).map((b) => b.id));
    if (leer) {
      runCommand('publish.bildFuellen', { sheetId: sheet.id, bildId: leer.id, assetId, ...lizenzFeld });
      runCommand('publish.bildAnpassen', { sheetId: sheet.id, bildId: leer.id, title: slotLabel });
    } else {
      const platz = freierBildPlatz(sheet.bilder ?? [], sheetPaperSize(sheet));
      if (platzierenMitAsset()) {
        runCommand('publish.bildPlatzieren', { sheetId: sheet.id, x: platz.x, y: platz.y, w: BLATTBILD_BREITE, title: slotLabel, assetId, ...lizenzFeld });
      } else {
        runCommand('publish.bildPlatzieren', { sheetId: sheet.id, x: platz.x, y: platz.y, w: BLATTBILD_BREITE, title: slotLabel, ...lizenzFeld });
        const feld = (doc.get<Sheet>(sheet.id)?.bilder ?? []).find((b) => !vorher.has(b.id));
        if (!feld) throw new Error('Das neue Bildfeld fehlt auf dem Blatt.');
        runCommand('publish.bildFuellen', { sheetId: sheet.id, bildId: feld.id, assetId, ...lizenzFeld });
      }
    }
    meldeDruckAmFeld(sheet.id, leer?.id, new Set(vorher));
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
 * zurück — seit P11/B5 «Herkunft unbekannt» statt der geratenen «Vorschau
 * (Fake-Render)» — NIE ein erfundenes «echter Render»/«KI-Bild».
 */
export async function bildAufsBlatt(
  jobId: string,
  imageName: string,
  titel: string,
  lizenz?: LizenzAngabe,
): Promise<string> {
  // Video-Befunde L4-16/L3-A4: liegt das Bild schon im Projekt (in voller Aufloesung,
  // `vis.bildSichern`), geht es von dort aufs Blatt — auch wenn der Heim-PC gerade fehlt. Das
  // Label ist das, mit dem es gesichert wurde (der Name des Projektbilds); die Lizenzmarke kommt
  // vom Aufrufer (sein Lauf stammt aus demselben Auftrag).
  // Label und Lizenzmarke kommen auch dann aus dem Job-Record (ein kleiner Abruf, nicht das Bild);
  // ist der Heim-PC weg, gilt der Name des Projektbilds und die Angabe des Aufrufers.
  const imProjekt = istBlattDa() ? projektBild(jobId, imageName) : undefined;
  if (imProjekt) {
    // Die Lizenzmarke: genannt gewinnt, sonst nimmt Publish sie aus der Herkunft des Bildes (Prepare).
    const h = await holeHerkunft(jobId, lizenz);
    // Ohne Angabe (Heim-PC weg) nimmt Publish die Marke aus der Herkunft des Bildes; genannt gewinnt.
    return platziereProjektBildAufsBlatt(imProjekt.id, h.label ?? imProjekt.name, h.angabe);
  }
  const { dataUrl, label, angabe } = await holeBildMitHerkunft(jobId, imageName, lizenz);
  if (istBlattDa() && ablegenDa()) {
    const stand = await sichereImProjekt(jobId, imageName, label, dataUrl, { lizenzOffen: lizenzFuersBlatt(angabe) });
    if (stand.zustand === 'gesichert') return platziereProjektBildAufsBlatt(stand.assetId, label, angabe);
    // Nie still verlieren: zu gross auch nach JPEG und Verkleinern, oder abgewiesen — mit Satz.
    throw new Error(stand.zustand === 'zu-gross' ? stand.satz : stand.zustand === 'fehler' ? stand.grund : 'Nicht abgelegt.');
  }
  // Ohne Ablegen (aeltere Gegenseite): wie bisher direkt eingebettet, mit der Abgleich-Grenze.
  return platziereBildAufsBlatt(dataUrl, titel, label, angabe);
}

/**
 * Das Bild eines Auftrags in voller Aufloesung (dataURL) samt Herkunfts-Label und Lizenzangabe
 * — der Teil von «Aufs Blatt», den auch das Sichern ins Projekt braucht (`bild-ablage.ts`).
 *
 * E13: holt `worker`/`requested_style` aus dem echten Job-Record (`holeJob`) und berechnet
 * daraus das Label — dieselbe Quelle, die den Job auch sonst beschreibt, keine zweite Wahrheit.
 * Schlägt der Zusatz-Fetch fehl (Netz-Aussetzer o.ä.), fällt das Label ehrlich auf
 * `bildLabel({})` zurück — seit P11/B5 «Herkunft unbekannt» statt der geratenen «Vorschau
 * (Fake-Render)» — NIE ein erfundenes «echter Render»/«KI-Bild».
 */
export async function holeBildMitHerkunft(
  jobId: string,
  imageName: string,
  lizenz?: LizenzAngabe,
): Promise<{ dataUrl: string; label: string; angabe: LizenzAngabe | undefined }> {
  // Über bridgeFetch (Token-Header + connect-src) statt rohem fetch — sonst
  // sperrt eine token-geschützte Bridge das Blatt-Einbetten aus (Fable-Auflage 1).
  const blob = await bildBlob(jobId, imageName);
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result));
    r.onerror = () => reject(r.error ?? new Error('Bild nicht lesbar'));
    r.readAsDataURL(blob);
  });
  const h = await holeHerkunft(jobId, lizenz);
  return { dataUrl, label: h.label ?? bildLabel({}), angabe: h.angabe };
}

/**
 * Herkunfts-Label und Lizenzangabe aus dem Job-Record — `label: null`, wenn der Record nicht zu
 * holen ist (dann entscheidet der Aufrufer: «Herkunft unbekannt» oder der Name des Projektbilds).
 */
export async function holeHerkunft(
  jobId: string,
  lizenz?: LizenzAngabe,
): Promise<{ label: string | null; angabe: LizenzAngabe | undefined }> {
  let label: string | null = null;
  // P-LIZENZMARKE (Publish-Teil 2): die Marke kommt aus DEMSELBEN Job-Record
  // wie das Label. Nur wenn er nicht zu holen ist oder kein Ergebnis traegt,
  // gilt die Angabe des Aufrufers (sein Lauf stammt aus demselben Job) — ein
  // Netz-Aussetzer soll die Marke nicht still verlieren.
  let angabe = lizenz;
  try {
    const job = await holeJob(jobId);
    label = bildLabel({
      ...(job.worker !== undefined ? { worker: job.worker } : {}),
      ...(job.requested_style !== undefined ? { requestedStyle: job.requested_style } : {}),
      ...(job.worker_seit !== undefined ? { workerSeit: job.worker_seit } : {}),
      ...(job.worker_quelle !== undefined ? { workerQuelle: job.worker_quelle } : {}),
      // Nachgang 3: Rueckfall, solange die Bruecke kein `worker` liefert.
      ...(job.result?.engine_used !== undefined ? { engineUsed: job.result.engine_used } : {}),
    });
    if (job.result) {
      angabe = {
        lizenzOffen: job.result.engine_license_open,
        engineUsed: job.result.engine_used,
        engineLicense: job.result.engine_license,
      };
    }
  } catch {
    // Ehrlicher Rückfall auf das Fake-Render-Label (s. Kommentar oben) —
    // ein gescheiterter Zusatz-Fetch darf das Platzieren selbst nicht kippen.
  }
  return { label, angabe };
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
export async function aufnahmeAufsBlatt(
  dataUrl: string,
  titel: string,
  // «Skizze vom iPad» (Entscheide 95/95a): ein Bild ohne Bridge, das keine Aufnahme ist, sagt
  // auf dem Blatt, was es ist. Ohne Angabe bleibt es wortgleich wie bisher.
  beschriftung: string = 'Aufnahme (Viewport)',
): Promise<string> {
  return platziereBildAufsBlatt(dataUrl, titel, beschriftung);
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
export async function bescheidFuerBridgeFehler(
  err: unknown,
  // CORS-Befund E156: ein schreibender Ruf (Render-POST) kann angekommen
  // sein, auch wenn die Antwort unlesbar ist — der Aufrufer weiss das, der
  // Fehler selbst nicht. Lesende Aufrufer lassen es weg (Verhalten wie bisher).
  optionen: { schreibRuf?: boolean } = {},
): Promise<string> {
  const netzfehler = err instanceof TypeError;
  const rohtext = err instanceof Error ? err.message : String(err);
  const lage: BescheidLage = {
    netzfehler,
    ...(optionen.schreibRuf ? { schreibRuf: true } : {}),
    ...(err instanceof BridgeHttpError ? { status: err.status } : {}),
    tokenGesetzt: (localStorage.getItem(BRIDGE_TOKEN_KEY) ?? '').trim().length > 0,
    cspVerdacht: netzfehler && bridgeVermutlichCspGeblockt(),
  };
  const gegenprobe = netzfehler && !lage.cspVerdacht ? await bridgeHealthGegenprobe() : undefined;
  if (gegenprobe !== undefined) lage.healthErreichbar = gegenprobe;
  return bridgeBescheid(lage, rohtext).text;
}

/**
 * Die tokenfreie Gegenprobe auf `/health` (P-BESCHEID) als eigener Schritt,
 * damit auch Wege ausserhalb von KosmoVis sie fahren (C3: der Video-Splat-
 * Start der Medienkarte). `true` = die Brücke läuft, `false` = auch `/health`
 * schweigt, `undefined` = die Probe selbst ist gescheitert (dann wird nichts
 * behauptet).
 */
export async function bridgeHealthGegenprobe(): Promise<boolean | undefined> {
  return pruefeBridge(bridgeBase())
    .then((s) => s === 'verbunden')
    .catch(() => undefined);
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
  // C3: derselbe Toast, bei einem Token-Bescheid mit dem Knopf zum HomeServer.
  meldeBrueckenFehler(await bescheidFuerBridgeFehler(err));
}
