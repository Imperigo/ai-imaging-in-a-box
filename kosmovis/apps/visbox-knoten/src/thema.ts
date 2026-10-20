/**
 * Visbox-eigen — das Thema der Knotenansicht wie in KosmoOrbit (Kopfteile, Entscheid 116 (3),
 * 20.10.2026: «dunkles Thema wie KosmoOrbit, umschaltbar»).
 *
 * KosmoOrbit setzt `document.documentElement.dataset.theme` und `dataset.akzent` in `App.tsx`
 * (Vorgabe ohne gemerkte Wahl: «orbit», der dunkle «Kosmos»; Akzent «tusche») und merkt beides in
 * `localStorage` (`kosmo.thema`, `kosmo.akzent`). Dieselben Schlüssel und Vorgaben hier — gesetzt
 * **vor dem ersten Bild**, sonst blitzt die helle Fläche auf.
 *
 * Umgeschaltet wird über die Mac-App (Menü «Darstellung», `window.visboxWirt.lage({thema})`) und seit
 * S4 in der Einstellungs-Insel («Darstellung», wortgleich aus KosmoOrbit). Das Webfenster hat keinen
 * bleibenden Speicher; die App merkt die Wahl über den Neustart hinaus (`merke`, `wirt-bruecke.ts`).
 */
import type { ThemeName } from '@kosmo/ui';

export const THEMA_SCHLUESSEL = 'kosmo.thema';
export const AKZENT_SCHLUESSEL = 'kosmo.akzent';
export const THEMA_VORGABE: ThemeName = 'orbit';
export const AKZENT_VORGABE = 'tusche';

function lies(schluessel: string): string | null {
  try {
    return localStorage.getItem(schluessel);
  } catch {
    return null;
  }
}

function schreib(schluessel: string, wert: string): void {
  try {
    localStorage.setItem(schluessel, wert);
  } catch {
    // Ohne Speicher gilt die Wahl bis zum Neuladen.
  }
}

/** Das gemerkte Thema; «ink» (alt, in KosmoOrbit entfernt) gilt als «orbit» wie dort. */
export function gemerktesThema(): ThemeName {
  const t = lies(THEMA_SCHLUESSEL);
  return t === 'paper' ? 'paper' : THEMA_VORGABE;
}

/** Vor dem ersten Bild: Thema und Akzent an `<html>`. */
export function legeThema(wurzel: HTMLElement = document.documentElement): ThemeName {
  const thema = gemerktesThema();
  wurzel.dataset.theme = thema;
  wurzel.dataset.akzent = lies(AKZENT_SCHLUESSEL) ?? AKZENT_VORGABE;
  return thema;
}

/** Ein anderes Thema (von der App) — gesetzt und gemerkt wie in KosmoOrbit. */
export function setzeThema(thema: ThemeName, wurzel: HTMLElement = document.documentElement): void {
  wurzel.dataset.theme = thema;
  schreib(THEMA_SCHLUESSEL, thema);
}

/** Ein anderer Akzent (Einstellungs-Insel) — gesetzt und gemerkt wie in KosmoOrbit. */
export function setzeAkzent(akzent: string, wurzel: HTMLElement = document.documentElement): void {
  wurzel.dataset.akzent = akzent;
  schreib(AKZENT_SCHLUESSEL, akzent);
}

/** Thema und Akzent, wie sie gerade an `<html>` stehen. */
export function jetzigeDarstellung(wurzel: HTMLElement = document.documentElement): { thema: ThemeName; akzent: string } {
  return { thema: wurzel.dataset.theme === 'paper' ? 'paper' : 'orbit', akzent: wurzel.dataset.akzent ?? AKZENT_VORGABE };
}
