/**
 * Claude-Anschluss — die sichtbare Seite (v0.1.7, E149, `docs/CLAUDE-ANSCHLUSS.md`).
 *
 * Unsichtbar, solange kein MCP-Server läuft. Ist Claude verbunden, steht
 * unten links eine kleine Marke «Claude verbunden»; jeder ändernde Aufruf
 * erscheint darüber als Karte mit «Anwenden» und «Ablehnen».
 *
 * Teil A (Auftrag Home-PC-Worker, A1; Entwurf «KosmoMaus Bedienteile»): die
 * Marke ist ein Knopf und klappt die Schalter «Mitschauen» und «Bedienen»
 * auf (`kosmo-maus-schalter`). Das Auge sagt, dass Claude mitschauen darf.
 * C7: «N offen» zählt Claudes Karten und klappt sie zu und auf. Gemountet in
 * `main.tsx` neben `<App />`, nicht in `App.tsx` (die gehört dem UI-Worker,
 * E147) — die Fläche liegt darum als eigene feste Ebene über der App.
 */

import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { KButton } from '@kosmo/ui';
import {
  CLAUDE_ADRESSE_SCHLUESSEL,
  CLAUDE_STANDARD_ADRESSE,
  claudeAnschlussErlaubt,
  lehneClaudeVorschlagAb,
  meldeClaudeAnschlussAus,
  starteClaudeVerbindung,
  useClaudeAnschluss,
  wendeClaudeVorschlagAn,
  type ClaudeVerbindung,
} from '../../state/claude-anschluss';
import { istTauriDesktop } from '../tauri-desktop';
import { useKosmoMaus } from '../../state/kosmo-maus-freigabe';
import { bedienWechselKurz, eigen, KosmoMausFreigabeSchalter } from '../kosmo-maus/KosmoMausSchalter';
import { KosmoCoopFlaeche, KosmoCoopKnopf, KosmoCoopSchild, useCoopSichtbar, VollautomatikAnzeige } from '../kosmo-maus/KosmoCoop';
import { beobachteCoopMarken } from '../../state/coop-marke';
import { useKosmoCoop } from '../../state/kosmo-coop';
import { beobachteClaudeFusszone, CLAUDE_STAPEL_TOKEN } from './fusszone';
import './claude-anschluss.css';

function leseAdresse(): string {
  try {
    return localStorage.getItem(CLAUDE_ADRESSE_SCHLUESSEL) || CLAUDE_STANDARD_ADRESSE;
  } catch {
    return CLAUDE_STANDARD_ADRESSE;
  }
}

/**
 * NAHTSTELLE FUER EINEN ZWEITEN WIRT (Visbox-Entscheide 115/116, 20.10.2026), wie
 * `registriereModellLaden`: Visbox zeigt dieselbe Marke und dieselben Karten, aber Claude bedient
 * dort nur ueber Werkzeuge — es gibt keinen eigenen Zeiger (keine KosmoMaus). Was an der Marke
 * aufklappt, reicht der Wirt darum selbst herein (in Visbox die Selbständigkeit: Karte, Coop,
 * Voll). **KosmoOrbit reicht nichts** — dann stehen «Mitschauen und Bedienen» wie bisher da.
 */
export interface ClaudeAusklapper {
  /** Titel des Abschnitts und Teil des Vorlesenamens der Marke. */
  readonly titel: string;
  readonly inhalt: ReactNode;
}

export function ClaudeAnschluss({ ausklapper }: { ausklapper?: ClaudeAusklapper } = {}) {
  const verbunden = useClaudeAnschluss((z) => z.verbunden);
  const vorschlaege = useClaudeAnschluss((z) => z.vorschlaege);
  const internet = useClaudeAnschluss((z) => z.internet);
  const verbindung = useRef<ClaudeVerbindung | null>(null);
  const schautMit = useKosmoMaus((z) => z.freigaben.claude.mitschauen);
  const darfBedienen = useKosmoMaus((z) => z.freigaben.claude.bedienen);
  // Nr. 75/77: hat nicht der Schalter das Bedienen beendet (Esc, «Stopp», Agent …), sagt es die Marke.
  const bedienWechsel = useKosmoMaus((z) => z.freigaben.claude.bedienen ? null : z.bedienWechsel.claude);
  const bedienEnde = bedienWechsel && bedienWechsel.grund !== 'schalter' ? bedienWechselKurz(bedienWechsel, false) : null;
  const coop = useKosmoCoop((z) => z.an.claude); // E158
  // Welcher Ausklapper offen ist: die Schalter an der Marke oder (E158) die Coop-Fläche.
  const [offen, setOffen] = useState<'schalter' | 'coop' | null>(null);
  const schalterOffen = offen === 'schalter';
  const schalteSchalter = () => setOffen((alt) => (alt === 'schalter' ? null : 'schalter'));
  const coopSichtbar = useCoopSichtbar();
  const flaeche = useRef<HTMLDivElement | null>(null);
  const kartenOffen = useClaudeAnschluss((z) => z.kartenOffen);
  const kartenFokus = useClaudeAnschluss((z) => z.kartenFokus);
  const setKartenOffen = (f: (alt: boolean) => boolean) => useClaudeAnschluss.setState((z) => ({ kartenOffen: f(z.kartenOffen) }));
  // Die Erzählzeile bittet um die Karten: sind sie aufgeklappt, steht der Fokus auf dem ersten «Anwenden».
  useEffect(() => {
    if (kartenFokus === 0) return;
    flaeche.current?.querySelector<HTMLElement>('[data-testid="claude-vorschlag-anwenden"]')?.focus();
  }, [kartenFokus]);
  // Nr. 56: die Zeile unten links meldet ihre Fusszone, Flaechen-Leisten weichen aus (`fusszone.ts`).
  const [zeile, setZeile] = useState<HTMLDivElement | null>(null);
  useEffect(() => (zeile ? beobachteClaudeFusszone(zeile) : undefined), [zeile]);
  // Befund LW 20.10.: der ganze Stapel (Karten + Zeile) für das, was in derselben Spalte unten links sitzt. Als
  // Ref-Rückruf mit Zustand wie die Zeile: ohne Claude rendert die Fläche nichts, ein Effekt beim Einhängen sähe sie nie.
  const [stapel, setStapel] = useState<HTMLDivElement | null>(null);
  useEffect(() => (stapel ? beobachteClaudeFusszone(stapel, document.documentElement, CLAUDE_STAPEL_TOKEN) : undefined), [stapel]);
  const flaecheRef = useCallback((el: HTMLDivElement | null) => {
    flaeche.current = el;
    setStapel(el);
  }, []);

  // B2: neue Coop-Schritte leuchten drei Sekunden (Schild hier, Bauteile in Grundriss/3D).
  useEffect(() => beobachteCoopMarken(), []);

  // Ausklapper: schliesst bei Esc und bei einem Klick ausserhalb.
  useEffect(() => {
    if (!offen) return;
    const taste = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOffen(null);
    };
    const zeiger = (e: PointerEvent) => {
      if (flaeche.current && e.target instanceof Node && !flaeche.current.contains(e.target)) setOffen(null);
    };
    window.addEventListener('keydown', taste);
    window.addEventListener('pointerdown', zeiger, true);
    return () => {
      window.removeEventListener('keydown', taste);
      window.removeEventListener('pointerdown', zeiger, true);
    };
  }, [offen]);

  useEffect(() => {
    let speicher: Storage | undefined;
    try {
      speicher = localStorage;
    } catch {
      speicher = undefined;
    }
    if (!claudeAnschlussErlaubt(speicher, navigator.webdriver === true)) {
      // E156: in der Desktop-App läuft der Server in der App selbst — der
      // Schalter «aus» schliesst ihn dort.
      meldeClaudeAnschlussAus();
      return;
    }
    if (!istTauriDesktop() && typeof EventSource === 'undefined') return;
    const v = starteClaudeVerbindung(leseAdresse());
    verbindung.current = v;
    return () => {
      v.stoppe();
      verbindung.current = null;
    };
  }, []);

  if (!verbunden && vorschlaege.length === 0 && !coopSichtbar) return null;

  const entscheide = (kennung: string, anwenden: boolean) => {
    const antwort = anwenden ? wendeClaudeVorschlagAn(kennung) : lehneClaudeVorschlagAb(kennung);
    if (antwort) verbindung.current?.antworte(antwort);
  };

  return (
    <div className="claude-anschluss" data-testid="claude-anschluss" ref={flaecheRef}>
      {kartenOffen && vorschlaege.map((v) => (
        <section
          key={v.kennung}
          className="claude-anschluss-karte"
          data-testid="claude-vorschlag"
          aria-label="Vorschlag von Claude"
        >
          <div className="claude-anschluss-titel">Vorschlag von Claude</div>
          <p className="claude-anschluss-text" data-testid="claude-vorschlag-text">
            {v.zusammenfassung}
          </p>
          {!verbunden && (
            // E276: die Karte bleibt bei Leitungsverlust stehen und sagt es.
            <p className="claude-anschluss-text" data-testid="claude-vorschlag-leitung">
              Leitung zu Claude unterbrochen. Die Entscheidung geht an Claude, sobald die Verbindung wieder steht.
            </p>
          )}
          {v.schritte && (
            // R35 E256: Vorschau aller Schritte des Pakets (eine Karte, ein Rückgängig).
            <ol className="claude-anschluss-text" data-testid="claude-vorschlag-schritte">
              {v.schritte.map((s, i) => (
                <li key={i}>{s.zusammenfassung}</li>
              ))}
            </ol>
          )}
          <div className="claude-anschluss-knoepfe">
            <KButton tone="ghost" onClick={() => entscheide(v.kennung, false)} data-testid="claude-vorschlag-ablehnen">
              Ablehnen
            </KButton>
            <KButton tone="accent" onClick={() => entscheide(v.kennung, true)} data-testid="claude-vorschlag-anwenden">
              Anwenden
            </KButton>
          </div>
        </section>
      ))}
      {verbunden && schalterOffen && (
        <section className="claude-anschluss-schalter" data-testid="kosmo-maus-schalter" aria-label={ausklapper?.titel ?? 'Mitschauen und Bedienen'} {...eigen()}>
          <div className="claude-anschluss-titel">{ausklapper?.titel ?? 'Mitschauen und Bedienen'}</div>
          {ausklapper ? (
            ausklapper.inhalt
          ) : (
            <>
              <KosmoMausFreigabeSchalter vorsatz="kosmo-maus" />
              <p className="claude-anschluss-hinweis">
                {coop
                  ? 'Bedienen heisst: mit eigenem Zeiger klicken. Im Coop ändert Claude das Projekt ohne Karte; du nimmst es je Agent zurück.'
                  : 'Bedienen heisst: mit eigenem Zeiger klicken. Änderungen am Projekt kommen weiter als Karte zum Anwenden.'}
              </p>
            </>
          )}
        </section>
      )}
      {coopSichtbar && offen === 'coop' && <KosmoCoopFlaeche />}
      {coopSichtbar && offen !== 'coop' && <KosmoCoopSchild />}
      {(verbunden || coopSichtbar) && (
        <div className="claude-anschluss-zeile" ref={setZeile}>
          {/* E158, Owner-Nachentscheid 07.10.: «Im Projekt: Du · Claude · Kosmo» unten links. */}
          {coopSichtbar && <KosmoCoopKnopf offen={offen === 'coop'} onUmschalten={() => setOffen((o) => (o === 'coop' ? null : 'coop'))} />}
          {/* E178: dauerhaft sichtbar, solange die Vollautomatik an ist, mit «Alle anhalten». */}
          <VollautomatikAnzeige />
          {verbunden && (
            <button
              type="button"
              className="claude-anschluss-marke"
              data-testid="claude-verbunden"
              aria-expanded={schalterOffen}
              aria-label={`Claude verbunden — ${ausklapper?.titel ?? 'Mitschauen und Bedienen'} einstellen`}
              onClick={schalteSchalter}
              {...eigen()}
            >
              <span className="claude-anschluss-punkt" aria-hidden="true" />
              Claude verbunden
              {schautMit && (
                <svg
                  className="claude-anschluss-auge"
                  data-testid="kosmo-maus-auge"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="Claude schaut mit"
                >
                  <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              )}
              {/* Die Leiste oben steht nur, solange Claude handelt (Ruhezeit in
                  KosmoMausEbene) — die Freigabe selbst bleibt hier sichtbar. */}
              {darfBedienen && (
                <svg
                  className="claude-anschluss-auge"
                  data-testid="kosmo-maus-darf-bedienen"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="Claude darf bedienen"
                >
                  <path d="M5 3 L5 19 L9.5 14.8 L13 21.5 L15.8 20.3 L12.4 13.6 L18.5 13.6 Z" />
                </svg>
              )}
              {bedienEnde && (
                <span className="claude-anschluss-coop" data-testid="kosmo-maus-bedien-ende">
                  {' '}
                  · Bedienen {bedienEnde}
                </span>
              )}
              {coop && (
                <span className="claude-anschluss-coop" data-testid="claude-coop-marke">
                  {' '}
                  · Coop: Claude ändert frei
                </span>
              )}
              {internet && (
                <span className="claude-anschluss-internet" data-testid="claude-internet">
                  {' '}
                  · aus dem Internet erreichbar
                </span>
              )}
            </button>
          )}
          {vorschlaege.length > 0 && (
            <button
              type="button"
              className="claude-anschluss-zaehler"
              data-testid="claude-karten-zaehler"
              data-wartet={!kartenOffen ? 'ja' : undefined}
              aria-expanded={kartenOffen}
              aria-label={`${vorschlaege.length} offene Vorschläge von Claude ${kartenOffen ? 'zuklappen' : 'aufklappen'}`}
              onClick={() => setKartenOffen((o) => !o)}
            >
              {vorschlaege.length} offen
            </button>
          )}
        </div>
      )}
    </div>
  );
}
