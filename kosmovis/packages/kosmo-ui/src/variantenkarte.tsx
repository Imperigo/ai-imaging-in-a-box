import type { HTMLAttributes, ReactNode } from 'react';
import { KIcon } from './icons';

/**
 * KVariantenKarte (v0.8.0B / P2, Spez §3 B-45) — Kuratier-Karte für
 * generierte Varianten (Blaupause: 0.7.5 Kosmo-Viz-Handoff, «Kuratierung»).
 * Seitenverhältnis 4/3, ID-Pill auf `rgba(5,6,8,.6)` + `blur(6px)`,
 * RENDERT/FAVORIT-Badges, Scan-Streifen NUR bei `laeuft`, gewählt = 1.5px
 * Akzent + `--k-glow-cyan-sm`. Einsatz in KuratierFlaeche ist W5-Scope, hier
 * nur Komponente + Tests.
 *
 * `rgba(5,6,8,.6)` ist ein wörtlicher, THEME-INVARIANTER Spec-Wert (§3/VIZ-
 * Handoff): die ID-/Badge-Chips liegen auf einem gerenderten Bild-Thumbnail
 * (nicht auf einer UI-Fläche) — ein Dunkel-Scrim über einem Renderbild ist
 * unabhängig vom aktiven Theme sinnvoll, genau wie das Planblatt (Gesetz 3)
 * theme-invariant bleibt, nur mit umgekehrtem Vorzeichen (das Bild ist
 * immer ein Renderbild, nie Papier).
 */
export interface KVariantenKarteProps extends Omit<HTMLAttributes<HTMLDivElement>, 'id' | 'children'> {
  id: string;
  /** Bild-URL fürs Vorschau-Thumbnail (CSS `background-image`). */
  bild?: string;
  /** RENDERT-Badge + Scan-Streifen-Animation. */
  laeuft?: boolean;
  /** FAVORIT-Badge (nur sichtbar, wenn NICHT `laeuft` — running sticht Favorit). */
  favorit?: boolean;
  /** 1.5px Akzent-Rand + Glow (Auswahl-Codierung, B-141). */
  gewaehlt?: boolean;
  /** Farbe der ID-Pill-Schrift (z.B. Rollenfarbe der Quelle). */
  idFarbe?: string;
  onVerwerfen?: () => void;
  onInsProjekt?: () => void;
  /** Fusszeile (z.B. Kurzname/Massangaben) — optional. */
  children?: ReactNode;
  'data-testid'?: string;
}

export function KVariantenKarte({
  id,
  bild,
  laeuft = false,
  favorit = false,
  gewaehlt = false,
  idFarbe,
  onVerwerfen,
  onInsProjekt,
  children,
  className,
  ...rest
}: KVariantenKarteProps) {
  const badge = laeuft ? 'RENDERT' : favorit ? 'FAVORIT' : undefined;
  const klassen = ['k-variantenkarte', gewaehlt ? 'k-variantenkarte--gewaehlt' : '', className].filter(Boolean).join(' ');
  return (
    <div className={klassen} {...rest}>
      <div className="k-variantenkarte-bild" style={bild !== undefined ? { backgroundImage: `url(${bild})` } : undefined}>
        {laeuft && <div className="k-variantenkarte-scan" aria-hidden="true" />}
        <div className="k-variantenkarte-embleme">
          <span className="k-variantenkarte-id" style={idFarbe !== undefined ? { color: idFarbe } : undefined}>
            {id}
          </span>
          {badge !== undefined && (
            <span className={`k-variantenkarte-badge${laeuft ? ' k-variantenkarte-badge--laeuft' : ' k-variantenkarte-badge--favorit'}`}>
              {badge}
            </span>
          )}
        </div>
        {(onVerwerfen !== undefined || onInsProjekt !== undefined) && (
          <div className="k-variantenkarte-aktionen">
            {onVerwerfen !== undefined && (
              <button type="button" aria-label="Verwerfen" className="k-variantenkarte-aktion" onClick={onVerwerfen}>
                <KIcon name="schliessen" size={14} />
              </button>
            )}
            {onInsProjekt !== undefined && (
              <button type="button" aria-label="Ins Projekt" className="k-variantenkarte-aktion" onClick={onInsProjekt}>
                <KIcon name="ordner" size={14} />
              </button>
            )}
          </div>
        )}
      </div>
      {children !== undefined && <div className="k-variantenkarte-fuss">{children}</div>}
    </div>
  );
}
