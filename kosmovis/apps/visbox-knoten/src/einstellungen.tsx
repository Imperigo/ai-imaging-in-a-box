/**
 * Visbox-eigen — die Einstellungs-Insel der Knotenansicht (Plan UI-Gleichheit S4, Entscheide 115/116,
 * 20.10.2026).
 *
 * In KosmoOrbit oeffnet der Einstellungs-Kreis das zentrale Panel (`Einstellungen.tsx`). Hier steht
 * dieselbe Insel: **die Schale und drei Abschnitte wortgleich** aus `shell/einstellungen-teile.tsx`
 * (Scrim, Panel, Kopf mit Schliessen; «Darstellung», «Anzeige», «Bewegung & Klang»), in derselben
 * Reihenfolge wie dort. Wo KosmoOrbit Abschnitte hat, die Visbox fachlich nicht kennt, stehen die
 * Visbox-Abschnitte an ihrer Stelle:
 *
 *  - **Heim-PC** statt «HomeServer»: die Lage der Leitung und «Am Mac einrichten» (Bruecke `oeffne`).
 *    **Adresse und Kennwort bleiben nativ** (Entscheid 116 (6)): Das Kennwort laeuft nie durch die Seite.
 *  - **Wer rechnet?** (Inhalt wie `Rechnerwahlansicht.swift`, die Wahl ueber die Bruecke `rechner`) und
 *    **Claude über MCP** (an/aus ueber die Bruecke `claude`, der Befehl zum Verbinden) statt «Kosmo»;
 *  - **Lizenzen** statt «Modell-Lizenzen», **Neuigkeiten** statt «Funktionen & Neues».
 *
 * Was KosmoOrbit dort sonst zeigt (Phase SIA, Projekt, Paket-Ursprung, Sonne, Nutzungszeit, Leistung …)
 * steht mit Grund in `kosmovis/UI_AUSNAHMEN.json`. Alle Saetze von «Wer rechnet?» und «Claude über MCP»
 * kommen aus dem Kern der App (`Rechnerwahl`, `Claudeeinrichtung`) — hier wird nur gezeichnet.
 */
import { useEffect, useRef, useState } from 'react';
import { create } from 'zustand';
import { Hairline, KButton, KSwitch, type ThemeName } from '@kosmo/ui';
import {
  AbschnittAnzeige,
  AbschnittBewegungKlang,
  AbschnittDarstellung,
  EinstellungenSchale,
  SchalterTouchUndo,
} from '../../kosmo-orbit/src/shell/einstellungen-teile';
import { merkeEinstellungen, sende, useWirt, type RechnerwahlLage } from './wirt-bruecke';
import { jetzigeDarstellung, setzeAkzent, setzeThema } from './thema';

/** Wohin die Insel beim Oeffnen springt (der Heim-PC-Chip: «Wer rechnet?»). */
export type EinstellungsZiel = 'heimpc' | 'rechner' | 'claude';

interface Insel {
  offen: boolean;
  ziel: EinstellungsZiel | null;
}

export const useEinstellungsInsel = create<Insel>(() => ({ offen: false, ziel: null }));

export function oeffneEinstellungen(ziel: EinstellungsZiel | null = null): void {
  useEinstellungsInsel.setState({ offen: true, ziel });
}

export function schliesseEinstellungen(): void {
  useEinstellungsInsel.setState({ offen: false, ziel: null });
}

/** Die Zeilen von «Lizenzen» — jede steht ausfuehrlich im NOTICE (Probe `test_kosmovis_ui_gleichheit.py`). */
export const LIZENZ_ZEILEN: readonly string[] = [
  'Visbox steht unter der Apache-Lizenz 2.0 — der ganze eigene Code, auch diese Knotenansicht.',
  'Blender (GPL) und IfcOpenShell (LGPL) laufen nur als eigene Programme am Heim-PC und werden nie eingebaut.',
  'Bildmodell der Vorgabe: Z-Image-Turbo (Apache-2.0). Qwen-Image-2.1 ist bestellbar, seine Lizenz ist noch offen — ein Bild damit ist nicht zur Veröffentlichung freigegeben.',
  'Der Assistent rechnet mit qwen3:14b (Apache-2.0) am Heim-PC.',
  'Schriften unter der SIL Open Font License (IBM Plex, Instrument Serif, Lato, PT Sans Narrow); Texturen und Himmelsbilder gemeinfrei (CC0).',
  'Jede Komponente mit Lizenz und Herkunft steht in der Datei NOTICE des Programms.',
];

/** «Heim-PC»: die Lage der Leitung, und wo man ihn einrichtet. */
function AbschnittHeimPc() {
  const rechner = useWirt((z) => z.rechner);
  const leitung = useWirt((z) => z.leitung);
  const sperre = useWirt((z) => z.sperre);
  return (
    <section data-testid="einstellungen-heimpc" className="orbit065-einstellungen-sektion">
      <div className="orbit065-einstellungen-sektionstitel">Heim-PC</div>
      <div className="es-feld-block">
        <span className="es-feld-label">Lage</span>
        <span className="es-feld-hinweis" data-testid="einstellungen-heimpc-lage" data-ton={rechner?.ton ?? 'aus'}>
          {rechner?.text ?? 'Heim-PC · …'}
        </span>
        {leitung && <span className="es-feld-hinweis">{leitung}</span>}
        {sperre && <span className="es-feld-hinweis">{sperre}</span>}
      </div>
      <div className="es-feld-block">
        <KButton size="sm" tone="quiet" data-testid="einstellungen-heimpc-einrichten" onClick={() => sende({ art: 'oeffne', ziel: 'einrichten' })}>
          Am Mac einrichten
        </KButton>
        <span className="es-feld-hinweis">
          Adresse und Kennwort des Heim-PC stehen in der Visbox-App am Mac (Schlüsselbund) — das Kennwort kommt nie in diese Ansicht.
        </span>
      </div>
    </section>
  );
}

/** «Wer rechnet?» — je Arbeit zwei Felder, gewählt, gesperrt mit Grund (`Rechnerwahlansicht.swift`). */
function AbschnittRechner({ wahl }: { wahl: RechnerwahlLage | null }) {
  return (
    <section data-testid="einstellungen-rechner" className="orbit065-einstellungen-sektion">
      <div className="orbit065-einstellungen-sektionstitel">{wahl?.titel || 'Wer rechnet?'}</div>
      {!wahl ? (
        <span className="es-feld-hinweis" data-testid="einstellungen-rechner-ohne-app">
          «Wer rechnet?» stellst du in der Visbox-App am Mac ein.
        </span>
      ) : (
        <>
          <span className="es-feld-hinweis">{wahl.untertitel}</span>
          {wahl.arbeiten.map((a) => (
            <div key={a.arbeit} className="es-feld-block" data-testid={`einstellungen-rechner-${a.arbeit}`}>
              <span className="es-feld-label">{a.titel}</span>
              <span role="group" aria-label={a.titel} className="es-segment es-segment--umbrechen">
                {a.felder.map((f) => (
                  <button
                    key={f.ort}
                    type="button"
                    data-testid={`einstellungen-rechner-${a.arbeit}-${f.ort}`}
                    aria-pressed={f.gewaehlt}
                    disabled={!f.waehlbar}
                    onClick={() => sende({ art: 'rechner', arbeit: a.arbeit, ort: f.ort })}
                    className={`es-segment-item${f.gewaehlt ? ' es-segment-item--aktiv' : ''}`}
                  >
                    {f.titel}
                  </button>
                ))}
              </span>
              {a.felder
                .filter((f) => f.zeile !== '')
                .map((f) => (
                  <span key={f.ort} className="es-feld-hinweis">
                    {f.titel} {f.zeile}
                  </span>
                ))}
            </div>
          ))}
          <span className="es-feld-hinweis">{wahl.mcpSatz}</span>
          <span className="es-feld-hinweis">{wahl.heuteSatz}</span>
        </>
      )}
    </section>
  );
}

/** «Claude über MCP» — an/aus, der Befehl für Claude Code, was Claude bekommt. */
function AbschnittClaude() {
  const c = useWirt((z) => z.claudeMcp);
  const [kopiert, setKopiert] = useState<string | null>(null);
  if (!c) {
    return (
      <section data-testid="einstellungen-claude" className="orbit065-einstellungen-sektion">
        <div className="orbit065-einstellungen-sektionstitel">Claude über MCP</div>
        <span className="es-feld-hinweis">Claude über MCP schaltest du in der Visbox-App am Mac ein und aus.</span>
      </section>
    );
  }
  const kopiere = () => {
    const ablage = typeof navigator !== 'undefined' ? navigator.clipboard : undefined;
    if (!ablage) {
      setKopiert('Kopieren geht hier nicht — den Befehl oben markieren und kopieren.');
      return;
    }
    ablage.writeText(c.befehl).then(
      () => setKopiert('Kopiert.'),
      () => setKopiert('Kopieren geht hier nicht — den Befehl oben markieren und kopieren.'),
    );
  };
  return (
    <section data-testid="einstellungen-claude" className="orbit065-einstellungen-sektion">
      <div className="orbit065-einstellungen-sektionstitel">{c.titel}</div>
      <KSwitch
        className="es-schalter-label"
        role="switch"
        label={c.an ? 'an' : 'aus'}
        aria-label={c.titel}
        data-testid="einstellungen-claude-schalter"
        checked={c.an}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => sende({ art: 'claude', an: e.target.checked })}
      />
      <span className="es-feld-hinweis" data-testid="einstellungen-claude-satz">
        {c.satz}
      </span>
      <div className="es-feld-block">
        <span className="es-feld-label">{c.codeTitel}</span>
        <code className="es-feld-hinweis" data-testid="einstellungen-claude-befehl">
          {c.befehl}
        </code>
        <KButton size="sm" tone="quiet" data-testid="einstellungen-claude-kopieren" onClick={kopiere}>
          {c.kopieren}
        </KButton>
        {kopiert && <span className="es-feld-hinweis">{kopiert}</span>}
      </div>
      <span className="es-feld-hinweis">
        <b>{c.datenTitel}</b> {c.daten}
      </span>
      <span className="es-feld-hinweis">
        <b>{c.werkzeugeTitel}</b> {c.werkzeuge}
      </span>
      <span className="es-feld-hinweis">
        <b>{c.nurHier}</b>
      </span>
    </section>
  );
}

function AbschnittLizenzen() {
  return (
    <section data-testid="einstellungen-lizenzen" className="orbit065-einstellungen-sektion">
      <div className="orbit065-einstellungen-sektionstitel">Lizenzen</div>
      <ul className="es-neuigkeit-liste">
        {LIZENZ_ZEILEN.map((z) => (
          <li key={z}>{z}</li>
        ))}
      </ul>
    </section>
  );
}

function AbschnittNeuigkeiten() {
  const n = useWirt((z) => z.neuigkeiten);
  const version = useWirt((z) => z.version);
  const fassung = n?.fassung || version || '';
  return (
    <section data-testid="einstellungen-neuigkeiten" className="orbit065-einstellungen-sektion">
      <div className="orbit065-einstellungen-sektionstitel">Neuigkeiten</div>
      <span className="es-feld-hinweis" data-testid="einstellungen-neuigkeiten-fassung">
        {fassung ? `Diese Fassung: ${fassung}. Was sie brachte, steht im Fassungsblatt der Freigabe.` : 'Die Fassung sagt die Visbox-App am Mac.'}
      </span>
      {n?.angebot && (
        <div data-testid={`neuigkeiten-version-${n.angebot.nummer}`} className="es-neuigkeit">
          <div className="es-neuigkeit-kopf">
            <span className="es-neuigkeit-titel">Version {n.angebot.nummer} — bereit zum Aktualisieren</span>
          </div>
          <ul className="es-neuigkeit-liste">
            {n.angebot.zeilen.map((z, i) => (
              <li key={i}>{z}</li>
            ))}
          </ul>
          <KButton size="sm" tone="quiet" data-testid="einstellungen-aktualisieren" onClick={() => sende({ art: 'oeffne', ziel: 'aktualisieren' })}>
            Aktualisieren …
          </KButton>
        </div>
      )}
    </section>
  );
}

/** Die Insel selbst — gezeichnet, solange sie offen ist. */
export function VisboxEinstellungen() {
  const offen = useEinstellungsInsel((z) => z.offen);
  const ziel = useEinstellungsInsel((z) => z.ziel);
  const wahl = useWirt((z) => z.rechnerwahl);
  const [darstellung, setDarstellung] = useState(jetzigeDarstellung);
  const koerper = useRef<HTMLDivElement | null>(null);

  // DER SPRUNG ZUM ABSCHNITT (Heim-PC-Chip → «Wer rechnet?»), nach der Fokusfalle der Schale (deren
  // Effekte laufen zuerst, wie in KosmoOrbit beim Sprung zum HomeServer).
  useEffect(() => {
    if (!offen || !ziel) return;
    koerper.current?.querySelector<HTMLElement>(`[data-testid="einstellungen-${ziel}"]`)?.scrollIntoView?.({ block: 'start' });
  }, [offen, ziel]);

  useEffect(() => {
    if (offen) setDarstellung(jetzigeDarstellung());
  }, [offen]);

  if (!offen) return null;
  const setTheme = (t: ThemeName) => {
    setzeThema(t);
    setDarstellung((d) => ({ ...d, thema: t }));
  };
  const setAkzent = (a: string) => {
    setzeAkzent(a);
    setDarstellung((d) => ({ ...d, akzent: a }));
  };
  return (
    <EinstellungenSchale titel="Einstellungen" onClose={schliesseEinstellungen}>
      {/* Jede Wahl, die die Seite selbst merkt (Thema, Akzent, Anzeige, Rückgängig-Schalter), sagt
          sie danach der App — das Webfenster vergisst sie sonst beim Neuladen. */}
      <div ref={koerper} onClickCapture={() => setTimeout(() => merkeEinstellungen(), 0)} data-testid="einstellungen-visbox">
        <AbschnittHeimPc />
        <Hairline />
        <AbschnittDarstellung theme={darstellung.thema} setTheme={setTheme} akzent={darstellung.akzent} setAkzent={setAkzent} />
        <Hairline />
        <AbschnittAnzeige />
        <Hairline />
        <AbschnittBewegungKlang>
          <SchalterTouchUndo />
        </AbschnittBewegungKlang>
        <Hairline />
        <AbschnittRechner wahl={wahl} />
        <Hairline />
        <AbschnittClaude />
        <Hairline />
        <AbschnittLizenzen />
        <Hairline />
        <AbschnittNeuigkeiten />
      </div>
    </EinstellungenSchale>
  );
}
