/**
 * KosmoMaus — die vier Schalter und das Journal (Teil A, A1/A3; Entwurf
 * «KosmoMaus Bedienteile», `docs/UI-LEINWAENDE.md`).
 *
 * Zwei Orte, dieselben Schalter: aufgeklappt an der Marke «Claude verbunden»
 * (`ClaudeAnschluss.tsx`) und als Abschnitt in Kosmos Einstellungen
 * (`KosmoMausAbschnitt`). Die Kennungen unterscheiden sich im Vorsatz
 * (`kosmo-maus-` bzw. `kosmo-einstellungen-`), weil beide gleichzeitig offen
 * sein können.
 *
 * Zwei Leitplanken aus E157 bleiben hier stehen, nicht im Zustand:
 *  - Die Schalter nehmen nur echte Klicks (`isTrusted`). Ein Agent schaltet
 *    sich nie selbst frei.
 *  - Jede Fläche mit Schaltern trägt `data-kosmo-maus-eigen` (Sperrzone für
 *    die KosmoMaus, im Blick ausgeblendet).
 */

import { useState } from 'react';
import { KSwitch } from '@kosmo/ui';
import {
  URHEBER,
  URHEBER_NAME,
  setzeFreigabe,
  useKosmoMaus,
  type AgentFreigabe,
  type BedienGrund,
  type BedienWechsel,
  type JournalEintrag,
  type Urheber,
} from '../../state/kosmo-maus-freigabe';
import { EIGENE_EBENE_ATTR } from '../../state/kosmo-blick-live';
import { setzeCoop, useKosmoCoop } from '../../state/kosmo-coop';
import { KosmoCoopVerlauf, VollautomatikSchalter } from './KosmoCoop';
import './kosmo-maus.css';

/** Sperrzone für die KosmoMaus. Erst beim Zeichnen ausgewertet: über den Kreis
 * Anschluss → KosmoMaus → Blick ist `EIGENE_EBENE_ATTR` beim Laden dieses Moduls
 * je nach Reihenfolge noch nicht gesetzt. */
export const eigen = (): Record<string, string> => ({ [EIGENE_EBENE_ATTR]: '' });

const ART_NAME: Record<keyof AgentFreigabe, string> = { mitschauen: 'Mitschauen', bedienen: 'Bedienen' };

/** Kurzformen der Gründe für die Zeile unter dem Schalter (die langen stehen in `BEDIEN_GRUND_NAME`). */
const BEDIEN_GRUND_KURZ: Record<BedienGrund, string> = {
  schalter: 'Schalter',
  esc: 'Esc',
  stopp: '«Stopp»',
  'alle-anhalten': '«Alle anhalten»',
  'anderes-fenster': 'anderes Fenster',
  agent: 'Agent selbst',
};

/**
 * Nr. 75/77 (Demolauf 16.10., Runde 34): der Schalter nennt, wodurch «Bedienen» zuletzt wechselte —
 * «aus — Esc, 16:36». `null`, solange es in dieser Sitzung keinen Wechsel gab oder der gemerkte Wechsel
 * nicht zum jetzigen Stand passt (dann gilt die gespeicherte Einstellung, ohne Grund).
 */
export function bedienWechselKurz(w: BedienWechsel | null, an: boolean): string | null {
  if (!w || w.an !== an) return null;
  const zeit = uhrzeit(w.zeit);
  return `${an ? 'an' : 'aus'} — ${BEDIEN_GRUND_KURZ[w.grund]}${zeit ? `, ${zeit}` : ''}`;
}

export function KosmoMausFreigabeSchalter({ vorsatz }: { vorsatz: 'kosmo-maus' | 'kosmo-einstellungen' }) {
  const freigaben = useKosmoMaus((z) => z.freigaben);
  const bedienWechsel = useKosmoMaus((z) => z.bedienWechsel);
  const coop = useKosmoCoop((z) => z.an);
  const schalte = (u: Urheber, art: keyof AgentFreigabe) => (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.nativeEvent.isTrusted) return;
    setzeFreigabe(u, art, e.target.checked);
  };
  // E158 Coop: dritter Schalter je Agent, Standard aus, nur echte Klicks.
  const schalteCoop = (u: Urheber) => (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.nativeEvent.isTrusted) return;
    setzeCoop(u, e.target.checked);
  };
  return (
    <div className="kosmo-maus-gruppen">
      {URHEBER.map((u) => {
        const grund = bedienWechselKurz(bedienWechsel[u], freigaben[u].bedienen);
        return (
          <fieldset key={u} className="kosmo-maus-gruppe" data-urheber={u}>
            <legend className="kosmo-maus-gruppe-name">{URHEBER_NAME[u]}</legend>
            {(['mitschauen', 'bedienen'] as const).map((art) => (
              <KSwitch
                key={art}
                className="kosmo-maus-schalter-zeile"
                role="switch"
                label={ART_NAME[art]}
                aria-label={`${URHEBER_NAME[u]}: ${ART_NAME[art]}`}
                data-testid={`${vorsatz}-freigabe-${u}-${art}`}
                checked={freigaben[u][art]}
                onChange={schalte(u, art)}
              />
            ))}
            {grund && (
              <span className="kosmo-maus-bedien-grund" data-testid={`${vorsatz}-bedien-grund-${u}`}>
                Bedienen {grund}
              </span>
            )}
            <KSwitch
              className="kosmo-maus-schalter-zeile"
              role="switch"
              label="Coop – ändert frei"
              aria-label={`${URHEBER_NAME[u]}: Coop – ändert das Projekt ohne Karte`}
              data-testid={`${vorsatz}-freigabe-${u}-coop`}
              checked={coop[u]}
              onChange={schalteCoop(u)}
            />
          </fieldset>
        );
      })}
    </div>
  );
}

const AKTION_WORT: Record<string, string> = {
  klick: 'klickt',
  doppelklick: 'doppelklickt',
  rechtsklick: 'klickt rechts',
  rad: 'scrollt',
  tippen: 'tippt',
  taste: 'drückt eine Taste',
  ziehen: 'zieht',
  waehlen: 'wählt',
  datei: 'gibt eine Datei',
  text: 'schaut sich die Lage an',
  bild: 'schaut sich die App an',
  angewendet: 'Vorschlag angewendet',
  abgelehnt: 'Vorschlag abgelehnt',
  'coop-angewendet': 'ändert im Coop',
};

/** Ein Journal-Eintrag in einem Satz für Laien: wer, was, worauf, mit welchem Ausgang. */
export function journalSatz(e: JournalEintrag): string {
  // Freigaben und Stopp schreibt der Zustand schon als ganzen Satz.
  if (e.werkzeug === 'freigabe') return e.text;
  // E158 Coop: die Zusammenfassung statt der Befehlskennung (Nutzersprache).
  if (e.werkzeug === 'coop') return e.aktion === 'coop-angewendet' ? `${AKTION_WORT[e.aktion]} · ${e.text}` : e.text;
  const was = AKTION_WORT[e.aktion] ?? e.aktion;
  const ziel = e.ziel ? ` · ${e.ziel}` : '';
  const ausgang = e.ergebnis === 'verweigert' ? ' — abgewiesen' : e.ergebnis === 'fehler' ? ' — ging nicht' : '';
  return `${was}${ziel}${ausgang}`;
}

function uhrzeit(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' });
}

type Filter = 'alle' | Urheber;

export function KosmoMausJournal({ hoechstens = 30 }: { hoechstens?: number }) {
  const journal = useKosmoMaus((z) => z.journal);
  const [filter, setFilter] = useState<Filter>('alle');
  const sichtbar = journal
    .filter((e) => filter === 'alle' || e.urheber === filter)
    .slice(-hoechstens)
    .reverse();
  return (
    <section className="kosmo-maus-journal" data-testid="kosmo-maus-journal" aria-label="Was Claude und Kosmo getan haben">
      <div className="kosmo-maus-journal-kopf" role="group" aria-label="Verlauf filtern">
        {(['alle', ...URHEBER] as const).map((f) => (
          <button
            key={f}
            type="button"
            className="kosmo-maus-filter"
            aria-pressed={filter === f}
            data-testid={`kosmo-maus-journal-filter-${f}`}
            onClick={() => setFilter(f)}
          >
            {f === 'alle' ? 'Alle' : URHEBER_NAME[f]}
          </button>
        ))}
      </div>
      {sichtbar.length === 0 ? (
        <p className="kosmo-maus-journal-leer">Noch keine Handlung von Claude oder Kosmo auf diesem Gerät.</p>
      ) : (
        <ol className="kosmo-maus-journal-liste">
          {sichtbar.map((e, i) => (
            <li
              key={`${e.zeit}-${i}`}
              className="kosmo-maus-journal-eintrag"
              data-testid="kosmo-maus-journal-eintrag"
              data-urheber={e.urheber}
              data-ergebnis={e.ergebnis}
            >
              <span className="kosmo-maus-journal-zeit">{uhrzeit(e.zeit)}</span>
              <span className="kosmo-maus-chip" data-urheber={e.urheber}>
                {URHEBER_NAME[e.urheber]}
              </span>
              <span className="kosmo-maus-journal-text">{journalSatz(e)}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

/** Der Abschnitt in Kosmos Einstellungen: Schalter, ein Satz, das Journal. */
export function KosmoMausAbschnitt() {
  return (
    <section className="kosmo-maus-abschnitt" data-testid="kosmo-einstellungen-maus" aria-label="Mitschauen und Bedienen" {...eigen()}>
      <div className="kosmo-maus-abschnitt-titel">Mitschauen und Bedienen</div>
      <KosmoMausFreigabeSchalter vorsatz="kosmo-einstellungen" />
      <p className="kosmo-maus-hinweis">
        Bedienen heisst: mit eigenem Zeiger klicken, deiner bleibt frei. Änderungen am Projekt kommen weiter als Karte zum
        Anwenden. Die Schalter nehmen nur deine eigenen Klicks und gelten nur für dieses Gerät.
      </p>
      <p className="kosmo-maus-hinweis">
        Coop heisst: Claude oder Kosmo ändern das Projekt ohne Karte. Jeder Schritt trägt ihren Namen; du nimmst ihn im
        Verlauf zurück und hältst alle jederzeit an. Strg+Z nimmt nur deine eigenen Schritte zurück. Projekte löschen und
        Veröffentlichen bleiben bei dir. Nach einem Neustart ist der Coop aus.
      </p>
      {/* E178: die Stufe über dem Coop, ein Schalter, ab Werk aus. */}
      <VollautomatikSchalter />
      <KosmoCoopVerlauf vorsatz="kosmo-einstellungen-coop" />
      <KosmoMausJournal />
    </section>
  );
}
