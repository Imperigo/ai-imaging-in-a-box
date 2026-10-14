import { materialkatalog, type MaterialEintrag } from '@kosmo/data';
import { REZEPT_KLASSEN } from '@kosmo/kernel';

/**
 * P16 — Abnahmezeile 6, «Textur-Knopf»: welche Materialien die Bedienung
 * anbietet.
 *
 * NUR Materialien, deren SIA-Klasse (`materialkatalog.ts`, Feld `sia`) ein
 * echtes Rezept in `derive/textur.ts` hat (`REZEPT_KLASSEN`). Ein Material
 * OHNE Rezept (SIA-Klasse `'sonstig'`) anzubieten hiesse, einen Knopf zu
 * zeigen, der dann `materialTextur()` mit `null` beantwortet — genau der
 * Fehler, gegen den `docs/kosmodata-neugestaltung/UI-REGELN.md` Regel 5
 * (Ehrlichkeit vor Vollstaendigkeit) steht.
 *
 * Reine Filterfunktion, keine eigene Kopie der Katalogdaten — `materialkatalog`
 * bleibt die eine Quelle (Sanktion gegen Zwillingslisten, s. `CLAUDE.md`
 * v0.9.38-Lehre: dreimal handgepflegte Listen, dreimal war die wahre Zahl
 * hoeher als die gemeldete).
 */
export function texturMaterialOptionen(): readonly MaterialEintrag[] {
  const rezeptKlassen = new Set<string>(REZEPT_KLASSEN);
  return materialkatalog.filter((m) => rezeptKlassen.has(m.sia));
}
