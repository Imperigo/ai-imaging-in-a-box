/**
 * E76 (Owner-Entscheid 19.09.2026, siehe `auftraege/ergebnisse/
 * erg-20260919-104-unbekannte-felder-in-der-bestellung.md` Abschnitt V3) —
 * unser Vertrag (`packages/kosmo-contracts`) traegt bewusst KEIN `.strict()`.
 * Unbekannte Felder in einer Antwort der Gegenseite (KosmoVis/HomeStation-
 * Bruecke) werden von zod still abgestreift, das ist dokumentiert und
 * getestet, also GEWOLLT: ein `.strict()` wuerde jede kuenftige
 * Feld-Ergaenzung der Gegenseite unsere Seite anhalten lassen.
 *
 * Der Owner-Entscheid ist das mildere Mittel: unbekannte Felder werden
 * GEMELDET statt verworfen — sichtbar, ohne den Lauf zu toeten. Diese Datei
 * baut NUR die Messung dafuer, keine Meldung und kein Urteil. `RenderJob.
 * result` traegt den Beleg, warum das ueberhaupt noetig ist — «Ohne dieses
 * Feld wuerde `RenderJob.parse()` es stumm strippen (Fable-Review-1)»: genau
 * dieser Fehler ist im Repo schon einmal von Hand gefunden worden.
 */

/** Unterscheidet ein echtes Objekt von einer Liste, `null` und Primitiven —
 * nur echte Objekte tragen benannte Schluessel, ueber die verglichen wird. */
function istEchtesObjekt(wert: unknown): wert is Record<string, unknown> {
  return typeof wert === 'object' && wert !== null && !Array.isArray(wert);
}

/**
 * Vergleicht die ROHE Nutzlast (`roh`) mit dem von zod GEPRUEFTEN Ergebnis
 * (`geprueft`) und gibt die Pfade zurueck, die in `roh` stehen und in
 * `geprueft` fehlen — in Punktschreibweise, Listen-Eintraege mit Index
 * (z. B. `result.qa.geometry.neues_feld`, `result.qa_je_kamera.0.fremdfeld`).
 *
 * Reine Funktion: sie urteilt nicht und wirft nicht, sie zaehlt nur auf.
 * Eine leere Liste heisst «nichts Unbekanntes». Sie braucht keinen
 * zod-Import — sie vergleicht zwei gewoehnliche Werte, egal wie sie
 * entstanden sind.
 *
 * NUR `roh` minus `geprueft`: ein Feld, das zod selbst HINZUFUEGT
 * (`.default(...)`), steht in `geprueft`, aber nicht in `roh` — das ist KEIN
 * Befund, weil hier ausschliesslich ueber die Schluessel von `roh` iteriert
 * wird. Ein `.default()`-Feld taucht darum nie in der Rueckgabe auf.
 *
 * `pfad` ist ein interner Rekursions-Parameter (Aufrufer lassen ihn weg).
 */
export function unbekannteFelder(roh: unknown, geprueft: unknown, pfad = ''): string[] {
  const treffer: string[] = [];

  if (Array.isArray(roh)) {
    // Ein geprueftes Gegenstueck, das keine Liste ist (oder fehlt), hat an
    // jedem Index nichts, womit verglichen werden koennte — dann bleibt der
    // ganze Eintrag unentschieden (keine falschen Treffer erfinden), die
    // Rekursion darunter faengt trotzdem echte Objekte/Listen im Eintrag ab.
    const geprüfteListe = Array.isArray(geprueft) ? geprueft : [];
    roh.forEach((eintrag, index) => {
      const teilpfad = pfad ? `${pfad}.${index}` : String(index);
      treffer.push(...unbekannteFelder(eintrag, geprüfteListe[index], teilpfad));
    });
    return treffer;
  }

  if (istEchtesObjekt(roh)) {
    const geprüftesObjekt = istEchtesObjekt(geprueft) ? geprueft : {};
    for (const schluessel of Object.keys(roh)) {
      const teilpfad = pfad ? `${pfad}.${schluessel}` : schluessel;
      if (!(schluessel in geprüftesObjekt)) {
        treffer.push(teilpfad);
        continue;
      }
      treffer.push(...unbekannteFelder(roh[schluessel], geprüftesObjekt[schluessel], teilpfad));
    }
    return treffer;
  }

  // Primitiver Wert (Zahl/Zeichenkette/Boolean), `null` oder `undefined` —
  // hier gibt es keine Schluessel/Indizes mehr, ueber die man abweichen
  // koennte.
  return treffer;
}
