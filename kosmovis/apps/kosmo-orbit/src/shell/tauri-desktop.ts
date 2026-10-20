/**
 * Läuft die App als Tauri-Desktop-Build?
 *
 * Eigene kleine Datei seit E155 (06.10.2026): die Funktion stand bis dahin in
 * `cloud-login.ts` (Abo-Anmeldung der Verbindung «Anthropic», ausgebaut). Sie
 * wird von der Shell vielfach gebraucht und soll von nichts Cloud-artigem
 * abhängen.
 *
 * `__TAURI_INTERNALS__` ist das offizielle Tauri-v2-Merkmal: der IPC-Kanal,
 * den `@tauri-apps/api` unter der Haube nutzt — anders als `window.__TAURI__`
 * ist er unabhängig von der `app.withGlobalTauri`-Einstellung immer da.
 */
export function istTauriDesktop(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}
