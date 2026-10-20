import AVFoundation
import SwiftUI
import UIKit
import VisionKit

/// «Mit QR-Code koppeln»: liest den QR-Code im Koppelfenster des Mac — **mit der Kamera in
/// der App** (Entscheid 99b), nicht mit der Kamera-App des Systems: Die gäbe den Text an
/// Safari weiter, und das iPad wüsste nichts davon.
///
/// * **VisionKit zuerst** (`DataScannerViewController`, iPadOS 16): Es findet den Code selbst
///   und markiert ihn. Wo es nicht geht (ältere Geräte, Simulator), **AVFoundation**
///   (`AVCaptureMetadataOutput`, nur QR).
/// * **Was der Code heisst, sagt der Kern** (`Koppelschein.lies`). Ein fremder QR-Code
///   schliesst den Leser nicht, sondern sagt, warum er nicht passt — man hält dann den
///   richtigen hin.
/// * Die Erlaubnis für die Kamera erbittet das Manifest (`.camera(purposeString:)`); ist sie
///   verweigert, steht der Weg in die Einstellungen da, und die Zahl bleibt.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — ob der Code am Bildschirm des Mac im
/// ersten Anlauf erkannt wird, zeigt erst ein Gerät.
@MainActor
struct QRLeser: View {
    /// Ein geprüfter Schein — der Leser ist damit fertig.
    let gelesen: (Koppelschein) -> Void
    let abbrechen: () -> Void

    private enum Weg: Equatable {
        case pruefen
        case datenscanner
        case kamera
        case keiner(String)
    }

    @State private var weg: Weg = .pruefen
    @State private var satz: String?
    @State private var fertig = false

    var body: some View {
        NavigationStack {
            ZStack(alignment: .bottom) {
                Color.black.ignoresSafeArea()
                switch weg {
                case .pruefen:
                    ProgressView()
                        .tint(.white)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                case .datenscanner:
                    Datenscannerhuelle(gefunden: pruefe)
                        .ignoresSafeArea()
                case .kamera:
                    Kamerahuelle(gefunden: pruefe, fehler: { weg = .keiner($0) })
                        .ignoresSafeArea()
                case .keiner(let grund):
                    Text(grund)
                        .font(Schrift.text(16))
                        .foregroundStyle(.white)
                        .multilineTextAlignment(.center)
                        .padding(32)
                        .frame(maxWidth: 520, maxHeight: .infinity)
                }
                Text(satz ?? "Den QR-Code im Koppelfenster des Mac in den Rahmen halten.")
                    .font(Schrift.text(15))
                    .foregroundStyle(.white)
                    .multilineTextAlignment(.center)
                    .padding(16)
                    .background(RoundedRectangle(cornerRadius: 12).fill(.black.opacity(0.6)))
                    .padding(24)
            }
            .navigationTitle("QR-Code vom Mac lesen")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Abbrechen", action: abbrechen)
                }
            }
        }
        .task { await waehleWeg() }
    }

    /// Welcher Weg geht — erst die Erlaubnis, dann VisionKit, dann AVFoundation.
    private func waehleWeg() async {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .notDetermined:
            let erlaubt = await AVCaptureDevice.requestAccess(for: .video)
            if !erlaubt {
                weg = .keiner(QRLeser.satzGesperrt)
                return
            }
        case .denied, .restricted:
            weg = .keiner(QRLeser.satzGesperrt)
            return
        case .authorized:
            break
        @unknown default:
            break
        }
        if DataScannerViewController.isSupported && DataScannerViewController.isAvailable {
            weg = .datenscanner
        } else if AVCaptureDevice.default(for: .video) != nil {
            weg = .kamera
        } else {
            weg = .keiner("Dieses Gerät hat keine Kamera, die QR-Codes liest. Abbrechen und "
                          + "die Zahl eintippen.")
        }
    }

    static let satzGesperrt = "Die Kamera ist für diese App gesperrt. Einstellungen → "
        + "\(Marke.name) → Kamera einschalten — oder abbrechen und die Zahl eintippen."

    /// Jeder gelesene Text geht durch den Kern; nur ein gültiger Schein beendet den Leser.
    private func pruefe(_ text: String) {
        guard !fertig else { return }
        switch Koppelschein.lies(text, jetzt: Date().timeIntervalSince1970) {
        case .gut(let schein):
            fertig = true
            gelesen(schein)
        case .schlecht(let grund):
            satz = grund
        }
    }
}

// ------------------------------------------------------------ VisionKit

/// `DataScannerViewController`, nur für QR-Codes, ein Code zugleich.
private struct Datenscannerhuelle: UIViewControllerRepresentable {
    let gefunden: @MainActor (String) -> Void

    func makeUIViewController(context: Context) -> DataScannerViewController {
        let leser = DataScannerViewController(recognizedDataTypes: [.barcode(symbologies: [.qr])],
                                              qualityLevel: .balanced,
                                              recognizesMultipleItems: false,
                                              isHighFrameRateTrackingEnabled: false,
                                              isHighlightingEnabled: true)
        leser.delegate = context.coordinator
        return leser
    }

    func updateUIViewController(_ leser: DataScannerViewController, context: Context) {
        context.coordinator.gefunden = gefunden
        // ERST HIER STARTEN, nicht beim Anlegen: Dort liegt die Ansicht noch in keinem
        // Fenster, und die Kamera bliebe dunkel.
        if !leser.isScanning { try? leser.startScanning() }
    }

    static func dismantleUIViewController(_ leser: DataScannerViewController,
                                          coordinator: Koordinator) {
        leser.stopScanning()
    }

    func makeCoordinator() -> Koordinator { Koordinator(gefunden: gefunden) }

    @MainActor
    final class Koordinator: NSObject, DataScannerViewControllerDelegate {
        var gefunden: @MainActor (String) -> Void

        init(gefunden: @escaping @MainActor (String) -> Void) {
            self.gefunden = gefunden
        }

        func dataScanner(_ dataScanner: DataScannerViewController,
                         didAdd addedItems: [RecognizedItem], allItems: [RecognizedItem]) {
            for eintrag in addedItems {
                if case .barcode(let code) = eintrag, let text = code.payloadStringValue {
                    gefunden(text)
                    return
                }
            }
        }
    }
}

// ------------------------------------------------------------ AVFoundation

/// Die Kamera über `AVCaptureSession` mit `AVCaptureMetadataOutput` — wo VisionKit nicht geht.
private struct Kamerahuelle: UIViewControllerRepresentable {
    let gefunden: @MainActor (String) -> Void
    let fehler: @MainActor (String) -> Void

    func makeUIViewController(context: Context) -> Kamerablatt {
        Kamerablatt(gefunden: gefunden, fehler: fehler)
    }

    func updateUIViewController(_ blatt: Kamerablatt, context: Context) {}
}

private final class Kamerablatt: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    private let gefunden: @MainActor (String) -> Void
    private let fehler: @MainActor (String) -> Void
    private let sitzung = AVCaptureSession()
    private var vorschau: AVCaptureVideoPreviewLayer?
    /// Derselbe Code wird nicht in jedem Bild neu gemeldet.
    private var zuletzt: String?

    init(gefunden: @escaping @MainActor (String) -> Void,
         fehler: @escaping @MainActor (String) -> Void) {
        self.gefunden = gefunden
        self.fehler = fehler
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) { nil }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        guard let kamera = AVCaptureDevice.default(for: .video),
              let eingang = try? AVCaptureDeviceInput(device: kamera),
              sitzung.canAddInput(eingang) else {
            melde("Die Kamera liess sich nicht öffnen. Abbrechen und die Zahl eintippen.")
            return
        }
        sitzung.addInput(eingang)
        let ausgang = AVCaptureMetadataOutput()
        guard sitzung.canAddOutput(ausgang) else {
            melde("Die Kamera liest hier keine Codes. Abbrechen und die Zahl eintippen.")
            return
        }
        sitzung.addOutput(ausgang)
        ausgang.setMetadataObjectsDelegate(self, queue: .main)
        // ERST NACH `addOutput`: Vorher kennt der Ausgang keine Arten, und `.qr` wirft.
        ausgang.metadataObjectTypes = [.qr]

        let schicht = AVCaptureVideoPreviewLayer(session: sitzung)
        schicht.videoGravity = .resizeAspectFill
        schicht.frame = view.bounds
        view.layer.addSublayer(schicht)
        vorschau = schicht
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        vorschau?.frame = view.bounds
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        // `startRunning` blockiert, bis die Kamera laeuft — nicht auf dem Hauptfaden.
        let s = sitzung
        DispatchQueue.global(qos: .userInitiated).async { if !s.isRunning { s.startRunning() } }
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        let s = sitzung
        DispatchQueue.global(qos: .userInitiated).async { if s.isRunning { s.stopRunning() } }
    }

    /// Ein Fehler beim Anlegen geht **nach** dem Aufbau der Ansicht hinaus: SwiftUI mag
    /// keinen Zustand, der sich mitten im Zeichnen ändert.
    private func melde(_ satz: String) {
        Task { @MainActor [fehler] in fehler(satz) }
    }

    // DER RUECKRUF KOMMT AUF `.main` (so beim Ausgang gesetzt) — darum `assumeIsolated`.
    // Herausgereicht werden nur die Texte, nicht die Objekte der Kamera.
    nonisolated func metadataOutput(_ output: AVCaptureMetadataOutput,
                                    didOutput metadataObjects: [AVMetadataObject],
                                    from connection: AVCaptureConnection) {
        let texte: [String] = metadataObjects.compactMap { objekt in
            guard let code = objekt as? AVMetadataMachineReadableCodeObject,
                  code.type == .qr else { return nil }
            return code.stringValue
        }
        MainActor.assumeIsolated { self.gelesen(texte) }
    }

    private func gelesen(_ texte: [String]) {
        guard let text = texte.first, text != zuletzt else { return }
        zuletzt = text
        gefunden(text)
    }
}
