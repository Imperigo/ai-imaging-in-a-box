/**
 * STELLVERTRETER für `apps/kosmo-orbit/src/state/home-server.ts` (KosmoOrbit, 426 Zeilen).
 *
 * Warum (E26, 24.09.2026): Das Original verwaltet die Verbindung zum Heimrechner des
 * Büros — Adresse, Sync-Kanal, Sprachmodell-Probe — und trägt dafür eine feste Adresse im
 * Code. Visbox braucht davon nur, was das Vis-Werkzeug ruft: den Schlüssel des
 * Brücken-Tokens und die `/health`-Probe der Brücke. Beides ist WÖRTLICH übernommen; die
 * feste Adresse kommt bewusst nicht mit (Regel 3: keine echten Betriebsdaten im Repo).
 */
export const BRIDGE_TOKEN_KEY = 'kosmo.bridge.token';

export const PROBE_TIMEOUT_MS = 5000;

export type KanalStatus = 'verbunden' | 'nicht-verbunden';

async function mitTimeout<T>(f: (signal: AbortSignal) => Promise<T>, ms: number = PROBE_TIMEOUT_MS): Promise<T> {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), ms);
  try {
    return await f(ctl.signal);
  } finally {
    clearTimeout(timer);
  }
}

/** Bridge `/health` — mit `X-Kosmo-Token` aus `kosmo.bridge.token`, wenn
 *  gesetzt (Serie-I-Härtung, `docs/VPN-HOMEPC-ANLEITUNG.md` §9). */
export async function pruefeBridge(bridgeUrl: string): Promise<KanalStatus> {
  if (!bridgeUrl) return 'nicht-verbunden';
  try {
    const token = (localStorage.getItem(BRIDGE_TOKEN_KEY) ?? '').trim();
    const res = await mitTimeout((signal) =>
      fetch(`${bridgeUrl.replace(/\/$/, '')}/health`, {
        signal,
        ...(token ? { headers: { 'X-Kosmo-Token': token } } : {}),
      }),
    );
    return res.ok ? 'verbunden' : 'nicht-verbunden';
  } catch {
    return 'nicht-verbunden';
  }
}
