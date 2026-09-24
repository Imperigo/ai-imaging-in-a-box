import { Component, type ReactNode } from 'react';
import { KButton } from './components';

/**
 * KFehlerzone (V1-Finish P1) — Error-Boundary je Station: ein Absturz in
 * einem Modul zeigt eine Werkplan-Fehlerkarte statt die App weiss zu
 * reissen. «Neu laden» remountet nur die Zone; die Diagnose hilft weiter.
 */
export class KFehlerzone extends Component<
  { bereich: string; onDiagnose?: () => void; children: ReactNode },
  { fehler: Error | null; anlauf: number }
> {
  override state = { fehler: null as Error | null, anlauf: 0 };

  static getDerivedStateFromError(fehler: Error) {
    return { fehler };
  }

  override componentDidCatch(fehler: Error): void {
    // bewusst geloggt — die Diagnose-Seite liest die Konsole des Betriebs
    console.error(`[${this.props.bereich}]`, fehler);
  }

  override render() {
    if (!this.state.fehler) {
      // key erzwingt beim Neuladen einen echten Remount der Zone
      return <div key={this.state.anlauf} style={{ display: 'contents' }}>{this.props.children}</div>;
    }
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 260, padding: 24 }}>
        <div className="k-karte" data-testid="fehlerzone" style={{ background: 'var(--k-raised)', padding: '18px 20px', maxWidth: 520, display: 'grid', gap: 10 }}>
          <div className="k-titel" style={{ fontSize: 13, fontWeight: 'var(--k-gewicht-stark)', color: 'var(--k-danger)' }}>
            {this.props.bereich} ist auf einen Fehler gelaufen
          </div>
          <div style={{ fontFamily: 'var(--k-font-mono)', fontSize: 12, color: 'var(--k-ink-soft)', overflowWrap: 'anywhere' }}>
            {this.state.fehler.message}
          </div>
          <div style={{ fontSize: 12.5, color: 'var(--k-ink-faint)' }}>
            Dein Projekt ist sicher — der Tresor speichert jede Änderung. Neu laden versucht es nochmal.
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <KButton
              size="sm"
              tone="accent"
              data-testid="fehlerzone-neuladen"
              onClick={() => this.setState((s) => ({ fehler: null, anlauf: s.anlauf + 1 }))}
            >
              Neu laden
            </KButton>
            {this.props.onDiagnose && (
              <KButton size="sm" tone="ghost" onClick={this.props.onDiagnose}>
                Diagnose öffnen
              </KButton>
            )}
          </div>
        </div>
      </div>
    );
  }
}

/** KLade — einheitlicher Ladezustand (Messrahmen-Verwandter, mono, ruhig). */
export function KLade({ text = 'lädt …', height = 120 }: { text?: string; height?: number | string }) {
  return (
    <div
      data-testid="lade"
      className="k-lade"
      style={{
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 10,
        fontFamily: 'var(--k-font-mono)',
        fontSize: 11.5,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        color: 'var(--k-ink-faint)',
      }}
    >
      <span aria-hidden className="k-lade-punkt" />
      {text}
    </div>
  );
}
