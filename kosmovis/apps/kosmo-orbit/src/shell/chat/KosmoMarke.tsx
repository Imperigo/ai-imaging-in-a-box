import './kosmo-c0-kopf.css';

export interface KosmoMarkeProps {
  /** «lokal» oder «Cloud» — wo das Modell rechnet. */
  readonly ort: string;
  readonly modell: string;
  readonly verbunden: boolean;
  /** R37 (L6-01): «verbunden» nur nach echter Modellantwort, «bereit» bei erreichbarem Modell. Ohne Angabe wie bisher. */
  readonly wort?: 'verbunden' | 'bereit' | 'nicht verbunden';
}

/**
 * C0 (Bild k1) — Verbindung und Modell als EINE Marke in der Kopfzeile:
 * «lokal · <Modell> · verbunden». Reine Anzeige; jeder Wert kommt aus
 * `KosmoPanel.tsx` (`motorInfo`), dieselbe Quelle wie die Leiste (C1).
 * Einzeilig (Bild k1); bei Platzmangel kuerzt nur der Modellname.
 */
export function KosmoMarke({ ort, modell, verbunden, wort }: KosmoMarkeProps) {
  // L71: «bereit» (Modell erreichbar, noch keine echte Antwort) hat einen eigenen Punkt — einen Ring
  // statt der vollen Scheibe; vorher leuchtete er wie «verbunden».
  const zustand = wort ?? (verbunden ? 'verbunden' : 'nicht verbunden');
  const punkt = zustand === 'bereit' ? ' kp-marke-punkt--bereit' : zustand === 'verbunden' ? '' : ' kp-marke-punkt--getrennt';
  return (
    <span className="kp-marke" data-testid="kp-marke" data-verbunden={verbunden ? 'ja' : 'nein'} data-zustand={zustand}>
      <span className={`kp-marke-punkt${punkt}`} data-testid="kp-marke-punkt" aria-hidden="true" />
      {/* Nur der Modellname darf kuerzen («…»), wenn die Kopfreihe zu schmal
          ist: ein langer Name schob sonst «Schliessen» aus dem Fenster
          (gesehen bei 1400×900, Paket c3-plan). Ort und Verbindung bleiben
          immer lesbar; der Text im DOM bleibt wortgleich. */}
      <span className="kp-marke-text">
        <span className="kp-marke-fest">{`${ort} · `}</span>
        <span className="kp-marke-modell">{modell}</span>
        <span className="kp-marke-fest">{` · ${zustand}`}</span>
      </span>
    </span>
  );
}
