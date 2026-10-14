import { useEffect, useSyncExternalStore } from 'react';
import { KSelect } from '@kosmo/ui';
import {
  abonniereSkizzen,
  aktualisiereSkizzen,
  holeSkizzenBild,
  SKIZZE_LEER_SATZ,
  SKIZZE_NEUESTE,
  SKIZZE_OHNE_WIRT_SATZ,
  skizzenName,
  skizzenStand,
  waehleSkizze,
} from './skizze-quelle';

/**
 * Der Körper des Knotens «Skizze vom iPad» (Owner-Entscheide 95/95a der Visbox, Blatt 25).
 *
 * **Ohne Wirt** (KosmoOrbit) ein ruhiger Satz: Skizzen vom iPad gibt es in Visbox.
 *
 * **Mit Wirt** (`registriereSkizzenQuelle`, Visbox) eine kleine Auswahl — «neueste» (Vorgabe,
 * nimmt von selbst die zuletzt in die Mappe gelegte) oder eine ältere — und darunter das
 * Daumenbild der geltenden Skizze. Die Wahl ist ein Knoten-Parameter (`skizze`) und geht über
 * `vis.nodeParametrieren`, ist also rückgängig machbar wie jeder Parameter. Die Liste wird beim
 * Erscheinen des Knotens gelesen, beim Öffnen der Auswahl und wenn das Fenster wieder nach
 * vorne kommt (vom iPad zurück an den Rechner) — nicht laufend, denn die Antwort der Mappe
 * rechnet am Heim-PC jedes Mal den Umriss des Modells mit.
 *
 * Eine Höhe für alle Zustände (`KOERPER_H.skizzeIpad`), damit der Knoten nicht springt.
 */
export function SkizzeKnotenKoerper({ wahl, onWahl }: { wahl: string; onWahl: (wahl: string) => void }) {
  const { quelle, liste, laedt, fehler } = useSyncExternalStore(abonniereSkizzen, skizzenStand, skizzenStand);
  const gewaehlt = waehleSkizze(liste, wahl);

  useEffect(() => {
    if (!quelle) return undefined;
    void aktualisiereSkizzen();
    const wiederVorne = () => void aktualisiereSkizzen();
    window.addEventListener('focus', wiederVorne);
    return () => window.removeEventListener('focus', wiederVorne);
  }, [quelle]);

  // Das Bild selbst holen, damit Vergleich und Blatt es haben, sobald eine Linie liegt.
  const gewaehltName = gewaehlt?.name;
  useEffect(() => {
    if (quelle && gewaehltName) void holeSkizzenBild(gewaehltName);
  }, [quelle, gewaehltName]);

  if (!quelle) {
    return (
      <div className="vis-skizze" data-testid="skizze-knoten" data-stand="ohne-wirt">
        <div className="vis-skizze-satz vis-skizze-flaeche" data-testid="skizze-satz">
          {SKIZZE_OHNE_WIRT_SATZ}
        </div>
      </div>
    );
  }

  if (liste === null || (liste.length === 0 && fehler)) {
    return (
      <div className="vis-skizze" data-testid="skizze-knoten" data-stand={fehler ? 'fehler' : 'liest'}>
        <div
          className={`vis-skizze-satz vis-skizze-flaeche${fehler ? ' vis-skizze-satz--fehler' : ''}`}
          data-testid="skizze-satz"
          {...(fehler ? { role: 'alert' } : {})}
        >
          {fehler ?? (laedt ? 'Die Skizzen der Mappe werden gelesen …' : 'Die Skizzen der Mappe sind noch nicht gelesen.')}
        </div>
      </div>
    );
  }

  if (liste.length === 0) {
    return (
      <div className="vis-skizze" data-testid="skizze-knoten" data-stand="leer">
        <div className="vis-skizze-satz vis-skizze-flaeche" data-testid="skizze-satz">
          {SKIZZE_LEER_SATZ}
        </div>
      </div>
    );
  }

  const neueste = liste[0]!;
  const fehltGewaehlte = wahl !== SKIZZE_NEUESTE && !gewaehlt;
  return (
    <div
      className="vis-skizze"
      data-testid="skizze-knoten"
      data-stand={fehltGewaehlte ? 'fehlt' : 'da'}
      onPointerDown={(e) => e.stopPropagation()}
    >
      <KSelect
        size="sm"
        value={wahl}
        data-testid="skizze-wahl"
        aria-label="Welche Skizze"
        onChange={(e) => onWahl(e.target.value)}
        onFocus={() => void aktualisiereSkizzen()}
        onPointerDown={(e) => e.stopPropagation()}
        className="vis-node-select-voll"
      >
        <option value={SKIZZE_NEUESTE}>{`neueste — ${skizzenName(neueste)}`}</option>
        {liste.map((s) => (
          <option key={s.name} value={s.name}>
            {skizzenName(s)}
          </option>
        ))}
        {fehltGewaehlte && <option value={wahl}>{`${wahl} (nicht mehr in der Mappe)`}</option>}
      </KSelect>
      {gewaehlt ? (
        <img
          src={quelle.bildUrl(gewaehlt.name)}
          alt={`Skizze ${skizzenName(gewaehlt)}`}
          data-testid="skizze-bild"
          className="vis-img-full vis-skizze-bild vis-skizze-flaeche"
        />
      ) : (
        <div className="vis-skizze-satz vis-skizze-flaeche" data-testid="skizze-satz">
          Diese Skizze liegt nicht mehr in der Mappe — «neueste» wählen oder eine andere.
        </div>
      )}
    </div>
  );
}
