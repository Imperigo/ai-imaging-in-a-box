import { useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type SyntheticEvent } from 'react';
import { createPortal } from 'react-dom';
import { KIcon, useHerkunft, useOverlaySchliessen, zEbeneLeiter } from '@kosmo/ui';
import { BridgeBild } from './BridgeBild';
import { LizenzOffenMarke } from './LizenzMarke';
import { grundlageText, startwertText } from './grundlage';
import type { NodeLauf } from './vis-runtime';
import {
  laufGrund,
  laufNummerVon,
  laufUrteil,
  laufZeit,
  treueText,
  uhrzeitText,
  URTEIL_LABEL,
  zeitpunktText,
  type LaufUrteil,
  type VerlaufEintrag,
} from './render-verlauf';
import './vis-visual.css';

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
 * Lauf, aufs Blatt geht nichts, die Auswahl der Knoten bleibt, wie sie ist.
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
}) {
  const [offenJob, setOffenJob] = useState<string | null>(null);
  const n = reihe.length;
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
  const offenIndex = offenJob === null ? -1 : reihe.findIndex((e) => e.jobId === offenJob);
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
            {n} Läufe
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
          die letzten {n} Läufe · neuester links
        </span>
      </div>
      <div className="vis-verlauf-reihe" data-anzahl={n}>
        {reihe.map((e, i) => {
          const nummer = laufNummerVon(e, i, n);
          const urteil = laufUrteil(e.qa);
          const uhrzeit = uhrzeitText(laufZeit(e));
          const istHaupt = i === 0 && e.jobId === hauptJobId;
          return (
            <button
              key={e.jobId}
              type="button"
              className={`vis-verlauf-knopf${istHaupt ? ' vis-verlauf-knopf--haupt' : ''}`}
              data-testid="render-verlauf-bild"
              data-urteil={urteil}
              data-job={e.jobId}
              {...(e.grundlageId ? { 'data-grundlage': e.grundlageId } : {})}
              aria-label={`Lauf ${nummer} von ${uhrzeit}, ${URTEIL_LABEL[urteil]}, gross anzeigen`}
              onPointerDown={halte}
              onClick={() => setOffenJob(e.jobId)}
            >
              <span className="vis-verlauf-daumen">
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
            reihe={reihe}
            index={offenIndex}
            hauptJobId={hauptJobId}
            onWahl={(i) => setOffenJob(reihe[i]?.jobId ?? null)}
            onClose={() => setOffenJob(null)}
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

function VerlaufGross({
  reihe,
  index,
  hauptJobId,
  onWahl,
  onClose,
  art,
}: {
  reihe: readonly VerlaufEintrag[];
  index: number;
  hauptJobId: string | undefined;
  onWahl: (index: number) => void;
  onClose: () => void;
  /** Ein Einzelbild ohne Ergebnis (s. `EinzelbildGross`); fehlt es, ein Lauf des Verlaufs. */
  art?: EinzelbildArt;
}) {
  const boxRef = useRef<HTMLDivElement | null>(null);
  const schliessenRef = useRef<HTMLButtonElement | null>(null);
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
  // Verlauf-Nachgang: die fortlaufende Nummer des Laufs am Knoten im Titel;
  // die Stelle in der Reihe (von links, neuestes zuerst) getrennt daneben.
  const nummer = laufNummerVon(e, index, n);
  const urteil = laufUrteil(e.qa);
  const hatAelteren = index < n - 1;
  const hatNeueren = index > 0;
  const erster = reihe[0];
  const hauptNummer = erster && erster.jobId === hauptJobId ? laufNummerVon(erster, 0, n) : undefined;

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

  const taste = (ev: ReactKeyboardEvent<HTMLDivElement>) => {
    ev.stopPropagation();
    if (ev.key === 'Tab') {
      const box = boxRef.current;
      if (!box) return;
      const knoepfe = [...box.querySelectorAll<HTMLElement>('button:not([disabled]), [tabindex="0"]')];
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
        className="k-dialog-box k-dialog k-aus-ausloeser vis-verlauf-gross"
        data-testid="render-verlauf-gross"
        data-job={e.jobId}
        {...(art ? { 'data-art': art } : {})}
      >
        <div className="vis-verlauf-gross-kopf">
          <span className="vis-verlauf-gross-titel" data-testid="render-verlauf-gross-titel">
            {art ? EINZELBILD_TEXT[art].titel : `LAUF ${nummer}`}
          </span>
          {!art && <span className="vis-verlauf-gross-zeit">{zeitpunktText(laufZeit(e))}</span>}
          {!art && (
            <span className="vis-verlauf-gross-stelle" data-testid="render-verlauf-gross-stelle">
              {index + 1} von {n} im Verlauf
            </span>
          )}
          <span className="vis-verlauf-gross-luecke" />
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
          <div className="vis-verlauf-gross-bild">
            <BridgeBild
              key={e.jobId}
              jobId={e.jobId}
              imageName={e.bild}
              alt={`Lauf ${nummer}`}
              testid="render-verlauf-gross-bild"
              className="vis-verlauf-gross-img"
            />
          </div>
          <div className="vis-verlauf-gross-seite">
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
      </div>
    </div>
  );
}
