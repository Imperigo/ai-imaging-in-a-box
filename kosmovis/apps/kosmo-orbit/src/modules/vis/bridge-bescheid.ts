/**
 * P-BESCHEID (v0.9.33, B43 Teil 2 §10) — **ein 401 ist kein Offline.**
 *
 * Der Home-PC-Worker hat gemessen: die App meldet «RENDER FEHLER — Bridge
 * nicht erreichbar (Offline)», während `curl :8600/health` mit 200
 * antwortet und die Render-Endpunkte 401 geben, weil die Web-Instanz
 * keinen Bridge-Token hat. **Die Meldung schickt den Nutzer die Bridge
 * neustarten, statt den Token zu prüfen.**
 *
 * **Und die Nachprüfung zeigt, warum die App das bisher nicht besser
 * konnte:** sie hat den 401 gar nicht gesehen. Wird eine abgelehnte
 * Antwort vom Browser wegen fehlender CORS-Freigabe verworfen, kommt beim
 * `fetch` kein Status an, sondern ein `TypeError` «Failed to fetch» — für
 * die App nicht von einem toten Server unterscheidbar. Die alte Meldung
 * war also nicht nachlässig, sondern **blind**.
 *
 * **Die Reparatur ist darum keine bessere Formulierung, sondern eine
 * zweite Messung:** `/health` ist tokenfrei und CORS-offen. Antwortet es,
 * während der Render-Ruf scheitert, LÄUFT die Bridge — und der Fehler
 * liegt am Token oder an der CORS-Freigabe der geschützten Route, nicht an
 * der Erreichbarkeit. Antwortet es nicht, ist «offline» richtig.
 *
 * Diese Datei enthält nur den ENTSCHEID als reine Funktion — ohne `fetch`,
 * ohne DOM, damit jeder Fall geprüft werden kann, statt am Gerät
 * nachgestellt zu werden.
 */

/**
 * C3 (Splat-Abnahme 06.10.2026) — DIE EINE STELLE für den Token-Satz.
 *
 * Am Heimrechner stand ohne Token «Brücke nicht erreichbar (Load failed)»,
 * obwohl die Brücke lief. Grund (nachgelesen in der Brücke, nur gelesen): die
 * Token-Wache ist die äusserste Schicht und antwortet mit 401, BEVOR die
 * CORS-Schicht ihren Kopf anhängen kann. Der Browser verwirft diese Antwort
 * und meldet der App bloss einen Netzfehler («Load failed» in WebKit,
 * «Failed to fetch» in Chromium). Die App sieht den 401 also nur, wenn er
 * mit CORS-Kopf ankommt (z.B. über einen Vorschalt-Dienst), sonst nicht.
 *
 * Darum drei Sätze, und jeder verweist auf denselben Ort, an dem der Token
 * eingetragen wird. Wer den Verweis im Text trägt, bekommt den Knopf
 * «Einstellungen öffnen» dazu (`brauchtHomeServerKnopf`,
 * `shell/homeserver-knopf.ts`) — der Knopf hängt am Verweis, nicht an einer
 * zweiten Liste von Fällen.
 */
export const HOMESERVER_VERWEIS = 'Einstellungen ▸ HomeServer';
/** Ein gesehener 401/403, und in den Einstellungen steht kein Token. */
export const BRIDGE_TOKEN_FEHLT_SATZ = `Bridge-Token fehlt — in ${HOMESERVER_VERWEIS} eintragen`;
/** Ein gesehener 401/403, obwohl ein Token eingetragen ist. */
export const BRIDGE_TOKEN_FALSCH_SATZ = `Bridge-Token passt nicht — in ${HOMESERVER_VERWEIS} prüfen`;
/** Netzfehler ohne Gegenprobe: die App kann «weg» und «Token fehlt» nicht
 *  sicher trennen und nennt darum beides (Regel 5, Ehrlichkeit). */
export const BRIDGE_WEG_ODER_TOKEN_FEHLT_SATZ = `Brücke nicht erreichbar oder Bridge-Token fehlt — in ${HOMESERVER_VERWEIS} prüfen`;
/** Dasselbe mit eingetragenem Token. */
export const BRIDGE_WEG_ODER_TOKEN_FALSCH_SATZ = `Brücke nicht erreichbar oder Bridge-Token passt nicht — in ${HOMESERVER_VERWEIS} prüfen`;
/** Ein 401/403 an einer Stelle, die den Token-Stand nicht kennt (z.B. ein
 *  laufender Job, der schon angelegt war). */
export const BRIDGE_TOKEN_FEHLT_ODER_FALSCH_SATZ = `Bridge-Token fehlt oder passt nicht — in ${HOMESERVER_VERWEIS} prüfen`;

/** Was die App über einen gescheiterten Ruf zum Token sagen kann. */
export interface TokenLage {
  /** Der `fetch` selbst ist geplatzt — kein Statuscode gesehen. */
  netzfehler: boolean;
  status?: number | undefined;
  tokenGesetzt: boolean;
  /** Gegenprobe auf `/health` (tokenfrei): `true` = Brücke läuft,
   *  `false` = auch sie schweigt, `undefined` = nicht geprüft. */
  healthErreichbar?: boolean | undefined;
}

/**
 * Der Token-Satz zur Lage, oder `null`, wenn der Token sicher nicht die
 * Ursache ist (anderer HTTP-Status, oder die Brücke ist gemessen weg).
 */
export function tokenSatz(lage: TokenLage): string | null {
  if (lage.status === 401 || lage.status === 403) {
    return lage.tokenGesetzt ? BRIDGE_TOKEN_FALSCH_SATZ : BRIDGE_TOKEN_FEHLT_SATZ;
  }
  if (!lage.netzfehler) return null;
  if (lage.healthErreichbar === true) return lage.tokenGesetzt ? BRIDGE_TOKEN_FALSCH_SATZ : BRIDGE_TOKEN_FEHLT_SATZ;
  if (lage.healthErreichbar === false) return null;
  return lage.tokenGesetzt ? BRIDGE_WEG_ODER_TOKEN_FALSCH_SATZ : BRIDGE_WEG_ODER_TOKEN_FEHLT_SATZ;
}

/** Trägt der Text den Verweis auf den HomeServer-Abschnitt? Dann gehört der
 *  Knopf dazu, der dorthin springt. */
export function brauchtHomeServerKnopf(text: string): boolean {
  return text.includes(HOMESERVER_VERWEIS);
}

/** Was die App über den gescheiterten Ruf weiss, bevor sie urteilt. */
export interface BescheidLage {
  /** Der `fetch` selbst ist geplatzt (Netzfehler ODER vom Browser
   *  verworfene Antwort) — die App hat KEINEN Statuscode gesehen. */
  netzfehler: boolean;
  /** Statuscode, falls die Antwort durchkam (401/403 = Ablehnung). */
  status?: number;
  /** Ergebnis der Gegenprobe auf `/health` (tokenfrei, CORS-offen).
   *  `undefined` = nicht geprüft (dann bleibt es beim alten Urteil). */
  healthErreichbar?: boolean;
  /** Liegt ein Bridge-Token in den Einstellungen? */
  tokenGesetzt: boolean;
  /** Die Bridge-Adresse liegt vermutlich ausserhalb der CSP-Freigabe. */
  cspVerdacht: boolean;
  /** Der gescheiterte Ruf war ein SCHREIBENDER (z.B. Render-POST), der die
   *  Bruecke erreicht haben KANN. WARUM (CORS-Befund E156, 06.10.2026): ohne
   *  CORS-Freigabe fuer die App-Herkunft nimmt die Bruecke den POST an, der
   *  Browser verwirft nur die Antwort — und die Gegenprobe `/health` scheitert
   *  aus demselben Grund. «Offline» waere dann falsch und laedt zum doppelten
   *  Senden ein. */
  schreibRuf?: boolean;
}

export type BescheidArt = 'csp' | 'token-fehlt' | 'token-abgelehnt' | 'antwort-unlesbar' | 'offline' | 'roh';

export interface Bescheid {
  art: BescheidArt;
  text: string;
}

/**
 * Der Urteilsspruch über einen gescheiterten Bridge-Ruf.
 *
 * Reihenfolge der Prüfung, und jede Stufe hat einen Grund:
 *
 * 1. **CSP-Verdacht** zuerst — er erklärt den Netzfehler vollständig und
 *    ist die einzige Ursache, die die App an der eigenen Konfiguration
 *    ablesen kann (Bestand seit v0.9.21 P-E).
 * 2. **Ein gesehener 401/403** — eindeutig, kein Raten nötig.
 * 3. **Netzfehler, aber `/health` antwortet** — die Bridge läuft. Das ist
 *    der Fall aus B43 §10, und er war bisher unsichtbar.
 * 4. **Netzfehler nach einem schreibenden Ruf** (`schreibRuf`) — der Auftrag
 *    KANN angekommen sein (CORS-Befund E156): ehrlich «unklar», mit der
 *    Bitte, zuerst nachzusehen statt erneut zu senden.
 * 5. **Netzfehler und `/health` schweigt** — jetzt ist «offline» eine
 *    Messung statt einer Vermutung.
 * 6. Alles andere bleibt der Rohtext; eine erfundene Erklärung wäre
 *    schlechter als eine ehrliche Unklarheit.
 */
export function bridgeBescheid(lage: BescheidLage, rohtext: string): Bescheid {
  if (lage.netzfehler && lage.cspVerdacht) {
    return {
      art: 'csp',
      text:
        'Bridge-Adresse liegt vermutlich ausserhalb der CSP-Freigabe (nur http auf 8600/8700/11434, ' +
        'IP oder DNS-Name) — Port/Protokoll pruefen oder localhost nutzen. (Offline)',
    };
  }

  if (lage.status === 401 || lage.status === 403) {
    // Nachtrag zu auf-orbit-20260824-06.md Punkt 1: die Token-Pflicht wird
    // NICHT von der App entschieden, sondern von der Umgebungsvariable
    // KOSMO_BRIDGE_TOKEN auf dem Home-PC (`main.py:183,264` — gesetzt =
    // 401 ausser auf /health, leer = keine Pflicht). Wer nur «in den
    // Einstellungen hinterlegen» liest, kennt die halbe Wahrheit: die
    // Variable liesse sich dort ebenso gut ENTFERNEN.
    //
    // «Ein Neustart der Bridge hilft hier nicht» bleibt trotzdem wahr und
    // WOERTLICH stehen — sie gilt fuer einen Neustart OHNE eine der beiden
    // Aenderungen (Token eintragen ODER Variable entfernen). Erst WENN die
    // Variable entfernt wird, liest die Bridge sie beim naechsten Start neu
    // ein — dafuer ist ein Neustart dann Pflicht. Die beiden Saetze
    // widersprechen sich nicht: der eine sagt, was ein blosser Neustart
    // NICHT bewirkt, der andere, was zusaetzlich zum Entfernen noetig ist.
    return lage.tokenGesetzt
      ? {
          art: 'token-abgelehnt',
          text:
            `${BRIDGE_TOKEN_FALSCH_SATZ}. ` +
            `Die Bridge laeuft, hat den Ruf aber abgelehnt (${lage.status}). Der hinterlegte ` +
            'Bridge-Token passt nicht zur Variable KOSMO_BRIDGE_TOKEN auf dem Home-PC — in den Einstellungen ' +
            'den richtigen Bridge-Token hinterlegen. Ein Neustart der Bridge hilft hier nicht — wer stattdessen ' +
            'KOSMO_BRIDGE_TOKEN auf dem Home-PC entfernt, muss die Bridge danach neu starten.',
        }
      : {
          art: 'token-fehlt',
          // UI-Befund C3: zuerst der Satz, der sagt, WAS zu tun ist und WO
          // (Einstellungen, Abschnitt «HomeServer», Feld «Bridge-Token»);
          // die Erklaerung zur Variable folgt danach.
          text:
            `${BRIDGE_TOKEN_FEHLT_SATZ}. ` +
            `Die Bridge laeuft, verlangt aber einen Token (${lage.status}), weil auf dem Home-PC die Variable ` +
            'KOSMO_BRIDGE_TOKEN gesetzt ist. Ein Neustart ' +
            'der Bridge hilft hier nicht — wer stattdessen KOSMO_BRIDGE_TOKEN auf dem Home-PC entfernt, muss ' +
            'die Bridge danach neu starten.',
        };
  }

  if (lage.netzfehler && lage.healthErreichbar === true) {
    // Der Fall, den die App bisher als «Offline» ausgegeben hat. Sie kann
    // hier NICHT zwischen «Token fehlt» und «CORS auf der geschuetzten
    // Route» unterscheiden — und sagt das, statt sich fuer eines der
    // beiden zu entscheiden. Eine Vermutung, die als Tatsache auftritt,
    // hat den Owner in v0.9.30 einen Abend gekostet.
    // Dieselbe Aufloesung wie oben bei 401/403, s. Kommentar dort: «Nicht
    // die Bridge neustarten» bleibt WOERTLICH stehen (gilt fuer den Weg
    // «Token pruefen», kein Neustart noetig) — der letzte Satz nennt den
    // zweiten Weg (Variable entfernen), fuer den ein Neustart Pflicht ist.
    return {
      art: lage.tokenGesetzt ? 'token-abgelehnt' : 'token-fehlt',
      text:
        `${lage.tokenGesetzt ? BRIDGE_TOKEN_FALSCH_SATZ : BRIDGE_TOKEN_FEHLT_SATZ}. ` +
        'Die Bridge ANTWORTET (Health-Probe erfolgreich) — der Render-Ruf wurde trotzdem abgewiesen. ' +
        (lage.tokenGesetzt
          ? 'Wahrscheinlich passt der hinterlegte Bridge-Token nicht zur Variable KOSMO_BRIDGE_TOKEN auf dem Home-PC, '
          : 'Wahrscheinlich fehlt der Bridge-Token in den Einstellungen — auf dem Home-PC ist KOSMO_BRIDGE_TOKEN gesetzt, ') +
        'oder die geschuetzte Route gibt keine CORS-Freigabe zurueck. Nicht die Bridge neustarten — den Token pruefen. ' +
        'Wer stattdessen KOSMO_BRIDGE_TOKEN auf dem Home-PC entfernt, muss die Bridge danach neu starten.',
    };
  }

  if (lage.netzfehler && lage.schreibRuf) {
    // CORS-Befund E156: der POST kann die Bruecke erreicht haben, nur die
    // Antwort war fuer die App nicht lesbar. Kein «nicht erreichbar» — das
    // waere eine Behauptung ohne Messung und fuehrt zum doppelten Auftrag.
    return {
      art: 'antwort-unlesbar',
      text:
        'Keine lesbare Antwort von der Bridge — der Auftrag kann trotzdem angekommen sein. ' +
        'Haeufigste Ursache: die Bridge gibt der Herkunft dieser App keine CORS-Freigabe ' +
        '(KOSMO_BRIDGE_ORIGIN auf dem Home-PC). Bitte zuerst in der Auftragsliste nachsehen und nicht erneut senden; ' +
        'erst wenn dort nichts steht: laeuft die HomeStation-Bridge?',
    };
  }

  if (lage.netzfehler) {
    return {
      art: 'offline',
      text:
        lage.healthErreichbar === false
          ? 'Bridge nicht erreichbar — auch die Health-Probe antwortet nicht. Laeuft die HomeStation-Bridge? (Offline)'
          : // C3: ohne Gegenprobe ist «weg» nicht von «Token fehlt» zu trennen
            // (401 ohne CORS-Kopf) — beide Möglichkeiten, mit dem Verweis.
            `${tokenSatz(lage) ?? 'Bridge nicht erreichbar'}. Laeuft die HomeStation-Bridge? (Offline)`,
    };
  }

  return { art: 'roh', text: rohtext };
}
