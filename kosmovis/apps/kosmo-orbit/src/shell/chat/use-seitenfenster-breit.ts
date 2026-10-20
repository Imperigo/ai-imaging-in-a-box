import { useEffect, useState } from 'react';
import { breakpoint } from '@kosmo/ui';

/**
 * C0 Nachbesserung 3 — ab welcher Fensterbreite das Seitenfenster stehen darf.
 *
 * Das Seitenfenster reserviert seine 430 px und nimmt sie der Station weg.
 * Die Kopfzeilen der Stationen (Vis: Logo, Orb, Ansicht-Insel, zweite
 * Kopfgruppe, Einstellungen) brauchen gemessen rund 850 px Restbreite, damit
 * die geoeffnete Ansicht-Insel keine Nachbarin beruehrt (b154, 1400x900: mit
 * 970 px Rest frei; bei 1024 px Fenster blieben 594 px, dort ueberlappen sich
 * Insel und Kopfgruppe zwangslaeufig). Darum gilt dieselbe Sprosse wie fuer die
 * dritte Spalte der Zentrale (`breakpoint.dreispaltig`, 1200 px): darunter ist
 * Kosmo wieder die Blase, die man ruft, mit ihren bewaehrten Ausweich-Regeln.
 *
 * Fehlt `matchMedia` (jsdom), wird `innerWidth` gelesen.
 */
export function useSeitenfensterBreit(): boolean {
  const frage = `(min-width: ${breakpoint.dreispaltig}px)`;
  const messen = (): boolean => {
    if (typeof window === 'undefined') return false;
    if (typeof window.matchMedia === 'function') return window.matchMedia(frage).matches;
    return window.innerWidth >= breakpoint.dreispaltig;
  };
  const [breit, setzeBreit] = useState(messen);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const nachmessen = () => setzeBreit(messen());
    nachmessen();
    if (typeof window.matchMedia === 'function') {
      const mql = window.matchMedia(frage);
      if (typeof mql.addEventListener === 'function') {
        mql.addEventListener('change', nachmessen);
        return () => mql.removeEventListener('change', nachmessen);
      }
    }
    window.addEventListener('resize', nachmessen);
    return () => window.removeEventListener('resize', nachmessen);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return breit;
}
