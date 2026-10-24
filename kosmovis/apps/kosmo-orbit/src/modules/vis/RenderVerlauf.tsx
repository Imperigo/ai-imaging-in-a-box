import { useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type SyntheticEvent } from 'react';
import { createPortal } from 'react-dom';
import { KCheckbox, KIcon, KTabs, KTooltip, useHerkunft, useOverlaySchliessen, zEbeneLeiter } from '@kosmo/ui';
import { BildAblageZeile } from './BildAblageZeile';
import { BridgeBild } from './BridgeBild';
import { GueteMarke, gueteZusatz, istVorschau } from './GueteMarke';
import { ModusMarke } from './ModusMarke';
import { modusAus, modusZusatz } from './modus-marke';
import { LizenzOffenMarke } from './LizenzMarke';
import { grundlageText, startwertText } from './grundlage';
import type { NodeLauf } from './vis-runtime';
import {
  HAUS_ANTEIL_VORBEHALT,
  hausAnteilText,
  laufGrund,
  laufNummerVon,
  laufUrteil,
  laufZeit,
  treueText,
  uhrzeitText,
  URTEIL_LABEL,
  zeitpunktText,
  type LaufUrteil,
  verlaufSichtbar,
  type VerlaufEintrag,
} from './render-verlauf';
import {
  DECKUNG_ABWEICHEND_SATZ,
  DECKUNG_GLEICH_SATZ,
  DECKUNG_HILFE,
  deckungDerReihe,
  deckungUrteilDesLaufs,
  GROSS_BEI_FERTIG_HILFE,
  GROSS_BEI_FERTIG_NAME,
  grundlageSchluessel,
  grundlagenZusatz,
  gruppierteReihe,
  laeufeDerGrundlage,
  PRUEFUNG_AUF,
  PRUEFUNG_HILFE,
  PRUEFUNG_ZU,
} from './grossansicht';
import './vis-visual.css';
import './vis-grossansicht.css';

/**
 * Entscheid 68 / E174 — der Verlauf am Render-Knoten (Vorlage: Entwurfsblatt
 * «15 · Verlauf am Render-Knoten»). Rechnung und Begruendung stehen in
 * `render-verlauf.ts`; hier nur die Anzeige.
 *
 * AM KNOTEN: unter dem Hauptbild die Reihe, neuestes links, jedes Daumenbild
 * mit seinem Urteilspunkt und der Uhrzeit. Das neueste traegt einen Rahmen,
 * wenn es das Hauptbild ist. Die Reihe steht in der Zeile `bild` des
 * Render-Koerpers, und der Knoten waechst um genau `VERLAUF_ZEILE_H`
 * (`NodeCanvas.tsx`), solange sie steht.
 *
 * GROSS: ein Klick zeigt den Lauf in einer Ansicht ueber allem — als
 * gewoehnliches HTML, per Portal an `document.body`, also AUSSERHALB der
 * verschobenen und gezoomten Knotenebene (ein `position: fixed` darin
 * richtete sich nach der Ebene statt nach dem Fenster) und ohne
 * `foreignObject` (WebKitGTK). Vor/zurueck/schliessen, Escape und die
 * Pfeiltasten. Die Ansicht setzt nichts: das Hauptbild bleibt der letzte
 * Lauf, die Auswahl der Knoten bleibt, wie sie ist. Seit den Video-Befunden
 * L4-16/L3-A4 (Demolauf 16.10.) traegt sie «Aufs Blatt» und «Exportieren» fuer
 * den gezeigten Lauf (`BildAblageZeile`) — beides nur auf Knopfdruck.
 * Geloescht wird nichts, es gibt keinen Knopf dafuer.
 */

/**
 * Ereignisse aus der grossen Ansicht gehoeren ihr. Das Portal haengt im
 * React-Baum unter dem Knoten: ohne diesen Riegel liefe ein Tastendruck dort
 * bis zum Knoten-Kasten (Pfeiltasten wandern sonst zum naechsten Knoten,
 * Enter waehlt ihn aus) und Escape bis zum Fenster-Horcher der Leinwand
 * (der die Mehrfachauswahl leert).
 */
function halte(e: SyntheticEvent): void {
  e.stopPropagation();
}

function UrteilPunkt({ urteil, testid }: { urteil: LaufUrteil; testid?: string }) {
  return (
    <span
      className={`vis-verlauf-punkt vis-verlauf-punkt--${urteil}`}
      aria-hidden="true"
      {...(testid !== undefined ? { 'data-testid': testid } : {})}
    />
  );
}

/**
 * Entscheid 68 / E174, Nachtrag (4) — die Abzeichen auf dem HAUPTBILD, wie
 * in der Vorlage: oben links «LAUF n · hh:mm», oben rechts das Urteil (Punkt
 * und Wort, dieselbe Logik und Farbe wie an den Daumenbildern). Die Nummer
 * ist dieselbe wie in der grossen Ansicht: das Hauptbild ist der neueste
 * Lauf der Reihe, also `n` von `n`. Reine Anzeige im Bild: kein Zeiger, kein
 * eigener Platz im Knoten.
 */
export function HauptbildAbzeichen({ lauf, nummer }: { lauf: VerlaufEintrag; nummer: number }) {
  const urteil = laufUrteil(lauf.qa);
  return (
    <span className="vis-hauptbild-abzeichen" aria-hidden="true">
      <span className="vis-hauptbild-lauf" data-testid="render-hauptbild-lauf">
        LAUF {nummer} · {uhrzeitText(laufZeit(lauf))}
      </span>
      <span
        className={`vis-hauptbild-urteil vis-verlauf-urteil--${urteil}`}
        data-testid="render-hauptbild-urteil"
        data-urteil={urteil}
      >
        <UrteilPunkt urteil={urteil} />
        {URTEIL_LABEL[urteil]}
      </span>
    </span>
  );
}

export function RenderVerlauf({
  reihe,
  hauptJobId,
  offen,
  onUmschalten,
  schalter,
}: {
  /** Neuestes zuerst (`verlaufReihe`). */
  reihe: readonly VerlaufEintrag[];
  /** Der Auftrag, dessen Bild der Knoten gerade als Hauptbild zeigt. */
  hauptJobId: string | undefined;
  /**
   * Owner-Entscheid 101a: aufgeklappt (die Reihe der Daumenbilder) oder nur der Kopf. Fehlt die
   * Angabe, ist die Reihe offen — so bleibt ein Aufrufer ohne Knoten-Parameter wie bisher.
   */
  offen?: boolean;
  /** Der Pfeil im Kopf: auf- bzw. zuklappen (am Knoten: Parameter `verlaufOffen`). */
  onUmschalten?: () => void;
  /** L4-14 B: der Schalter «bei fertig gross oeffnen» in der grossen Ansicht (Knoten-Parameter). */
  schalter?: GrossSchalter;
}) {
  const [offenJob, setOffenJob] = useState<string | null>(null);
  const n = reihe.length;
  // L4-15 (Blatt «Grossansicht und Vergleich» C): die Daumen nach Grundlage, neueste Grundlage links. Das Hauptbild
  // (der neueste Lauf) bleibt vorn — es gehoert zur neuesten Grundlage.
  const anzeige = gruppierteReihe(reihe);
  const gruppenZusatz = grundlagenZusatz(reihe);
  const zu = offen === false;
  const pfeil = onUmschalten ? (
    <button
      type="button"
      className="k-druck vis-klapptext-mehr vis-verlauf-umschalten"
      data-testid="render-verlauf-umschalten"
      aria-expanded={!zu}
      aria-label={zu ? 'Verlauf aufklappen' : 'Verlauf zuklappen'}
      onPointerDown={halte}
      onClick={onUmschalten}
    >
      {zu ? '▸ aufklappen' : '▾ zuklappen'}
    </button>
  ) : null;
  const offenIndex = offenJob === null ? -1 : anzeige.findIndex((e) => e.jobId === offenJob);
  // Faellt der gezeigte Lauf aus der Reihe (ein neuer Lauf kam dazu, und er
  // war der fuenfte), schliesst die Ansicht, statt einen anderen zu zeigen.
  useEffect(() => {
    if (offenJob !== null && offenIndex < 0) setOffenJob(null);
  }, [offenJob, offenIndex]);

  // Zugeklappt (Entscheid 101a) — erst NACH allen Hooks, damit ihre Reihenfolge beim Umschalten gleich bleibt.
  if (zu) {
    return (
      <div className="vis-verlauf vis-verlauf--zu" data-testid="render-verlauf" data-offen="false" onPointerDown={halte}>
        <div className="vis-verlauf-kopf vis-verlauf-kopf--zu">
          <span className="vis-verlauf-titel">VERLAUF</span>
          <span className="vis-verlauf-zusatz" data-testid="render-verlauf-anzahl">
            {n} Läufe{gruppenZusatz}
          </span>
          {pfeil}
        </div>
      </div>
    );
  }

  return (
    <div className="vis-verlauf" data-testid="render-verlauf" data-offen="true" onPointerDown={halte}>
      <div className="vis-verlauf-kopf">
        <span className="vis-verlauf-titel">VERLAUF</span>
        {/* Der Pfeil steht vorne, damit er in der ersten der zwei Kopfzeilen bleibt und der
            Kopf (26 px, `overflow: hidden`) ihn nie abschneidet. */}
        {pfeil && <>{pfeil} </>}
        <span className="vis-verlauf-zusatz">
          {gruppenZusatz ? `die letzten ${n} Läufe${gruppenZusatz}` : `die letzten ${n} Läufe · neuester links`}
        </span>
      </div>
      <div className="vis-verlauf-reihe" data-anzahl={n}>
        {anzeige.map((e, i) => {
          const nummer = laufNummerVon(e, reihe.indexOf(e), n);
          const neueGrundlage = i > 0 && grundlageSchluessel(anzeige[i - 1]!) !== grundlageSchluessel(e);
          const urteil = laufUrteil(e.qa);
          const uhrzeit = uhrzeitText(laufZeit(e));
          const istHaupt = i === 0 && e.jobId === hauptJobId;
          return (
            <button
              key={e.jobId}
              type="button"
              className={`vis-verlauf-knopf${istHaupt ? ' vis-verlauf-knopf--haupt' : ''}${neueGrundlage ? ' vis-verlauf-knopf--neue-grundlage' : ''}`}
              data-testid="render-verlauf-bild"
              data-urteil={urteil}
              data-job={e.jobId}
              {...(e.grundlageId ? { 'data-grundlage': e.grundlageId } : {})}
              {...(istVorschau(e) ? { 'data-guete': 'vorschau' } : {})}
              aria-label={`Lauf ${nummer} von ${uhrzeit}, ${URTEIL_LABEL[urteil]}${gueteZusatz(e)}${modusZusatz(modusAus(e))}, gross anzeigen`}
              onPointerDown={halte}
              onClick={() => setOffenJob(e.jobId)}
            >
              <span className={`vis-verlauf-daumen${istVorschau(e) ? ' vis-verlauf-daumen--vorschau' : ''}`}>
                <BridgeBild jobId={e.jobId} imageName={e.bild} alt="" className="vis-verlauf-daumen-bild" />
                <UrteilPunkt urteil={urteil} testid="render-verlauf-punkt" />
              </span>
            </button>
          );
        })}
      </div>
      {offenIndex >= 0 &&
        typeof document !== 'undefined' &&
        createPortal(
          <VerlaufGross
            reihe={anzeige}
            nummerReihe={reihe}
            index={offenIndex}
            hauptJobId={hauptJobId}
            onWahl={(i) => setOffenJob(anzeige[i]?.jobId ?? null)}
            onClose={() => setOffenJob(null)}
            {...(schalter ? { schalter } : {})}
          />,
          document.body,
        )}
    </div>
  );
}

/**
 * Blatt 29 «Fortschritt und Vorschau»: ein einzelnes Bild eines Laufs ohne fertiges Ergebnis in
 * derselben grossen Ansicht — das Zwischenbild eines laufenden Renders (`progress.vorschau`) oder
 * das Teilbild nach einem Abbruch (`teilbild`). Beide sind NICHT geprueft und unvollstaendig; die
 * Ansicht sagt das an der Stelle des Urteils. Am Knoten kostet das keinen Platz: geoeffnet wird
 * sie mit einem Klick auf den Warteplatz bzw. die Abbruch-Zeile.
 */
export type EinzelbildArt = 'teilbild' | 'zwischenbild';

/** L4-16: ein Bild ohne fertiges Ergebnis geht weder aufs Blatt noch zum Export. */
export const EINZELBILD_NICHT_WAEHLBAR = 'Unvollständig — nicht aufs Blatt und nicht zum Export.';

const EINZELBILD_TEXT: Record<EinzelbildArt, { titel: string; grund: string; fuss: string }> = {
  teilbild: {
    titel: 'TEILBILD',
    grund: 'Abgebrochen — das zuletzt fertige Bild dieses Laufs, unvollständig und ohne Gütewerte.',
    fuss: 'Am Knoten ändert sich nichts. «Variante erzeugen» rechnet neu.',
  },
  zwischenbild: {
    titel: 'ZWISCHENBILD',
    grund: 'Das zuletzt fertige Bild des laufenden Renders — der Lauf rechnet weiter; geprüft wird erst am Ende.',
    fuss: 'Am Knoten ändert sich nichts. Hier wird nur angesehen.',
  },
};

export function EinzelbildGross({
  lauf,
  jobId,
  bild,
  art,
  onClose,
}: {
  lauf: NodeLauf;
  jobId: string;
  bild: string;
  art: EinzelbildArt;
  onClose: () => void;
}) {
  if (typeof document === 'undefined') return null;
  const eintrag: VerlaufEintrag = { ...lauf, jobId, bild };
  return createPortal(
    <VerlaufGross reihe={[eintrag]} index={0} hauptJobId={undefined} onWahl={() => {}} onClose={onClose} art={art} />,
    document.body,
  );
}

/** L4-14 B: der Schalter «bei fertig gross oeffnen» — Wert und Setzer kommen vom Knoten (`grossBeiFertig`). */
export interface GrossSchalter {
  an: boolean;
  setzen: (an: boolean) => void;
}

/**
 * L4-14 (Blatt «Grossansicht und Vergleich» A/B): der Lauf, den der Render-Knoten gerade zeigt, gross — ein Klick
 * auf das Hauptbild ohne Grundbild oder, mit Schalter, von selbst bei «fertig». Dieselbe Ansicht wie im Verlauf; ist
 * der Lauf in der Reihe, wird darin geblaettert, sonst steht er allein.
 */
export function LaufGross({
  reihe,
  lauf,
  hauptJobId,
  onClose,
  schalter,
}: {
  reihe: readonly VerlaufEintrag[];
  lauf: VerlaufEintrag;
  hauptJobId: string | undefined;
  onClose: () => void;
  schalter?: GrossSchalter;
}) {
  const imVerlauf = reihe.some((e) => e.jobId === lauf.jobId);
  const anzeige = imVerlauf ? gruppierteReihe(reihe) : [lauf];
  const [jobId, setJobId] = useState(lauf.jobId);
  if (typeof document === 'undefined') return null;
  const index = Math.max(0, anzeige.findIndex((e) => e.jobId === jobId));
  return createPortal(
    <VerlaufGross
      reihe={anzeige}
      nummerReihe={imVerlauf ? reihe : anzeige}
      index={index}
      hauptJobId={hauptJobId}
      onWahl={(i) => setJobId(anzeige[i]?.jobId ?? lauf.jobId)}
      onClose={onClose}
      {...(schalter ? { schalter } : {})}
    />,
    document.body,
  );
}

type GrossModus = 'einzeln' | 'nebeneinander';

function VerlaufGross({
  reihe,
  nummerReihe,
  index,
  hauptJobId,
  onWahl,
  onClose,
  art,
  schalter,
}: {
  /** In der Reihenfolge der Daumen (nach Grundlage, `gruppierteReihe`). */
  reihe: readonly VerlaufEintrag[];
  /** Die Reihe neuestes zuerst — fuer die Laufnummer, wenn der Lauf keine eigene traegt. Fehlt sie, gilt `reihe`. */
  nummerReihe?: readonly VerlaufEintrag[];
  index: number;
  hauptJobId: string | undefined;
  onWahl: (index: number) => void;
  onClose: () => void;
  /** Ein Einzelbild ohne Ergebnis (s. `EinzelbildGross`); fehlt es, ein Lauf des Verlaufs. */
  art?: EinzelbildArt;
  schalter?: GrossSchalter;
}) {
  const boxRef = useRef<HTMLDivElement | null>(null);
  const schliessenRef = useRef<HTMLButtonElement | null>(null);
  // L4-14 A: die Pruefung ist eingeklappt; das Urteil steht im Kopf.
  const [pruefungOffen, setPruefungOffen] = useState(false);
  // L4-15 C: einzeln oder die Laeufe derselben Grundlage nebeneinander.
  const [modus, setModus] = useState<GrossModus>('einzeln');
  // Das Haus-Gesetz fuer modale Flaechen (Stapel, Fokusrueckgabe an das
  // Daumenbild). Escape, die Pfeiltasten und die Tab-Falle stehen unten in
  // eigenen Horchern, weil die Taste hier enden muss (s. `halte`); der
  // Horcher des Gesetzes sitzt am `document` und kaeme erst danach.
  useOverlaySchliessen(boxRef, onClose, { modal: true, esc: false, aussenklick: false, fokusfalle: false });
  useHerkunft(boxRef);
  useEffect(() => {
    schliessenRef.current?.focus();
  }, []);

  const e = reihe[index]!;
  const n = reihe.length;
  const nummern = nummerReihe ?? reihe;
  const nummerVon = (x: VerlaufEintrag) => laufNummerVon(x, Math.max(0, nummern.indexOf(x)), nummern.length);
  // Verlauf-Nachgang: die fortlaufende Nummer des Laufs am Knoten im Titel;
  // die Stelle in der Reihe (von links, nach Grundlage) getrennt daneben.
  const nummer = nummerVon(e);
  const urteil = laufUrteil(e.qa);
  const hatAelteren = index < n - 1;
  const hatNeueren = index > 0;
  const erster = nummern[0];
  const hauptNummer = erster && erster.jobId === hauptJobId ? laufNummerVon(erster, 0, nummern.length) : undefined;
  const geschwister = art ? [e] : laeufeDerGrundlage(reihe, e);
  const kannNebeneinander = geschwister.length >= 2;
  const nebeneinander = modus === 'nebeneinander' && kannNebeneinander;

  // Am Ende der Reihe wird der Knopf gesperrt, mit dem man dorthin kam — und
  // ein gesperrter Knopf verliert den Fokus. Der Fokus bleibt dann in der
  // Ansicht (auf ihrem Kasten), statt ins Leere zu fallen.
  useEffect(() => {
    const box = boxRef.current;
    const aktiv = document.activeElement;
    if (box && (!box.contains(aktiv) || (aktiv instanceof HTMLButtonElement && aktiv.disabled))) box.focus();
  }, [index]);

  // Escape und die Pfeiltasten gelten, solange die Ansicht offen ist — wo
  // immer der Fokus gerade steht. Im Einfang-Durchgang am Fenster und dort
  // beendet: der Fenster-Horcher der Leinwand (Escape leert die Auswahl)
  // und die Pfeiltasten der Knoten bekommen sie nicht.
  const steuer = useRef({ onClose, onWahl, index, hatAelteren, hatNeueren });
  steuer.current = { onClose, onWahl, index, hatAelteren, hatNeueren };
  useEffect(() => {
    const beiTaste = (ev: KeyboardEvent) => {
      const s = steuer.current;
      if (ev.key === 'Escape') s.onClose();
      else if (ev.key === 'ArrowLeft') {
        if (s.hatAelteren) s.onWahl(s.index + 1);
      } else if (ev.key === 'ArrowRight') {
        if (s.hatNeueren) s.onWahl(s.index - 1);
      } else return;
      ev.preventDefault();
      ev.stopPropagation();
    };
    window.addEventListener('keydown', beiTaste, true);
    return () => window.removeEventListener('keydown', beiTaste, true);
  }, []);

  // C18 (Blatt «Hausanteil»): nur an echten Laeufen, nicht an Teil- oder Zwischenbildern.
  const hausZeile = art ? undefined : hausAnteilText(e.qa);

  const taste = (ev: ReactKeyboardEvent<HTMLDivElement>) => {
    ev.stopPropagation();
    if (ev.key === 'Tab') {
      const box = boxRef.current;
      if (!box) return;
      const knoepfe = [...box.querySelectorAll<HTMLElement>('button:not([disabled]), [tabindex="0"], input:not([disabled])')];
      if (knoepfe.length === 0) return;
      const aktiv = document.activeElement;
      const erster = knoepfe[0]!;
      const letzter = knoepfe[knoepfe.length - 1]!;
      if (ev.shiftKey && (aktiv === erster || !box.contains(aktiv))) {
        ev.preventDefault();
        letzter.focus();
      } else if (!ev.shiftKey && (aktiv === letzter || !box.contains(aktiv))) {
        ev.preventDefault();
        erster.focus();
      }
    }
  };

  return (
    <div
      className="k-dialog-scrim k-bestaetigung-scrim vis-verlauf-scrim"
      data-testid="render-verlauf-gross-scrim"
      style={{ zIndex: zEbeneLeiter.modal + 20 }}
      onClick={(ev) => {
        ev.stopPropagation();
        if (ev.target === ev.currentTarget) onClose();
      }}
      onPointerDown={halte}
      onPointerUp={halte}
      onPointerMove={halte}
      onDoubleClick={halte}
      onContextMenu={halte}
      onWheel={halte}
      onKeyDown={taste}
    >
      <div
        ref={boxRef}
        role="dialog"
        aria-modal="true"
        aria-label={art === 'teilbild' ? 'Teilbild gross' : art === 'zwischenbild' ? 'Zwischenbild gross' : `Lauf ${nummer} gross`}
        tabIndex={-1}
        className="k-dialog-box k-dialog k-aus-ausloeser vis-verlauf-gross vis-gross"
        data-testid="render-verlauf-gross"
        data-job={e.jobId}
        data-pruefung={pruefungOffen ? 'offen' : 'zu'}
        data-modus={nebeneinander ? 'nebeneinander' : 'einzeln'}
        {...(art ? { 'data-art': art } : {})}
      >
        <div className="vis-verlauf-gross-kopf">
          <span className="vis-verlauf-gross-titel" data-testid="render-verlauf-gross-titel">
            {art ? EINZELBILD_TEXT[art].titel : `LAUF ${nummer}`}
          </span>
          {!art && <span className="vis-verlauf-gross-zeit">{zeitpunktText(laufZeit(e))}</span>}
          {/* Owner-Entscheid 21.10.2026 (A, erstes Bild gross): ein Lauf ohne sichtbaren Verlauf (das allererste Bild)
              oeffnet hier auch — «1 von 1 im Verlauf» naennte dann einen Verlauf, den der Knoten nicht zeigt. */}
          {!art && verlaufSichtbar(reihe) && (
            <span className="vis-verlauf-gross-stelle" data-testid="render-verlauf-gross-stelle">
              {index + 1} von {n} im Verlauf
            </span>
          )}
          {!art && !pruefungOffen && (
            <span
              className={`vis-gross-kopf-urteil vis-verlauf-urteil vis-verlauf-urteil--${urteil}`}
              data-testid="render-verlauf-gross-kopf-urteil"
              data-urteil={urteil}
            >
              <UrteilPunkt urteil={urteil} />
              {URTEIL_LABEL[urteil]}
            </span>
          )}
          {!pruefungOffen && <LizenzOffenMarke lizenz={e} testid="render-verlauf-gross-kopf-lizenz" />}
          <span className="vis-verlauf-gross-luecke" />
          {kannNebeneinander && (
            <KTooltip text="Die Läufe derselben Grundlage gleich gross nebeneinander — höchstens die vier des Verlaufs." lage="unten">
              <span>
                <KTabs
                  size="sm"
                  items={[
                    { id: 'einzeln', label: 'einzeln', testid: 'render-verlauf-gross-einzeln' },
                    { id: 'nebeneinander', label: 'nebeneinander', testid: 'render-verlauf-gross-nebeneinander' },
                  ]}
                  aktiv={nebeneinander ? 'nebeneinander' : 'einzeln'}
                  onChange={(id) => setModus(id as GrossModus)}
                  data-testid="render-verlauf-gross-modus"
                />
              </span>
            </KTooltip>
          )}
          {schalter && !art && (
            <KTooltip text={GROSS_BEI_FERTIG_HILFE} lage="unten">
              <span className="vis-gross-schalter">
                <KCheckbox
                  size="sm"
                  label={GROSS_BEI_FERTIG_NAME}
                  checked={schalter.an}
                  onChange={(ev) => schalter.setzen(ev.currentTarget.checked)}
                  data-testid="render-gross-bei-fertig"
                />
              </span>
            </KTooltip>
          )}
          <KTooltip text={PRUEFUNG_HILFE} lage="unten">
            <button
              type="button"
              className="vis-verlauf-gross-knopf vis-gross-pruefung"
              data-testid="render-verlauf-gross-pruefung"
              aria-expanded={pruefungOffen}
              aria-label={pruefungOffen ? 'Prüfung zuklappen' : 'Prüfung aufklappen'}
              onClick={() => setPruefungOffen((o) => !o)}
            >
              {pruefungOffen ? PRUEFUNG_ZU : PRUEFUNG_AUF}
            </button>
          </KTooltip>
          <button
            type="button"
            className="vis-verlauf-gross-knopf"
            aria-label="Vorheriger Lauf"
            data-testid="render-verlauf-zurueck"
            disabled={!hatAelteren}
            onClick={() => onWahl(index + 1)}
          >
            <KIcon name="pfeil-links" size={16} />
          </button>
          <button
            type="button"
            className="vis-verlauf-gross-knopf"
            aria-label="Nächster Lauf"
            data-testid="render-verlauf-vor"
            disabled={!hatNeueren}
            onClick={() => onWahl(index - 1)}
          >
            <KIcon name="pfeil-rechts" size={16} />
          </button>
          <button
            ref={schliessenRef}
            type="button"
            className="vis-verlauf-gross-knopf"
            aria-label="Schliessen"
            data-testid="render-verlauf-schliessen"
            onClick={onClose}
          >
            <KIcon name="schliessen" size={16} />
          </button>
        </div>
        <div className="vis-verlauf-gross-inhalt">
          {nebeneinander ? (
            <div
              className="vis-gross-reihe"
              data-testid="render-verlauf-gross-reihe"
              data-anzahl={geschwister.length}
              style={{ ['--_n' as string]: String(geschwister.length) }}
            >
              {/* L4-1: was «nebeneinander» belegt — gleiche Grundlage; die Form misst der Heim-PC noch nicht. */}
              <KTooltip text={DECKUNG_HILFE} lage="unten">
                <span
                  tabIndex={0}
                  className={`vis-gross-deckung vis-gross-deckung--${deckungDerReihe(geschwister).urteil}`}
                  data-testid="render-verlauf-gross-deckung"
                  data-deckung={deckungDerReihe(geschwister).urteil}
                >
                  {deckungDerReihe(geschwister).satz}
                </span>
              </KTooltip>
              {geschwister.map((g) => {
                const gNummer = nummerVon(g);
                const gUrteil = laufUrteil(g.qa);
                return (
                  <figure
                    key={g.jobId}
                    className={`vis-gross-reihe-zelle${g.jobId === e.jobId ? ' vis-gross-reihe-zelle--gezeigt' : ''}`}
                    data-testid="render-verlauf-gross-reihe-zelle"
                    data-job={g.jobId}
                  >
                    <button
                      type="button"
                      className="vis-gross-reihe-bild"
                      aria-label={`Lauf ${gNummer} einzeln zeigen`}
                      onClick={() => {
                        onWahl(reihe.indexOf(g));
                        setModus('einzeln');
                      }}
                    >
                      <BridgeBild jobId={g.jobId} imageName={g.bild} alt={`Lauf ${gNummer}${gueteZusatz(g)}${modusZusatz(modusAus(g))}`} className="vis-gross-reihe-img" />
                      <div className="vis-marken-leiste">
                        <GueteMarke lauf={g} testid="render-verlauf-gross-reihe-guete" />
                        <ModusMarke lauf={g} testid="render-verlauf-gross-reihe-modus" />
                      </div>
                    </button>
                    <figcaption className="vis-gross-reihe-text">
                      <UrteilPunkt urteil={gUrteil} />
                      <span>
                        Lauf {gNummer} · Startwert {startwertText(g)} · {URTEIL_LABEL[gUrteil]}
                        {g.stufe !== 'grundlage' && deckungUrteilDesLaufs(g) !== 'ungemessen' && (
                          <span
                            className={`vis-gross-deckung-zelle vis-gross-deckung-zelle--${deckungUrteilDesLaufs(g)}`}
                            data-testid="render-verlauf-gross-reihe-deckung"
                          >
                            {' · '}
                            {deckungUrteilDesLaufs(g) === 'deckungsgleich' ? DECKUNG_GLEICH_SATZ : `⚠ ${DECKUNG_ABWEICHEND_SATZ}`}
                          </span>
                        )}
                      </span>
                    </figcaption>
                  </figure>
                );
              })}
            </div>
          ) : (
            <div className="vis-verlauf-gross-bild">
              <BridgeBild
                key={e.jobId}
                jobId={e.jobId}
                imageName={e.bild}
                alt={`Lauf ${nummer}${gueteZusatz(e)}${modusZusatz(modusAus(e))}`}
                testid="render-verlauf-gross-bild"
                className="vis-verlauf-gross-img"
              />
              <div className="vis-marken-leiste">
                <GueteMarke lauf={e} testid="render-verlauf-gross-guete-marke" />
                <ModusMarke lauf={e} testid="render-verlauf-gross-modus-marke" />
              </div>
            </div>
          )}
          <div className="vis-verlauf-gross-seite" data-testid="render-verlauf-gross-seite">
            {art ? (
              <span className="vis-verlauf-urteil vis-verlauf-urteil--ohne-qa" data-testid="render-verlauf-gross-urteil" data-urteil="nicht-geprueft">
                nicht geprüft · unvollständig
              </span>
            ) : (
              <span
                className={`vis-verlauf-urteil vis-verlauf-urteil--${urteil}`}
                data-testid="render-verlauf-gross-urteil"
                data-urteil={urteil}
              >
                <UrteilPunkt urteil={urteil} />
                {URTEIL_LABEL[urteil]}
              </span>
            )}
            <div className="vis-verlauf-gross-grund" data-testid="render-verlauf-gross-grund">
              {art ? EINZELBILD_TEXT[art].grund : laufGrund(e.qa)}
            </div>
            <dl className="vis-verlauf-gross-werte">
              {!art && (
                <div>
                  <dt>Treue zur Geometrie</dt>
                  <dd data-testid="render-verlauf-gross-treue">{treueText(e.qa)}</dd>
                </div>
              )}
              {hausZeile && (
                <div>
                  <dt>Haus im Bild</dt>
                  <dd data-testid="render-verlauf-gross-hausanteil">
                    {hausZeile.text}
                    {hausZeile.anders && (
                      <span className="vis-verlauf-ausschnitt" data-testid="render-verlauf-gross-ausschnitt">
                        Ausschnitt anders
                      </span>
                    )}
                  </dd>
                </div>
              )}
              <div>
                <dt>Bildwerkzeug</dt>
                <dd data-testid="render-verlauf-gross-werkzeug">{e.engineUsed ?? 'nicht gemeldet'}</dd>
              </div>
              {/* Nr. 85 Paket 2: auf welcher Grundlage der Lauf steht, und mit welchem Startwert —
                  zwei Varianten auf derselben Grundlage sind deckungsgleich. */}
              <div>
                <dt>Grundlage</dt>
                <dd data-testid="render-verlauf-gross-grundlage">{grundlageText(e)}</dd>
              </div>
              <div>
                <dt>Startwert</dt>
                <dd data-testid="render-verlauf-gross-startwert">{startwertText(e)}</dd>
              </div>
              <div>
                <dt>Gerechnet von</dt>
                <dd data-testid="render-verlauf-gross-herkunft">{e.worker ?? 'nicht gemeldet'}</dd>
              </div>
            </dl>
            {hausZeile && (
              <p className="vis-verlauf-gross-vorbehalt" data-testid="render-verlauf-gross-hausanteil-vorbehalt">
                {HAUS_ANTEIL_VORBEHALT}
              </p>
            )}
            <LizenzOffenMarke lizenz={e} testid="render-verlauf-gross-lizenz-offen" />
            <span className="vis-verlauf-gross-luecke" />
            <div className="vis-verlauf-gross-fuss" data-testid="render-verlauf-gross-fuss">
              {art
                ? EINZELBILD_TEXT[art].fuss
                : <>
                    {hauptNummer !== undefined
                      ? `Am Knoten bleibt Lauf ${hauptNummer} das Hauptbild. Hier wird nur angesehen.`
                      : 'Am Knoten ändert sich nichts. Hier wird nur angesehen.'}{' '}
                    Ältere Läufe zeigt der Verlauf nicht mehr; gelöscht wird dabei nichts.
                  </>}
            </div>
          </div>
        </div>
        {/* Video-Befunde L4-16/L3-A4 (Blatt «Bild aufs Blatt»): Ablage und Export im Original — unter dem Bild,
            immer sichtbar, auch wenn die Pruefung (L4-14) eingeklappt ist. */}
        <BildAblageZeile lauf={e} grund={art ? EINZELBILD_NICHT_WAEHLBAR : undefined} testid="render-verlauf-gross" fuss />
      </div>
    </div>
  );
}
