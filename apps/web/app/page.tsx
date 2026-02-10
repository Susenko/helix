"use client";

import { RealtimeAgent, RealtimeSession, tool } from "@openai/agents/realtime";
import { useEffect, useRef, useState } from "react";
import { z } from "zod";

const CORE_HTTP =
  process.env.NEXT_PUBLIC_CORE_HTTP_URL || "http://localhost:8000";

export default function Page() {
  const [status, setStatus] = useState("idle");
  const [lastTranscript, setLastTranscript] = useState("");
  const [calendarStatus, setCalendarStatus] = useState<
    "unknown" | "checking" | "connected" | "disconnected" | "error"
  >("unknown");
  const [calendarReason, setCalendarReason] = useState("");

  const sessionRef = useRef<RealtimeSession | null>(null);

  async function runCalendarFreeSlots(args: any) {
    const res = await fetch(`${CORE_HTTP}/calendar/free-slots`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }

    return await res.json(); // {date, timezone, slots:[...]}
  }

  async function runCalendarDay(args: any) {
    const params = new URLSearchParams();
    if (args?.date) params.set("date", String(args.date));
    const url = `${CORE_HTTP}/calendar/day${params.toString() ? `?${params}` : ""}`;
    const res = await fetch(url, { method: "GET" });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }

    return await res.json(); // {date, timezone, events:[...]}
  }

  async function runCalendarCreateEvent(args: any) {
    const res = await fetch(`${CORE_HTTP}/calendar/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }

    return await res.json(); // {timezone, event:{...}}
  }

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

  async function fetchCalendarStatus() {
    setCalendarStatus("checking");
    setCalendarReason("");
    try {
      const res = await fetch(`${CORE_HTTP}/calendar/status`, {
        method: "GET",
      });
      let data: any = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (!res.ok) {
        setCalendarStatus("error");
        setCalendarReason(`http_${res.status}`);
        return;
      }

      if (data?.connected) {
        setCalendarStatus("connected");
        setCalendarReason("");
      } else {
        setCalendarStatus("disconnected");
        setCalendarReason(data?.reason ? String(data.reason) : "");
      }
    } catch (e) {
      console.error("calendar status error", e);
      setCalendarStatus("error");
      setCalendarReason("network_error");
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

      const calendarFreeSlotsTool = tool({
        name: "calendar_free_slots",
        description:
          "Find free time slots in the user's calendar. Use when user asks to find free time, schedule, plan a meeting, or find an opening.",
        parameters: z.object({
          date: z
            .string()
            .optional()
            .describe("Date in YYYY-MM-DD. If omitted, use today."),
          duration_min: z
            .number()
            .int()
            .default(30)
            .describe("Desired duration in minutes (e.g., 30, 60)."),
          work_start: z
            .string()
            .default("09:00")
            .describe("Workday start HH:MM"),
          work_end: z.string().default("18:00").describe("Workday end HH:MM"),
          buffer_min: z
            .number()
            .int()
            .default(10)
            .describe("Buffer between meetings in minutes"),
          max_slots: z
            .number()
            .int()
            .default(3)
            .describe("Max number of returned slots"),
        }),
        async execute(args) {
          return await runCalendarFreeSlots(args);
        },
      });

      const calendarTodayTool = tool({
        name: "calendar_day",
        description:
          "List calendar events for a specific date (or today if omitted). Use when user asks what's on the calendar today/tomorrow/on a date, or asks for the schedule.",
        parameters: z.object({
          date: z
            .string()
            .optional()
            .describe("Date in YYYY-MM-DD. If omitted, use today."),
        }),
        async execute(args) {
          return await runCalendarDay(args);
        },
      });

      const calendarCreateTool = tool({
        name: "calendar_create_event",
        description:
          "Create a calendar event with date, start_time, duration, and title. Use when user asks to create or schedule a meeting/event.",
        parameters: z.object({
          date: z.string().describe("Date in YYYY-MM-DD"),
          start_time: z.string().describe("Start time in HH:MM"),
          duration_min: z
            .number()
            .int()
            .describe("Duration in minutes, e.g., 30 or 60"),
          title: z.string().describe("Event title"),
        }),
        async execute(args) {
          return await runCalendarCreateEvent(args);
        },
      });

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
        # HELIX — Identity (v0.1)

HELIX (Human–Extended Logic & Intent eXecutor) — это не “ассистент” и не “планировщик”.
Это ядро согласованности системы человек ↔ машина ↔ устройства.

HELIX удерживает напряжение, помогает ему созреть и переводит его в форму (действие),
сохраняя экологичность и автономию человека.

## Ключевые определения

- **Напряжение (Tension)** — незавершённый узел, который давит и требует формы.
- **Контейнер** — место, где узел хранится без преждевременной разрядки.
- **Форма (Form)** — способ реализовать узел (ответ, перенос, делегирование, пауза, разговор, действие).
- **Фаза (State/Mode)** — режим энергии и контекста (Focus/Admin/Reflect).
- **Возврат (Return Loop)** — корректный момент, когда HELIX возвращает контейнер в поле внимания.

## Обещание HELIX

HELIX никогда не оптимизирует день ценой выгорания.
HELIX не подменяет волю человека — он расширяет её радиус.


1) **Container first**
Любое входящее сначала попадает в контейнер. Не в действие.

2) **State before decision**
Сначала определяется режим/фаза и контекст, потом предлагается форма.

3) **Right to refuse**
HELIX имеет право сказать “сейчас нельзя” и предложить “когда можно”.

4) **Reversible by default**
По умолчанию: сводка → предложение → черновик → подтверждение → действие.

5) **Minimal questions**
Если можно вывести по контексту — не спрашивать. Если риск — спрашивать.

6) **Communication windows**
Почта/сообщения/звонки обрабатываются в специальных окнах (Admin), не разрывая Focus.

7) **Forms > tasks**
HELIX работает с формой, а не с задачей. “Как сделать” важнее “что сделать”.

8) **Return loop**
HELIX возвращает контейнер тогда, когда шанс на хорошую форму максимален.

9) **Memory = resonance**
Храним повторяющиеся узлы и незакрытые контейнеры. Не храним всё подряд.

10) **Humor after validation**
Сначала признание и безопасность, затем лёгкий юмор (если уместно).

11) **Devices are organs**
Устройства — продолжение человека. HELIX выбирает правильный канал/устройство по умолчанию.

12) **Human remains the author**
Человек — автор. HELIX — усилитель и исполнитель намерений.


Tool policy:
- If the user asks about calendar availability, schedule, free time, openings, or meeting slots, you MUST call the tool calendar_free_slots.
- If the user asks about today's schedule, tomorrow, or a specific date, you MUST call the tool calendar_day.
- If the user asks to create, schedule, or add a meeting/event, you MUST call the tool calendar_create_event.
- Never invent calendar data. Only use tool results.
- After tool results arrive, summarize options briefly and ask which slot to pick.

          `,
        tools: [calendarFreeSlotsTool, calendarTodayTool, calendarCreateTool],
      });

      const session = new RealtimeSession(agent, {
        model: "gpt-realtime",
      });
      sessionRef.current = session;

      session.on("history_added", (item: any) => {
        try {
          if (item?.type !== "message" || item?.role !== "assistant") return;
          if (!Array.isArray(item.content)) return;
          let transcript = "";
          for (const c of item.content) {
            if (
              c?.type === "output_audio" &&
              typeof c?.transcript === "string"
            ) {
              transcript = c.transcript;
              break;
            }
            if (c?.type === "output_text" && typeof c?.text === "string") {
              transcript = c.text;
            }
          }
          if (transcript) {
            console.log("assistant transcript:", transcript);
            setLastTranscript(transcript);
          }
        } catch (e) {
          console.error("history_added parse error", e);
        }
      });

      await session.connect({ apiKey: clientSecret });
      setStatus("connected");
    } catch (e) {
      console.error(e);
      setStatus("error");
    }
  }

  async function stop() {
    const session = sessionRef.current;
    if (!session) return;
    setStatus("disconnecting");
    try {
      await session.disconnect?.();
    } catch (e) {
      console.error("disconnect error", e);
    } finally {
      sessionRef.current = null;
      setStatus("idle");
    }
  }

  useEffect(() => {
    fetchCalendarStatus();
  }, []);

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

      <button onClick={fetchCalendarStatus} style={{ marginLeft: 10 }}>
        Check Calendar
      </button>

      <a
        href="http://localhost:8000/oauth/google/start"
        style={{ marginLeft: 10 }}
      >
        Google OAuth
      </a>

      <p>
        Status: <b>{status}</b>
      </p>

      <p>
        Last assistant transcript: <b>{lastTranscript || "—"}</b>
      </p>

      <p>
        Calendar: <b>{calendarStatus}</b>
        {calendarReason ? ` (${calendarReason})` : ""}
      </p>
    </main>
  );
}
