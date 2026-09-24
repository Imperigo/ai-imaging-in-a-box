import { useState } from 'react';
import { KButton, Hairline } from '@kosmo/ui';
import {
  ANSICHT_SLOTS,
  ANSICHT_SLOT_LABEL,
  useVisRuntime,
  waehleAufnahme,
  type AnsichtSlotId,
} from './vis-runtime';

/**
 * GespeicherteAnsichten (v0.8.1 / P8, 0.7.2-Rest «Viz gespeicherte Ansichten
 * + Review-Pins», Spec §6.2, B-92/B-105) — drei feste Slots ISO/NORD/DETAIL
 * über den ECHTEN Viewport-Aufnahmen (`modules/vis/vis-runtime.ts`
 * `Aufnahme`, «Für Vis aufnehmen»-Knopf in `Viewport3D.tsx`, unverändert).
 *
 * Laufzeit- statt Doc-Entscheid (s. Kopfkommentar `vis-runtime.ts`): eine
 * gespeicherte Ansicht ist ein Zeiger auf eine bereits laufzeit-only lebende
 * Aufnahme — sie kann nicht Doc-/Yjs-fähiger sein als ihr eigenes Ziel.
 *
 * Review-Modus: ein Klick auf die gezeigte Aufnahme legt einen Kommentar-Pin
 * an einer NORMIERTEN Bildposition an (0..1 je Achse — eine `Aufnahme` ist
 * ein flaches Bild, keine echte 3D-Weltkoordinate; das ist hier bewusst
 * ehrlich benannt statt eine 3D-Position vorzutäuschen, die es nicht gibt).
 */
export function GespeicherteAnsichten() {
  const aufnahmen = useVisRuntime((s) => s.aufnahmen);
  const gespeicherteAnsichten = useVisRuntime((s) => s.gespeicherteAnsichten);
  const reviewPins = useVisRuntime((s) => s.reviewPins);
  const speichereAnsicht = useVisRuntime((s) => s.speichereAnsicht);
  const entferneAnsicht = useVisRuntime((s) => s.entferneAnsicht);
  const fuegeReviewPinHinzu = useVisRuntime((s) => s.fuegeReviewPinHinzu);
  const entferneReviewPin = useVisRuntime((s) => s.entferneReviewPin);

  const [reviewSlot, setReviewSlot] = useState<AnsichtSlotId | null>(null);
  const [neuerPin, setNeuerPin] = useState<{ x: number; y: number } | null>(null);
  const [pinText, setPinText] = useState('');
  const [offenerPin, setOffenerPin] = useState<string | null>(null);

  const jüngsteAufnahme = waehleAufnahme(aufnahmen);

  return (
    <div data-testid="gespeicherte-ansichten" style={{ display: 'grid', gap: 14 }}>
      <div
        style={{
          fontFamily: 'var(--k-font-mono)',
          fontSize: 11,
          fontWeight: 'var(--k-gewicht-betont)',
          letterSpacing: '0.14em',
          textTransform: 'uppercase',
          color: 'var(--k-ink-faint)',
        }}
      >
        Gespeicherte Ansichten
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 14,
        }}
      >
        {ANSICHT_SLOTS.map((slot) => {
          const eintrag = gespeicherteAnsichten[slot];
          const aufnahme = eintrag ? aufnahmen[eintrag.aufnahmeId] : undefined;
          const verwaist = eintrag !== undefined && aufnahme === undefined;
          const pins = aufnahme ? (reviewPins[aufnahme.id] ?? []) : [];
          const imReview = reviewSlot === slot;

          return (
            <div
              key={slot}
              data-testid={`ansicht-slot-${slot}`}
              className="k-glass"
              style={{ display: 'grid', gap: 8, padding: 12, borderRadius: 'var(--k-radius-md)' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span
                  style={{
                    fontFamily: 'var(--k-font-mono)',
                    fontSize: 12,
                    fontWeight: 'var(--k-gewicht-betont)',
                    letterSpacing: '0.1em',
                    color: 'var(--k-ink)',
                  }}
                >
                  {ANSICHT_SLOT_LABEL[slot]}
                </span>
                {eintrag && aufnahme && (
                  <span
                    data-testid={`ansicht-slot-${slot}-autosave`}
                    style={{
                      fontFamily: 'var(--k-font-mono)',
                      fontSize: 9,
                      letterSpacing: '0.06em',
                      color: 'var(--k-ink-faint)',
                    }}
                  >
                    AUTOSAVE · v{String(eintrag.version).padStart(3, '0')}
                  </span>
                )}
              </div>

              {aufnahme ? (
                <div
                  data-testid={`ansicht-slot-${slot}-flaeche`}
                  onClick={(e) => {
                    if (!imReview) return;
                    const rect = e.currentTarget.getBoundingClientRect();
                    setNeuerPin({
                      x: (e.clientX - rect.left) / rect.width,
                      y: (e.clientY - rect.top) / rect.height,
                    });
                    setPinText('');
                  }}
                  style={{
                    position: 'relative',
                    borderRadius: 'var(--k-radius-sm)',
                    overflow: 'hidden',
                    border: '1px solid var(--k-line)',
                    cursor: imReview ? 'crosshair' : 'default',
                  }}
                >
                  <img
                    data-testid={`ansicht-slot-${slot}-bild`}
                    src={aufnahme.dataUrl}
                    alt={`Gespeicherte Ansicht ${ANSICHT_SLOT_LABEL[slot]}`}
                    style={{ width: '100%', display: 'block' }}
                  />
                  {pins.map((pin, i) => (
                    <button
                      key={pin.id}
                      type="button"
                      data-testid={`review-pin-${pin.id}`}
                      title={`${pin.wer}: ${pin.text}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setOffenerPin(offenerPin === pin.id ? null : pin.id);
                      }}
                      style={{
                        position: 'absolute',
                        left: `${pin.x * 100}%`,
                        top: `${pin.y * 100}%`,
                        transform: 'translate(-50%, -50%)',
                        width: 18,
                        height: 18,
                        borderRadius: '999px',
                        background: 'var(--k-signal)',
                        // P-MF3: `--k-ink-1000` existierte nie. Der Punkt liegt auf
                        // `--k-signal` (Zeile darüber), und `--k-signal`/`--k-signal-tinte`
                        // stehen beide NUR in `:root` — themeninvariant. Die Tinte auf
                        // Signalfläche ist also `--k-signal-tinte` (`aura.css:295`, so
                        // schon in der soliden Pille, `aura.css:2229`). `--k-ink` wäre
                        // hier falsch: im Kosmos-Theme ist das `#f4f6fa`, hell auf Teal.
                        color: 'var(--k-signal-tinte)',
                        border: '1px solid var(--k-surface)',
                        fontFamily: 'var(--k-font-mono)',
                        fontSize: 9,
                        fontWeight: 'var(--k-gewicht-betont)',
                        display: 'grid',
                        placeItems: 'center',
                        cursor: 'pointer',
                        padding: 0,
                      }}
                    >
                      {i + 1}
                    </button>
                  ))}
                  {offenerPin && pins.some((p) => p.id === offenerPin) && (
                    <div
                      data-testid={`review-pin-${offenerPin}-notiz`}
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        position: 'absolute',
                        left: `${(pins.find((p) => p.id === offenerPin)?.x ?? 0) * 100}%`,
                        top: `${(pins.find((p) => p.id === offenerPin)?.y ?? 0) * 100}%`,
                        transform: 'translate(8px, 8px)',
                        background: 'var(--k-raised)',
                        border: '1px solid var(--k-line)',
                        borderRadius: 'var(--k-radius-sm)',
                        padding: '6px 8px',
                        maxWidth: 180,
                        fontSize: 11.5,
                        color: 'var(--k-ink-soft)',
                        boxShadow: 'var(--k-shadow-overlay)',
                        display: 'grid',
                        gap: 4,
                      }}
                    >
                      <div>{pins.find((p) => p.id === offenerPin)?.text}</div>
                      <KButton
                        size="sm"
                        tone="ghost"
                        data-testid={`review-pin-${offenerPin}-entfernen`}
                        onClick={() => {
                          entferneReviewPin(aufnahme.id, offenerPin);
                          setOffenerPin(null);
                        }}
                      >
                        Entfernen
                      </KButton>
                    </div>
                  )}
                  {neuerPin && imReview && (
                    <div
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        position: 'absolute',
                        left: `${neuerPin.x * 100}%`,
                        top: `${neuerPin.y * 100}%`,
                        transform: 'translate(8px, 8px)',
                        background: 'var(--k-raised)',
                        border: '1px solid var(--k-line-strong)',
                        borderRadius: 'var(--k-radius-sm)',
                        padding: 8,
                        display: 'grid',
                        gap: 6,
                        boxShadow: 'var(--k-shadow-overlay)',
                        minWidth: 160,
                      }}
                    >
                      <input
                        data-testid="review-pin-neu-text"
                        autoFocus
                        value={pinText}
                        onChange={(e) => setPinText(e.target.value)}
                        placeholder="Notiz …"
                        style={{
                          font: 'inherit',
                          fontSize: 12,
                          padding: '4px 6px',
                          borderRadius: 'var(--k-radius-sm)',
                          border: '1px solid var(--k-line)',
                          background: 'var(--k-surface)',
                          color: 'var(--k-ink)',
                        }}
                      />
                      <div style={{ display: 'flex', gap: 6 }}>
                        <KButton
                          size="sm"
                          data-testid="review-pin-neu-speichern"
                          disabled={pinText.trim().length === 0}
                          onClick={() => {
                            fuegeReviewPinHinzu(aufnahme.id, {
                              x: neuerPin.x,
                              y: neuerPin.y,
                              text: pinText.trim(),
                              wer: 'Du',
                            });
                            setNeuerPin(null);
                          }}
                        >
                          Speichern
                        </KButton>
                        <KButton size="sm" tone="ghost" data-testid="review-pin-neu-abbrechen" onClick={() => setNeuerPin(null)}>
                          Abbrechen
                        </KButton>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div
                  data-testid={`ansicht-slot-${slot}-leer`}
                  style={{
                    fontSize: 12,
                    color: 'var(--k-ink-faint)',
                    padding: '20px 6px',
                    textAlign: 'center',
                    border: '1px dashed var(--k-line)',
                    borderRadius: 'var(--k-radius-sm)',
                  }}
                >
                  {verwaist ? 'Snapshot nicht mehr vorhanden' : 'Kein Snapshot gespeichert'}
                </div>
              )}

              <Hairline />

              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <KButton
                  size="sm"
                  tone={aufnahme ? 'ghost' : 'accent'}
                  data-testid={`ansicht-slot-${slot}-speichern`}
                  disabled={!jüngsteAufnahme}
                  title={jüngsteAufnahme ? undefined : 'Erst «Für Vis aufnehmen» in KosmoDesign nutzen — im 3D-Viewport oder in der AUSTAUSCH-Insel unter «Rendern»'}
                  onClick={() => jüngsteAufnahme && speichereAnsicht(slot, jüngsteAufnahme.id)}
                >
                  {aufnahme ? 'Aktualisieren' : 'Aktuelle Ansicht speichern'}
                </KButton>
                {aufnahme && (
                  <>
                    <KButton
                      size="sm"
                      tone="ghost"
                      aria-pressed={imReview}
                      data-testid={`ansicht-slot-${slot}-review`}
                      style={imReview ? { borderColor: 'var(--k-signal)', color: 'var(--k-signal)' } : undefined}
                      onClick={() => {
                        setReviewSlot(imReview ? null : slot);
                        setNeuerPin(null);
                      }}
                    >
                      {imReview ? 'Review beenden' : `Review${pins.length > 0 ? ` (${pins.length})` : ''}`}
                    </KButton>
                    <KButton
                      size="sm"
                      tone="ghost"
                      data-testid={`ansicht-slot-${slot}-entfernen`}
                      onClick={() => entferneAnsicht(slot)}
                    >
                      Entfernen
                    </KButton>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
