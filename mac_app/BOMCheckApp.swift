import AppKit
import SwiftUI
import UniformTypeIdentifiers

@main
struct BOMCheckApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 760, minHeight: 520)
        }
        .windowStyle(.titleBar)
    }
}

struct ContentView: View {
    @State private var bomURL: URL?
    @State private var pdfURL: URL?
    @State private var outputURL: URL = AppPaths.defaultOutputDirectory
    @State private var isRunning = false
    @State private var statusText = "就绪"
    @State private var logText = ""
    @State private var lastRunSucceeded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("BOM Check")
                        .font(.system(size: 26, weight: .semibold))
                    Text("Excel + 原理图 PDF")
                        .foregroundStyle(.secondary)
                }
                Spacer()
                if isRunning {
                    ProgressView()
                        .controlSize(.small)
                }
                Text(statusText)
                    .foregroundStyle(lastRunSucceeded ? .green : .secondary)
            }

            VStack(spacing: 12) {
                PickerRow(
                    title: "BOM Excel",
                    systemImage: "tablecells",
                    url: bomURL,
                    placeholder: "未选择",
                    buttonTitle: "选择 Excel",
                    action: chooseBOM
                )

                PickerRow(
                    title: "原理图 PDF",
                    systemImage: "doc.richtext",
                    url: pdfURL,
                    placeholder: "未选择",
                    buttonTitle: "选择 PDF",
                    action: choosePDF
                )

                PickerRow(
                    title: "输出目录",
                    systemImage: "folder",
                    url: outputURL,
                    placeholder: "未选择",
                    buttonTitle: "选择目录",
                    action: chooseOutput
                )
            }

            HStack(spacing: 10) {
                Button(action: runCheck) {
                    Label("运行检查", systemImage: "play.fill")
                }
                .keyboardShortcut(.return, modifiers: .command)
                .disabled(isRunning || bomURL == nil || pdfURL == nil)

                Button(action: openOutput) {
                    Label("打开输出", systemImage: "arrow.up.right.square")
                }
                .disabled(!lastRunSucceeded)

                Spacer()

                Button(action: clearLog) {
                    Label("清空日志", systemImage: "trash")
                }
                .disabled(logText.isEmpty || isRunning)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("日志")
                    .font(.headline)
                TextEditor(text: $logText)
                    .font(.system(.body, design: .monospaced))
                    .scrollContentBackground(.hidden)
                    .background(Color(nsColor: .textBackgroundColor))
                    .clipShape(RoundedRectangle(cornerRadius: 6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color(nsColor: .separatorColor), lineWidth: 1)
                    )
            }
        }
        .padding(22)
        .onAppear {
            createDefaultOutputDirectory()
            appendLog("Workspace: \(AppPaths.workspaceRoot.path)")
            appendLog("CLI: \(AppPaths.bomcheckExecutable.path)")
        }
    }

    private func chooseBOM() {
        let types = [
            UTType(filenameExtension: "xlsx"),
            UTType(filenameExtension: "xlsm"),
            UTType(filenameExtension: "xltx"),
            UTType(filenameExtension: "xltm"),
            UTType(filenameExtension: "csv"),
        ].compactMap { $0 }
        if let url = openFilePanel(types: types) {
            bomURL = url
            lastRunSucceeded = false
        }
    }

    private func choosePDF() {
        if let url = openFilePanel(types: [.pdf]) {
            pdfURL = url
            lastRunSucceeded = false
        }
    }

    private func chooseOutput() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.canCreateDirectories = true
        panel.allowsMultipleSelection = false
        panel.directoryURL = outputURL
        if panel.runModal() == .OK, let url = panel.url {
            outputURL = url
            lastRunSucceeded = false
        }
    }

    private func openFilePanel(types: [UTType]) -> URL? {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.allowedContentTypes = types
        return panel.runModal() == .OK ? panel.url : nil
    }

    private func runCheck() {
        guard let bomURL, let pdfURL else { return }
        createDefaultOutputDirectory()
        isRunning = true
        lastRunSucceeded = false
        statusText = "运行中"
        appendLog("")
        appendLog("开始检查")
        appendLog("BOM: \(bomURL.path)")
        appendLog("PDF: \(pdfURL.path)")
        appendLog("OUT: \(outputURL.path)")

        DispatchQueue.global(qos: .userInitiated).async {
            let result = BOMCheckRunner.run(bom: bomURL, pdf: pdfURL, outdir: outputURL)
            DispatchQueue.main.async {
                appendLog(result.output)
                isRunning = false
                lastRunSucceeded = result.exitCode == 0
                statusText = result.exitCode == 0 ? "完成" : "失败"
                if result.exitCode == 0 {
                    appendLog("输出完成: \(outputURL.path)")
                } else {
                    appendLog("退出码: \(result.exitCode)")
                }
            }
        }
    }

    private func openOutput() {
        NSWorkspace.shared.open(outputURL)
    }

    private func clearLog() {
        logText = ""
    }

    private func appendLog(_ text: String) {
        if logText.isEmpty {
            logText = text
        } else {
            logText += "\n" + text
        }
    }

    private func createDefaultOutputDirectory() {
        try? FileManager.default.createDirectory(at: outputURL, withIntermediateDirectories: true)
    }
}

struct PickerRow: View {
    let title: String
    let systemImage: String
    let url: URL?
    let placeholder: String
    let buttonTitle: String
    let action: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Label(title, systemImage: systemImage)
                .frame(width: 120, alignment: .leading)

            Text(url?.path ?? placeholder)
                .lineLimit(1)
                .truncationMode(.middle)
                .foregroundStyle(url == nil ? .secondary : .primary)
                .frame(maxWidth: .infinity, alignment: .leading)

            Button(action: action) {
                Label(buttonTitle, systemImage: "folder")
            }
        }
    }
}

struct CommandResult {
    let exitCode: Int32
    let output: String
}

enum BOMCheckRunner {
    static func run(bom: URL, pdf: URL, outdir: URL) -> CommandResult {
        let process = Process()
        process.executableURL = AppPaths.bomcheckExecutable
        process.currentDirectoryURL = AppPaths.devkitDirectory
        process.arguments = [
            "run",
            "--bom", bom.path,
            "--pdf", pdf.path,
            "--outdir", outdir.path,
        ]
        process.environment = [
            "PATH": "\(AppPaths.venvBinDirectory.path):/usr/bin:/bin:/usr/sbin:/sbin",
            "PYTHONUTF8": "1",
            "LC_ALL": "en_US.UTF-8",
        ]

        let stdout = Pipe()
        let stderr = Pipe()
        process.standardOutput = stdout
        process.standardError = stderr

        do {
            try process.run()
            process.waitUntilExit()
        } catch {
            return CommandResult(exitCode: -1, output: "无法启动 bomcheck: \(error.localizedDescription)")
        }

        let output = read(stdout) + read(stderr)
        return CommandResult(exitCode: process.terminationStatus, output: output.trimmingCharacters(in: .whitespacesAndNewlines))
    }

    private static func read(_ pipe: Pipe) -> String {
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8) ?? ""
    }
}

enum AppPaths {
    static let workspaceRoot: URL = {
        let bundleURL = Bundle.main.bundleURL
        let candidate = bundleURL.deletingLastPathComponent().deletingLastPathComponent()
        if FileManager.default.fileExists(atPath: candidate.appendingPathComponent("bom_check_devkit").path) {
            return candidate
        }
        return URL(fileURLWithPath: "/Users/steed/Sync/AI/BOM_Check")
    }()

    static let devkitDirectory = workspaceRoot.appendingPathComponent("bom_check_devkit")
    static let venvBinDirectory = devkitDirectory.appendingPathComponent(".venv/bin")
    static let bomcheckExecutable = venvBinDirectory.appendingPathComponent("bomcheck")
    static let defaultOutputDirectory = workspaceRoot.appendingPathComponent("out_app")
}
