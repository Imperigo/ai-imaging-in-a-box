/**
 * STELLVERTRETER (Visbox) (Plan UI-Gleichheit S3, Entscheide 115/116 (2), 20.10.2026) fuer
 * `shell/KosmoPanel.tsx` von KosmoOrbit.
 *
 * Dort ist diese Datei Kosmos Gespraechsfeld — rund 10 000 Zeilen mit Kosmos Motor (ChatSession,
 * Rollen, Laeufe, Karten, Feedback, Vorlesen, Blick, Zeitleiste, Einstellungen des Motors). Nichts
 * davon gibt es in Visbox: Der Assistent ist ein eigener (qwen3:14b am Heim-PC), und das Gespraech
 * fuehrt die Mac-App (`shell/kosmo-gespraech.ts`, Stellvertreter). Dieser Stellvertreter zeichnet
 * darum **dieselbe Anatomie** mit denselben Klassen aus `kosmo-panel.css` (woertlich) — so sieht das
 * Feld aus wie dort:
 *
 *  - `aside.kp-panel` mit `data-stufe`, schwebend (`k-panel-eintritt`) oder ab der Breite der
 *    Zentrale-Spalte als Seitenfenster rechts (`kp-panel--seitenfenster`, wie dort
 *    `useSeitenfensterBreit`, woertlich);
 *  - `.kp-kopf` mit dem Orb im Kopf (`KosmoKopfOrb`, woertlich), dem Namen (`.kp-titel`, aus der
 *    Nahtstelle `kosmoName()`), der Marke Ort · Modell · Zustand (`KosmoMarke`, woertlich) und
 *    «Schliessen» (`kosmo-panel-schliessen`); dann `Hairline`;
 *  - `.kp-verlauf` (role=log) mit den Blasen `kp-bubble--du`/`--kosmo`, «denkt» (`kp-denkt`), der
 *    Karte des Vorschlags (`kp-karte kp-karte--offen`, Anwenden · Ablehnen · Ändern — Blatt 14),
 *    dem Hinweis (`kp-system-zeile`) und «Was der Assistent nicht tut»;
 *  - `.kp-eingabe-reihe` mit `kosmo-input` und `kosmo-send` — oder, wo kein Feld steht (ohne Rechner,
 *    Modell nicht bereit, ohne App), **der Satz**, warum nicht (Entscheid 103b, wie
 *    `brueckeSagtDenSatz` am Render-Knoten): kein Feld, das nur einen Fehler zurueckbraechte.
 *
 * Was dort im Kopf steht und hier nicht (Kosten des Motors, Lizenz, Projektfarbe, Vorlesen,
 * Zeitleiste, Motor-Einstellungen) und was unten steht (Feedback, Anhang, Mikrofon, Zuruf), hat in
 * Visbox keinen Gegenstand — benannt in `kosmovis/UI_AUSNAHMEN.json`.
 */
import { useEffect, useRef, useState } from 'react';
import { Hairline, KButton, KIcon, useBewegung } from '@kosmo/ui';
import { KosmoKopfOrb } from './kosmo-fenster/KosmoKopfOrb';
import { kosmoZustandAusStatus } from './kosmo-eck-orb/KosmoEckOrb';
import { KosmoMarke } from './chat/KosmoMarke';
import { useSeitenfensterBreit } from './chat/use-seitenfenster-breit';
import { useKosmoGespraech, wuenscheGespraech } from './kosmo-gespraech';
import { useKosmoStatus } from '../state/kosmo-status';
import { kosmoName } from '../state/kosmo-name';
import './kosmo-panel.css';

export interface KosmoPanelProps {
  /** Wie dort: gemountet, aber verborgen, wenn `false`. */
  sichtbar?: boolean;
  /** Wie dort (die Station); in Visbox immer «vis». */
  station?: string;
  onClose: () => void;
  /** Der Satz, wenn niemand das Gespraech fuehrt (keine App) — statt eines Felds ohne Wirkung. */
  ohneMotorSatz?: string;
  /** Wo das Modell rechnet (Marke im Kopf). */
  ort?: string;
}

/** Der Text fuer das Feld nach einer Ansage der App — nur, wenn er niemandes Tippen ueberschreibt. */
export function feldNachApp(jetzt: string, gesendet: string | null, vonApp: string): string | null {
  if (jetzt.trim() === '') return vonApp;
  if (gesendet !== null && jetzt === gesendet) return vonApp;
  return null;
}

export function KosmoPanel({ sichtbar = true, onClose, ohneMotorSatz, ort = 'Heim-PC' }: KosmoPanelProps) {
  const g = useKosmoGespraech();
  const zustand = useKosmoStatus((s) => s.zustand);
  const pegel = useKosmoStatus((s) => s.pegel);
  const seitenfenster = useSeitenfensterBreit();
  const bewegung = useBewegung();
  const [eingabe, setEingabe] = useState('');
  const gesendet = useRef<string | null>(null);
  const feldRef = useRef<HTMLTextAreaElement | null>(null);

  // EIN TEXT DER APP FUERS FELD (Ändern, eine zurueckgelegte Nachricht, nach dem Senden leer): die
  // Regel, wann, steht im Kern der App; hier nur, dass niemandes Tippen ueberschrieben wird.
  const feldNummer = g.feld?.nummer;
  useEffect(() => {
    if (!g.feld) return;
    const vorher = gesendet.current;
    const vonApp = g.feld.text;
    setEingabe((jetzt) => feldNachApp(jetzt, vorher, vonApp) ?? jetzt);
    gesendet.current = null;
    // Nur die Nummer zaehlt: derselbe Text zweimal ist zweimal eine Ansage.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feldNummer]);

  useEffect(() => {
    if (sichtbar) feldRef.current?.focus({ preventScroll: true });
  }, [sichtbar]);

  if (!sichtbar) return null;
  const name = kosmoName();
  const satzStattFeld = g.motor ? g.feldSatz : (ohneMotorSatz ?? null);
  const senden = () => {
    const text = eingabe.trim();
    if (!text || g.wartet) return;
    gesendet.current = eingabe;
    wuenscheGespraech({ tat: 'frage', text: eingabe });
  };
  const bereit = g.stand === 'bereit';
  const klassen = [
    seitenfenster ? (bewegung === 'voll' ? 'kp-aus-orb' : '') : 'k-panel-eintritt',
    'kp-panel',
    seitenfenster ? 'kp-panel--seitenfenster' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <aside data-testid="kosmo-panel" data-stufe="m" data-stufe-gespeichert="m" className={klassen} aria-label={`Gespräch mit ${name}`}>
      <div className="kp-kopf">
        <KosmoKopfOrb
          zustand={kosmoZustandAusStatus(zustand)}
          pegel={pegel}
          arbeitet={false}
          abbruchVerlangt={false}
          onStopp={() => undefined}
          wandert={false}
        />
        <div className="kp-titel">{name}</div>
        <KosmoMarke ort={ort} modell={g.modell ?? '—'} verbunden={bereit} wort={bereit ? 'bereit' : 'nicht verbunden'} />
        <div className="kp-fuell" />
        <KButton size="sm" tone="ghost" onClick={onClose} aria-label="Schliessen" data-testid="kosmo-panel-schliessen">
          <KIcon name="schliessen" size={16} />
        </KButton>
      </div>
      <Hairline />
      <div className="kp-verlauf" role="log" aria-live="polite" aria-relevant="additions" aria-label={`Gespräch mit ${name}`}>
        {g.beitraege.map((b, i) => (
          <div
            key={i}
            className={`k-einblenden kp-bubble ${b.von === 'mensch' ? 'kp-bubble--du' : 'kp-bubble--kosmo'}`}
            data-testid="assistent-beitrag"
            data-von={b.von}
          >
            {b.text}
          </div>
        ))}
        {g.wartet && (
          <div className="kp-denkt" data-testid="kosmo-fortschritt">
            {name} antwortet …
          </div>
        )}
        {g.karte && (
          <div className="kp-karte kp-karte--offen" data-testid="assistent-karte">
            <div className="kp-eyebrow k-label k-label-eng">Vorschlag von {name}</div>
            <ol className="kp-schritt-liste">
              {g.karte.zeilen.map((zeile, i) => (
                <li key={i} className="kp-schritt-zeile">
                  <KIcon name="haken" size={14} className="kp-schritt-haken" />
                  <span className="kp-schritt-satz">{zeile}</span>
                </li>
              ))}
            </ol>
            {g.karte.rechenzeit && (
              <div className="kp-hinweis-soft" data-testid="assistent-rechenzeit">
                {g.karte.rechenzeit}
              </div>
            )}
            <div className="kp-knopf-reihe">
              <KButton size="sm" tone="accent" disabled={g.wartet} data-testid="assistent-anwenden" onClick={() => wuenscheGespraech({ tat: 'anwenden' })}>
                Anwenden
              </KButton>
              <KButton size="sm" tone="ghost" disabled={g.wartet} data-testid="assistent-ablehnen" onClick={() => wuenscheGespraech({ tat: 'ablehnen' })}>
                Ablehnen
              </KButton>
              <KButton size="sm" tone="ghost" disabled={g.wartet} data-testid="assistent-aendern" onClick={() => wuenscheGespraech({ tat: 'aendern' })}>
                Ändern
              </KButton>
            </div>
          </div>
        )}
        {g.hinweis && (
          <div className="k-einblenden kp-system-zeile kp-system-zeile--fluss" data-testid="assistent-hinweis">
            <span className="kp-system-text">{g.hinweis}</span>
          </div>
        )}
        {g.grenzen && (
          <div className="kp-hinweis-soft" data-testid="assistent-grenzen">
            <b>{g.grenzen.titel}:</b> {g.grenzen.satz}
          </div>
        )}
      </div>
      <div className="kp-eingabe-reihe">
        {satzStattFeld !== null ? (
          <p className="kp-hinweis-soft" data-testid="assistent-sperre" role="status">
            {satzStattFeld}
          </p>
        ) : (
          <>
            <textarea
              ref={feldRef}
              className="kp-input kp-eingabe-feld"
              data-testid="kosmo-input"
              rows={seitenfenster ? 2 : 1}
              value={eingabe}
              placeholder={`Schreiben, was das Bild zeigen soll …`}
              aria-label={`Nachricht an ${name}`}
              onChange={(e) => setEingabe(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  senden();
                }
              }}
            />
            <KButton tone="accent" size="sm" onClick={senden} disabled={g.wartet || eingabe.trim() === ''} data-testid="kosmo-send">
              Senden
            </KButton>
          </>
        )}
      </div>
    </aside>
  );
}
