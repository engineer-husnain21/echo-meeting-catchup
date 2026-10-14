// Renders the catch-up board of one topic.

import { day, esc, isMine, quoteList } from "./format.js";

export function renderBoard(board, userName) {
  const mine = board.action_items.filter((a) => a.status === "open" && isMine(a.owner, userName));
  const nobody = board.action_items.filter((a) => a.status === "open" && !a.owner);
  const others = board.action_items.filter((a) => !mine.includes(a) && !nobody.includes(a));
  return [
    decisions(board.decisions),
    actions("Your action items", mine, userName
      ? "Open items owned by you."
      : "Add your name on the left to see what is yours.", "action"),
    actions("Nobody owns this yet", nobody, "Work that was raised but never picked up.", "nobody"),
    openItems(board.open_items),
    stances(board.stances),
    actions("Everyone else's action items", others, "Owned by other people, or already done.", "action"),
    timeline(board.timeline),
  ].join("");
}

function section(title, sub, body) {
  return `<section class="section"><h2>${title}</h2><p class="sub">${sub}</p>${body}</section>`;
}

function decisions(items) {
  if (!items.length) return "";
  const body = items.map((d) => {
    const c = d.current;
    const changed = d.history.length ? `<span class="tag">Changed</span>` : "";
    const history = d.history.length
      ? `<ul class="history">${d.history.map((h) => `<li>Before: ${esc(h.summary)} (${day(h.meeting_date)})</li>`).join("")}</ul>`
      : "";
    const by = c.decided_by ? `${esc(c.decided_by)}, ` : "";
    const reason = c.reason ? `<p class="item-line">Why: ${esc(c.reason)}</p>` : "";
    return `<article class="item">
      <p class="item-subject">${changed}${esc(d.subject)}</p>
      <p class="item-main">${esc(c.summary)}</p>
      <p class="item-line">Decided by ${by}${day(c.meeting_date)}</p>
      ${reason}${history}${quoteList(c.quotes)}
    </article>`;
  }).join("");
  return section("Decisions", "The latest decision on each subject. Older versions are kept below it.", body);
}

function actions(title, items, sub, kind) {
  if (!items.length && kind !== "action") return "";
  if (!items.length) return section(title, sub, `<p class="sub">Nothing here.</p>`);
  const body = items.map((a) => {
    const owner = a.owner ? esc(a.owner) : "Unassigned";
    const due = a.due ? `, due ${esc(a.due)}` : "";
    const done = a.status === "done" ? `<span class="tag muted">Done</span>` : "";
    const cls = a.owner ? "action" : "nobody";
    return `<article class="item ${cls}">
      <p class="item-subject">${done}${esc(a.subject)}</p>
      <p class="item-main">${esc(a.task)}</p>
      <p class="item-line"><span class="tag ${cls}">${owner}</span>${day(a.meeting_date)}${due}</p>
      ${quoteList(a.quotes)}
    </article>`;
  }).join("");
  return section(title, sub, body);
}

function openItems(items) {
  if (!items.length) return "";
  const body = items.map((o) => `<article class="item open">
      <p class="item-subject">${esc(o.subject)}</p>
      <p class="item-main">${esc(o.question)}</p>
      <p class="item-line"><span class="tag open">Open</span>raised ${day(o.raised_on)}</p>
      ${quoteList(o.quotes)}
    </article>`).join("");
  return section("Still open", "Questions nobody has answered yet.", body);
}

function stances(items) {
  if (!items.length) return "";
  const body = items.map((s) => `<article class="item stance">
      <p class="item-subject"><span class="tag muted">Inferred</span>${esc(s.subject)}</p>
      <p class="item-main">${esc(s.person)}: ${esc(s.leaning)}</p>
      <p class="item-line">${esc(s.explanation)} Trend: ${esc(s.trend)}.</p>
      ${quoteList(s.quotes)}
    </article>`).join("");
  return section("Reading between the lines", "ECHO's impression from how people talked. Check the quotes before relying on it.", body);
}

function timeline(items) {
  if (!items.length) return "";
  const body = `<ol class="timeline">${items.map((t) => `<li>
      <span class="when">${day(t.meeting_date)}, ${esc(t.meeting_title)}</span>
      <p class="item-line"><strong>${esc(t.change)}</strong>${t.reason ? ` ${esc(t.reason)}` : ""}</p>
      ${quoteList(t.quotes)}
    </li>`).join("")}</ol>`;
  return section("How decisions changed", "Every change, in meeting order.", body);
}
