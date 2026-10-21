/**
 * KosmoMaus — die sichtbare Ebene (Owner-Entscheid E157; Gestaltung Teil A,
 * Entwurf «KosmoMaus Bedienteile»). Hier stehen Zeiger, Leiste und Karten:
 *
 *  - `kosmo-maus-zeiger` (Attribut `data-urheber`): seit Teil C (Owner
 *    07.10.2026) eine **Figur** statt eines Pfeils — Spitze in der Form der
 *    KosmoOrbit-Maus, federnder Körper mit Blick, Schild mit der Handlung
 *    (`AgentFigur.tsx`); die Stelle leuchtet kurz auf (`kosmo-maus-leuchten`,
 *    Owner-Wahl C17 A),
 *  - `kosmo-maus-leiste` «… bedient — Esc beendet» mit `kosmo-maus-stopp`,
 *    nur solange gehandelt wird: nach der letzten Handlung bleiben Zeiger und
 *    Leiste `KOSMO_MAUS_RUHEZEIT_MS` stehen und blenden dann aus. Die
 *    Freigabe selbst bleibt, bis Esc, Stopp oder der Schalter sie nimmt; an
 *    der Marke «Claude verbunden» zeigt sie ein Zeiger-Zeichen
 *    (L27-Nachprobe, 07.10.2026: die Leiste stand nach dem letzten Aufruf
 *    über alle Bildschirme, auch nach einer Ruhezeit),
 *  - `kosmo-maus-vorschlag` mit `kosmo-maus-vorschlag-anwenden`/`-ablehnen`.
 *
 * Die Schalter stehen NICHT mehr hier, sondern an der Marke «Claude verbunden»
 * (`kosmo-maus-schalter`) und in Kosmos Einstellungen
 * (`kosmo-einstellungen-maus`), siehe `KosmoMausSchalter.tsx`.
 *
 * Die ganze Ebene trägt `data-kosmo-maus-eigen`: die KosmoMaus kann hier
 * nichts treffen (Sperrzone in `state/kosmo-maus.ts`), und der Blick zählt sie
 * nicht mit. Zusätzlich nehmen die Schalter nur echte Klicks
 * (`isTrusted`) — ein Agent schaltet sich nie selbst frei.
 *
 * Gemountet in `main.tsx` neben `<ClaudeAnschluss />`, nicht in `App.tsx`
 * (UI-Worker, E147) und nicht in `KosmoPanel.tsx`.
 */

import { useEffect, useRef, useState } from 'react';
import { KButton, melde } from '@kosmo/ui';
import { URHEBER, URHEBER_NAME, stoppeBedienen, useKosmoMaus, type AgentZeiger, type Urheber } from '../../state/kosmo-maus-freigabe';
import { lehneMausVorschlagAb, wendeMausVorschlagAn } from '../../state/kosmo-maus';
import { useMausKartenImPanel } from '../../state/maus-karten-im-panel';
import type { MausVorschlag } from '../../state/kosmo-maus-freigabe';
import { hoereAufFehler, istSichtbar } from '../../state/kosmo-blick-live';
import { eigen } from './KosmoMausSchalter';
import { AgentFigur } from './AgentFigur';
import './agent-figur.css';
import './kosmo-maus.css';

/** Esc beendet das Bedienen — nur der echte Tastendruck, nie ein synthetischer. */
export function istStoppTaste(e: Pick<KeyboardEvent, 'key' | 'isTrusted'>): boolean {
  return e.key === 'Escape' && e.isTrusted;
}

/**
 * Runde 34 (Demolauf 16.10.2026, Nr. 73–77): was Esc zuerst schliesst. Ist
 * davon etwas sichtbar offen, gehört Esc der Oberfläche (Menü, Liste, Dialog,
 * aufgeklappter Knopf) — das Bedienen bleibt.
 */
const OFFEN_FUER_ESC =
  '[aria-expanded="true"], [role="menu"], [role="listbox"], [role="dialog"], [role="alertdialog"], [aria-modal="true"], dialog[open]';

function etwasOffen(): boolean {
  return [...document.querySelectorAll(OFFEN_FUER_ESC)].some(istSichtbar);
}

/** Bedient gerade ein Agent sichtbar (Leiste steht: Zeiger jünger als die Ruhezeit, Freigabe an)? */
export function agentBedientSichtbar(jetzt = Date.now()): Urheber[] {
  const z = useKosmoMaus.getState();
  return URHEBER.filter((u) => {
    const zeiger = z.zeigerJe[u];
    return zeiger !== null && z.freigaben[u].bedienen && jetzt - zeiger.zeit < KOSMO_MAUS_RUHEZEIT_MS;
  });
}

/**
 * Runde 34: beendet Esc das Bedienen? Nur ein echter Tastendruck, den noch
 * niemand behandelt hat, nur solange die Leiste «… bedient — Esc beendet»
 * steht, und nur, wenn nichts aufgeklappt ist. Vorher beendete JEDES echte
 * Esc das Bedienen beider Agenten still — auch das Esc, mit dem der Architekt
 * ein Menü schloss, während gar niemand bediente.
 */
export function escBeendetBedienen(e: Pick<KeyboardEvent, 'key' | 'isTrusted' | 'defaultPrevented'>): boolean {
  if (!istStoppTaste(e) || e.defaultPrevented) return false;
  if (agentBedientSichtbar().length === 0) return false;
  return !etwasOffen();
}

/** Sichtbar melden, dass das Bedienen endete (Nr. 75/77: «Esc-Beenden sichtbar machen»). */
export function meldeBedienEnde(wer: readonly Urheber[], wodurch: 'Esc' | '«Stopp»'): void {
  if (wer.length === 0) return;
  const namen = wer.map((u) => URHEBER_NAME[u]).join(' und ');
  melde(`Bedienen für ${namen} beendet (${wodurch}). Wieder einschalten: Marke «Claude verbunden» oder Kosmos Einstellungen.`, {
    dauerMs: 8000,
  });
}

/** Am Wurzelelement, solange ein Agent sichtbar bedient (Wert: der zuletzt Handelnde). */
export const BEDIENT_ATTR = 'data-kosmo-maus-bedient';

/** So lange verabschiedet sich die Figur, wenn sie geht. */
export const FIGUR_GEHT_MS = 420;

/** So lange bleiben Zeiger und Leiste nach der letzten Handlung stehen. */
export const KOSMO_MAUS_RUHEZEIT_MS = 10_000;

/**
 * Wer gerade als `urheber` handelt: sein Zeiger (`zeigerJe`, Home-PC-Worker, lw-kosmo-maus-2), solange
 * seine Freigabe gilt und die Ruhezeit nicht abgelaufen ist. Je Urheber für sich — so stehen Claude
 * und Kosmo gleichzeitig als Figur da (Entwurf C3 «Beide zugleich»).
 */
function useHandelt(urheber: Urheber): AgentZeiger | null {
  const zeiger = useKosmoMaus((z) => z.zeigerJe[urheber]);
  const darf = useKosmoMaus((z) => z.freigaben[urheber].bedienen);
  const [abgelaufen, setAbgelaufen] = useState<number | null>(null);
  useEffect(() => {
    if (!zeiger) return;
    const rest = zeiger.zeit + KOSMO_MAUS_RUHEZEIT_MS - Date.now();
    if (rest <= 0) {
      setAbgelaufen(zeiger.zeit);
      return;
    }
    const t = window.setTimeout(() => setAbgelaufen(zeiger.zeit), rest);
    return () => window.clearTimeout(t);
  }, [zeiger]);
  return zeiger && darf && abgelaufen !== zeiger.zeit ? zeiger : null;
}

/** Teil C: geht die Figur (Ruhezeit, Esc, Stopp), verabschiedet sie sich kurz (C2 «Geht»). */
function useGehend(handelt: AgentZeiger | null): AgentZeiger | null {
  const [gehend, setGehend] = useState<AgentZeiger | null>(null);
  const vorher = useRef<AgentZeiger | null>(null);
  useEffect(() => {
    const war = vorher.current;
    vorher.current = handelt;
    if (war && !handelt) {
      setGehend(war);
      const t = window.setTimeout(() => setGehend(null), FIGUR_GEHT_MS);
      return () => window.clearTimeout(t);
    }
    if (handelt) setGehend(null);
    return undefined;
  }, [handelt]);
  return handelt ? null : gehend;
}

/**
 * Eine Vorschlagskarte aus der Bedienung. Steht unten rechts (schwebend) und — für Kosmos eigene, solange
 * ein Kosmo-Panel sichtbar ist — in dessen Vorschlagszone (`state/maus-karten-im-panel.ts`).
 */
export function MausVorschlagKarte({ v }: { v: MausVorschlag }) {
  return (
    <section className="kosmo-maus-karte" data-testid="kosmo-maus-vorschlag" data-kennung={v.kennung} aria-label="Vorschlag aus der Bedienung">
      <div className="kosmo-maus-titel">{URHEBER_NAME[v.urheber]} möchte ändern</div>
      <p className="kosmo-maus-text">{v.zusammenfassung}</p>
      <div className="kosmo-maus-knoepfe">
        <KButton tone="ghost" data-testid="kosmo-maus-vorschlag-ablehnen" onClick={() => lehneMausVorschlagAb(v.kennung)}>
          Ablehnen
        </KButton>
        <KButton tone="accent" data-testid="kosmo-maus-vorschlag-anwenden" onClick={() => wendeMausVorschlagAn(v.kennung)}>
          Anwenden
        </KButton>
      </div>
    </section>
  );
}

export function KosmoMausEbene() {
  const vorschlaege = useKosmoMaus((z) => z.vorschlaege);
  const imPanel = useMausKartenImPanel((z) => z.panels > 0);
  const claude = useHandelt('claude');
  const kosmo = useHandelt('kosmo');
  const claudeGeht = useGehend(claude);
  const kosmoGeht = useGehend(kosmo);
  // Die Leiste nennt alle, die gerade bedienen; `data-urheber` trägt den zuletzt Handelnden.
  const aktive = [claude, kosmo].filter((z): z is AgentZeiger => z !== null).sort((a, b) => a.zeit - b.zeit);
  const handelt = aktive.at(-1) ?? null;

  // KosmoVis-Kopf (Visbox Stufe 6, 21.10.2026): solange ein Agent sichtbar bedient, zeigt die
  // Wurzel die Sperrzonen gestrichelt (`kosmo-maus.css`, `SPERRZONEN_SICHTBAR_SELEKTOR`) — was die
  // Figur nie trifft, sieht der Architekt, während sie unterwegs ist.
  useEffect(() => {
    const wurzel = document.documentElement;
    if (handelt) wurzel.setAttribute(BEDIENT_ATTR, handelt.urheber);
    else wurzel.removeAttribute(BEDIENT_ATTR);
    return () => wurzel.removeAttribute(BEDIENT_ATTR);
  }, [handelt]);

  useEffect(() => {
    hoereAufFehler();
    const beiTaste = (e: KeyboardEvent) => {
      if (escBeendetBedienen(e)) meldeBedienEnde(stoppeBedienen('esc'), 'Esc');
    };
    window.addEventListener('keydown', beiTaste, true);
    return () => window.removeEventListener('keydown', beiTaste, true);
  }, []);

  return (
    <div className="kosmo-maus-ebene" {...eigen()}>
      {handelt && (
        <div
          className="kosmo-maus-leiste"
          data-testid="kosmo-maus-leiste"
          data-urheber={handelt.urheber}
          role="status"
        >
          <span className="kosmo-maus-leiste-punkt" aria-hidden="true" />
          <span>
            {aktive.map((z, i) => (
              <span key={z.urheber}>
                {i > 0 ? ' und ' : ''}
                <b className="kosmo-maus-leiste-name">{URHEBER_NAME[z.urheber]}</b>
              </span>
            ))}{' '}
            {aktive.length > 1 ? 'bedienen' : 'bedient'} — Esc beendet (wenn kein Menü offen)
          </span>
          <KButton
            size="sm"
            tone="ghost"
            data-testid="kosmo-maus-stopp"
            aria-label="Bedienen beenden"
            onClick={() => meldeBedienEnde(stoppeBedienen('stopp'), '«Stopp»')}
          >
            Stopp
          </KButton>
        </div>
      )}
      {/* Die Figur nach der Leiste im DOM (Lage und Ebene kommen aus dem CSS). */}
      {/* Je Urheber eine Figur (C3): Claude und Kosmo können zugleich unterwegs sein. */}
      {claude && <AgentFigur key="claude" zeiger={claude} />}
      {claudeGeht && <AgentFigur key="geht-claude" zeiger={claudeGeht} gehend />}
      {kosmo && <AgentFigur key="kosmo" zeiger={kosmo} />}
      {kosmoGeht && <AgentFigur key="geht-kosmo" zeiger={kosmoGeht} gehend />}
      <div className="kosmo-maus-unten">
        {vorschlaege
          .filter((v) => !(imPanel && v.urheber === 'kosmo'))
          .map((v) => (
            <MausVorschlagKarte key={v.kennung} v={v} />
          ))}
      </div>
    </div>
  );
}
