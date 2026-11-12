import http from "node:http";
import { Sandbox } from "railway";
import { makeTemplate, runIsolatedAnalysis, MAX_REQUEST_BYTES } from "./runtime.js";

const port = Number(process.env.PORT || 9000);
const maxConcurrent = Number(process.env.MAX_CONCURRENT_SCANS || 2);
let template;
let active = 0;

function send(res, status, body) {
  res.writeHead(status, { "content-type": "application/json", "cache-control": "no-store", "connection": "close" });
  res.end(JSON.stringify(body));
}

async function readJson(req) {
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_REQUEST_BYTES) throw new Error("request_too_large");
    chunks.push(chunk);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8")); } catch { throw new Error("invalid_json"); }
}

const server = http.createServer(async (req, res) => {
  if (req.method === "GET" && req.url === "/health") return send(res, template ? 200 : 503, { status: template ? "ok" : "starting" });
  if (req.method !== "POST" || req.url !== "/analyze") return send(res, 404, { error: "not_found" });
  if (!template) return send(res, 503, { error: "starting" });
  if (active >= maxConcurrent) return send(res, 429, { error: "busy" });
  active++;
  try {
    const payload = await readJson(req);
    const report = await runIsolatedAnalysis({ Sandbox, template, payload });
    send(res, 200, report);
  } catch (error) {
    const clientError = ["invalid_payload", "invalid_html", "invalid_stylesheets", "invalid_json", "request_too_large"].includes(error?.message);
    send(res, clientError ? 400 : 502, { error: clientError ? error.message : "analysis_failed" });
  } finally { active--; }
});

server.listen(port, "::", async () => {
  try {
    template = await makeTemplate(Sandbox).build({ environmentId: process.env.RAILWAY_ENVIRONMENT_ID });
    console.log("browser broker ready");
  } catch {
    console.error("browser broker template build failed");
    process.exitCode = 1;
    server.close();
  }
});
