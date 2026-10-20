/**
 * STELLVERTRETER (Visbox) (Plan UI-Gleichheit S3, Entscheide 115/116 (2), 20.10.2026) fuer
 * `shell/kosmo-gespraech.ts` von KosmoOrbit.
 *
 * Dort ist diese Datei Kosmos EIN Gespraech: Ansicht (zu, klein, gross), Verlauf, Rolle, Motor, der
 * Weg zum Sprachmodell. Die Kugel (`KosmoOrb.tsx`, woertlich) liest daraus nur, ob das Feld offen ist.
 *
 * **In Visbox fuehrt das Gespraech die Mac-App**, nicht die Seite: Der Assistent (qwen3:14b am
 * Heim-PC, `POST /api/assistent`) wird mit der Anmeldung der App gefragt — das Kennwort laeuft nie
 * durch die Seite (Entscheid 116 (6)) —, und die Regeln des Gespraechs stehen an EINER Stelle, im
 * Kern der App (`Assistentengespraech`: hoechstens eine Karte, keine zweite Anfrage, solange eine
 * unterwegs ist, in den Verlauf nur, was der Server annahm, die Laengen). Dieser Stellvertreter haelt
 * darum nur, **was die App sagt** (`setzeGespraechVonApp`, ueber `window.visboxWirt.lage({assistent})`),
 * und reicht die Wuensche des Felds an sie weiter (`wuenscheGespraech`, Boten-Wunsch «assistent»).
 *
 * Und er fuehrt den Zustand der Kugel nach (`state/kosmo-status.ts`, woertlich): solange eine Anfrage
 * unterwegs ist, «denkt nach»; kommt eine Antwort, waehrend das Feld zu ist, steht sie als Blase an
 * der Kugel (C22, wie dort).
 */
import { create } from 'zustand';
import { kurzform, useKosmoStatus } from '../state/kosmo-status';

/** Wortgleich wie dort; Visbox kennt nur «zu» und «gross» (das Feld). */
export type KosmoAnsicht = 'zu' | 'klein' | 'gross';

export type Sprecher = 'mensch' | 'assistent';

export interface Gespraechsbeitrag {
  von: Sprecher;
  text: string;
}

/** Die violett gerahmte Karte (Blatt 14) — die Zeilen baut der Kern aus den geprueften Einstellungen. */
export interface Vorschlagskarte {
  zeilen: string[];
  rechenzeit: string | null;
}

/** Die Zeile «Assistent» aus `GET /api/heim` (Kern `Assistentenzeile`). */
export type Assistentenstand = 'bereit' | 'laedt' | 'fehlt' | 'aus';

/** Was die App ueber das Gespraech sagt — genau die Felder von `Knotenwirt.Assistentenlage`. */
export interface GespraechVonApp {
  /** Verlauf samt der Nachricht, die gerade unterwegs ist (`angezeigt`). */
  beitraege: Gespraechsbeitrag[];
  wartet: boolean;
  /** Der letzte Satz, der kein Beitrag ist (ein Fehler, «Angewendet …»). */
  hinweis: string | null;
  karte: Vorschlagskarte | null;
  stand: Assistentenstand | null;
  modell: string | null;
  /** Wo sonst das Feld stuende: der Satz, warum nicht (ohne Rechner, Modell fehlt …); `null`: Feld. */
  feldSatz: string | null;
  /** «Was der Assistent nicht tut» — Titel und Satz aus dem Kern (`Assistentengrenzen`). */
  grenzen: { titel: string; satz: string } | null;
  /** Ein Text fuer das Eingabefeld (Ändern, eine zurueckgelegte Nachricht), mit laufender Nummer. */
  feld: { nummer: number; text: string } | null;
}

export type GespraechWunsch =
  | { tat: 'frage'; text: string }
  | { tat: 'anwenden' }
  | { tat: 'ablehnen' }
  | { tat: 'aendern' };

interface Gespraech extends GespraechVonApp {
  ansicht: KosmoAnsicht;
  /** Wortgleich wie dort: ob ein Motor bereitsteht — in Visbox, ob die App das Gespraech fuehrt. */
  motor: boolean;
}

const LEER: GespraechVonApp = {
  beitraege: [],
  wartet: false,
  hinweis: null,
  karte: null,
  stand: null,
  modell: null,
  feldSatz: null,
  grenzen: null,
  feld: null,
};

export const useKosmoGespraech = create<Gespraech>(() => ({ ...LEER, ansicht: 'zu', motor: false }));

/** Oeffnet oder schliesst das Feld (wie dort). */
export function zeigeKosmo(ansicht: KosmoAnsicht): void {
  useKosmoGespraech.setState({ ansicht });
}

let weg: ((w: GespraechWunsch) => void) | null = null;
let blasenNummer = 0;

/** Der Wirt meldet an, wohin die Wuensche gehen (der Bote der App); `null` meldet ab. */
export function registriereGespraechWeg(fn: ((w: GespraechWunsch) => void) | null): void {
  weg = fn;
  useKosmoGespraech.setState({ motor: fn !== null });
}

/** Ein Wunsch des Felds — ohne Weg (keine App) geschieht nichts; das Feld sagt dann, wo es das gibt. */
export function wuenscheGespraech(w: GespraechWunsch): boolean {
  if (!weg) return false;
  weg(w);
  return true;
}

/** Wortgleicher Name wie dort: eine Nachricht an den Assistenten. */
export function sendeAnKosmo(text: string): boolean {
  return wuenscheGespraech({ tat: 'frage', text });
}

/** Legt, was die App sagt, in das Gespraech — und fuehrt die Kugel nach. */
export function setzeGespraechVonApp(neu: GespraechVonApp): void {
  const vorher = useKosmoGespraech.getState();
  useKosmoGespraech.setState({ ...neu });
  const status = useKosmoStatus.getState();
  if (neu.wartet !== vorher.wartet) status.setzeBeschaeftigt(neu.wartet);
  // EINE NEUE ANTWORT BEI GESCHLOSSENEM FELD: als Blase an der Kugel (C22), gekuerzt wie dort.
  const letzte = neu.beitraege[neu.beitraege.length - 1];
  const neueAntwort =
    letzte?.von === 'assistent' &&
    neu.beitraege.filter((b) => b.von === 'assistent').length >
      vorher.beitraege.filter((b) => b.von === 'assistent').length;
  if (neueAntwort && vorher.ansicht !== 'gross') {
    blasenNummer += 1;
    status.setzeAntwortBlase({ id: blasenNummer, text: kurzform(letzte.text) });
  }
}

/** Nur fuer Proben. */
export function _setzeGespraechZurueck(): void {
  weg = null;
  useKosmoGespraech.setState({ ...LEER, ansicht: 'zu', motor: false });
}
