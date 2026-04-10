// @ts-check

/**
 * @param {{ fsp: typeof import("fs/promises"), stepbitAppConfigPath: string }} options
 */
function createStepbitService({ fsp, stepbitAppConfigPath }) {
  function parseYamlSectionValue(raw, sectionName, keyName) {
    const sectionPattern = new RegExp(`^${sectionName}:\\s*$([\\s\\S]*?)(?=^\\S|\\Z)`, "m");
    const sectionMatch = String(raw || "").match(sectionPattern);
    if (!sectionMatch) return "";
    const keyPattern = new RegExp(`^\\s*${keyName}:\\s*(.+)\\s*$`, "m");
    const keyMatch = sectionMatch[1].match(keyPattern);
    return keyMatch ? keyMatch[1].trim() : "";
  }

  function normalizeStepbitHost(rawHost) {
    const host = String(rawHost || "").trim();
    if (!host) return "127.0.0.1";
    return host.replace(/^https?:\/\//i, "").replace(/\/+$/, "");
  }

  function normalizeStepbitPort(rawPort) {
    const port = Number.parseInt(String(rawPort || "").trim(), 10);
    return Number.isFinite(port) && port > 0 ? port : 7860;
  }

  async function readStepbitAppConfig() {
    const raw = await fsp.readFile(stepbitAppConfigPath, "utf8");
    return {
      apiKey: parseYamlSectionValue(raw, "api_keys", "stepbit"),
      host: normalizeStepbitHost(parseYamlSectionValue(raw, "stepbit", "host")),
      port: normalizeStepbitPort(parseYamlSectionValue(raw, "stepbit", "port")),
    };
  }

  function extractStepbitDelta(payload) {
    if (!payload || typeof payload !== "object") return "";
    if (typeof payload.delta === "string") return payload.delta;
    if (typeof payload.content === "string") return payload.content;
    if (typeof payload.text === "string") return payload.text;
    if (Array.isArray(payload.choices) && payload.choices.length) {
      return extractStepbitDelta(payload.choices[0]?.delta || payload.choices[0]?.message || payload.choices[0]);
    }
    return "";
  }

  async function readStepbitSseResponse(response) {
    const reader = response.body?.getReader?.();
    if (!reader) {
      throw new Error("Stepbit response body could not be read.");
    }

    const decoder = new TextDecoder();
    let buffer = "";
    let content = "";

    function processEventBlock(block) {
      const lines = block
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
      if (!lines.length) return;
      const dataLines = lines.filter((line) => line.startsWith("data:"));
      if (!dataLines.length) return;
      const payloadText = dataLines.map((line) => line.slice(5).trim()).join("\n");
      if (!payloadText || payloadText === "[DONE]") return;
      try {
        const payload = JSON.parse(payloadText);
        content += extractStepbitDelta(payload);
      } catch (_error) {
        // Ignore partial or non-JSON event chunks.
      }
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split(/\r?\n\r?\n/);
      buffer = parts.pop() || "";
      parts.forEach(processEventBlock);
    }

    if (buffer.trim()) processEventBlock(buffer);
    return { content };
  }

  async function askChat(payload) {
    const prompt = typeof payload?.prompt === "string" ? payload.prompt.trim() : "";
    if (!prompt) throw new Error("Stepbit prompt is required.");

    const config = await readStepbitAppConfig();
    if (!config.apiKey) {
      throw new Error("Stepbit API key is missing from stepbit-app/config.yaml.");
    }

    const endpoint = `http://${config.host}:${config.port}/ai/completions`;
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": config.apiKey,
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      let errorMessage = `Stepbit request failed (${response.status}).`;
      try {
        const body = await response.text();
        const parsed = body ? JSON.parse(body) : null;
        if (parsed?.error) errorMessage = parsed.error;
      } catch (_error) {
        // Ignore body parse failures and return the HTTP-derived message.
      }
      if (response.status === 401) {
        throw new Error("Stepbit rejected the local API key from config.yaml.");
      }
      throw new Error(errorMessage);
    }

    const result = await readStepbitSseResponse(response);
    if (!result.content) {
      throw new Error("Stepbit returned no final content for this request.");
    }
    return {
      ...result,
      endpoint,
    };
  }

  return { askChat };
}

module.exports = { createStepbitService };
