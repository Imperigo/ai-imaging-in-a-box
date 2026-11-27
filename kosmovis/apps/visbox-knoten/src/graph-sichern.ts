/**
 * Der Graph der Knotenansicht übersteht das Neuladen (Visbox-eigen, 15.10.2026).
 *
 * Anlass (HomeStation, auf-20261015-286): In Visbox lebt das Dokument nur in dieser Seite — kein
 * Tresor, keine Mitarbeitenden. Nach dem Neuladen war der Graph weg. Der Wirt sichert darum die
 * Render-Graphen (Einträge der Art `visgraph`) je Mappe auf dem Heim-PC (`./graph`, siehe
 * `oberflaeche/server.py` WEG_KNOTEN_GRAPH und `aiimaging.knotenweg.schreibe_graph`) und legt sie
 * beim Öffnen wieder ins Dokument — VOR dem ersten Bild, damit der fertige Anfang (Entscheid 91)
 * nicht zusätzlich angelegt wird.
 *
 * Beim Legen wird ein Graph **einmal sanft entzerrt, nur wenn Knoten sich überlappen**
 * (Owner-Befund am Mac, 20.10.2026: die Auto-Kamera lag über dem unteren Rand des Modell-Knotens,
 * seit der mit dem 3D-Fenster gewachsen ist — der Graph war vorher gesichert). Ohne Überlappung
 * bleibt jede Lage, wie sie gesichert ist (`entzerreGraph` in `knoten-entzerren.ts`). Der Wirt
 * hat die Lade-Fähigkeit zu diesem Zeitpunkt schon gemeldet (`main.tsx`), die Höhe des
 * Modell-Knotens stimmt also.
 *
 * Seit den Kopfteilen (Entscheide 115/116, 20.10.2026) meldet das Sichern seine Lage an den
 * Speichern-Kreis (wortgleich aus KosmoOrbit): «sichert …», «Gesichert · zuletzt HH:MM» oder
 * «NICHT gesichert» mit Grund — auch dann, wenn der Heim-PC mit einem Fehler antwortet, statt dass
 * die Anzeige still «gesichert» sagt (Fund F7 dort).
 */
import type { VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import type { AutosaveLage } from '../../kosmo-orbit/src/state/project-vault';
import { entzerreGraph } from '../../kosmo-orbit/src/modules/vis/knoten-entzerren';
import { startGraphAnlegen } from '../../kosmo-orbit/src/modules/vis/start-graph';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';

/** Wie lange nach der letzten Änderung gesichert wird. */
export const SICHERN_NACH_MS = 1000;

/** Die Render-Graphen des Dokuments. */
export function renderGraphen(): VisGraph[] {
  return useProject.getState().doc.byKind<VisGraph>('visgraph');
}

/** Legt gesicherte Graphen ins Dokument (ohne Rückgängig-Schritt: Es ist der Stand beim Öffnen). */
export function legeGraphen(graphen: VisGraph[]): number {
  if (graphen.length === 0) return 0;
  const { doc } = useProject.getState();
  doc.apply(graphen.filter((g) => !doc.get(g.id)).map((g) => ({ id: g.id, before: null, after: entzerreGraph(g) })));
  useProject.setState((s) => ({ revision: s.revision + 1 }));
  return graphen.length;
}

/**
 * Mac-Befund 0.3.33 (22.10.2026, Protokoll 74 §231): **die Mappe, deren Graph diese Seite gelesen
 * hat.** Der Heim-PC hat EINE «zuletzt geöffnete» Mappe für alle Geräte. Öffnete ein anderes Gerät
 * eine andere Mappe, sicherte eine schon offene Knotenansicht ihren Graph bis 0.3.34 in DIESE — der
 * Heim-PC nahm beim Sichern die Mappe, die gerade zuletzt offen war. Jetzt nennt der Heim-PC beim
 * Lesen die Kennung (`mappe`), und gesichert wird mit `?mappe=` genau dorthin. `null`: keine
 * genannt (Mappe am Mac — die App sichert dann in die offene Mappe am Mac, wie bisher).
 */
let mappeDesGraphen: string | null = null;

/** Die Kennung der Mappe, deren Graph die Seite gelesen hat (`null`: keine genannt). */
export function graphMappe(): string | null {
  return mappeDesGraphen;
}

/**
 * §231 Nachtrag (22.10.2026): **der Stand, auf dem diese Seite arbeitet.** Der Mac und ein zweites
 * Gerät arbeiteten gleichzeitig in derselben Mappe; eine offene Knotenansicht zieht fremde
 * Änderungen nicht nach, und ihr nächstes Sichern hätte sie still überschrieben. Der Heim-PC nennt
 * beim Lesen den Stand (`stand`), die Seite sichert mit `&stand=`; hat inzwischen ein anderes Gerät
 * gesichert, weist der Heim-PC ab (409, «… neu laden»), und der Speichern-Kreis sagt es.
 * `null`: keiner genannt (Mappe am Mac, ältere Heim-PC) — dann wie bisher.
 */
let standDesGraphen: string | null = null;

export function graphStand(): string | null {
  return standDesGraphen;
}

/**
 * A0835 (Audit 24.11.2026, V3): **die Anfragenummer der gelesenen Mappe.** Sie zählt bei jedem
 * Lesen einer Mappe hoch. Ein Sicher-Aufruf merkt sich die Nummer, mit der er startete; kommt seine
 * Antwort erst nach dem Wechsel zu einer anderen Mappe, ändert sie weder den Speichern-Kreis noch
 * den Stand der jetzigen.
 */
let anfrageNummer = 0;

/** Nur für Proben. */
export function setzeGraphMappe(kennung: string | null, stand: string | null = null): void {
  anfrageNummer += 1;
  mappeDesGraphen = kennung;
  standDesGraphen = stand;
}

function text(x: unknown): string | null {
  return typeof x === 'string' && x.trim() !== '' ? x : null;
}

function merkeMappe(sicht: { mappe?: unknown; stand?: unknown }): void {
  mappeDesGraphen = text(sicht.mappe);
  standDesGraphen = text(sicht.stand);
}

/**
 * Entscheid 129 (22.10.2026): Die Mac-App öffnet die Knotenansicht mit `?mappe=<Name>` — der Mappe,
 * die SIE zuletzt offen hatte, nicht der, die ein anderes Gerät zuletzt geöffnet hat. Gelesen wird
 * dann diese (wie `./mappe`, `./modell.glb`, Skizzen und Standpunkte schon mit `location.search`).
 * Nach «Datei laden …» fällt die Angabe aus der Adresse (`verfolge`), dann gilt die neue Mappe.
 */
export function mappeAusAdresse(suche: string = typeof location !== 'undefined' ? location.search : ''): string | null {
  return text(new URLSearchParams(suche).get('mappe'));
}

/** Der Weg zum Lesen: mit der Mappe aus der Adresse (Entscheid 129), sonst die zuletzt geöffnete. */
export function leseWeg(suche?: string): string {
  const mappe = mappeAusAdresse(suche);
  return mappe ? `./graph?mappe=${encodeURIComponent(mappe)}` : './graph';
}

/** Der Weg zum Sichern: mit der gelesenen Mappe und ihrem Stand, sonst wie bisher. */
export function sicherWeg(): string {
  const frage = new URLSearchParams();
  if (mappeDesGraphen) frage.set('mappe', mappeDesGraphen);
  if (standDesGraphen) frage.set('stand', standDesGraphen);
  const t = frage.toString();
  return t ? `./graph?${t}` : './graph';
}

/** Holt den gesicherten Graph vom Heim-PC und legt ihn ins Dokument. Gibt die Zahl zurück. */
export async function ladeGesichertenGraph(holen: typeof fetch = fetch, suche?: string): Promise<number> {
  // OHNE LESBARE ANTWORT (Mappe aus der Adresse gibt es nicht mehr …): gesichert wird trotzdem nur
  // in die verlangte Mappe — der Heim-PC weist ab, statt dass der fertige Anfang eine fremde
  // Mappe überschreibt.
  anfrageNummer += 1;
  mappeDesGraphen = mappeAusAdresse(suche);
  standDesGraphen = null;
  try {
    const antwort = await holen(leseWeg(suche));
    if (!antwort.ok) return 0;
    const sicht = (await antwort.json()) as { graphen?: VisGraph[]; mappe?: unknown; stand?: unknown };
    merkeMappe(sicht);
    return legeGraphen(Array.isArray(sicht.graphen) ? sicht.graphen : []);
  } catch {
    return 0; // Ohne Antwort beginnt die Ansicht wie bisher — mit dem fertigen Anfang.
  }
}

/**
 * Generalprobe 327 (S2, 22.10.2026): **eine andere Mappe, ihr Graph.** Nach «Datei laden …» ist die
 * neue Mappe am Heim-PC die zuletzt geöffnete — der Graph der vorigen blieb aber im Dokument stehen,
 * bis man die Seite neu lud (und eine Änderung daran wäre in die neue Mappe gesichert worden). Jetzt:
 * erst den gesicherten Graph der neuen Mappe holen, dann in EINEM Schritt die alten Graphen
 * herausnehmen und die neuen legen — hat die neue Mappe keinen, den fertigen Anfang (Entscheid 91),
 * wie beim Öffnen. Ohne Rückgängig-Schritt für das Herausnehmen: Es ist der Stand beim Öffnen.
 * Gibt die Zahl der gelegten Graphen zurück (der Anfang zählt als einer).
 */
export async function graphDerNeuenMappe(holen: typeof fetch = fetch): Promise<number> {
  let neu: VisGraph[] = [];
  anfrageNummer += 1;
  // Die alte Mappe gilt nicht mehr — ohne lesbare Antwort sichert die Seite wie bisher (die neue
  // ist am Heim-PC die zuletzt geöffnete), nie in die alte.
  mappeDesGraphen = null;
  standDesGraphen = null;
  try {
    const antwort = await holen('./graph');
    if (antwort.ok) {
      const sicht = (await antwort.json()) as { graphen?: VisGraph[]; mappe?: unknown; stand?: unknown };
      // Die neue Mappe ist jetzt die des Graphen — gesichert wird ab hier in sie.
      merkeMappe(sicht);
      neu = Array.isArray(sicht.graphen) ? sicht.graphen : [];
    }
  } catch {
    neu = []; // Ohne Antwort: der fertige Anfang, wie beim Öffnen ohne Heim-PC.
  }
  const { doc } = useProject.getState();
  const alt = renderGraphen();
  if (alt.length > 0) doc.apply(alt.map((g) => ({ id: g.id, before: g, after: null })));
  if (neu.length > 0) {
    legeGraphen(neu);
    useVisRuntime.getState().setAktiverGraphId(neu[0]!.id);
    return neu.length;
  }
  useProject.setState((s) => ({ revision: s.revision + 1 }));
  return startGraphAnlegen() ? 1 : 0;
}

/**
 * Sichert die Graphen nach jeder Änderung (mit Verzögerung, und nur, wenn sich etwas
 * geändert hat). Gibt eine Abmeldung zurück.
 *
 * A0835 (Audit 24.11.2026, V3): **ein Sichern zur Zeit.** Antwortete der Heim-PC langsam, startete
 * jede weitere Änderung einen eigenen Aufruf gegen denselben Stand; der zweite lief in den 409 des
 * ersten, als hätte ein anderes Gerät gesichert. Jetzt ist je Mappe höchstens ein Aufruf offen.
 * Was sich währenddessen ändert, merkt sich die Seite (`wartet`) und schickt nach der Bestätigung
 * die dann jüngste Fassung mit dem neuen Stand. Nach einem Fehler schickt sie nichts nach — die
 * nächste Änderung versucht es wieder, wie bisher. Eine Antwort, die erst nach dem Wechsel zu einer
 * anderen Mappe kommt (Anfragenummer), lässt Kreis und Stand der jetzigen Mappe in Ruhe.
 */
export function sichereBeiAenderung(
  senden: (rumpf: string) => Promise<unknown> = (rumpf) =>
    fetch(sicherWeg(), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: rumpf }),
  nachMs: number = SICHERN_NACH_MS,
  melde: (lage: AutosaveLage) => void = () => {},
): () => void {
  let zuletzt = JSON.stringify({ graphen: renderGraphen() });
  let uhr: ReturnType<typeof setTimeout> | null = null;
  let gesichertUm: string | null = null;
  // Die Anfragenummer des offenen Aufrufs (`null`: keiner offen).
  let offenFuer: number | null = null;
  let wartet = false;
  let abgemeldet = false;
  const sichern = (): void => {
    const rumpf = JSON.stringify({ graphen: renderGraphen() });
    if (rumpf === zuletzt) return;
    if (offenFuer === anfrageNummer) {
      wartet = true; // nach der Bestätigung nachschicken
      return;
    }
    wartet = false;
    zuletzt = rumpf;
    const nummer = anfrageNummer;
    offenFuer = nummer;
    const frei = (): void => {
      if (offenFuer === nummer) offenFuer = null;
    };
    melde({ stand: 'sichert', iso: gesichertUm });
    void senden(rumpf)
      .then(async (antwort) => {
        if (nummer !== anfrageNummer) return frei(); // späte Antwort einer früheren Mappe
        const grund = await abgewiesen(antwort);
        if (grund !== null) throw new Error(grund);
        // Der neue Stand nach dem eigenen Sichern (§231 Nachtrag).
        const neu = await neuerStand(antwort);
        if (nummer !== anfrageNummer) return frei();
        if (neu) standDesGraphen = neu;
        gesichertUm = new Date().toISOString();
        frei();
        melde({ stand: 'gesichert', iso: gesichertUm });
        if (wartet && !abgemeldet) sichern();
      })
      .catch((fehler: unknown) => {
        frei();
        if (nummer !== anfrageNummer) return;
        wartet = false;
        zuletzt = ''; // beim nächsten Mal noch einmal versuchen
        melde({ stand: 'fehler', iso: gesichertUm, grund: fehler instanceof Error ? fehler.message : String(fehler) });
      });
  };
  const abmelden = useProject.subscribe((s, vorher) => {
    if (s.revision === vorher.revision) return;
    if (uhr) clearTimeout(uhr);
    uhr = setTimeout(() => {
      uhr = null;
      sichern();
    }, nachMs);
  });
  return () => {
    abgemeldet = true;
    if (uhr) clearTimeout(uhr);
    abmelden();
  };
}

/** Der Stand aus der Antwort auf das Sichern (`{gesichert, stand}`) — `null`: keiner. */
async function neuerStand(antwort: unknown): Promise<string | null> {
  const a = antwort as { clone?: () => { json: () => Promise<unknown> } } | null;
  if (!a || typeof a.clone !== 'function') return null;
  try {
    return text(((await a.clone().json()) as { stand?: unknown } | null)?.stand);
  } catch {
    return null;
  }
}

/** Der Grund, wenn der Heim-PC das Sichern abwies (eine Antwort mit `ok: false`), sonst `null`. */
async function abgewiesen(antwort: unknown): Promise<string | null> {
  const a = antwort as { ok?: unknown; status?: unknown; text?: () => Promise<string> } | null;
  if (!a || typeof a !== 'object' || a.ok !== false) return null;
  let satz = '';
  try {
    satz = typeof a.text === 'function' ? (await a.text()).trim() : '';
  } catch {
    satz = '';
  }
  // Der Satz des Heim-PC steht als `{"fehler": …}` (z. B. 409 «anderes Gerät …»).
  try {
    const fehler = (JSON.parse(satz) as { fehler?: unknown } | null)?.fehler;
    if (typeof fehler === 'string' && fehler.trim() !== '') satz = fehler.trim();
  } catch {
    /* kein JSON: der Text selbst */
  }
  // Ein kurzer Satz (wie der der App ohne Heim-PC) wird gezeigt, eine Fehlerseite nicht.
  return satz && satz.length <= 200 && !satz.startsWith('<') ? satz : `Der Heim-PC hat nicht gesichert (Antwort ${String(a.status)}).`;
}
