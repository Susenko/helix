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
        instructions:
          "Start the conversation with: 'How can I assist you?' Keep it short.",
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
      <h1>HELIX Voice v0.1</h1>

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
