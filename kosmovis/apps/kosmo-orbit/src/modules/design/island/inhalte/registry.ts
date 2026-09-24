import type { ComponentType } from 'react';

/**
 * Inhalts-Registry der Island-Stufen 2/3 (Fable-Naht für PD3a ‖ PD3b,
 * `docs/ISLAND-UI-SPEZ.md` §4.4/§7).
 *
 * Zweck: PD3a (ZEICHNEN+ANSICHT) und PD3b (PROJEKT+AUSTAUSCH) laufen
 * parallel und dürfen KEINE gemeinsame Datei anfassen. Jedes Werkzeug
 * registriert seine Stufe-2-/Stufe-3-Komponenten deshalb in seiner
 * Insel-Inhaltsdatei (`zeichnen.tsx`/`ansicht.tsx` → PD3a,
 * `projekt.tsx`/`austausch.tsx` → PD3b); `IslandShell.tsx` liest hier nur.
 * Registrierung passiert als Import-Seiteneffekt — `IslandShell.tsx`
 * importiert die vier Inhaltsdateien genau einmal.
 *
 * `Stufe2` = Mini-Popup-Inhalt (2–4 Schnelleinstellungen, §4.1); `Stufe3` =
 * Einstellungsfenster-Inhalt. Beide sind gewöhnliche React-Komponenten und
 * dürfen die bestehenden Stores (`useUiZustand`, `useProject`, …) direkt
 * nutzen — jede Modell-Änderung läuft über den bestehenden
 * Command→Patch→Undo-Weg, nie an ihm vorbei.
 */
export interface WerkzeugInhalt {
  /** Mini-Popup (Stufe 2). Fehlt sie, zeigt IslandShell den PD2-Hinweis/Rahmen. */
  Stufe2?: ComponentType;
  /** Einstellungsfenster (Stufe 3). Fehlt sie, zeigt IslandShell den PD2-Hinweis/Rahmen. */
  Stufe3?: ComponentType;
}

/**
 * PC0 v0.8.4 (`docs/V084-SPEZ.md` E1): Registry als INSTANZ statt
 * Modul-Singleton — der Island-Rollout auf alle Stationen braucht je Station
 * einen eigenen Namensraum, sonst kollidieren gleichnamige Werkzeug-Ids
 * («export» gibt es in AUSTAUSCH und künftig in publish) am harten
 * Doppelregistrierungs-Wurf. Die design-Station behält ihre Instanz als
 * Default; die bestehenden Modul-Funktionen delegieren UNVERÄNDERT dorthin —
 * kein Bestands-Importeur (inhalte/*.tsx, IslandShell, Tests) ändert sich.
 */
export class InhaltsRegistry {
  private readonly eintraege = new Map<string, WerkzeugInhalt>();

  constructor(
    /** Nur für Fehlermeldungen — benennt die Station im Kollisions-Wurf. */
    private readonly namensraum: string = 'design',
  ) {}

  /** Doppelregistrierung ist ein Programmierfehler (zwei Pakete, ein Werkzeug) — hart werfen. */
  registriere(werkzeugId: string, inhalt: WerkzeugInhalt): void {
    if (this.eintraege.has(werkzeugId)) {
      throw new Error(
        `Island-Inhalt für «${werkzeugId}» ist im Namensraum «${this.namensraum}» bereits registriert (Dateikreis-Kollision?).`,
      );
    }
    this.eintraege.set(werkzeugId, inhalt);
  }

  inhaltFuer(werkzeugId: string): WerkzeugInhalt | undefined {
    return this.eintraege.get(werkzeugId);
  }

  /** Für das harte Gate C-38 («kein Werkzeug endet bei Stufe 1») — testbar. */
  registrierteIds(): readonly string[] {
    return [...this.eintraege.keys()];
  }
}

/** Die design-Station — Default-Registry aller bestehenden `inhalte/*.tsx`. */
export const designInhaltsRegistry = new InhaltsRegistry('design');

export function registriereInhalt(werkzeugId: string, inhalt: WerkzeugInhalt): void {
  designInhaltsRegistry.registriere(werkzeugId, inhalt);
}

export function inhaltFuer(werkzeugId: string): WerkzeugInhalt | undefined {
  return designInhaltsRegistry.inhaltFuer(werkzeugId);
}

/** Für das harte Gate C-38 («kein Werkzeug endet bei Stufe 1») — testbar. */
export function registrierteWerkzeugIds(): readonly string[] {
  return designInhaltsRegistry.registrierteIds();
}
