import { useEffect } from 'react';
import { KButton } from '@kosmo/ui';
import { useKosmoFragt, type ArtFrage } from './kosmo-fragt';
import './kosmo-fragt.css';

/**
 * E2 · die Karte, mit der Kosmo nach der Art eines Dokuments fragt (Entwurf
 * `docs/entwuerfe/ipad-und-nachfrage/e2-kosmo-fragt-*`). Gebaut als Baustein:
 * der Integrator setzt sie in die Karte des Kosmo-Knopfs (`KosmoOrb`) und die
 * Zahl an den Knopf — beides nicht mein Dateikreis. Daten und Handlungen kommen
 * aus `useKosmoFragtNach()`.
 *
 * Solange die Karte steht, meldet sie, welches Dokument sie nennt; der
 * Knotenbaum markiert es (`pb-knoten--gefragt`).
 */
export function KosmoFragtKarte({
  frage,
  anzahl,
  gesamt,
  onBestimmen,
  onSpaeter,
}: {
  frage: ArtFrage;
  anzahl: number;
  /** L6-02: alle Dokumente des Projekts — die Karte fasst zusammen statt jede Datei zu nennen. */
  gesamt?: number;
  onBestimmen: () => void;
  onSpaeter: () => void;
}) {
  const zeige = useKosmoFragt((s) => s.zeige);
  useEffect(() => {
    zeige(frage.nodeId);
    return () => zeige(null);
  }, [frage.nodeId, zeige]);
  const weitere = anzahl - 1;
  return (
    <section className="kfn-karte" data-testid="kosmo-fragt-karte" aria-label="Kosmo fragt nach">
      {gesamt !== undefined && gesamt > 1 && (
        <p className="kfn-satz" data-testid="kosmo-fragt-zusammenfassung">
          {gesamt} Dokumente — bei {anzahl} kenne ich die Art nicht.
        </p>
      )}
      <p className="kfn-satz">
        Im Knotenbaum steht ein Dokument, dessen Art ich nicht kenne: <b>«{frage.dateiname}»</b>
        {weitere > 0 ? ` (und ${weitere} ${weitere === 1 ? 'weiteres' : 'weitere'})` : ''}. Magst du es einordnen? Dann kann
        ich es richtig lesen.
      </p>
      <div className="kfn-reihe">
        <KButton tone="accent" className="k-touch-ziel" data-testid="kosmo-fragt-bestimmen" onClick={onBestimmen}>
          Art bestimmen
        </KButton>
        <KButton tone="ghost" className="k-touch-ziel" data-testid="kosmo-fragt-spaeter" onClick={onSpaeter}>
          Später
        </KButton>
      </div>
    </section>
  );
}

/** Die Zahl am Kosmo-Knopf. Nichts, wenn nichts fragt — keine Null, die nach Arbeit aussieht. */
export function KosmoFragtZahl({ anzahl }: { anzahl: number }) {
  if (anzahl <= 0) return null;
  return (
    <span className="kfn-zahl" data-testid="kosmo-fragt-zahl" aria-label={`${anzahl} ${anzahl === 1 ? 'Frage' : 'Fragen'} von Kosmo`}>
      {anzahl}
    </span>
  );
}
