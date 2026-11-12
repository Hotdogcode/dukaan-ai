# Barcode Management Architecture

## 1. Multi-Barcode Support
Packaged FMCG goods in India frequently update outer wrappers, causing barcode changes while retaining the same product identity. DukaanAI supports:
- Multiple barcodes mapped to a single `ProductVariant`.
- Primary vs secondary barcode designations (`is_primary = TRUE/FALSE`).
- Direct barcode lookup API: `GET /api/v1/barcodes/lookup?barcode={barcode}` returning product, variant, current prices, and stock indicators.
- Quick barcode registration endpoint: `POST /api/v1/barcodes` associating new barcode labels with existing products directly from the mobile scanner.

## 2. Barcode Scanning Experience
On Android, barcode scanning is built natively in `BarcodeScannerScreen.kt`:
- **Engine:** Google ML Kit Barcode Scanning (`BarcodeScanning.getClient(...)`) with CameraX `ImageAnalysis`.
- **Supported Formats:** EAN-13, EAN-8, UPC-A, UPC-E, Code-128, Code-39, QR Code.
- **Performance Optimizations:**
  - Fast throttle (1500 ms cooldown) prevents repeat double-scans of the same item.
  - Custom UI viewfinder with corner reticles and animated laser line.
  - Flashlight / Torch toggle button for dim kirana storage environments.
  - Manual entry fallback dialog if camera cannot focus on damaged or torn packaging barcodes.
