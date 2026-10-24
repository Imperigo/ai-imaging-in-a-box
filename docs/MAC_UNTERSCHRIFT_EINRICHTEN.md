# Feste Unterschrift für die Mac-App einrichten (Entscheid 128)

**Wozu:** Heute fragt macOS nach jedem Update der Mac-App zweimal nach deinem Passwort, weil die App bei
jedem Bau anders unterschrieben ist. Mit einer festen, eigenen Unterschrift fragt der Mac nach dem
nächsten Update **ein letztes Mal** – danach nicht mehr.

**Dauer:** etwa 10 Minuten, einmalig.

> **Wichtig – zuerst den Mac prüfen.** Mach das erst, **nachdem der Malware-Scan des Macs sauber
> abgeschlossen ist.** Die Unterschrift ist nur so vertrauenswürdig wie der Rechner, auf dem sie entsteht.

> **Geheim halten.** Die Zertifikat-Datei und ihr Passwort gehören nur in GitHub (Schritt 2) und in deinen
> Passwortmanager – nie in einen Chat, eine Mail, eine Zentrale-Nachricht oder ins Repo.

---

## Schritt 1 · Die Unterschrift am Mac erzeugen

1. Öffne das Programm **Terminal** (Programme → Dienstprogramme → Terminal).
2. Kopiere den folgenden Block **ganz** hinein und drücke die Eingabetaste:

```sh
mkdir -p ~/visbox-zertifikat && cd ~/visbox-zertifikat
cat > einstellung.cnf <<'ENDE'
[req]
distinguished_name=dn
x509_extensions=ext
prompt=no
[dn]
CN=Visbox Eigenzertifikat
O=Visbox
[ext]
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature
extendedKeyUsage=critical,codeSigning
subjectKeyIdentifier=hash
ENDE
/usr/bin/openssl req -x509 -newkey rsa:2048 -nodes -keyout schluessel.pem -out zert.pem -days 3650 -config einstellung.cnf
/usr/bin/openssl pkcs12 -export -inkey schluessel.pem -in zert.pem -name "Visbox Eigenzertifikat" -out visbox-zertifikat.p12
```

3. Das Terminal fragt zweimal nach einem **Export Password**. Denk dir ein **neues** Passwort aus (nicht dein
   Mac-Passwort), tippe es zweimal ein und **notiere es im Passwortmanager**. Beim Tippen erscheinen keine
   Zeichen – das ist normal.

(`/usr/bin/openssl` ist das Werkzeug, das macOS mitbringt – bewusst dieses, weil seine Datei-Art von der Prüfstrecke sicher gelesen wird.)

Die Unterschrift gilt 10 Jahre und heisst «Visbox Eigenzertifikat». Ändere den Namen nicht – die
Prüfstrecke sucht genau diesen.

## Schritt 2 · Bei GitHub hinterlegen

1. Öffne im Browser das Visbox-Repo bei GitHub → *Settings* → links *Secrets and variables* → *Actions*.
2. **Erstes Geheimnis:**
   - Im Terminal eintippen und Eingabe drücken:
     ```sh
     base64 -i ~/visbox-zertifikat/visbox-zertifikat.p12 | pbcopy
     ```
     Damit liegt die Datei als langer Text in der Zwischenablage.
   - Bei GitHub: **New repository secret** → *Name*: `MAC_ZERT_P12` → ins Feld *Secret* einfügen (⌘V) →
     **Add secret**.
3. **Zweites Geheimnis:**
   - **New repository secret** → *Name*: `MAC_ZERT_PASSWORT` → das Passwort aus Schritt 1 eintippen →
     **Add secret**.
4. Lege die Datei `~/visbox-zertifikat/visbox-zertifikat.p12` zusammen mit dem Passwort im
   Passwortmanager ab (als Reserve) und lösche danach den Ordner:
   ```sh
   rm -rf ~/visbox-zertifikat
   ```

## Schritt 3 · Prüfen, dass es wirkt

1. Bei GitHub: **Actions** → links **iPad** → rechts **Run workflow** → **Run workflow**.
2. Nach etwa 3 Minuten den Lauf öffnen → Job mit der Mac-App → Schritt
   **«Unterschrift (festes Eigenzertifikat, sonst Behelf)»**. Dort muss stehen:
   **«Unterschrieben mit dem festen Eigenzertifikat (Entscheid 128)»**.
   Steht dort eine Warnung «Kein MAC_ZERT_P12 …», ist ein Name falsch geschrieben – Schritt 2 prüfen.
3. Beim **nächsten Update** am Mac fragt macOS **ein letztes Mal** nach deinem Passwort – zweimal, für beide
   Schlüsselbund-Einträge. Jedes Mal das Passwort eingeben und **«Immer erlauben»** wählen.
4. Beim **übernächsten** Update fragt der Mac nicht mehr. Fragt er doch, sag Bescheid.

**Was sich nicht ändert:** Beim allerersten Öffnen einer neu heruntergeladenen App warnt macOS weiterhin
(«nicht verifizierter Entwickler») – das liesse sich nur mit einer kostenpflichtigen Apple-Kennung ändern
und ist vor der Demo nicht nötig (Entscheid 128, Variante B).

---

## Nach einem Update: die iPads und die alten Einträge im Schlüsselbund

**Was du sehen kannst (bis die feste Unterschrift wirkt):** Nach einem Update fragt macOS beim Start
der Mac-App unter Umständen **ein drittes Mal** nach deinem Passwort – für den Schlüssel der
iPad-Verbindung («Visbox · iPad-Leitung»). Gib das Passwort ein und wähle **«Immer erlauben»**: Dann
behält der Mac sein Zertifikat, und die iPads bleiben gekoppelt.

**Wenn es trotzdem nicht geht** (abgelehnt, oder macOS lässt die App nicht an den Schlüssel): Der Mac
legt **einmal** ein neues Zertifikat an und sagt es in der Zeile «iPad»: *«… jedes iPad muss einmal neu
koppeln»*. Dann am Mac **iPad → iPad koppeln** und am iPad neu koppeln. Ein weiteres Mal legt er in
derselben Fassung kein neues an.

**Am Demotag:** nach dem Koppeln den Mac **nicht mehr aktualisieren**.

### Alte Einträge löschen (einmalig, etwa 3 Minuten)

Bis Fassung 0.3.54 legte die Mac-App nach jedem Update still ein neues Zertifikat an; die alten liegen
noch im Schlüsselbund. Sie schaden nichts, verwirren aber. Die App kann sie selbst nicht löschen (sie
gehören für macOS einer «anderen» App), darum von Hand:

1. Die Mac-App **beenden** (Visbox → Visbox beenden).
2. Das Programm **Schlüsselbundverwaltung** öffnen (Programme → Dienstprogramme → Schlüsselbundverwaltung;
   ab macOS 15 auch über die Suche «Schlüsselbundverwaltung»).
3. Links **«Anmeldung»** wählen, oben **«Zertifikate»**. Ins Suchfeld oben rechts **`Visbox Mac`** tippen.
4. Alle Einträge **«Visbox Mac …»** markieren (⌘A), Rechtsklick → **Löschen** → bestätigen. macOS fragt
   dabei nach deinem Passwort.
5. Oben **«Schlüssel»** wählen und ins Suchfeld **`iPad-Leitung`** tippen. Alle Einträge
   **«Visbox · iPad-Leitung»** ebenso löschen.
6. **Nichts anderes löschen** – besonders nicht die Einträge mit dem Kennwort des Heim-PCs und dem Zugang
   des iPad (Art «Programmpasswort»).
7. Die Mac-App wieder öffnen: Sie legt ein frisches Zertifikat an und sagt in der Zeile «iPad», dass die
   iPads neu koppeln müssen. **iPad → iPad koppeln**, am iPad neu koppeln – fertig.

Am besten machst du das **direkt nach dem Einrichten der festen Unterschrift** (Schritt 3), oder vor dem
Demotag **vor** dem letzten Koppeln – nicht danach.
