/**
 * Wählbare Farbakzente (Gestaltungskonzept «Werkplan»): Standard = Tusche.
 * Eigene Datei (statt in `App.tsx`), damit das zentrale Einstellungs-Panel
 * (Serie K / A4, `Einstellungen.tsx`) dieselbe Liste importiert statt sie ein
 * zweites Mal zu pflegen — App.tsx (Kopfleiste) und Einstellungen.tsx (Panel)
 * rufen für den eigentlichen Wechsel weiterhin denselben `setAkzent`-Setter
 * aus App.tsx auf (per Prop), nur die Datentabelle ist geteilt.
 */
export interface Akzent {
  key: string;
  name: string;
  farbe: string | null;
}

export const AKZENTE: Akzent[] = [
  { key: 'tusche', name: 'Tusche', farbe: null },
  { key: 'kupfer', name: 'Kupfer', farbe: '#a84b2b' },
  { key: 'signal', name: 'Signal', farbe: '#c8501e' },
  { key: 'blau', name: 'Blau', farbe: '#2455a4' },
  { key: 'gruen', name: 'Grün', farbe: '#1e6b47' },
];
