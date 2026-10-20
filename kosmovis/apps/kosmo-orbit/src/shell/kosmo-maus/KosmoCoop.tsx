/**
 * Coop-Modus — schlichte, funktionierende Bedienung (Owner-Entscheid E158,
 * Nachentscheide 07.10.2026; Entwurf `docs/COOP-MODUS.md` §5). Gestaltung ist
 * Sache des UI-Workers (Teil B); hier stehen die festen Kennungen, auf die
 * sich die Proben stützen. Der Zustand liegt in `state/kosmo-coop.ts`.
 *
 *  - `KosmoCoopKnopf` — «Im Projekt: Du · Claude · Kosmo» unten links, dort
 *    wo «Claude verbunden» steht (`ClaudeAnschluss.tsx`). Ein Klick zeigt
 *  - `KosmoCoopFlaeche` — wer woran arbeitet, «Alle anhalten», und den
 *  - `KosmoCoopVerlauf` — die Schritte von Claude und Kosmo mit «Zurücknehmen»
 *    je Schritt; hängt ein späterer Schritt daran, fragt die Nachfrage.
 *
 * Gestaltung (UI-Worker, Teil B, Entwurfsfläche «KosmoOrbit Coop-Modus»,
 * Owner 07.10.2026: B1 Variante A, B3 «Ja, so»): je Beteiligtem ein Punkt in
 * seiner Farbe (Du Akzent, Claude Gold der Agenten-Rolle, Kosmo Rot seines
 * Orbs); der Verlauf zeigt ALLE Schritte des Projekts in einer rollenden
 * Liste mit Filter je Urheber (eine Datensatz-Liste, UI-Regel 1 Ausnahme);
 * `KosmoCoopSchild` zeigt einen neuen Schritt drei Sekunden lang (B2,
 * Quelle `state/coop-marke.ts`).
 *
 * E178 Vollautomatik (08.10.2026): `VollautomatikAnzeige` steht dauerhaft
 * unten links, solange die Stufe an ist, mit «Alle anhalten» direkt daneben;
 * `VollautomatikSchalter` ist der eine Schalter in Kosmos Einstellungen. Der
 * Verlauf nennt je Schritt Quelle und Stufe.
 *
 * Alles liegt in Flächen mit `data-kosmo-maus-eigen` (Sperrzone der KosmoMaus)
 * und nimmt nur echte Klicks — ein Agent nimmt nie selbst zurück, hält nicht
 * an und startet keinen Coop.
 */

import { useState } from 'react';
import { KButton, KSwitch, melde } from '@kosmo/ui';
import { URHEBER_NAME, useKosmoMaus } from '../../state/kosmo-maus-freigabe';
import {
  COOP_WEG_NAME,
  coopPraesenz,
  coopSchritte,
  halteAlleAn,
  nimmSchrittZurueck,
  setzeVollautomatik,
  useKosmoCoop,
  type CoopGruppe,
  type Zuruecknahme,
} from '../../state/kosmo-coop';
import { useProject } from '../../state/project-store';
import { useCoopMarke } from '../../state/coop-marke';
import { eigen } from './KosmoMausSchalter';

/** Nur echte Klicks des Architekten. */
function echt(e: React.MouseEvent): boolean {
  return e.nativeEvent.isTrusted;
}

/** Zeichnet neu bei Coop-, Freigabe- und Projektänderungen. */
function useCoopStand() {
  useKosmoCoop((z) => z.gruppen);
  useKosmoCoop((z) => z.an);
  useKosmoCoop((z) => z.vollautomatik);
  useKosmoMaus((z) => z.freigaben);
  useProject((s) => s.revision);
  useProject((s) => s.doc);
}

/** Soll die Präsenz unten links stehen? Solange ein Coop läuft oder es Coop-Schritte im Projekt gibt. */
export function useCoopSichtbar(): boolean {
  const an = useKosmoCoop((z) => z.an);
  const voll = useKosmoCoop((z) => z.vollautomatik);
  const gruppen = useKosmoCoop((z) => z.gruppen);
  const doc = useProject((s) => s.doc);
  return voll || an.claude || an.kosmo || gruppen.some((g) => g.doc === doc);
}

/**
 * E178, Auflagen des Integrators: die Stufe ist dauerhaft sichtbar, solange
 * sie an ist, und «Alle anhalten» liegt ohne Umweg daneben (schaltet auch die
 * Vollautomatik aus).
 */
export function VollautomatikAnzeige() {
  const voll = useKosmoCoop((z) => z.vollautomatik);
  if (!voll) return null;
  return (
    <span className="claude-anschluss-marke kosmo-vollautomatik-anzeige" data-testid="kosmo-vollautomatik-anzeige" role="status" {...eigen()}>
      <span className="claude-anschluss-punkt" aria-hidden="true" />
      Vollautomatik an
      <KButton
        tone="ghost"
        data-testid="kosmo-vollautomatik-anhalten"
        aria-label="Alle anhalten — Vollautomatik und Coop aus, Claude und Kosmo bedienen nicht mehr"
        onClick={(e) => echt(e) && halteAlleAn()}
      >
        Alle anhalten
      </KButton>
    </span>
  );
}

/** E178: der eine Schalter (Kosmos Einstellungen). Nimmt nur echte Klicks. */
export function VollautomatikSchalter() {
  const voll = useKosmoCoop((z) => z.vollautomatik);
  return (
    <div className="kosmo-vollautomatik-schalter" {...eigen()}>
      <KSwitch
        className="kosmo-maus-schalter-zeile"
        role="switch"
        label="Vollautomatik"
        aria-label="Vollautomatik: Claude und Kosmo wenden ihre Vorschläge selbst an"
        data-testid="kosmo-einstellungen-vollautomatik"
        checked={voll}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
          if (!e.nativeEvent.isTrusted) return;
          setzeVollautomatik(e.target.checked);
        }}
      />
      <p className="kosmo-maus-hinweis">
        Vollautomatik heisst: Claude und Kosmo wenden ihre Vorschläge selbst an, auch Pakete und Werkzeuge, die sonst eine
        Bestätigung brauchen. Jeder Schritt steht im Verlauf mit Namen und Quelle und lässt sich dort zurücknehmen.
        Veröffentlichen fragt weiter dich, ein gelöschtes Projekt kommt in den Papierkorb. «Immer ablehnen» gilt weiter. Nur
        an diesem Gerät, nicht über das Internet. «Alle anhalten» schaltet sie aus.
      </p>
    </div>
  );
}

export function KosmoCoopKnopf({ offen, onUmschalten }: { offen: boolean; onUmschalten: () => void }) {
  useCoopStand();
  const dabei = coopPraesenz().filter((p) => p.wer === 'du' || p.coop || p.bedient);
  return (
    <button
      type="button"
      className="claude-anschluss-marke kosmo-coop-knopf"
      data-testid="kosmo-coop-praesenz"
      aria-expanded={offen}
      aria-label={`Im Projekt: ${dabei.map((p) => p.name).join(', ')} — zeigen, wer woran arbeitet`}
      onClick={onUmschalten}
      {...eigen()}
    >
      <span className="kosmo-coop-punkte" aria-hidden="true">
        {dabei.map((p) => (
          <span key={p.wer} className="kosmo-coop-punkt" data-urheber={p.wer} />
        ))}
      </span>
      <span>
        Im Projekt:{' '}
        {dabei.map((p, i) => (
          <span key={p.wer} className="kosmo-coop-name" data-urheber={p.wer} data-testid={`kosmo-coop-praesenz-${p.wer}`}>
            {i > 0 ? ' · ' : ''}
            {p.name}
          </span>
        ))}
      </span>
    </button>
  );
}

function uhrzeit(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' });
}

export function KosmoCoopFlaeche() {
  useCoopStand();
  const leute = coopPraesenz();
  const voll = useKosmoCoop((z) => z.vollautomatik);
  const laeuft = voll || leute.some((p) => p.wer !== 'du' && (p.coop || p.bedient));
  return (
    <section className="claude-anschluss-schalter kosmo-coop-flaeche" data-testid="kosmo-coop-flaeche" aria-label="Wer woran arbeitet" {...eigen()}>
      <div className="claude-anschluss-titel">Im Projekt</div>
      <ul className="kosmo-coop-leute">
        {leute.map((p) => (
          <li key={p.wer} className="kosmo-coop-person" data-urheber={p.wer} data-testid={`kosmo-coop-wer-${p.wer}`}>
            <span className="kosmo-coop-punkt" data-urheber={p.wer} aria-hidden="true" />
            <b className="kosmo-coop-name" data-urheber={p.wer}>
              {p.name}
            </b>
            <span className="kosmo-coop-zustand">
              {p.wer === 'du' ? '' : p.vollautomatik ? 'ändert frei (Vollautomatik)' : p.coop ? 'ändert frei' : p.bedient ? 'bedient, Änderungen als Karte' : 'nicht aktiv'}
            </span>
            {p.zuletzt && (
              <span className="kosmo-coop-zuletzt">
                {uhrzeit(p.zuletzt.zeit)} {p.zuletzt.zusammenfassung}
              </span>
            )}
          </li>
        ))}
      </ul>
      {laeuft && (
        <KButton
          tone="ghost"
          className="kosmo-coop-anhalten"
          data-testid="kosmo-coop-alle-anhalten"
          aria-label="Alle anhalten — Claude und Kosmo ändern und bedienen nicht mehr"
          onClick={(e) => echt(e) && halteAlleAn()}
        >
          Alle anhalten
        </KButton>
      )}
      {laeuft && (
        <p className="claude-anschluss-hinweis">Anhalten: Claude und Kosmo ändern und bedienen nicht mehr. Ihre Schritte bleiben und lassen sich zurücknehmen.</p>
      )}
      {/* Alle Schritte des Projekts in einer rollenden Liste (Datensatz-Liste, UI-Regel 1 Ausnahme). */}
      <KosmoCoopVerlauf vorsatz="kosmo-coop" />
    </section>
  );
}

/** Die Schritte von Claude und Kosmo, neueste zuerst, mit «Zurücknehmen» je Schritt. */
export function KosmoCoopVerlauf({ vorsatz, hoechstens = 200 }: { vorsatz: 'kosmo-coop' | 'kosmo-einstellungen-coop'; hoechstens?: number }) {
  useCoopStand();
  const [nachfrage, setNachfrage] = useState<{ kennung: string; antwort: Zuruecknahme } | null>(null);
  const [filter, setFilter] = useState<'alle' | 'claude' | 'kosmo'>('alle');
  const alle = coopSchritte().slice(-hoechstens).reverse();
  if (alle.length === 0) return null;
  const schritte = filter === 'alle' ? alle : alle.filter((g) => g.urheber === filter);
  const nimm = (g: CoopGruppe, mitAbhaengigen: boolean) => {
    const r = nimmSchrittZurueck(g.kennung, { mitAbhaengigen });
    if (r.status === 'nachfrage') {
      setNachfrage({ kennung: g.kennung, antwort: r });
      return;
    }
    setNachfrage(null);
    melde(r.satz, { ton: r.status === 'zurueckgenommen' ? 'erfolg' : 'info' });
  };
  return (
    <div className="kosmo-coop-verlauf" data-testid={`${vorsatz}-verlauf`}>
      <div className="claude-anschluss-titel">Schritte von Claude und Kosmo</div>
      <div className="kosmo-coop-filter" role="group" aria-label="Schritte filtern">
        {(['alle', 'claude', 'kosmo'] as const).map((f) => (
          <button
            key={f}
            type="button"
            className="kosmo-maus-filter"
            aria-pressed={filter === f}
            data-testid={`${vorsatz}-filter-${f}`}
            onClick={() => setFilter(f)}
          >
            {f === 'alle' ? 'Alle' : URHEBER_NAME[f]}
          </button>
        ))}
      </div>
      {schritte.length === 0 && <p className="claude-anschluss-hinweis">Keine Schritte von {filter === 'claude' ? 'Claude' : 'Kosmo'}.</p>}
      <ol className="kosmo-coop-schritte kosmo-coop-schritte--liste">
        {schritte.map((g) => (
          <li
            key={g.kennung}
            className="kosmo-coop-schritt"
            data-testid={`${vorsatz}-schritt`}
            data-kennung={g.kennung}
            data-urheber={g.urheber}
            data-zurueckgenommen={g.zurueckgenommen ? 'ja' : 'nein'}
            data-stufe={g.stufe}
            data-weg={g.weg}
          >
            <span className="kosmo-maus-chip" data-urheber={g.urheber}>
              {URHEBER_NAME[g.urheber]}
            </span>
            <span className="kosmo-coop-schritt-text">
              {uhrzeit(g.zeit)} {g.zusammenfassung}
            </span>
            {/* E178: Quelle (Chat/Werkzeug/KosmoMaus, ggf. Anlass) und Stufe je Schritt. */}
            <span className="kosmo-coop-schritt-zurueck" data-testid={`${vorsatz}-quelle`}>
              {COOP_WEG_NAME[g.weg]}
              {g.anlass ? ` · ${g.anlass}` : ''}
              {g.stufe === 'vollautomatik' ? ' · Vollautomatik' : ''}
            </span>
            {g.vermerk ? (
              <span className="kosmo-coop-schritt-zurueck" data-testid={`${vorsatz}-vermerk`}>
                {g.vermerk}
              </span>
            ) : g.zurueckgenommen ? (
              <span className="kosmo-coop-schritt-zurueck">zurückgenommen</span>
            ) : (
              <KButton
                tone="ghost"
                data-testid={`${vorsatz}-zuruecknehmen-${g.kennung}`}
                aria-label={`Schritt von ${URHEBER_NAME[g.urheber]} zurücknehmen: ${g.zusammenfassung}`}
                onClick={(e) => echt(e) && nimm(g, false)}
              >
                Zurücknehmen
              </KButton>
            )}
            {nachfrage?.kennung === g.kennung && (
              <div className="kosmo-coop-nachfrage" data-testid={`${vorsatz}-nachfrage`} role="alertdialog" aria-label="Spätere Schritte hängen daran">
                <p className="claude-anschluss-hinweis">{nachfrage.antwort.satz}</p>
                <div className="claude-anschluss-knoepfe">
                  <KButton tone="ghost" data-testid={`${vorsatz}-nachfrage-nein`} onClick={(e) => echt(e) && setNachfrage(null)}>
                    Abbrechen
                  </KButton>
                  <KButton tone="accent" data-testid={`${vorsatz}-nachfrage-ja`} onClick={(e) => echt(e) && nimm(g, true)}>
                    Mit zurücknehmen
                  </KButton>
                </div>
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

/**
 * B2: ein neuer Schritt von Claude oder Kosmo — drei Sekunden lang über der
 * Präsenz, in der Farbe des Urhebers (`state/coop-marke.ts`). Grundriss und 3D
 * färben dieselben Bauteile über dieselbe Quelle ein.
 */
export function KosmoCoopSchild() {
  const marke = useCoopMarke((z) => z.marke);
  if (!marke) return null;
  return (
    <div className="kosmo-coop-schild" data-urheber={marke.urheber} data-testid="kosmo-coop-schild" data-kennung={marke.kennung} role="status" {...eigen()}>
      <b>{URHEBER_NAME[marke.urheber]}</b> · {marke.zusammenfassung}
    </div>
  );
}
