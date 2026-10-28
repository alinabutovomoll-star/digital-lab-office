// Vercel serverless: отдаёт данные дашборда только Алине.
// Доступ: из Telegram (подпись initData от бота Алисы) или из браузера по секретному ключу ?key=
const crypto = require("crypto");

function checkTelegram(initData, botToken, ownerId) {
  if (!initData) return false;
  const params = new URLSearchParams(initData);
  const hash = params.get("hash");
  params.delete("hash");
  const dataCheck = [...params.entries()].map(([k, v]) => `${k}=${v}`).sort().join("\n");
  const secret = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
  const calc = crypto.createHmac("sha256", secret).update(dataCheck).digest("hex");
  if (!hash || calc.length !== hash.length ||
      !crypto.timingSafeEqual(Buffer.from(calc), Buffer.from(hash))) return false;
  const authDate = Number(params.get("auth_date") || 0);
  if (Date.now() / 1000 - authDate > 86400) return false;
  try { return String(JSON.parse(params.get("user")).id) === String(ownerId); }
  catch { return false; }
}

async function sb(path) {
  const r = await fetch(`${process.env.SUPABASE_URL}/rest/v1/${path}`, {
    headers: {
      apikey: process.env.SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${process.env.SUPABASE_SERVICE_KEY}`,
    },
  });
  if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`);
  return r.json();
}

module.exports = async (req, res) => {
  const { DASHBOARD_KEY, ALICE_BOT_TOKEN, OWNER_TELEGRAM_ID } = process.env;
  const key = req.query.key || "";
  const byKey = DASHBOARD_KEY && key.length === DASHBOARD_KEY.length &&
    crypto.timingSafeEqual(Buffer.from(key), Buffer.from(DASHBOARD_KEY));
  const byTg = checkTelegram(req.headers["x-telegram-init-data"], ALICE_BOT_TOKEN, OWNER_TELEGRAM_ID);
  if (!byKey && !byTg) return res.status(401).json({ error: "Нет доступа" });

  try {
    const since = new Date(Date.now() - 14 * 864e5).toISOString();
    const [projects, open, doneRecent] = await Promise.all([
      sb("project_progress?select=*&order=id.desc"),
      sb("tasks?select=*&status=neq.done&order=priority.asc,due.asc.nullslast&limit=500"),
      sb(`tasks?select=*&status=eq.done&done_at=gte.${since}&order=done_at.desc&limit=200`),
    ]);
    res.setHeader("Cache-Control", "no-store");
    res.json({ projects, tasks: [...open, ...doneRecent], now: new Date().toISOString() });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
};
