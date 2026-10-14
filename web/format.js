// Formatting helpers shared by the board and the conversation.

export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

export function day(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function clock(seconds) {
  if (seconds === null || seconds === undefined) return "";
  const s = Math.floor(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const pad = (n) => String(n).padStart(2, "0");
  return h ? `${h}:${pad(m)}:${pad(s % 60)}` : `${pad(m)}:${pad(s % 60)}`;
}

export function seconds(ms) {
  return `${(ms / 1000).toFixed(1)} s`;
}

/** Clickable quotes; data attributes let one click handler open the transcript. */
export function quoteList(quotes) {
  if (!quotes?.length) return "";
  const items = quotes.map((q) => `
    <li><button class="quote" type="button" data-meeting="${q.meeting_id}" data-line="${q.line}"
        title="Open ${esc(q.meeting_title)} at line ${q.line}">
      <span class="q-who">${esc(q.speaker.split(" ")[0])}, ${day(q.meeting_date)}</span>
      <span class="q-text">“${esc(q.text)}”</span>
    </button></li>`).join("");
  return `<ul class="quotes">${items}</ul>`;
}

export function isMine(owner, userName) {
  if (!owner || !userName) return false;
  const a = owner.toLowerCase().trim().split(/\s+/);
  const b = userName.toLowerCase().trim().split(/\s+/);
  return a.join(" ") === b.join(" ") || a[0] === b[0];
}
