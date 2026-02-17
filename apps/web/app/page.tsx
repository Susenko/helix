"use client";

import { RealtimeAgent, RealtimeSession, tool } from "@openai/agents/realtime";
import { useEffect, useRef, useState } from "react";
import { z } from "zod";

const CORE_HTTP =
  process.env.NEXT_PUBLIC_CORE_HTTP_URL ||
  process.env.NEXT_PUBLIC_CORE_URL ||
  "http://localhost:8000";

type TensionRow = {
  id: number;
  title: string;
  status: string;
  charge: number;
  vector: string;
};

type BaselineFieldRow = {
  id: number;
  user_id: string | null;
  name: string;
  description: string | null;
  mode: "any" | "focus" | "admin" | "reflect";
  min_quota_min_per_week: number;
  max_quota_min_per_week: number;
  preferred_windows: Record<string, unknown>;
  is_active: boolean;
};

export default function Page() {
  const [status, setStatus] = useState("idle");
  const [lastTranscript, setLastTranscript] = useState("");
  const [voiceError, setVoiceError] = useState("");
  const [calendarStatus, setCalendarStatus] = useState<
    "unknown" | "checking" | "connected" | "disconnected" | "error"
  >("unknown");
  const [calendarReason, setCalendarReason] = useState("");
  const [tensions, setTensions] = useState<TensionRow[]>([]);
  const [tensionsLoading, setTensionsLoading] = useState(false);
  const [tensionsError, setTensionsError] = useState("");
  const [baselineFields, setBaselineFields] = useState<BaselineFieldRow[]>([]);
  const [baselineLoading, setBaselineLoading] = useState(false);
  const [baselineError, setBaselineError] = useState("");

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

  async function runTensionsCreate(args: any) {
    const res = await fetch(`${CORE_HTTP}/tensions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }

    return await res.json(); // {id, title, status, charge, vector}
  }

  async function runTensionsListActive(args: any) {
    const params = new URLSearchParams();
    if (typeof args?.limit === "number") {
      params.set("limit", String(args.limit));
    }
    const url = `${CORE_HTTP}/tensions/active${params.toString() ? `?${params}` : ""}`;
    const res = await fetch(url, { method: "GET" });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }

    return await res.json(); // [{id, title, status, charge, vector}]
  }

  async function runTensionsUpdate(args: any) {
    const id = Number(args?.id);
    if (!Number.isInteger(id) || id <= 0) {
      throw new Error("invalid tension id");
    }

    const payload: Record<string, unknown> = {};
    if (typeof args?.charge === "number") payload.charge = args.charge;
    if (typeof args?.vector === "string") payload.vector = args.vector;
    if (typeof args?.status === "string") payload.status = args.status;

    const res = await fetch(`${CORE_HTTP}/tensions/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }

    return await res.json(); // {id, title, status, charge, vector}
  }

  async function runBaselineFieldsList(args: any) {
    const params = new URLSearchParams();
    if (typeof args?.limit === "number") {
      params.set("limit", String(args.limit));
    }
    if (typeof args?.include_inactive === "boolean") {
      params.set("include_inactive", String(args.include_inactive));
    }
    const url = `${CORE_HTTP}/baseline-fields${params.toString() ? `?${params}` : ""}`;
    const res = await fetch(url, { method: "GET" });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }
    return await res.json(); // BaselineFieldRow[]
  }

  async function runBaselineFieldsCreate(args: any) {
    const res = await fetch(`${CORE_HTTP}/baseline-fields`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }
    return await res.json(); // BaselineFieldRow
  }

  async function runBaselineFieldsUpdate(args: any) {
    const id = Number(args?.id);
    if (!Number.isInteger(id) || id <= 0) {
      throw new Error("invalid baseline field id");
    }
    const payload: Record<string, unknown> = {};
    const keys = [
      "name",
      "description",
      "mode",
      "min_quota_min_per_week",
      "max_quota_min_per_week",
      "preferred_windows",
      "is_active",
    ] as const;
    for (const key of keys) {
      if (args?.[key] !== undefined) payload[key] = args[key];
    }
    const res = await fetch(`${CORE_HTTP}/baseline-fields/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }
    return await res.json(); // BaselineFieldRow
  }

  async function runBaselineFieldsDelete(args: any) {
    const id = Number(args?.id);
    if (!Number.isInteger(id) || id <= 0) {
      throw new Error("invalid baseline field id");
    }
    const res = await fetch(`${CORE_HTTP}/baseline-fields/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`core error ${res.status}: ${text}`);
    }
    return await res.json(); // {ok, id}
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

  async function refreshTensions() {
    setTensionsLoading(true);
    setTensionsError("");
    try {
      const data = await runTensionsListActive({ limit: 50 });
      if (!Array.isArray(data)) {
        throw new Error("invalid tensions payload");
      }
      setTensions(data as TensionRow[]);
    } catch (e) {
      console.error("tensions refresh error", e);
      setTensionsError("Failed to load tensions");
    } finally {
      setTensionsLoading(false);
    }
  }

  async function refreshBaselineFields() {
    setBaselineLoading(true);
    setBaselineError("");
    try {
      const data = await runBaselineFieldsList({ limit: 100, include_inactive: true });
      if (!Array.isArray(data)) {
        throw new Error("invalid baseline payload");
      }
      setBaselineFields(data as BaselineFieldRow[]);
    } catch (e) {
      console.error("baseline refresh error", e);
      setBaselineError("Failed to load baseline fields");
    } finally {
      setBaselineLoading(false);
    }
  }

  async function enableVoice() {
    setStatus("connecting");
    setVoiceError("");

    if (!window.isSecureContext) {
      setStatus("error");
      setVoiceError(
        "Voice requires a secure context. Open the app via HTTPS (or localhost).",
      );
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus("error");
      setVoiceError(
        "Microphone API is unavailable in this browser/context. Use HTTPS and allow microphone access.",
      );
      return;
    }

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

      const tensionsCreateTool = tool({
        name: "tensions_create",
        description:
          "Capture and store a new tension. Use when user asks to add/save/capture a tension (e.g. 'добавь напряжение').",
        parameters: z.object({
          title: z.string().min(1).max(500).describe("Short tension title"),
          note: z.string().max(5000).optional().describe("Optional details"),
          charge: z
            .number()
            .int()
            .min(0)
            .max(5)
            .default(3)
            .describe("Intensity from 0 to 5"),
          vector: z
            .enum([
              "unknown",
              "action",
              "message",
              "meeting",
              "focus_block",
              "decision",
              "research",
              "delegate",
              "drop",
            ])
            .default("unknown")
            .describe("Preferred form of action"),
          status: z
            .enum(["held", "forming", "released", "parked", "dropped"])
            .default("held")
            .describe("Lifecycle stage"),
        }),
        async execute(args) {
          return await runTensionsCreate(args);
        },
      });

      const tensionsListActiveTool = tool({
        name: "tensions_list_active",
        description:
          "List active tensions. Use when user asks what tensions are currently active/open/held.",
        parameters: z.object({
          limit: z
            .number()
            .int()
            .min(1)
            .max(200)
            .default(50)
            .describe("Maximum number of items"),
        }),
        async execute(args) {
          return await runTensionsListActive(args);
        },
      });

      const tensionsUpdateTool = tool({
        name: "tensions_update",
        description:
          "Update an existing tension by id. Use when user asks to change charge/vector/status for a specific tension id.",
        parameters: {
          type: "object",
          properties: {
            id: { type: "integer", minimum: 1, description: "Tension ID" },
            charge: { type: "integer", minimum: 0, maximum: 5 },
            vector: {
              type: "string",
              enum: [
                "unknown",
                "action",
                "message",
                "meeting",
                "focus_block",
                "decision",
                "research",
                "delegate",
                "drop",
              ],
            },
            status: {
              type: "string",
              enum: ["held", "forming", "released", "parked", "dropped"],
            },
          },
          required: ["id"],
          additionalProperties: false,
        },
        async execute(args) {
          const updated = await runTensionsUpdate(args);
          await refreshTensions();
          return updated;
        },
      });

      const baselineFieldsListTool = tool({
        name: "baseline_fields_list",
        description:
          "List baseline fields (background domains). Use when user asks to show/list baseline fields.",
        parameters: {
          type: "object",
          properties: {
            limit: { type: "integer", minimum: 1, maximum: 500, default: 100 },
            include_inactive: { type: "boolean", default: true },
          },
          additionalProperties: false,
        },
        async execute(args) {
          return await runBaselineFieldsList(args);
        },
      });

      const baselineFieldsCreateTool = tool({
        name: "baseline_fields_create",
        description:
          "Create a baseline field (background domain like work or pet project).",
        parameters: {
          type: "object",
          properties: {
            name: { type: "string", minLength: 1, maxLength: 300 },
            description: { type: "string", maxLength: 3000 },
            mode: {
              type: "string",
              enum: ["any", "focus", "admin", "reflect"],
              default: "any",
            },
            min_quota_min_per_week: { type: "integer", minimum: 0, default: 0 },
            max_quota_min_per_week: { type: "integer", minimum: 0, default: 0 },
            preferred_windows: { type: "object", additionalProperties: true, default: {} },
            is_active: { type: "boolean", default: true },
            user_id: { type: "string", maxLength: 255 },
          },
          required: ["name"],
          additionalProperties: false,
        },
        async execute(args) {
          const created = await runBaselineFieldsCreate(args);
          await refreshBaselineFields();
          return created;
        },
      });

      const baselineFieldsUpdateTool = tool({
        name: "baseline_fields_update",
        description: "Update an existing baseline field by id.",
        parameters: {
          type: "object",
          properties: {
            id: { type: "integer", minimum: 1 },
            name: { type: "string", minLength: 1, maxLength: 300 },
            description: { type: "string", maxLength: 3000 },
            mode: { type: "string", enum: ["any", "focus", "admin", "reflect"] },
            min_quota_min_per_week: { type: "integer", minimum: 0 },
            max_quota_min_per_week: { type: "integer", minimum: 0 },
            preferred_windows: { type: "object", additionalProperties: true },
            is_active: { type: "boolean" },
          },
          required: ["id"],
          additionalProperties: false,
        },
        async execute(args) {
          const updated = await runBaselineFieldsUpdate(args);
          await refreshBaselineFields();
          return updated;
        },
      });

      const baselineFieldsDeleteTool = tool({
        name: "baseline_fields_delete",
        description: "Delete a baseline field by id.",
        parameters: {
          type: "object",
          properties: {
            id: { type: "integer", minimum: 1 },
          },
          required: ["id"],
          additionalProperties: false,
        },
        async execute(args) {
          const deleted = await runBaselineFieldsDelete(args);
          await refreshBaselineFields();
          return deleted;
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

          Voice style:
          HELIX speaks calmly and clearly.
          Short sentences.
          No corporate tone.
          No therapy tone.
          No motivational speech.
          Precise. Grounded. Slightly warm.

          Avoid AI-generic phrases like:
          - "How can I help?"
          - "Let me know how else I can help."
          - "Is there anything else?"
          - "I'm here for you."
          Use concrete next-step questions instead.

          If unsure — ask one specific question.

          Start by saying:
          "HELIX online. State your focus."
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
- If the user asks to add/capture/save a tension, you MUST call the tool tensions_create.
- If the user asks to show current tensions, you MUST call the tool tensions_list_active.
- If the user asks to modify a tension by id (charge/vector/status), you MUST call the tool tensions_update.
- If the user asks to list baseline fields, you MUST call the tool baseline_fields_list.
- If the user asks to add a baseline field, you MUST call the tool baseline_fields_create.
- If the user asks to update a baseline field by id, you MUST call the tool baseline_fields_update.
- If the user asks to delete a baseline field by id, you MUST call the tool baseline_fields_delete.
- Never invent calendar data. Only use tool results.
- Never invent tensions data. Only use tool results.
- Never invent baseline fields data. Only use tool results.
- After tool results arrive, summarize briefly and ask one focused follow-up question.
- Never end with generic assistant-style offers.

          `,
        tools: [
          calendarFreeSlotsTool,
          calendarTodayTool,
          calendarCreateTool,
          tensionsCreateTool,
          tensionsListActiveTool,
          tensionsUpdateTool,
          baselineFieldsListTool,
          baselineFieldsCreateTool,
          baselineFieldsUpdateTool,
          baselineFieldsDeleteTool,
        ],
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
    refreshTensions();
    refreshBaselineFields();
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

      <button onClick={refreshTensions} style={{ marginLeft: 10 }}>
        Refresh Tensions
      </button>

      <button onClick={refreshBaselineFields} style={{ marginLeft: 10 }}>
        Refresh Baseline
      </button>

      <a
        href={`${CORE_HTTP}/oauth/google/start`}
        style={{ marginLeft: 10 }}
      >
        Google OAuth
      </a>

      <p>
        Status: <b>{status}</b>
      </p>
      {voiceError ? (
        <p>
          Voice error: <b>{voiceError}</b>
        </p>
      ) : null}

      <p>
        Last assistant transcript: <b>{lastTranscript || "—"}</b>
      </p>

      <p>
        Calendar: <b>{calendarStatus}</b>
        {calendarReason ? ` (${calendarReason})` : ""}
      </p>

      <h2>Active Tensions</h2>
      {tensionsLoading ? <p>Loading tensions...</p> : null}
      {tensionsError ? <p>{tensionsError}</p> : null}
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          marginTop: 8,
        }}
      >
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              ID
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Title
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Status
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Charge
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Vector
            </th>
          </tr>
        </thead>
        <tbody>
          {tensions.map((t) => (
            <tr key={t.id}>
              <td style={{ padding: "6px 0" }}>{t.id}</td>
              <td style={{ padding: "6px 0" }}>{t.title}</td>
              <td style={{ padding: "6px 0" }}>{t.status}</td>
              <td style={{ padding: "6px 0" }}>{t.charge}</td>
              <td style={{ padding: "6px 0" }}>{t.vector}</td>
            </tr>
          ))}
          {!tensionsLoading && tensions.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ paddingTop: 8 }}>
                No active tensions
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>

      <h2 style={{ marginTop: 20 }}>Baseline Fields</h2>
      {baselineLoading ? <p>Loading baseline fields...</p> : null}
      {baselineError ? <p>{baselineError}</p> : null}
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          marginTop: 8,
        }}
      >
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              ID
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Name
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Mode
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Min/Week
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Max/Week
            </th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              Active
            </th>
          </tr>
        </thead>
        <tbody>
          {baselineFields.map((f) => (
            <tr key={f.id}>
              <td style={{ padding: "6px 0" }}>{f.id}</td>
              <td style={{ padding: "6px 0" }}>{f.name}</td>
              <td style={{ padding: "6px 0" }}>{f.mode}</td>
              <td style={{ padding: "6px 0" }}>{f.min_quota_min_per_week}</td>
              <td style={{ padding: "6px 0" }}>{f.max_quota_min_per_week}</td>
              <td style={{ padding: "6px 0" }}>{f.is_active ? "yes" : "no"}</td>
            </tr>
          ))}
          {!baselineLoading && baselineFields.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ paddingTop: 8 }}>
                No baseline fields
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </main>
  );
}
