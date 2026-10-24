/**
 * **@kosmo/insel** — Bausteine der Insel-Oberfläche ohne App-Stores, die
 * gemeinsame Quelle für KosmoOrbit und Visbox (Owner-Entscheid «Visbox-
 * Knotenansicht immer identisch zur KosmoOrbit-Vis-Oberfläche»; Abstimmung mit
 * KosmoVis und dem Integrator am 20.10.2026). Was der Wirt beisteuert, kommt
 * über Props oder eine Quelle (`ErzaehlQuelle`), nie über einen Store-Import.
 *
 * Schnitt 1: Navi-Insel, Erzählzeile, Tastennamen, Name des Assistenten. Hülle, Kopf und Pille folgen.
 * Privat wie alle Pakete hier (kein Lizenzfeld); Visbox bezieht es erst nach
 * dem Owner-Entscheid zu Lizenz und Veröffentlichung.
 */
export * from './NaviInsel';
export * from './erzaehl-zeile';
export { ErzaehlZeile, type ErzaehlQuelle } from './ErzaehlZeile';
export { istMac, kuerzel, taste } from './tastennamen';
export { KOSMO_NAME_VORGABE, kosmoName, registriereKosmoName } from './kosmo-name';
