export default async function Page() {
  const coreUrl = process.env.NEXT_PUBLIC_CORE_URL || "http://helix-core:8000";

  // server-side fetch from container network:
  const r = await fetch(`${coreUrl}/health`, { cache: "no-store" });
  const data = await r.json();

  return (
    <main>
      <h1>HELIX Web v0.1</h1>
      <p>Core health: <b>{data.ok ? "OK" : "FAIL"}</b></p>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </main>
  );
}
