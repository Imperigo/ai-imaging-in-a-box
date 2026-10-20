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
 * Es zaehlen nur Schritte von Claude: Der Assistent bedient die Knotenansicht heute nicht (S3).
 */
import { create } from 'zustand';
import { isSettingsPatch, type AnyPatch, type KosmoDoc } from '@kosmo/kernel';
import { useProject } from './project-store';
import { URHEBER_NAME, type Urheber } from './kosmo-maus-freigabe';
import { abonniere, kiSchritte, rueckgaengigKi } from '../modules/vis/ki-werkzeuge';

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

function leseSchritte(): void {
  const z = useKosmoCoop.getState();
  const gruppen = kiSchritte()
    .filter((s) => s.urheber === 'claude')
    .map((s): CoopGruppe => {
      let merk = gesehen.get(s.kennung);
      if (!merk) {
        merk = { zeit: new Date().toISOString(), folge: ++folge, stufe: z.vollautomatik ? 'vollautomatik' : 'coop' };
        gesehen.set(s.kennung, merk);
      }
      return {
        kennung: s.kennung,
        urheber: 'claude',
        weg: 'mcp',
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

/** Wer im Projekt arbeitet: du und Claude (ohne KosmoMaus bedient niemand mit eigenem Zeiger). */
export function coopPraesenz(): PraesenzEintrag[] {
  const st = useProject.getState();
  const z = useKosmoCoop.getState();
  const eigen = [...st.journal].reverse().find((e) => e.actor === 'benutzer');
  const letzte = [...coopSchritte(z)].reverse().find((g) => g.urheber === 'claude');
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
    {
      wer: 'claude',
      name: URHEBER_NAME.claude,
      coop: z.an.claude || z.vollautomatik,
      vollautomatik: z.vollautomatik,
      bedient: false,
      zuletzt: letzte ? { zusammenfassung: letzte.zusammenfassung, zeit: letzte.zeit, kennungen: kennungenVon(letzte) } : null,
      offen: coopSchritte(z).filter((g) => !g.zurueckgenommen).length,
    },
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
 * «Zurücknehmen» an einem Schritt. Der Verlauf des Werkzeugsatzes nimmt nur den **letzten** stehenden
 * Schritt von Claude zurueck (Entscheid 114, `rueckgaengigKi`); an einem frueheren sagt der Satz, dass
 * zuerst die spaeteren dran sind — statt sie still mitzunehmen.
 */
export function nimmSchrittZurueck(kennung: string, _opts: { mitAbhaengigen?: boolean } = {}): Zuruecknahme {
  const alle = coopSchritte();
  const g = alle.find((x) => x.kennung === kennung);
  if (!g) return { status: 'unbekannt', abhaengige: [], schritte: [], satz: 'Diesen Schritt gibt es im offenen Projekt nicht (mehr).' };
  const letzter = alle[alle.length - 1];
  if (letzter && letzter.kennung !== kennung) {
    return {
      status: 'blockiert',
      abhaengige: [],
      schritte: [],
      satz: `«${g.zusammenfassung}» lässt sich erst zurücknehmen, wenn die späteren Schritte von Claude zurückgenommen sind — zuerst «${letzter.zusammenfassung}».`,
    };
  }
  const r = rueckgaengigKi('claude');
  leseSchritte();
  return r.ok
    ? { status: 'zurueckgenommen', abhaengige: [], schritte: [g], satz: r.satz }
    : { status: 'blockiert', abhaengige: [], schritte: [], satz: r.satz };
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
}
