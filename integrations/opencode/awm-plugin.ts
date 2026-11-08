import type { Plugin } from "@opencode-ai/plugin";

const baseUrl = process.env.AWM_BASE_URL ?? "http://127.0.0.1:8765";
const apiKey = process.env.AWM_API_KEY;

function pickSessionId(value: unknown): string {
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    for (const key of ["sessionID", "sessionId", "session_id", "id"]) {
      if (typeof record[key] === "string") return record[key] as string;
    }
  }
  return "unknown";
}

export const AWMPlugin: Plugin = async () => {
  if (!apiKey) {
    console.warn("[awm] AWM_API_KEY is unset; OpenCode events will not be recorded.");
    return {};
  }

  const send = async (eventType: string, value: unknown, sessionId?: string) => {
    const content = JSON.stringify(value);
    const clientEventId = `${eventType}:${Date.now()}:${crypto.randomUUID()}`;
    try {
      const response = await fetch(`${baseUrl.replace(/\/$/, "")}/v1/events`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source: "opencode",
          session_id: sessionId ?? pickSessionId(value),
          event_type: eventType,
          occurred_at: new Date().toISOString(),
          content,
          metadata: { adapter_version: "0.1.0" },
          client_event_id: clientEventId,
        }),
        signal: AbortSignal.timeout(3000),
      });
      if (!response.ok) console.warn(`[awm] event intake returned HTTP ${response.status}`);
    } catch (error) {
      console.warn("[awm] could not send OpenCode event; the event was not persisted", error);
    }
  };

  return {
    event: async ({ event }) => {
      const eventType = (event as { type?: string }).type ?? "opencode.event";
      await send(eventType, event);
    },
    "tool.execute.after": async (input, output) => {
      await send(
        "tool.execute.after",
        { tool: input.tool, args: input.args, output },
        pickSessionId(input),
      );
    },
  };
};
