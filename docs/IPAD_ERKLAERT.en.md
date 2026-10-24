# Visbox on the iPad — what each part does

*Source of the board section «Visbox · iPad» (cards `20261024-ipad-NN-*`), written by `tools/ipad_tafel.py --markdown`. Do not edit by hand — change the tool and regenerate.*

Only what is in the code under `ipad/Visbox.swiftpm` is described. Every on-screen label in parentheses is the German wording of the app; a probe (`tests/test_ipad_tafel.py`) finds each one in the Swift sources. Planned items stand only under **Planned — decided, not built**, each with the decision that settles it. The pictures on the cards are drawn schematics, not screenshots.

## 00 · Overview: the iPad app at a glance

A sketch pad for the Apple Pencil. Sketches go into the project folder (Mappe); finished images come back to be looked at. The iPad itself never computes.

**On screen**

1. **Status line** — Says whether the iPad is paired with the Mac and what is waiting to be sent. A tap opens pairing.
2. **Toolbar** (Werkzeugleiste) — Pen, two erasers, the pan-and-zoom hand and three stroke widths — at the edge, never over the drawing.
3. **Sheet** — The drawing sheet, always 1536 × 1024 pixels, drawn on with the Pencil.
4. **Side panel** (Seitenfeld) — One column that switches between Layers (Ebenen) and Folder (Mappe) — never both at once.
5. **Place in folder** (In die Mappe legen) — The one button that sends something out: the visible layers as a sketch.

**What happens.** Turning the iPad keeps the same view: in landscape the toolbar sits left or right, in portrait at the bottom with the side panel below the sheet. Full screen (Vollbild) hides everything but the sheet. The iPad talks only to the Mac, encrypted; with a project folder open on the Mac, the sketch is kept there, otherwise the Mac passes it on to the home PC.

**Honest limit.** The app only shows what the computer says: verdicts, numbers and images come from there. Without a paired Mac, sketches wait on the iPad.

*Source: Startansicht.swift · Leiste/Arbeitsplatz.swift · Leiste/Seitentafel.swift · Kern/Macmappensicht.swift*

## 01 · Pairing with the Mac (Mit dem Mac koppeln)

Connect the iPad to the Mac once. Three ways, from easiest to last resort — all three end in the same pairing.

**On screen**

1. **Mac nearby** (Mac in der Nähe) — Appears when «iPad koppeln» is open on the Mac. The iPad asks «Mit diesem Mac koppeln?» — Accept (Annehmen), then confirm on the Mac. Only when both agree does the Mac send address and number, never the password.
2. **QR code** (Mit QR-Code koppeln) — Reads the code the Mac shows for two minutes, with the iPad camera. Highlighted when no Mac shows up nearby.
3. **Macs on the Wi-Fi** (Macs im WLAN) — Encrypted Macs found on the network. One: pre-selected. Several: you choose — the app does not guess.
4. **Type the address** (Oder die Adresse des Mac eintippen) — Always https; the app says what is wrong with an address before anything is sent.
5. **Six-digit number** (Zahl eintippen — vom Mac) — Digits only, at most six, checked before sending, so a typo costs no attempt. Cleared after every try.
6. **Pair** (Koppeln) — Active once address and number are complete; the answer appears below it.
- **Re-pair** (Neu koppeln) — If the paired Mac stops answering, nearby and QR code are offered again; the old pairing holds until the new one succeeds.
- **Disconnect** (Trennen) — Forgets the Mac on this iPad; parked sketches stay.

**What happens.** After pairing the iPad accepts only this Mac's certificate. Under «Gekoppelt» it shows the Mac's sign (Zeichen des Mac) to compare with the Mac's screen.

**Honest limit.** Only with the Mac and only encrypted — an old pairing straight to the home PC no longer works. The nearby search needs «Lokales Netzwerk» allowed on the iPad; after 30 seconds without a Mac the screen says so.

*Source: Verbindung/Koppelbildschirm.swift · Naehesucher.swift · QRLeser.swift · Kern/Naehekopplung.swift*

## 02 · Status line (Verbindungszeile)

The top line says who the iPad is talking to — and claims nothing it does not know.

**On screen**

1. **Off** (Aus) — Hollow ring. Not paired: «Nicht gekoppelt. Skizzen warten auf dem iPad.»
2. **Searching** (Suche) — Grey dot that breathes. Searching, or the paired Mac has not answered yet — «Gekoppelt» is shown only after an answer.
3. **Paired** (Gekoppelt) — Green dot. The last request arrived; the lock means «über den Mac, verschlüsselt» (via the Mac, encrypted).
4. **Disconnected** (Getrennt) — Hollow ring. Paired, but the last request did not arrive — the reason is written underneath.
5. **Parking bay button** (Parkfach) — Only counts that are not zero: parked (geparkt), uncertain (ungewiss), on the way (unterwegs), open (offen). A tap opens the list.
6. **Hand-over strip** — While a sketch travels, one mark moves along a thread from iPad to Mac — see card 05.

**What happens.** A tap on the status opens pairing. When the app comes back to the front, it asks the remembered Mac again. With Reduce Motion on, the dot does not breathe.

**Honest limit.** The dot is never the whole message — the word next to it is. In full screen the line is hidden, and with it the travelling mark.

*Source: Verbindung/Verbindungszeile.swift · Uebergabe.swift · Kern/Suche.swift · Kern/Parkfach.swift*

## 03 · Drawing sheet (Zeichenfläche)

Only the Pencil draws. Fingers move and zoom the sheet.

**On screen**

1. **Pen** (Stift) — Pressure changes the line width; the width chosen below is the base.
2. **Eraser: whole strokes** (Radierer: ganze Striche) — Removes a stroke with one touch.
3. **Eraser: wipe area** (Radierer: flächig wegwischen) — Rubs away like a real eraser.
4. **Pan and zoom** (Schieben und zoomen) — With this, the Pencil also moves the sheet.
5. **Stroke width** (Mittlerer Strich) — Thin, middle or thick (Dünner, Mittlerer, Dicker Strich).
6. **Toolbar to the other side** (Leiste auf die andere Seite) — Landscape only; remembered on the iPad, e.g. for left-handers.
7. **Full screen** — Only the sheet; one button leads back (Vollbild verlassen).
8. **Undo / Redo** — Up to 20 steps (Zurück / Vor); the small number shows how many remain.
9. **Pen colours** (Weitere Farbe) — Four presets — Orange, Hell (light), Blau, Grün — and a colour picker for any other colour.

**What happens.** A double tap on Apple Pencil (2nd generation) switches between the current tool and the eraser. The sheet keeps its size and fits the screen; turning the iPad does not lose the drawing or the undo steps.

**Honest limit.** Fingers cannot draw. If the chosen layer is hidden, nothing is drawn — the sheet says so and offers «Einblenden» (show it).

**Planned — decided, not built**

- A switch «Mit dem Finger zeichnen» (draw with the finger), default off; with the Pencil, the finger keeps moving and zooming. *(Decision 141)*

*Source: Zeichnen/Zeichenflaeche.swift · Zeichenleinwand.swift · Leiste/Leiste.swift · Leistenwahl.swift*

## 04 · Layers and underlay (Ebenen)

Each layer is a variant. Only what is visible goes out.

**On screen**

1. **Add layer** (Ebene hinzufügen) — Up to 8 layers, named Variante A, B, C …; the new one is selected.
2. **Show / hide** — The checkbox. A hidden layer reads «ausgeblendet» and never goes with the sketch.
3. **Layer row** — Tap to choose the layer you draw on. On the right: opacity, «leer» (nothing drawn) or «ausgeblendet» (hidden).
4. **Opacity** (Deckkraft) — Slider from 10 % to 100 % for the chosen layer.
5. **Up, down, rename, delete** (Ebene löschen?) — Renaming (Ebene umbenennen) and deleting ask first; a deleted layer cannot be undone.
6. **Underlay** (Unterlage) — An image from the folder under all layers — dashed row at the bottom: show, hide or remove (✕). Not a layer: nothing is drawn or erased on it.
7. **What goes with it** — One sentence says exactly what would go out, from the same rule as the sending.

**What happens.** The underlay comes from «Darauf skizzieren» in the image view. It goes along with the sketch only if it is visible and from the folder the sketch goes to; the sheet title then reads «Skizze über … · Variante A».

**Honest limit.** At most three visible layers go as variants at once. An underlay of another shape is stretched to the sheet, exactly as the computer will place it — the row says «gestreckt».

*Source: Zeichnen/Ebenentafel.swift · Kern/Ebenen.swift · Kern/Blattunterlage.swift*

## 05 · Placing a sketch in the folder (In die Mappe legen)

One button sends the sketch into the project folder. Nothing is computed by itself.

**On screen**

1. **Place in folder** (In die Mappe legen) — Fixed at the foot of the side panel, under both tabs.
- **What goes** — The visible layers as one sketch; with «Drei Ebenen» chosen in the folder, each visible layer as a sketch of its own. The underlay goes along if it is visible.
2. **Hand-over strip** (in der Mappe · noch nicht gerechnet) — One mark on a thread: placing (legt ab), counted megabytes, waiting for the reply, arrived (in der Mappe), or back on the iPad (nicht angekommen).
3. **Reply sentence** — Under the button when there is something to say — nothing drawn, parked because nobody answers, underlay from another folder.

**What happens.** The sketch is stored as open (offen) and waits. It is computed only on request: «Rechnen lassen» in the folder tab, or as the Sketch from iPad node in the node view on the Mac. If the Mac is not there, the sketch stays in the parking bay and goes when it is back.

**Honest limit.** There is no note field when placing — an instruction is typed when ordering («Was soll sich ändern?»). Without a known total size the strip says «nicht gezählt» instead of showing a bar.

*Source: Leiste/Mappenknopf.swift · Verbindung/Uebergabe.swift · Kern/Parkfach.swift (Flugbahn)*

## 06 · Parking bay (Parkfach)

Every sketch passes through the parking bay first — so none is lost when the connection drops.

**On screen**

1. **Parked** (geparkt) — Waiting to be sent; goes by itself once the Mac answers.
2. **On the way** (unterwegs) — Being sent right now.
3. **Arrived** (angekommen) — In the folder over there; the thumbnail reads «drüben». Cleared from the list after 7 days.
4. **Rejected** (abgewiesen) — Refused, with the computer's sentence; stays until you decide.
5. **Uncertain** (ungewiss) — Whether it arrived is not known. With its key it is resent by itself, and no second file appears over there.
6. **Send again / Discard** (Noch einmal senden) — Discard (Verwerfen) asks first; «Behalten» keeps the sketch.

**What happens.** The list opens from the parking bay button in the status line. Each entry shows the drawing, date and time, and the reason when there is one.

**Honest limit.** The guard against sending twice lives only in the computer's memory (the last 512 keys): after a restart over there, a resend can make a duplicate — visible and removable, whereas a lost sketch would go unnoticed.

*Source: Verbindung/Parkfachliste.swift · Kern/Parkfach.swift*

## 07 · Folder tab (Mappe)

What is in the project folder, what is computing, and what can be ordered from the iPad.

**On screen**

1. **Folder name, reload** (Mappe neu laden) — The folder's name and a button that asks again.
2. **What the sketch does** (Was die Skizze tut) — Check (Prüfen): invented volume is an error, geometry is checked. Design (Entwerfen): invented volume is the point — fast, no check, blue mark.
3. **Run** (Lauf abbrechen) — What is computing now. A bar only for counted steps, otherwise just a sign of life; cancel run asks for a stop between two steps.
4. **Three variants** (Drei Varianten) — From three seeds (Drei Startwerte) or from three layers (Drei Ebenen); «Drei Startwerte rechnen» orders them.
5. **Images** (Bilder) — Every image with its check mark; a tap opens it full size.
6. **Sketches** — Open, computed or discarded (offen, gerechnet, verworfen). Compute (Rechnen lassen) with an optional instruction, give a name (Namen geben), open the result (Bild ansehen). With «Drei Ebenen» chosen: add sketches to a row (Zur Reihe) and compute it («Als Ebenen-Reihe rechnen»).

**What happens.** One run at a time: while one runs, ordering waits and says so. On the Layers tab a button leads to the running job, so cancelling is never hidden behind the other tab.

**Honest limit.** With a project folder open on the Mac, computing and naming from the iPad are refused with a sentence — images are then made in the node view on the Mac. A discarded sketch cannot be brought back from the iPad.

*Source: Bilder/Mappentafel.swift · Laufanzeige.swift · Skizzenliste.swift · Bildband.swift*

## 08 · Viewing an image (Bildansicht)

One image full size, with its check mark and what the computer says about it.

**On screen**

1. **Back, name, rename** (Namen geben) — Back to the strip (Zurück zum Bildband); the pencil gives the image its own name in the folder.
2. **Check mark** — Frame and stripe on the image: passed (BESTANDEN, green), failed (DURCHGEFALLEN, red), draft (ENTWURF — NICHT GEPRÜFT, blue); dashed means not measured. A missing number reads «ohne Zahl», never 0.
3. **Before / after** — Underlay and AI image side by side (Nebeneinander) or with a slider (Wischregler).
4. **Sketch on it** (Darauf skizzieren) — Puts this image under the layers as underlay and returns to the sheet.
5. **How the image is read** (Wie das Bild gelesen wird) — Check or Design, right at the image.
6. **What the server says** (Was der Server sagt) — Verdict, number, threshold (Schwelle), caveat (Vorbehalt) and hints.
7. **Variants side by side** (Varianten nebeneinander) — Three places; an empty place says it is empty.
8. **Share** (Teilen) — Shares only the image with its mark burned in — the caveat travels with it.

**What happens.** Portrait puts the information panel below the image — same content, other arrangement.

**Honest limit.** The iPad decides nothing about an image: colour, word, number and caveat come from the computer. Naming is refused when the folder is on the Mac.

*Source: Bilder/Bildansicht.swift · Bildvergleich.swift · Varianten.swift · Teilen.swift · Kern/Pruefzeichen.swift*

## 09 · Settings and updates

The iPad app has no settings page. A few things are remembered; updates arrive only as a notice.

**On screen**

1. **New version notice** (am Mac in Xcode aufspielen) — Under the status line when a newer version exists; checked at start and once a day; can be hidden (✕).
2. **Expiry notice** (am Mac in Xcode neu aufspielen) — From two days before the app's permission runs out.
3. **Remembered** — The toolbar side, the paired Mac (its key in the iPad keychain) and the project folder field on the pairing screen.
4. **Not remembered** — Tool and stroke start with the pen and the middle width every time.

**What happens.** Installing is done on the Mac in Xcode; the notice says exactly that.

**Honest limit.** An iPad app may not replace itself — Apple allows that only through the App Store or TestFlight. With a free Apple account the app runs seven days, then it is installed again.

**Planned — decided, not built**

- A settings page with the switch «Mit dem Finger zeichnen», default off. *(Decision 141)*

*Source: Verbindung/Fassungshinweis.swift · Kern/Aktualisierung.swift · Leiste/Leistenwahl.swift*

## 10 · Limits today — and what is planned

What the iPad app cannot do yet, kept apart from what has been decided for after the demo.

**Limits today**

- **Pencil only** — Fingers move and zoom; they do not draw.
- **Never computes** — Every image is made elsewhere; without a paired Mac nothing leaves the iPad.
- **Only via the Mac** — Encrypted, through the Mac — no direct way to the home PC any more.
- **Folder on the Mac** — Computing and naming from the iPad are refused; images are made in the node view.
- **No note when sending** — The instruction is typed when ordering, not when placing.
- **No settings page** — See card 09.

**What happens.** Order after the demo: first drawn sheets for the owner to decide on, then the build — I8 before I9.

**Honest limit.** Nothing in the planned list exists in the app today; the cards before this one describe only what is built.

**Planned — decided, not built**

- Draw with the finger: a switch «Mit dem Finger zeichnen» in the settings, default off. *(Decision 141)*
- I8 · Sketch on a Visbox base: for perspective and axonometric views a light line drawing of the model from the camera, switchable to the computed base image; a locked lower layer at 60 % opacity that can be hidden and is never drawn into. *(Decision 145)*
- I9 · Templates per sketch type: plan, section and elevation get a true-to-scale base from the model at the chosen scale; freehand gets only a grid. The type is chosen when the sketch is created. *(Decision 145)*
- The iPad in floating islands with a tool wheel at the top left. *(Decision 135)*

*Source: docs/ENTSCHEIDE_IPAD_2026-09-21.md (Decisions 135, 141, 145)*
