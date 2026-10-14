import { useEffect, useRef, useState } from 'react';
import { materialTextur, type MaterialKarten } from '@kosmo/kernel';
import { KButton } from '@kosmo/ui';
import { texturMaterialOptionen } from '../../textur-material';
import { kachelBlobUrl } from '../../textur-bild';
import { visInhaltsRegistry } from './registry';
import '../../vis-visual.css';
import '../vis-island.css';

/**
 * STIMMUNG-Insel, zweites Werkzeug — der «Textur-Knopf» (Abnahmezeile 6,
 * `docs/V016-SPEZ.md` Zeile 246, P16 Welle 2).
 *
 * DER ZURUF: «bitte entweder hochaufloesende texturen im interner gratis
 * finden mit allen maps oder selber generieren und maps hinzufuegen».
 * `derive/textur.ts` kann seit dem 17.09.2026 generieren (reine Funktion,
 * kein DOM, s. dort) — es fehlte nur der Bedienweg (P60-Nachmessung
 * 23.09.2026, `docs/RENDERPROJEKT-2026-09-10/60-ABNAHMELISTE.md` Zeile 526:
 * «kein Bedienelement (P16 baut den ‹Textur-Knopf› noch)»).
 *
 * WAS DIESER KNOPF TUT, und was nicht: zu einem AUSGEWAEHLTEN Material
 * (Auswahlfeld, keine Freitext-Eingabe — der Kern rechnet nur fuer
 * Katalog-Schluessel mit einem Rezept, s. `textur-material.ts`) erzeugt er
 * Farb- und Rauheitskarte und zeigt beide sofort, mit Lade-Link. Er sucht
 * NICHT im Netz («…im Internet gratis finden…») — das waere ein zweiter,
 * unabhaengiger Weg (Lizenzpruefung noetig, s. Abnahmezeile 9) und ist hier
 * nicht gebaut; der Hinweistext sagt das ehrlich (Regel 5, `UI-REGELN.md`).
 *
 * KEIN Laufzeit-Zustand im Doc: die erzeugten Bilder sind `blob:`-URLs im
 * lokalen Komponentenzustand (Sanktion «Laufzeit ≠ Modell», `CLAUDE.md`
 * Eigenheiten) — sie werden bei jedem neuen Erzeugen UND beim Verlassen der
 * Insel abgeraeumt (`URL.revokeObjectURL`), Muster `bild-rechnen.ts`s
 * `quellUrl`.
 */

const OPTIONEN = texturMaterialOptionen();

interface TexturUrls {
  farbe: string;
  rauheit: string;
}

function TexturStufe2() {
  const [key, setKey] = useState<string>(OPTIONEN[0]?.key ?? '');
  const [karten, setKarten] = useState<MaterialKarten | null>(null);
  const [urls, setUrls] = useState<TexturUrls | null>(null);
  // Die zuletzt vergebenen URLs, ausserhalb des Render-Zyklus greifbar — fuer
  // das Abraeumen beim naechsten Erzeugen UND beim Unmount (zwei Stellen,
  // ein Speicher, Muster `KuratierInspektor.tsx`s Store-Griffe).
  const urlsRef = useRef<TexturUrls | null>(null);

  useEffect(() => {
    return () => {
      if (urlsRef.current) {
        URL.revokeObjectURL(urlsRef.current.farbe);
        URL.revokeObjectURL(urlsRef.current.rauheit);
      }
    };
  }, []);

  const erzeugen = () => {
    const gefunden = materialTextur(key);
    if (urlsRef.current) {
      URL.revokeObjectURL(urlsRef.current.farbe);
      URL.revokeObjectURL(urlsRef.current.rauheit);
      urlsRef.current = null;
    }
    if (!gefunden) {
      // Sollte `texturMaterialOptionen()` je einen Schluessel ohne Rezept
      // anbieten (Regressionsfall, s. `vis-textur-material.test.ts`), zeigt
      // dieser Zweig ehrlich nichts statt eines erfundenen Bilds.
      setKarten(null);
      setUrls(null);
      return;
    }
    const neu: TexturUrls = { farbe: kachelBlobUrl(gefunden.farbe), rauheit: kachelBlobUrl(gefunden.rauheit) };
    urlsRef.current = neu;
    setKarten(gefunden);
    setUrls(neu);
  };

  return (
    <div className="visisl-stufe2" data-testid="island-textur-stufe2" onClick={(e) => e.stopPropagation()}>
      <label className="visisl-reihe">
        <span>Material</span>
        <select
          className="vis-node-select-voll"
          data-testid="island-textur-material"
          value={key}
          onChange={(e) => setKey(e.target.value)}
        >
          {OPTIONEN.map((m) => (
            <option key={m.key} value={m.key}>
              {m.name}
            </option>
          ))}
        </select>
      </label>

      <KButton
        size="touch"
        tone="accent"
        data-testid="island-textur-erzeugen"
        disabled={!key}
        onClick={erzeugen}
      >
        Bildkarten erzeugen
      </KButton>

      {urls ? (
        <div className="visisl-textur-reihe" data-testid="island-textur-vorschau">
          <div className="visisl-textur-kachel">
            <img
              src={urls.farbe}
              alt="Farbkarte"
              width={56}
              height={56}
              className="visisl-textur-bild"
              data-testid="island-textur-farbe"
            />
            <span className="visisl-textur-label">Farbe</span>
            <a href={urls.farbe} download={`${key}-farbe.png`} data-testid="island-textur-farbe-laden">
              Laden
            </a>
          </div>
          <div className="visisl-textur-kachel">
            <img
              src={urls.rauheit}
              alt="Rauheitskarte"
              width={56}
              height={56}
              className="visisl-textur-bild"
              data-testid="island-textur-rauheit"
            />
            <span className="visisl-textur-label">Rauheit</span>
            <a href={urls.rauheit} download={`${key}-rauheit.png`} data-testid="island-textur-rauheit-laden">
              Laden
            </a>
          </div>
        </div>
      ) : (
        <p className="visisl-hinweis-klein" data-testid="island-textur-leer">
          Noch keine Bildkarten erzeugt.
        </p>
      )}

      {karten ? (
        <p className="visisl-hinweis-klein" data-testid="island-textur-hinweis">
          Rezept «{karten.rezept}», 256 Bildpunkte je Meter, hier gerechnet — keine echten
          Fotoaufnahmen aus dem Internet und keine Normalenkarte (dafür fehlen dem Kern Tangenten
          je Eckpunkt, siehe die Ableitung Textur).
        </p>
      ) : null}
    </div>
  );
}

visInhaltsRegistry.registriere('textur', { Stufe2: TexturStufe2, Stufe3: TexturStufe2 });

export { TexturStufe2 };
