import { ErzaehlZeile as InselErzaehlZeile, type ErzaehlQuelle } from '@kosmo/insel';
import { useClaudeAnschluss, zeigeClaudeKarten } from '../../state/claude-anschluss';
import { useClaudeTaetigkeit } from '../../state/claude-taetigkeit';
import { useKosmoCoop } from '../../state/kosmo-coop';

/**
 * Die Erzählzeile von `@kosmo/insel`, gespeist aus den Stores von KosmoOrbit:
 * offene Claude-Karten, Coop-Schritte und der Tätigkeitsstrom (R37).
 */
export function ErzaehlZeile() {
  const verbunden = useClaudeAnschluss((z) => z.verbunden);
  const vorschlaege = useClaudeAnschluss((z) => z.vorschlaege);
  const zuletztAktiv = useClaudeAnschluss((z) => z.zuletztAktiv);
  const gruppen = useKosmoCoop((z) => z.gruppen);
  // L71: jüngste Tätigkeit von Claude (R37-Strom; Kosmo-Schritte kommen über die Coop-Gruppen).
  const taetigkeit = useClaudeTaetigkeit((z) => {
    for (let i = z.eintraege.length - 1; i >= 0; i--) if (z.eintraege[i]!.urheber === 'claude') return z.eintraege[i]!;
    return null;
  });
  const letzte = gruppen.length > 0 ? gruppen[gruppen.length - 1]! : null;
  const quelle: ErzaehlQuelle = {
    verbunden,
    offeneKarten: vorschlaege,
    letzterSchritt: letzte
      ? {
          kennung: letzte.kennung,
          urheber: letzte.urheber,
          zusammenfassung: letzte.zusammenfassung,
          zeit: Date.parse(letzte.zeit),
          zurueckgenommen: letzte.zurueckgenommen,
        }
      : null,
    zuletztAktiv,
    taetigkeit,
    zeigeKarten: zeigeClaudeKarten,
  };
  return <InselErzaehlZeile quelle={quelle} />;
}
