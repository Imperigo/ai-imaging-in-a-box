/**
 * Zeiger-Helfer (D-8, E-8 B `docs/design/GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`) —
 * DER zentrale Ort für die Frage «war das Touch/Pen statt Maus?».
 *
 * E-8 legt fest: in TSX gilt ereignisbasiert `e.pointerType !== 'mouse'`
 * (robust bei Convertibles — dasselbe Gerät kann Maus UND Finger liefern,
 * eine Geräte-/UA-Weiche wie `navigator.platform` ist TABU, §6 des
 * Unterauftrags). Dieser Helfer kapselt genau diesen Vergleich, damit keine
 * Aufrufstelle ihre eigene Variante erfindet.
 *
 * Ehrlichkeits-Klausel: Events OHNE `pointerType` (klassische MouseEvents,
 * jsdom-Synthetik, ältere Engines) gelten als Maus — der bestehende
 * Maus-/Tastaturweg bleibt der Default und verschlechtert sich nie dadurch,
 * dass ein Event die Auskunft schuldig bleibt (E-8-Zusicherung 5).
 */

/** Minimalform statt `PointerEvent`: nimmt native UND React-synthetische
 *  Events (React reicht `pointerType` durch), ohne DOM-Typ-Zwang in
 *  Nicht-DOM-Testumgebungen. */
export interface ZeigerAuskunft {
  readonly pointerType?: string | undefined;
}

/** true, wenn das Ereignis von Touch oder Stift stammt (`pointerType`
 *  vorhanden und nicht `'mouse'`) — false für Maus UND für Events ohne
 *  `pointerType`-Auskunft (s. Kopfkommentar). */
export function istTouchArtig(e: ZeigerAuskunft): boolean {
  const typ = e.pointerType;
  return typeof typ === 'string' && typ !== '' && typ !== 'mouse';
}
