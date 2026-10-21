/**
 * STELLVERTRETER (Visbox) (Kopfteile S2, Entscheide 108, 114–116, 20.10.2026) fuer
 * `state/kosmo-coop.ts` von KosmoOrbit.
 *
 * In KosmoOrbit fuehrt diese Datei den Coop (Agenten aendern ohne Karte), die Vollautomatik, die
 * Schritte der Agenten mit «Zurücknehmen» und die Wache fuer Strg+Z. **In Visbox liegt das an zwei
 * anderen Orten:**
 *
 *  - **Die Selbständigkeit** (Karte | Coop | Voll, Entscheid 108 A) haelt die Mac-App (`Kizentrale`),
 *    und sie gilt fuer jeden Aufruf (`visboxKi.rufe(…, modus)`). Die woertlichen Schalter der Seite
 *    (`KosmoCoop.tsx`, der Wirt) schicken ihren Wunsch ueber den Wirt an die App (`registriereModusWeg`);
 *    die App bestaetigt mit `window.visboxWirt.lage({modus})` (`setzeModusVonApp`). Coop heisst
 *    «Coop», Vollautomatik «Voll», beides aus «Karte».
 *  - **Die Schritte ohne Karte und ihre Ruecknahme** fuehrt der KI-Werkzeugsatz der Knotenansicht
 *    (`modules/vis/ki-werkzeuge.ts`: `kiSchritte`, `rueckgaengigKi`, Entscheid 114 — ein eigener
 *    Verlauf, getrennt von Strg+Z des Architekten). Dieser Stellvertreter zeigt sie als Coop-Schritte
 *    (`haengeAnKiVerlauf`) und nimmt sie dort zurueck. Die Wache fuer Strg+Z setzt der Wirt
 *    (`ki-wirt.ts`), nicht diese Datei.
 *
 * Die Schritte von Claude und vom Assistenten (Plan KI-Bedienung Stufe 5, 21.10.2026) stehen hier;
 * der zweite Urheber heisst in den woertlichen Teilen «kosmo» (sein Name kommt aus `kosmoName()`,
 * in Visbox «Assistent»), im Werkzeugsatz «assistent».
 *
 * **Die Wache der KosmoMaus** (Stufe 6, `state/kosmo-maus.ts` woertlich) fragt hier, bevor eine
 * Handlung der Agenten-Maus einen Befehl ausfuehrt (`versucheCoop`). In KosmoOrbit wendet der Coop
 * dort direkt an, sonst wird eine Maus-Karte. **In Visbox geht jeder Vis-Befehl einer Agenten-Hand
 * durch den KI-Werkzeugsatz** (`behandle` mit dem Modus der App): dieselbe Regel wie ein Werkzeug-
 * aufruf (`brauchtKarte` — Karte, Coop oder Voll; Loeschen und Rendern immer Karte), dieselben
 * Karten in der Leiste der Mac-App, derselbe KI-Verlauf mit «zurücknehmen» (Entscheid 114). Eine
 * zweite Kartenart fuer dieselbe Aenderung gaebe es sonst nur, weil die KI geklickt statt gerufen hat.
 */
import { create } from 'zustand';
import { execute, isSettingsPatch, type AnyPatch, type ExecutionResult, type KosmoDoc } from '@kosmo/kernel';
import { merkeAngehalten, useProject } from './project-store';
import { URHEBER_NAME, useKosmoMaus, type Urheber } from './kosmo-maus-freigabe';
import { abonniere, behandle, kiSchritte, offeneVorschlaege, rueckgaengigKi, werkzeugNameFuer, type KiUrheber } from '../modules/vis/ki-werkzeuge';

export type CoopWeg = 'mcp' | 'maus' | 'chat' | 'werkzeug';

/** Die Quelle in Worten fuer den Verlauf — wortgleich wie dort. */
export const COOP_WEG_NAME: Record<CoopWeg, string> = {
  mcp: 'Werkzeug (Claude)',
  maus: 'KosmoMaus',
  chat: 'Chat',
  werkzeug: 'Werkzeug',
};

export type CoopStufe = 'coop' | 'vollautomatik';

/** Ein Schritt eines Agenten ohne Karte — Form wie dort. */
export interface CoopGruppe {
  kennung: string;
  urheber: Urheber;
  weg: CoopWeg;
  commandId: string;
  zusammenfassung: string;
  /** ISO-Zeit */
  zeit: string;
  folge: number;
  doc: KosmoDoc;
  patches: readonly AnyPatch[];
  zurueckgenommen: boolean;
  stufe: CoopStufe;
  anlass?: string;
  vermerk?: string;
}

/** Die Selbständigkeit wie in der Mac-App (`Selbstaendigkeit`). */
export type VisboxModus = 'karte' | 'coop' | 'voll';

interface CoopZustand {
  an: Record<Urheber, boolean>;
  vollautomatik: boolean;
  vollautomatikSeit: string | null;
  seit: Record<Urheber, string | null>;
  gruppen: CoopGruppe[];
}

export const useKosmoCoop = create<CoopZustand>(() => ({
  an: { claude: false, kosmo: false },
  vollautomatik: false,
  vollautomatikSeit: null,
  seit: { claude: null, kosmo: null },
  gruppen: [],
}));

/** Die Selbständigkeit aus dem Zustand. */
export function modusAus(z: Pick<CoopZustand, 'an' | 'vollautomatik'> = useKosmoCoop.getState()): VisboxModus {
  if (z.vollautomatik) return 'voll';
  return z.an.claude ? 'coop' : 'karte';
}

function setzeModus(modus: VisboxModus): void {
  const z = useKosmoCoop.getState();
  const jetzt = new Date().toISOString();
  const coop = modus !== 'karte';
  const voll = modus === 'voll';
  useKosmoCoop.setState({
    // Die Selbständigkeit der App gilt fuer Claude und den Assistenten zugleich.
    an: { claude: coop, kosmo: coop },
    seit: coop && !z.an.claude ? { claude: jetzt, kosmo: jetzt } : z.seit,
    vollautomatik: voll,
    vollautomatikSeit: voll && !z.vollautomatik ? jetzt : z.vollautomatikSeit,
  });
}

let modusWeg: ((modus: VisboxModus) => void) | null = null;

/** Der Wirt meldet, wie ein Wunsch die App erreicht (`visboxWirt` → `{art:'modus'}`). */
export function registriereModusWeg(weg: ((modus: VisboxModus) => void) | null): void {
  modusWeg = weg;
}

function wuensche(modus: VisboxModus): void {
  setzeModus(modus);
  modusWeg?.(modus);
}

/** Die App bestaetigt (oder setzt beim Laden) die Selbständigkeit — ohne Rueckmeldung an sie. */
export function setzeModusVonApp(modus: VisboxModus): void {
  setzeModus(modus);
}

export function coopAn(urheber: Urheber): boolean {
  return useKosmoCoop.getState().an[urheber];
}

/** «Coop – ändert frei»: aus «Karte» wird «Coop», aus «Coop»/«Voll» wieder «Karte». */
export function setzeCoop(_urheber: Urheber, wert: boolean): void {
  wuensche(wert ? (useKosmoCoop.getState().vollautomatik ? 'voll' : 'coop') : 'karte');
}

/** «Vollautomatik»: an heisst «Voll», aus heisst zurueck auf «Coop». */
export function setzeVollautomatik(wert: boolean): void {
  wuensche(wert ? 'voll' : useKosmoCoop.getState().an.claude ? 'coop' : 'karte');
}

/** «Alle anhalten»: zurueck auf «Karte». */
export function halteAlleAn(): void {
  wuensche('karte');
}
export const stoppeCoop = halteAlleAn;

// ---------------------------------------------------------------------------------- Schritte

const gesehen = new Map<string, { zeit: string; folge: number; stufe: CoopStufe }>();
let folge = 0;

/** Der Urheber der woertlichen Teile zum Urheber des Werkzeugsatzes — und zurueck. */
export function kiUrheberVon(u: Urheber): KiUrheber {
  return u === 'claude' ? 'claude' : 'assistent';
}
function urheberVon(u: KiUrheber): Urheber {
  return u === 'claude' ? 'claude' : 'kosmo';
}

/** Die Kennungen der Schritte aus der Agenten-Maus («M-…», wie «K-…» der Werkzeugaufrufe). */
const MAUS_KENNUNG = 'M-';

function leseSchritte(): void {
  const z = useKosmoCoop.getState();
  const gruppen = kiSchritte()
    .map((s): CoopGruppe => {
      let merk = gesehen.get(s.kennung);
      if (!merk) {
        merk = { zeit: new Date().toISOString(), folge: ++folge, stufe: z.vollautomatik ? 'vollautomatik' : 'coop' };
        gesehen.set(s.kennung, merk);
      }
      return {
        kennung: s.kennung,
        urheber: urheberVon(s.urheber),
        weg: s.kennung.startsWith(MAUS_KENNUNG) ? 'maus' : s.urheber === 'claude' ? 'mcp' : 'chat',
        commandId: '',
        zusammenfassung: s.zusammenfassung,
        zeit: merk.zeit,
        folge: merk.folge,
        doc: s.doc,
        patches: s.patches,
        zurueckgenommen: s.zurueckgenommen,
        stufe: merk.stufe,
      };
    });
  useKosmoCoop.setState({ gruppen });
}

/** Haengt die Schritte an den KI-Verlauf des Werkzeugsatzes. Gerufen vom Wirt. Liefert das Abhaengen. */
export function haengeAnKiVerlauf(): () => void {
  leseSchritte();
  const ab = abonniere((e) => {
    if (e.art === 'kiverlauf') leseSchritte();
  });
  // Ein anderes Dokument (Mappe gewechselt): die Schritte gehoerten zum alten.
  const abDoc = useProject.subscribe((s, vorher) => {
    if (s.doc !== vorher.doc) leseSchritte();
  });
  return () => {
    ab();
    abDoc();
  };
}

export function coopSchritte(z: Pick<CoopZustand, 'gruppen'> = useKosmoCoop.getState()): CoopGruppe[] {
  const doc = useProject.getState().doc;
  return z.gruppen.filter((g) => g.doc === doc);
}

/** Kennungen der Teile eines Schritts — wortgleich wie dort (`coop-marke.ts` liest sie). */
export function kennungenVon(g: Pick<CoopGruppe, 'patches'>): string[] {
  return [...new Set(g.patches.filter((p) => !isSettingsPatch(p)).map((p) => (p as { id: string }).id))];
}

// ---------------------------------------------------------------------------------- Praesenz

export interface PraesenzEintrag {
  wer: 'du' | Urheber;
  name: string;
  coop: boolean;
  vollautomatik: boolean;
  bedient: boolean;
  zuletzt: { zusammenfassung: string; zeit: string; kennungen: string[] } | null;
  offen: number;
}

/** Wer im Projekt arbeitet: du, Claude und der Assistent; «bedient» aus der KosmoMaus (Zeiger steht). */
export function coopPraesenz(): PraesenzEintrag[] {
  const st = useProject.getState();
  const z = useKosmoCoop.getState();
  const eigen = [...st.journal].reverse().find((e) => e.actor === 'benutzer');
  const agent = (u: Urheber): PraesenzEintrag => {
    const seine = coopSchritte(z).filter((g) => g.urheber === u);
    const letzte = seine.at(-1);
    return {
      wer: u,
      name: URHEBER_NAME[u],
      coop: z.an[u] || z.vollautomatik,
      vollautomatik: z.vollautomatik,
      bedient: useKosmoMaus.getState().zeigerJe[u] !== null,
      zuletzt: letzte ? { zusammenfassung: letzte.zusammenfassung, zeit: letzte.zeit, kennungen: kennungenVon(letzte) } : null,
      offen: seine.filter((g) => !g.zurueckgenommen).length,
    };
  };
  return [
    {
      wer: 'du',
      name: 'Du',
      coop: true,
      vollautomatik: false,
      bedient: false,
      zuletzt: eigen ? { zusammenfassung: eigen.summary, zeit: eigen.ts, kennungen: [] } : null,
      offen: 0,
    },
    agent('claude'),
    agent('kosmo'),
  ];
}

// ---------------------------------------------------------------------------------- Zuruecknehmen

export type ZuruecknahmeStatus = 'zurueckgenommen' | 'nachfrage' | 'blockiert' | 'schon' | 'unbekannt';

export interface Zuruecknahme {
  status: ZuruecknahmeStatus;
  abhaengige: CoopGruppe[];
  schritte: CoopGruppe[];
  satz: string;
}

/**
 * «Zurücknehmen» an einem Schritt. Der Verlauf des Werkzeugsatzes nimmt je Urheber nur den **letzten**
 * stehenden Schritt zurueck (Entscheid 114, `rueckgaengigKi`); an einem frueheren sagt der Satz, dass
 * zuerst die spaeteren dran sind — statt sie still mitzunehmen.
 */
export function nimmSchrittZurueck(kennung: string, _opts: { mitAbhaengigen?: boolean } = {}): Zuruecknahme {
  const g = coopSchritte().find((x) => x.kennung === kennung);
  if (!g) return { status: 'unbekannt', abhaengige: [], schritte: [], satz: 'Diesen Schritt gibt es im offenen Projekt nicht (mehr).' };
  const seine = coopSchritte().filter((x) => x.urheber === g.urheber);
  const letzter = seine[seine.length - 1];
  if (letzter && letzter.kennung !== kennung) {
    return {
      status: 'blockiert',
      abhaengige: [],
      schritte: [],
      satz: `«${g.zusammenfassung}» lässt sich erst zurücknehmen, wenn die späteren Schritte von ${URHEBER_NAME[g.urheber]} zurückgenommen sind — zuerst «${letzter.zusammenfassung}».`,
    };
  }
  const r = rueckgaengigKi(kiUrheberVon(g.urheber));
  leseSchritte();
  return r.ok
    ? { status: 'zurueckgenommen', abhaengige: [], schritte: [g], satz: r.satz }
    : { status: 'blockiert', abhaengige: [], schritte: [], satz: r.satz };
}

// ---------------------------------------------------------------------------------- Wache der KosmoMaus

let wendetAn = false;
let mausFolge = 0;

/** Laeuft gerade ein Schritt aus `versucheCoop`? Dann laesst die Wache den Befehl durch (wie dort). */
export function coopWendetGeradeAn(): boolean {
  return wendetAn;
}

/** Wendet die App Aenderungen dieses Agenten ohne Karte an (Coop oder Voll)? */
export function coopWirksam(urheber: Urheber): boolean {
  const z = useKosmoCoop.getState();
  return z.vollautomatik || z.an[urheber];
}

/**
 * Die Wache der KosmoMaus fragt, bevor ein Befehl einer Agenten-Hand laeuft. Ein Vis-Befehl geht durch
 * den Werkzeugsatz (`behandle`, Modus der App): in «Karte» und bei Loeschen/Rendern eine Karte, sonst
 * direkt als KI-Schritt. Das Ergebnis traegt bei einer Karte oder einem Fehler das Kennzeichen
 * «angehalten» (`merkeAngehalten`) — das Projekt ist dann unveraendert. `null`: kein Vis-Befehl, die
 * Wache legt wie dort eine Maus-Karte an. `_weg` wie dort (immer «maus» in Visbox).
 */
export function versucheCoop(wer: Urheber, commandId: string, params: unknown, _weg: CoopWeg = 'maus'): ExecutionResult | null {
  if (!commandId.startsWith('vis.')) return null;
  let probe: ExecutionResult;
  try {
    probe = execute(useProject.getState().doc, commandId, params, { actor: wer === 'claude' ? 'claude' : 'kosmo', dryRun: true });
  } catch {
    return null;
  }
  // NACH DEM NEULADEN zaehlt die Folge von vorn, die App gibt aber die alten Maus-Karten zurueck
  // (Strang Karten): eine Kennung, die schon als Karte liegt, wird uebersprungen.
  const belegt = new Set(offeneVorschlaege().map((v) => v.kennung));
  let kennung = `${MAUS_KENNUNG}${++mausFolge}`;
  while (belegt.has(kennung)) kennung = `${MAUS_KENNUNG}${++mausFolge}`;
  wendetAn = true;
  let antwort;
  try {
    antwort = behandle({ kennung, werkzeug: werkzeugNameFuer(commandId), argumente: params, urheber: kiUrheberVon(wer) }, modusAus());
  } finally {
    wendetAn = false;
  }
  leseSchritte();
  if ('sofort' in antwort && antwort.sofort.ok) return probe;
  return merkeAngehalten(probe);
}

/** Nur fuer Proben. */
export function setzeCoopZurueck(): void {
  useKosmoCoop.setState({
    an: { claude: false, kosmo: false },
    vollautomatik: false,
    vollautomatikSeit: null,
    seit: { claude: null, kosmo: null },
    gruppen: [],
  });
  gesehen.clear();
  folge = 0;
  mausFolge = 0;
}
