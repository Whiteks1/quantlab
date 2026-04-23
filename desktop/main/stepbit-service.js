// @ts-nocheck -- legacy JS file, not migrated to strict TypeScript. See #462.

/**
 * @param {object} _options  (kept for API compatibility — no longer reads stepbit-app config)
 */
function createStepbitService(_options) {

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

    // Route through stepbit-core OpenAI-compatible endpoint.
    const STEPBIT_CORE_URL = String(process.env.STEPBIT_CORE_URL || "http://127.0.0.1:3000").trim();
    const STEPBIT_CORE_API_KEY = String(process.env.STEPBIT_CORE_API_KEY || "").trim();
    if (!STEPBIT_CORE_API_KEY) {
      throw new Error("STEPBIT_CORE_API_KEY is required.");
    }

    const messages =
      Array.isArray(payload?.messages) && payload.messages.length > 0
        ? payload.messages
        : [{ role: "user", content: prompt }];

    const endpoint = `${STEPBIT_CORE_URL}/v1/chat/completions`;

    let response;
    try {
      response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${STEPBIT_CORE_API_KEY}`,
        },
        body: JSON.stringify({
          model: "default",
          messages,
          stream: true,
        }),
      });
    } catch (networkError) {
      throw new Error(
        `stepbit-core is not reachable at ${STEPBIT_CORE_URL}. ` +
        `Make sure the stack is running. (${networkError?.message || networkError})`
      );
    }

    if (!response.ok) {
      let errorMessage = `stepbit-core request failed (${response.status}).`;
      try {
        const body = await response.text();
        const parsed = body ? JSON.parse(body) : null;
        if (parsed?.error) {
          errorMessage = typeof parsed.error === "string"
            ? parsed.error
            : JSON.stringify(parsed.error);
        }
      } catch (_error) {
        // Ignore body parse failures and return the HTTP-derived message.
      }
      if (response.status === 401) {
        throw new Error("stepbit-core rejected the API key. Check STEPBIT_CORE_API_KEY.");
      }
      throw new Error(errorMessage);
    }

    const result = await readStepbitSseResponse(response);
    if (!result.content) {
      throw new Error("stepbit-core returned no content for this request.");
    }
    return {
      ...result,
      endpoint,
    };
  }

  return { askChat };
}

module.exports = { createStepbitService };
