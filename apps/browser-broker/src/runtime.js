import { createReadStream } from "node:fs";
import path from "node:path";

export const MAX_HTML_BYTES = 2 * 1024 * 1024;
export const MAX_STYLESHEETS = 3;
export const MAX_STYLESHEET_BYTES = 256 * 1024;
export const MAX_REQUEST_BYTES = 4 * 1024 * 1024 + 65536;
export const MAX_REPORT_BYTES = 1024 * 1024;
export const VM_TIMEOUT_SECONDS = 40;

const BROWSER_ROOT = "/broker/omnisight-browser";
const VM_ROOT = "/opt/omnisight";
const FILES = ["runner.py", "visual_capture.py", "visual.js", "axe_scan.js", "vendor/axe.min.js", "vendor/pt_BR.json"];

export function startupDiagnostic(error, secrets = []) {
  let message = String(error?.message || "unknown_error");
  for (const secret of secrets) if (secret) message = message.replaceAll(secret, "[REDACTED]");
  return { name: String(error?.name || "Error"), status: error?.status, message: message.slice(0, 500) };
}

export function validatePayload(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("invalid_payload");
  if (typeof value.html !== "string" || Buffer.byteLength(value.html, "utf8") > MAX_HTML_BYTES) throw new Error("invalid_html");
  const stylesheets = value.stylesheets ?? [];
  if (!Array.isArray(stylesheets) || stylesheets.length > MAX_STYLESHEETS || stylesheets.some((css) => typeof css !== "string" || Buffer.byteLength(css, "utf8") > MAX_STYLESHEET_BYTES)) throw new Error("invalid_stylesheets");
  return { html: value.html, stylesheets };
}

export function makeTemplate(Sandbox) {
  return Sandbox.template()
    .withEnv({ DEBIAN_FRONTEND: "noninteractive", PLAYWRIGHT_BROWSERS_PATH: "/opt/pw-browsers" })
    .withPackages("python3", "python3-venv", "python3-pip", "ca-certificates")
    .workdir("/opt")
    .run("python3 -m venv /opt/scan-venv && /opt/scan-venv/bin/pip install --no-cache-dir playwright==1.62.0 && PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers /opt/scan-venv/bin/python -m playwright install --with-deps chromium && useradd --create-home --uid 1001 scanuser && chown -R scanuser:scanuser /opt/scan-venv /opt/pw-browsers");
}

export async function runIsolatedAnalysis({ Sandbox, template, payload, bundleDir = BROWSER_ROOT, timeoutSec = VM_TIMEOUT_SECONDS }) {
  const input = validatePayload(payload);
  let sandbox;
  try {
    sandbox = await Sandbox.create(template, { idleTimeoutMinutes: 1, networkIsolation: "ISOLATED", resources: { cpu: 2, memoryGB: 2 } });
    for (const rel of FILES) {
      const bytes = await new Promise((resolve, reject) => {
        const chunks = [];
        createReadStream(path.join(bundleDir, rel)).on("data", (chunk) => chunks.push(chunk)).on("error", reject).on("end", () => resolve(Buffer.concat(chunks)));
      });
      await sandbox.files.write(`${VM_ROOT}/${rel}`, bytes, { mode: 0o644 });
    }
    const handle = sandbox.exec("/usr/sbin/runuser -u scanuser -- env PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers /opt/scan-venv/bin/python /opt/omnisight/runner.py", {
      cwd: VM_ROOT, timeoutSec, maxOutputBytes: MAX_REPORT_BYTES, stdin: true,
      env: { HOME: "/home/scanuser", PYTHONUNBUFFERED: "1" },
    });
    await handle.stdin.write(JSON.stringify(input));
    await handle.stdin.end();
    const result = await handle;
    if (result.truncated || result.timedOut || result.exitCode !== 0 || Buffer.byteLength(result.stdout, "utf8") > MAX_REPORT_BYTES) throw new Error("analysis_failed");
    let report;
    try { report = JSON.parse(result.stdout); } catch { throw new Error("invalid_report"); }
    if (!report || typeof report !== "object" || Array.isArray(report)) throw new Error("invalid_report");
    return report;
  } finally {
    if (sandbox) await sandbox.destroy();
  }
}
