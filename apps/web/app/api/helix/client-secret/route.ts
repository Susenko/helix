export async function POST() {
  const coreUrl = process.env.NEXT_PUBLIC_CORE_URL || "http://helix-core:8000";

  const r = await fetch(`${coreUrl}/realtime/client_secret`, {
    method: "POST",
  });

  const body = await r.text();
  return new Response(body, {
    status: r.status,
    headers: {
      "Content-Type": r.headers.get("content-type") || "application/json",
    },
  });
}
