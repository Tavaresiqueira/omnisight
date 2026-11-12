import test from "node:test";
import assert from "node:assert/strict";
import { runIsolatedAnalysis, validatePayload, MAX_HTML_BYTES, startupDiagnostic } from "../src/runtime.js";

test("validates HTML and bounded stylesheet input", () => {
  assert.deepEqual(validatePayload({ html: "<main/>", stylesheets: ["body{}"] }), { html: "<main/>", stylesheets: ["body{}"] });
  assert.throws(() => validatePayload({ html: "x".repeat(MAX_HTML_BYTES + 1) }), /invalid_html/);
});

test("executes the report and destroys the isolated sandbox", async () => {
  const calls = [];
  const sandbox = {
    id: "test-vm",
    files: { write: async (...args) => calls.push(["write", ...args]) },
    exec: (command, options) => {
      calls.push(["exec", command, options]);
      return { stdin: { write: async (data) => calls.push(["stdin", data]), end: async () => calls.push(["eof"]) },
        then: (resolve) => resolve({ exitCode: 0, timedOut: false, truncated: false, stdout: '{"version":1}', stderr: "" }) };
    },
    destroy: async () => calls.push(["destroy"]),
  };
  const report = await runIsolatedAnalysis({ Sandbox: { create: async (_template, options) => { calls.push(["create", options]); return sandbox; } }, template: {}, payload: { html: "<main/>" }, bundleDir: new URL("../../browser", import.meta.url).pathname });
  assert.deepEqual(report, { version: 1 });
  assert.equal(calls[0][0], "create");
  assert.equal(calls.at(-1)[0], "destroy");
  assert.equal(calls[0][1].networkIsolation, "ISOLATED");
});

test("destroys VM after an execution failure", async () => {
  let destroyed = false;
  const sandbox = { files: { write: async () => {} }, exec: () => ({ stdin: { write: async () => {}, end: async () => {} }, then: (resolve) => resolve({ exitCode: 2, timedOut: false, truncated: false, stdout: "", stderr: "" }) }), destroy: async () => { destroyed = true; } };
  await assert.rejects(runIsolatedAnalysis({ Sandbox: { create: async () => sandbox }, template: {}, payload: { html: "<main/>" }, bundleDir: new URL("../../browser", import.meta.url).pathname }), /analysis_failed/);
  assert.equal(destroyed, true);
});


test("startup diagnostics redact credentials and bound provider messages", () => {
  const diagnostic = startupDiagnostic(Object.assign(new Error("token secret secret " + "x".repeat(1000)), { status: 403 }), ["secret"]);
  assert.equal(diagnostic.status, 403);
  assert.equal(diagnostic.message.includes("secret"), false);
  assert.ok(diagnostic.message.startsWith("token [REDACTED] [REDACTED]"));
  assert.equal(diagnostic.message.length, 500);
});
