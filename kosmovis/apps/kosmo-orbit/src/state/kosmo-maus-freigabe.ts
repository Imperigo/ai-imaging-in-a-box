/**
 * KosmoBlick/KosmoMaus — Freigabe, Urheber und Journal (Owner-Entscheid E157,
 * 06.10.2026; Anleitung `docs/CLAUDE-ANSCHLUSS.md` «Mitschauen und Bedienen»).
 *
 * Owner wörtlich: «freigabe für eine eigene bedienung nicht fernsteuerung
 * meiner maus sondern einer eigenen innerhalb der software die mich nicht
 * tangiert (dito für die llms von kosmo)».
 *
 * Diese Datei hält nur den Zustand: wer darf mitschauen, wer darf bedienen,
 * wer hat was getan. Sehen (`kosmo-blick-live.ts`) und Bedienen
 * (`kosmo-maus.ts`) fragen hier, bevor sie etwas tun.
 *
 * WARUM im Gerätespeicher (`localStorage`) und nicht im Projekt: die Freigabe
 * gilt für DIESES Gerät und diesen Menschen, nicht für das Bauwerk. Sie reist
 * nicht über Sync und nicht in ein `.kosmo`-Paket.
 *
 * Standard (Owner-Entscheid 07.10.2026, ersetzt «Bedienen aus» aus E157):
 * Mitschauen an, Bedienen an — für Claude und Kosmo. Owner wörtlich: «schalte
 * bitte beide funktionen bedienen standardmässig ein.» Ein gespeicherter
 * Gerätewert schlägt den Standard: wer «Bedienen» bewusst ausschaltet (Schalter,
 * Esc, «Stopp»), findet es nach dem Neuladen aus. Nur lokal bleibt (E157):
 * über den Tunnel gibt es weder Blick noch Maus.
 */

import { create } from 'zustand';
import type { PaketSchritt } from './project-store';

/** Wer handelt. Jede Handlung trägt genau einen davon (E158: «Urheber je Änderung»). */
export type Urheber = 'claude' | 'kosmo';
export const URHEBER: readonly Urheber[] = ['claude', 'kosmo'];
export const URHEBER_NAME: Record<Urheber, string> = { claude: 'Claude', kosmo: 'Kosmo' };

export interface AgentFreigabe {
  mitschauen: boolean;
  bedienen: boolean;
}
export type Freigaben = Record<Urheber, AgentFreigabe>;

export const FREIGABE_SCHLUESSEL = 'kosmo.maus.freigabe';
export const JOURNAL_SCHLUESSEL = 'kosmo.maus.journal';
/** So viele Einträge bleiben im Journal; ältere fallen hinten weg. */
export const JOURNAL_MAX = 200;

/**
 * Ab Werk (Owner 07.10.2026: «schalte bitte beide funktionen bedienen
 * standardmässig ein.»): beide Agenten dürfen mitschauen UND bedienen.
 */
export const STANDARD_FREIGABEN: Freigaben = {
  claude: { mitschauen: true, bedienen: true },
  kosmo: { mitschauen: true, bedienen: true },
};

export interface JournalEintrag {
  /** ISO-Zeit */
  zeit: string;
  urheber: Urheber;
  /** `coop`: eine Änderung im Coop-Modus oder deren Rücknahme (E158, `kosmo-coop.ts`). */
  werkzeug: 'blick' | 'maus' | 'freigabe' | 'coop';
  /** z.B. «klick», «tippen», «bild», «stopp», «coop-angewendet» */
  aktion: string;
  /** Ziel in Worten (testid, Text oder Punkt) */
  ziel?: string;
  ergebnis: 'ok' | 'verweigert' | 'fehler';
  text: string;
}

/** Eine Projektänderung, die eine Agenten-Handlung auslösen wollte (E157: weiter über Karten). */
export interface MausVorschlag {
  kennung: string;
  urheber: Urheber;
  commandId: string;
  params: unknown;
  zusammenfassung: string;
  /**
   * Sammelweg (`alsEinVorschlag`, project-store.ts): mehrere Befehle EINER
   * Handlung als EINE Karte; «Anwenden» wendet sie atomar als EINE
   * Rückgängig-Gruppe an. Fehlt das Feld, ist es ein Einzelbefehl.
   */
  schritte?: readonly PaketSchritt[];
}

export interface AgentZeiger {
  urheber: Urheber;
  x: number;
  y: number;
  /** Zeitpunkt der letzten Handlung — für das Ausblenden nach Ruhe */
  zeit: number;
}

/** Je Agent der eigene Zeiger (UI-L31: Claude und Kosmo gleichzeitig sichtbar). */
export type ZeigerJe = Record<Urheber, AgentZeiger | null>;

export const KEIN_ZEIGER_JE: ZeigerJe = { claude: null, kosmo: null };

/**
 * Runde 34 (Demolauf 16.10.2026, Fehlerprotokoll Nr. 73–77): wodurch «Bedienen»
 * zuletzt an- oder ausging. Der Owner sah den Schalter «an», Claude bekam
 * «ausgeschaltet» — und keiner wusste, wodurch. Jetzt trägt der EINE Zustand
 * (`freigaben`) den letzten Wechsel mit Grund und Zeit; Schalter, Leiste,
 * Absage, `kosmo_blick` und `kosmo_status` lesen ihn von hier.
 */
export type BedienGrund = 'schalter' | 'esc' | 'stopp' | 'alle-anhalten' | 'anderes-fenster' | 'agent';
export interface BedienWechsel {
  an: boolean;
  grund: BedienGrund;
  /** ISO-Zeit */
  zeit: string;
}
export type BedienWechselJe = Record<Urheber, BedienWechsel | null>;
export const KEIN_WECHSEL_JE: BedienWechselJe = { claude: null, kosmo: null };

export const BEDIEN_GRUND_NAME: Record<BedienGrund, string> = {
  schalter: 'Schalter',
  esc: 'Esc',
  stopp: '«Stopp»',
  'alle-anhalten': '«Alle anhalten»',
  'anderes-fenster': 'anderes Fenster',
  agent: 'den Agenten selbst',
};

interface KosmoMausZustand {
  freigaben: Freigaben;
  /**
   * Der Zeiger des ZULETZT handelnden Agenten — für die bestehenden Leser
   * (`KosmoMausEbene`, Leiste). Bleibt unverändert, wie er war.
   */
  zeiger: AgentZeiger | null;
  /**
   * UI-L31 (kosmo-maus-2, 08.10.2026): je Agent sein letzter Zeiger, damit
   * beide Figuren gleichzeitig stehen können. `null` = dieser Agent hat
   * (noch) nicht gehandelt, oder sein Bedienen wurde beendet.
   */
  zeigerJe: ZeigerJe;
  journal: JournalEintrag[];
  vorschlaege: MausVorschlag[];
  /** Runde 34: der letzte Wechsel von «Bedienen» je Agent (nur Arbeitsspeicher; das Journal hält den Verlauf). */
  bedienWechsel: BedienWechselJe;
}

function speicher(): Storage | undefined {
  try {
    return typeof localStorage === 'undefined' ? undefined : localStorage;
  } catch {
    return undefined;
  }
}

/**
 * Liest die Freigaben; alles Fehlende oder Unlesbare fällt auf den Standard
 * zurück (seit 07.10.2026 Bedienen an). Ein gespeichertes `false` bleibt aus.
 */
export function leseFreigaben(s: Pick<Storage, 'getItem'> | undefined = speicher()): Freigaben {
  let roh: unknown = null;
  try {
    roh = JSON.parse(s?.getItem(FREIGABE_SCHLUESSEL) ?? 'null');
  } catch {
    roh = null;
  }
  const aus = (u: Urheber): AgentFreigabe => {
    const r = (roh as Record<string, Partial<AgentFreigabe>> | null)?.[u];
    return {
      mitschauen: typeof r?.mitschauen === 'boolean' ? r.mitschauen : STANDARD_FREIGABEN[u].mitschauen,
      bedienen: typeof r?.bedienen === 'boolean' ? r.bedienen : STANDARD_FREIGABEN[u].bedienen,
    };
  };
  return { claude: aus('claude'), kosmo: aus('kosmo') };
}

function leseJournal(): JournalEintrag[] {
  try {
    const roh = JSON.parse(speicher()?.getItem(JOURNAL_SCHLUESSEL) ?? '[]') as unknown;
    return Array.isArray(roh) ? (roh as JournalEintrag[]).slice(-JOURNAL_MAX) : [];
  } catch {
    return [];
  }
}

export const useKosmoMaus = create<KosmoMausZustand>(() => ({
  freigaben: leseFreigaben(),
  zeiger: null,
  zeigerJe: { ...KEIN_ZEIGER_JE },
  journal: leseJournal(),
  vorschlaege: [],
  bedienWechsel: { ...KEIN_WECHSEL_JE },
}));

/**
 * Runde 34 (Nr. 75/77, «ein einziger Zustand»): ein zweites Fenster derselben
 * App (gleicher Gerätespeicher) ändert die Freigabe — dieses Fenster folgt,
 * statt still beim alten Stand zu bleiben. Der Zeiger geht mit, wenn Bedienen
 * dort ausging.
 */
function folgeAnderemFenster(e: StorageEvent): void {
  if (e.key !== FREIGABE_SCHLUESSEL) return;
  const vorher = useKosmoMaus.getState().freigaben;
  const neu = leseFreigaben();
  const zeit = new Date().toISOString();
  const wechsel = URHEBER.filter((u) => vorher[u].bedienen !== neu[u].bedienen);
  useKosmoMaus.setState((z) => {
    const zeigerJe = { ...z.zeigerJe };
    const bedienWechsel = { ...z.bedienWechsel };
    for (const u of wechsel) {
      bedienWechsel[u] = { an: neu[u].bedienen, grund: 'anderes-fenster', zeit };
      if (!neu[u].bedienen) zeigerJe[u] = null;
    }
    const zeiger = z.zeiger && !neu[z.zeiger.urheber].bedienen ? null : z.zeiger;
    return { freigaben: neu, zeigerJe, zeiger, bedienWechsel };
  });
}
if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
  window.addEventListener('storage', folgeAnderemFenster);
}

function schreibe(schluessel: string, wert: unknown): void {
  try {
    speicher()?.setItem(schluessel, JSON.stringify(wert));
  } catch {
    /* privates Fenster oder voll: die Freigabe gilt dann nur bis zum Neuladen */
  }
}

export function freigabe(urheber: Urheber): AgentFreigabe {
  return useKosmoMaus.getState().freigaben[urheber];
}

export function protokolliere(e: Omit<JournalEintrag, 'zeit'>): JournalEintrag {
  const eintrag: JournalEintrag = { zeit: new Date().toISOString(), ...e };
  useKosmoMaus.setState((z) => ({ journal: [...z.journal, eintrag].slice(-JOURNAL_MAX) }));
  schreibe(JOURNAL_SCHLUESSEL, useKosmoMaus.getState().journal);
  return eintrag;
}

/**
 * Freigabe setzen. NUR für den Menschen: der Schalter in der Oberfläche ruft
 * das mit einem echten (vertrauenswürdigen) Klick. Die KosmoMaus selbst kann
 * den Schalter nicht treffen (`kosmo-maus.ts`, Sperrzone).
 */
export function setzeFreigabe(urheber: Urheber, art: keyof AgentFreigabe, wert: boolean): void {
  const neu: Freigaben = {
    ...useKosmoMaus.getState().freigaben,
    [urheber]: { ...useKosmoMaus.getState().freigaben[urheber], [art]: wert },
  };
  useKosmoMaus.setState((z) => ({
    freigaben: neu,
    ...(art === 'bedienen' && !wert ? { zeiger: null, zeigerJe: { ...z.zeigerJe, [urheber]: null } } : {}),
    ...(art === 'bedienen'
      ? { bedienWechsel: { ...z.bedienWechsel, [urheber]: { an: wert, grund: 'schalter', zeit: new Date().toISOString() } } }
      : {}),
  }));
  schreibe(FREIGABE_SCHLUESSEL, neu);
  protokolliere({
    urheber,
    werkzeug: 'freigabe',
    aktion: `${art} ${wert ? 'an' : 'aus'}`,
    ergebnis: 'ok',
    text: `${art === 'mitschauen' ? 'Mitschauen' : 'Bedienen'} für ${URHEBER_NAME[urheber]} ${wert ? 'eingeschaltet' : 'ausgeschaltet'}.`,
  });
}

/**
 * Esc, «Stopp» oder «Alle anhalten»: Bedienen für alle Agenten aus, Zeiger weg.
 * Liefert, für wen Bedienen an war (die Oberfläche meldet es sichtbar).
 * Esc ruft das seit Runde 34 nur noch, solange ein Agent sichtbar bedient und
 * nichts aufgeklappt ist (`KosmoMausEbene.tsx#escBeendetBedienen`).
 */
export function stoppeBedienen(grund: 'esc' | 'stopp' | 'alle-anhalten'): Urheber[] {
  const z = useKosmoMaus.getState();
  const liefen = URHEBER.filter((u) => z.freigaben[u].bedienen);
  if (liefen.length === 0 && !z.zeiger && !z.zeigerJe.claude && !z.zeigerJe.kosmo) return [];
  const neu: Freigaben = {
    claude: { ...z.freigaben.claude, bedienen: false },
    kosmo: { ...z.freigaben.kosmo, bedienen: false },
  };
  const zeit = new Date().toISOString();
  const bedienWechsel = { ...z.bedienWechsel };
  for (const u of liefen) bedienWechsel[u] = { an: false, grund, zeit };
  useKosmoMaus.setState({ freigaben: neu, zeiger: null, zeigerJe: { ...KEIN_ZEIGER_JE }, bedienWechsel });
  schreibe(FREIGABE_SCHLUESSEL, neu);
  for (const u of liefen) {
    protokolliere({
      urheber: u,
      werkzeug: 'freigabe',
      aktion: 'stopp',
      ergebnis: 'ok',
      text: `Bedienen für ${URHEBER_NAME[u]} beendet (${BEDIEN_GRUND_NAME[grund]}).`,
    });
  }
  return liefen;
}

/**
 * Owner-Entscheid 20.10.2026 (Runde 34): ein Agent darf SEIN Bedienen selbst
 * beenden, nie einschalten. Nur dieser Urheber; der andere bleibt, wie er ist.
 * Liefert false, wenn Bedienen fuer ihn schon aus war.
 */
export function beendeEigenesBedienen(urheber: Urheber): boolean {
  const z = useKosmoMaus.getState();
  if (!z.freigaben[urheber].bedienen) return false;
  const neu: Freigaben = { ...z.freigaben, [urheber]: { ...z.freigaben[urheber], bedienen: false } };
  const zeit = new Date().toISOString();
  useKosmoMaus.setState({
    freigaben: neu,
    zeigerJe: { ...z.zeigerJe, [urheber]: null },
    ...(z.zeiger?.urheber === urheber ? { zeiger: null } : {}),
    bedienWechsel: { ...z.bedienWechsel, [urheber]: { an: false, grund: 'agent', zeit } },
  });
  schreibe(FREIGABE_SCHLUESSEL, neu);
  protokolliere({
    urheber,
    werkzeug: 'freigabe',
    aktion: 'stopp',
    ergebnis: 'ok',
    text: `Bedienen für ${URHEBER_NAME[urheber]} beendet (${BEDIEN_GRUND_NAME.agent}).`,
  });
  return true;
}

function uhrzeit(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

/**
 * Runde 34 (Nr. 74/77): «Bedienen» in einem Satz — an/aus, seit wann, wodurch.
 * Dieselbe Zeile lesen die Absage der KosmoMaus, `kosmo_blick` und `kosmo_status`.
 */
export function bedienZustandText(urheber: Urheber): string {
  const z = useKosmoMaus.getState();
  const an = z.freigaben[urheber].bedienen;
  const w = z.bedienWechsel[urheber];
  if (an) return w?.an ? `Bedienen: an (seit ${uhrzeit(w.zeit)}, ${BEDIEN_GRUND_NAME[w.grund]})` : 'Bedienen: an';
  if (!w || w.an) return 'Bedienen: aus (gespeicherte Einstellung dieses Geräts); nur der Architekt schaltet es ein';
  const wodurch = w.grund === 'schalter' ? 'ausgeschaltet am Schalter' : `beendet durch ${BEDIEN_GRUND_NAME[w.grund]}`;
  return `Bedienen: aus — ${wodurch} um ${uhrzeit(w.zeit)}; nur der Architekt schaltet es wieder ein`;
}

export function setzeZeiger(urheber: Urheber, x: number, y: number): void {
  const zeiger: AgentZeiger = { urheber, x: Math.round(x), y: Math.round(y), zeit: Date.now() };
  useKosmoMaus.setState((z) => ({ zeiger, zeigerJe: { ...z.zeigerJe, [urheber]: zeiger } }));
}

let naechsteVorschlagKennung = 1;

export function legeVorschlagAn(v: Omit<MausVorschlag, 'kennung'>): MausVorschlag {
  const vorschlag: MausVorschlag = { kennung: `m-${naechsteVorschlagKennung++}`, ...v };
  useKosmoMaus.setState((z) => ({ vorschlaege: [...z.vorschlaege, vorschlag] }));
  return vorschlag;
}

export function nimmVorschlag(kennung: string): MausVorschlag | undefined {
  const v = useKosmoMaus.getState().vorschlaege.find((x) => x.kennung === kennung);
  if (v) useKosmoMaus.setState((z) => ({ vorschlaege: z.vorschlaege.filter((x) => x.kennung !== kennung) }));
  return v;
}

/**
 * Owner-Entscheid 08.10.2026 («A: sichtbar verwerfen»): alle offenen
 * Maus-Karten fallen weg, jede mit einer Zeile «verworfen: <grund>» im
 * Journal. Liefert die verworfenen Karten (für die Meldung).
 */
export function verwirfMausVorschlaege(grund: string): MausVorschlag[] {
  const weg = useKosmoMaus.getState().vorschlaege;
  if (weg.length === 0) return [];
  useKosmoMaus.setState({ vorschlaege: [] });
  for (const v of weg) {
    protokolliere({
      urheber: v.urheber,
      werkzeug: 'maus',
      aktion: 'verworfen',
      ziel: v.commandId,
      ergebnis: 'ok',
      text: `verworfen: ${grund} — Karte ${v.kennung} «${v.zusammenfassung}»`,
    });
  }
  return weg;
}

/** Nur für Proben: alles auf den Anfang. */
export function setzeKosmoMausZurueck(): void {
  useKosmoMaus.setState({
    freigaben: structuredClone(STANDARD_FREIGABEN),
    zeiger: null,
    zeigerJe: { ...KEIN_ZEIGER_JE },
    journal: [],
    vorschlaege: [],
    bedienWechsel: { ...KEIN_WECHSEL_JE },
  });
  try {
    speicher()?.removeItem(FREIGABE_SCHLUESSEL);
    speicher()?.removeItem(JOURNAL_SCHLUESSEL);
  } catch {
    /* egal */
  }
}
