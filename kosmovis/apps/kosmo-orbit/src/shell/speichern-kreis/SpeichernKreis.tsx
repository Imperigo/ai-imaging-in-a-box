import { useRef, useState } from 'react';
import { KIcon, useOverlaySchliessen } from '@kosmo/ui';
import type { AutosaveLage } from '../../state/project-vault';
import './speichern-kreis.css';

/**
 * A · Speichern als Kreis neben dem Zahnrad (Entwurf `docs/entwuerfe/palette-und-
 * speichern/pa-*`). Owner 30.09.2026: «links unten die insel mit dem speichern
 * komisch … das ist ja immer irgendwo im hintergrund … muss auch keine
 * eigenständige insel sein … vieleicht ein symbol neben den einstellungen?»
 *
 * * **Zu:** ein Kreis gleicher Bauart wie das Zahnrad; ein Punkt sagt still
 *   «gesichert». Gesichert wird bei jedem Schritt — hundertmal am Tag —, darum
 *   bewegt sich hier nichts. Nur bei einem Fehler wird der Punkt rot, und der
 *   Fehler wird laut gesagt (`role="alert"`, mit Grund — Fund F7).
 * * **Angetippt:** der Stand («Gesichert · jeder Schritt · zuletzt HH:MM») und
 *   die drei Handgriffe, die heute in der Insel unten links stehen: Sichern
 *   (.kosmo), Weitergeben (.kosmo), Projekt öffnen.
 *
 * Ein Baustein: der Integrator setzt ihn neben `island-einstellungen-kreis`
 * (`App.tsx`, nicht mein Dateikreis), reicht `autosaveLage` und die drei
 * bestehenden Wege herein und nimmt die Insel unten links weg. Die Lage
 * kommt von aussen, weil `App.tsx` sie schon haelt (`beiAutosave`) — ein
 * zweiter Hoerer erzaehlte dasselbe ein zweites Mal.
 */

/**
 * NAHTSTELLE FUER EINEN ZWEITEN WIRT (Visbox-Entscheide 115/116, 20.10.2026): Jeder Handgriff ist
 * wahlfrei — ohne Weg steht sein Knopf nicht da, statt ohne Wirkung dazustehen. Visbox sichert
 * den Render-Graph still bei jedem Schritt auf dem Heim-PC und kennt keine .kosmo-Datei; dort
 * zeigt die Karte nur den Stand. KosmoOrbit reicht alle drei Wege wie bisher.
 */
export interface SpeichernKreisProps {
  lage: AutosaveLage;
  /** «Sichern (.kosmo)» — vollstaendige Datei fuers eigene Archiv (`speichereProjektVollstaendig`). */
  onSichern?: () => void;
  /** «Weitergeben (.kosmo)» — Kopie ohne Herstellerteile (`downloadProject`). */
  onWeitergeben?: () => void;
  /** «Projekt öffnen» — eine .kosmo-Datei laden (`oeffneProjektDatei`). */
  onOeffnen?: () => void;
}

function uhrzeit(iso: string): string {
  return new Date(iso).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' });
}

/** Der Stand in Worten: Titel und Nachsatz. Dieselben Staende wie `autosaveText`. */
function stand(lage: AutosaveLage): { titel: string; nachsatz: string; name: string } {
  if (lage.stand === 'fehler') {
    const grund = lage.grund ?? 'Grund unbekannt, s. Konsole';
    const zuletzt = lage.iso ? ` · zuletzt gesichert ${uhrzeit(lage.iso)}` : '';
    return { titel: 'NICHT gesichert', nachsatz: `${grund}${zuletzt}`, name: `Speichern — NICHT gesichert: ${grund}` };
  }
  if (lage.stand === 'sichert') return { titel: 'Sichert …', nachsatz: 'jeder Schritt', name: 'Speichern — sichert gerade' };
  if (lage.iso === null) return { titel: 'Gesichert', nachsatz: 'jeder Schritt', name: 'Speichern — gesichert bei jedem Schritt' };
  return { titel: 'Gesichert', nachsatz: `jeder Schritt · zuletzt ${uhrzeit(lage.iso)}`, name: `Speichern — gesichert, zuletzt ${uhrzeit(lage.iso)}` };
}

export function SpeichernKreis({ lage, onSichern, onWeitergeben, onOeffnen }: SpeichernKreisProps) {
  const [offen, setOffen] = useState(false);
  const wurzelRef = useRef<HTMLDivElement | null>(null);
  useOverlaySchliessen(wurzelRef, () => setOffen(false), { esc: true, aussenklick: true });
  const s = stand(lage);
  const handgriff = (fn: () => void) => () => {
    setOffen(false);
    fn();
  };

  return (
    <div ref={wurzelRef} className="spk-wurzel">
      <button
        type="button"
        className={`spk-kreis${lage.stand === 'fehler' ? ' spk-kreis--fehler' : ''}${offen ? ' spk-kreis--offen' : ''}`}
        data-testid="speichern-kreis"
        aria-label={s.name}
        aria-expanded={offen}
        aria-controls="speichern-kreis-karte"
        onClick={() => setOffen((o) => !o)}
      >
        <KIcon name="speichern" size={16} />
        <span className="spk-punkt" data-testid="speichern-kreis-punkt" data-stand={lage.stand} aria-hidden="true" />
      </button>
      {/* Laut nur beim Fehler: die Meldung steht immer im Baum (sonst liest ein
          Vorlesegeraet den Wechsel nicht), leer, solange alles gesichert ist. */}
      <span className="k-nur-sr" data-testid="speichern-kreis-meldung" role="alert">
        {lage.stand === 'fehler' ? s.name : ''}
      </span>
      {offen && (
        <section id="speichern-kreis-karte" className="spk-karte" data-testid="speichern-kreis-karte" aria-label="Speichern">
          <div className="spk-kopf">
            <span className="spk-punkt spk-punkt--frei" data-stand={lage.stand} aria-hidden="true" />
            <span className="spk-titel">{s.titel}</span>
            <span className="spk-nachsatz">{s.nachsatz}</span>
          </div>
          {onSichern && (
            <button type="button" className="spk-zeile" data-testid="speichern-kreis-sichern" onClick={handgriff(onSichern)}>
              <b>Sichern (.kosmo)</b>
              <span>Vollständige Datei für das eigene Archiv</span>
            </button>
          )}
          {onWeitergeben && (
            <button type="button" className="spk-zeile" data-testid="speichern-kreis-weitergeben" onClick={handgriff(onWeitergeben)}>
              <b>Weitergeben (.kosmo)</b>
              <span>Eine Kopie für jemand anderen — ohne Herstellerteile</span>
            </button>
          )}
          {onOeffnen && (
            <button type="button" className="spk-zeile" data-testid="speichern-kreis-oeffnen" onClick={handgriff(onOeffnen)}>
              <b>Projekt öffnen</b>
              <span>Eine .kosmo-Datei laden</span>
            </button>
          )}
        </section>
      )}
    </div>
  );
}
