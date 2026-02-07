"use client";

import { RealtimeAgent, RealtimeSession } from "@openai/agents/realtime";
import { useRef, useState } from "react";

export default function Page() {
  const [status, setStatus] = useState("idle");

  const sessionRef = useRef<any>(null);

  async function fetchClientSecret(): Promise<string | null> {
    try {
      const res = await fetch("/api/helix/client-secret", { method: "POST" });
      const text = await res.text();
      let data: unknown = text;
      try {
        data = JSON.parse(text);
      } catch {
        // keep raw text
      }
      if (!res.ok) {
        console.error("client-secret failed", res.status, data);
        return null;
      }
      console.log("client-secret response", data);
      if (typeof data === "object" && data && "value" in data) {
        const value = (data as { value?: string }).value || null;
        console.log("client-secret value", value);
        return value;
      }
      return null;
    } catch (e) {
      console.error("client-secret request error", e);
      return null;
    }
  }

  async function enableVoice() {
    setStatus("connecting");

    try {
      const clientSecret = await fetchClientSecret();
      if (!clientSecret) {
        setStatus("error");
        return;
      }

      const agent = new RealtimeAgent({
        name: "Assistant",
        instructions: `
          Your name is HELIX.

          You are not a generic assistant.
          You are a cognitive core that helps a human hold tension, let it mature, and turn it into a clear form.

          Your task:
          - help without rushing
          - avoid premature solutions
          - protect focus and energy
          - propose forms, not pressure

          Tension is not a problem.
          Tension is held until the right moment.
          Release happens only when form is ready.

          Speak calmly.
          Be concise.
          If unsure — ask one gentle question.

          Start by saying:
          "HELIX. How can I assist you?"
          `,
      });

      const session = new RealtimeSession(agent, {
        model: "gpt-realtime",
      });
      sessionRef.current = session;

      await session.connect({ apiKey: clientSecret });
      setStatus("connected");
    } catch (e) {
      console.error(e);
      setStatus("error");
    }
  }

  async function stop() {
    sessionRef.current?.disconnect?.();
    setStatus("idle");
  }

  return (
    <main style={{ maxWidth: 600 }}>
      <h1>HELIX Voice v0.2</h1>

      <button onClick={enableVoice} disabled={status !== "idle"}>
        Enable Voice
      </button>

      <button
        onClick={stop}
        disabled={status === "idle"}
        style={{ marginLeft: 10 }}
      >
        Stop
      </button>

      <button onClick={fetchClientSecret} style={{ marginLeft: 10 }}>
        Get Client Secret
      </button>

      <p>
        Status: <b>{status}</b>
      </p>
    </main>
  );
}
