import { useClaudeAnschluss } from '../../state/claude-anschluss';
import { useKosmoCoop } from '../../state/kosmo-coop';

/**
 * Nr. 55 «Claude im Bild», Baustein 4 (Owner-Entscheid 20.10.2026: ja) — solange
 * die Vollautomatik läuft und Claude verbunden ist, trägt das Fenster einen feinen
 * Rahmen in Claudes Gold (`--k-rolle-agent`). Er fängt keinen Zeiger und deckt
 * nichts ab; die Anzeige «Vollautomatik · Alle anhalten» unten links bleibt der
 * Ort zum Beenden. Endet die Vollautomatik oder die Verbindung, ist er weg.
 */
export function ClaudeFensterRahmen() {
  const voll = useKosmoCoop((z) => z.vollautomatik);
  const verbunden = useClaudeAnschluss((z) => z.verbunden);
  if (!voll || !verbunden) return null;
  return <div className="claude-fenster-rahmen" data-testid="claude-fenster-rahmen" aria-hidden="true" />;
}
