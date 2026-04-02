export async function apiGet(path: string) {
  const res = await fetch(path, { credentials: "include" });
  if (!res.ok) throw new Error(`API request failed: ${res.status}`);
  return res.json();
}
