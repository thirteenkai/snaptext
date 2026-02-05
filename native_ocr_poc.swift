import Cocoa
import Vision

// 1. Get image from clipboard or path (simulation: take screenshot to temp)
func takeScreenshot() -> String? {
    let path = "/tmp/test_ocr_swift.png"
    let task = Process()
    task.launchPath = "/usr/sbin/screencapture"
    task.arguments = ["-x", path] // -x: quiet
    task.launch()
    task.waitUntilExit()
    return FileManager.default.fileExists(atPath: path) ? path : nil
}

// 2. Perform OCR using Vision Framework
func recognizeText(imagePath: String) {
    guard let image = NSImage(contentsOfFile: imagePath),
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("Failed to load image")
        return
    }

    let request = VNRecognizeTextRequest { (request, error) in
        if let error = error {
            print("Error: \(error)")
            return
        }
        guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
        
        let recognizedStrings = observations.compactMap { observation in
            return observation.topCandidates(1).first?.string
        }
        
        print("\n--- OCR Result (Native Swift) ---")
        print(recognizedStrings.joined(separator: "\n"))
        print("---------------------------------")
    }

    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["zh-Hans", "en-US"] // Support Chinese & English

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try? handler.perform([request])
}

// Main execution
print("📸 Taking screenshot...")
if let path = takeScreenshot() {
    print("✨ Recognizing text from \(path)...")
    let start = DispatchTime.now()
    recognizeText(imagePath: path)
    let end = DispatchTime.now()
    let nanoTime = end.uptimeNanoseconds - start.uptimeNanoseconds
    let timeInterval = Double(nanoTime) / 1_000_000_000
    print("⏱️ Time taken: \(String(format: "%.3f", timeInterval)) seconds")
}
