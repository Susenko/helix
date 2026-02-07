export async function POST(req: Request) {
  const offer = await req.text();
  const coreUrl = process.env.NEXT_PUBLIC_CORE_URL || "http://helix-core:8000";

  const r = await fetch(`${coreUrl}/realtime/session`, {
    method: "POST",
    headers: { "Content-Type": "application/sdp" },
    body: offer
  });

  const answer = await r.text();
  return new Response(answer, {
    status: r.status,
    headers: { "Content-Type": "application/sdp" }
  });
}
