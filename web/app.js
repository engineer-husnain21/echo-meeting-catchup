// ECHO web UI: topics, uploads, board, transcript viewer and the conversation panel.

import { getJson, postFile, postForAudio, postJson } from "./api.js";
import { renderBoard } from "./board.js";
import { clock, day, esc, quoteList, seconds } from "./format.js";

const API = "/api/v1";
const MAX_TURNS = 6;
const $ = (id) => document.getElementById(id);

const state = {
  topics: [],
  topicId: null,
  meetings: [],
  history: [], // [{role: "user" | "echo", text}]
  audio: null,
  speechText: "", // what ECHO is saying right now (to ignore its own voice on the mic)
  busy: false,
  listening: false, // set by voice.js while the microphone is on
};

// ---------- presence ----------

const LABELS = { idle: "Ready", listening: "Listening", thinking: "Thinking", speaking: "Speaking" };

/** Presence to fall back to when ECHO is not thinking or speaking. */
function resting() {
  return state.listening ? "listening" : "idle";
}

export function setListening(on) {
  state.listening = on;
  if (!state.busy && !state.audio) setPresence(resting());
}

export function setPresence(mode) {
  $("presence").className = `presence ${mode}`;
  $("presence-label").textContent = LABELS[mode];
}

export function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.hidden = true; }, 5000);
}

// ---------- topics and meetings ----------

async function loadTopics(selectId = state.topicId) {
  state.topics = await getJson(`${API}/topics`);
  const list = $("topic-list");
  list.innerHTML = state.topics.map((t) => `<li>
      <button type="button" data-topic="${t.id}" aria-current="${t.id === selectId}">
        <span>${esc(t.name)}</span><span class="count">${t.meeting_count}</span>
      </button></li>`).join("") || `<li class="hint">No topics yet. Add one below.</li>`;
  const pick = selectId ?? state.topics[0]?.id;
  if (pick) await selectTopic(pick);
}

const SUGGESTIONS = [
  "What changed since the kickoff?",
  "What do I need to do this week?",
  "Who owns the on-call runbook?",
];

function showSuggestions() {
  $("conversation").innerHTML = `<li class="suggestions">
    <p>Tap the circle and ask out loud, or type. Answers come with the exact lines they are based on.</p>
    ${SUGGESTIONS.map((s) => `<button type="button" class="btn-quiet" data-suggest="${esc(s)}">${esc(s)}</button>`).join("")}
  </li>`;
}

async function selectTopic(topicId) {
  state.topicId = topicId;
  state.history = [];
  showSuggestions();
  $("upload-log").innerHTML = "";
  document.querySelectorAll("[data-topic]").forEach((b) => {
    b.setAttribute("aria-current", String(Number(b.dataset.topic) === topicId));
  });
  const topic = state.topics.find((t) => t.id === topicId);
  $("topic-title").textContent = topic?.name ?? "Topic";
  await Promise.all([loadMeetings(), loadBoard()]);
}

async function loadMeetings() {
  state.meetings = await getJson(`${API}/topics/${state.topicId}/meetings`);
  $("meeting-list").innerHTML = state.meetings.map((m) => `<li>
      <button type="button" data-open-meeting="${m.id}">
        <span class="m-title">${esc(m.title)}</span>
        <span class="m-sub">${day(m.meeting_date)}, ${m.line_count} lines</span>
      </button></li>`).join("") || `<li class="hint">No meetings yet.</li>`;
}

// ---------- board ----------

async function loadBoard() {
  const body = $("board-body");
  try {
    const board = await getJson(`${API}/topics/${state.topicId}/board`);
    const updated = new Date(board.updated_at).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" });
    $("board-meta").textContent = `${board.meetings.length} meetings, updated ${updated}`;
    $("rebuild-btn").hidden = false;
    body.innerHTML = renderBoard(board, userName());
  } catch (error) {
    if (error.status !== 404) throw error;
    $("rebuild-btn").hidden = true;
    $("board-meta").textContent = `${state.meetings.length} meetings`;
    body.innerHTML = state.meetings.length
      ? `<div class="empty"><h2>The board is not built yet</h2>
           <p>ECHO reads every meeting once and pulls out decisions, owners and open questions.</p>
           <button class="btn-primary" type="button" data-build>Build the board</button></div>`
      : `<div class="empty"><h2>Upload the first meeting</h2>
           <p>Add .vtt, .txt or .docx transcripts on the left. ECHO builds the board after each upload.</p></div>`;
  }
}

async function refreshBoard(rebuild = false) {
  const status = $("board-status");
  const started = Date.now();
  status.className = "board-status";
  status.hidden = false;
  const tick = () => {
    status.textContent = `Reading the meetings and updating the board, ${Math.round((Date.now() - started) / 1000)} s`;
  };
  tick();
  const timer = setInterval(tick, 1000);
  setPresence("thinking");
  try {
    await postJson(`${API}/topics/${state.topicId}/board/refresh${rebuild ? "?rebuild=true" : ""}`);
    status.hidden = true;
    await loadBoard();
  } catch (error) {
    status.className = "board-status error";
    status.textContent = `The board was not updated: ${error.message}`;
  } finally {
    clearInterval(timer);
    setPresence(resting());
  }
}

// ---------- uploads ----------

async function uploadFiles(files) {
  const log = $("upload-log");
  let added = 0;
  for (const file of files) {
    const row = document.createElement("li");
    row.textContent = `Uploading ${file.name}`;
    log.prepend(row);
    try {
      const result = await postFile(`${API}/topics/${state.topicId}/meetings`, file);
      row.className = "ok";
      row.textContent = `Added ${result.meeting.title} (${result.meeting.line_count} lines)`;
      added += 1;
    } catch (error) {
      row.className = "bad";
      row.textContent = `${file.name}: ${error.message}`;
    }
  }
  if (added) {
    await loadTopics(state.topicId);
    await refreshBoard();
  }
}

// ---------- transcript drawer ----------

async function openTranscript(meetingId, line = null) {
  try {
    const data = await getJson(`${API}/meetings/${meetingId}/transcript`);
    $("drawer-title").textContent = data.meeting.title;
    $("drawer-meta").textContent = `${day(data.meeting.meeting_date)}, ${data.lines.length} lines, ${data.meeting.source_filename}`;
    $("drawer-lines").innerHTML = data.lines.map((l) => `
      <li id="line-${l.line_number}" class="${l.line_number === line ? "target" : ""}">
        <span class="t-time">${clock(l.start_seconds) || `L${l.line_number}`}</span>
        <div><span class="t-speaker">${esc(l.speaker)}</span><p class="t-text">${esc(l.text)}</p></div>
      </li>`).join("");
    $("drawer").hidden = false;
    $("drawer-close").focus();
    if (line) $(`line-${line}`)?.scrollIntoView({ block: "center" });
  } catch (error) {
    toast(error.message);
  }
}

function closeDrawer() {
  $("drawer").hidden = true;
}

// ---------- conversation ----------

function userName() {
  return $("user-name").value.trim() || null;
}

function addTurn(role, text, extra = {}) {
  document.querySelector(".suggestions")?.remove();
  const li = document.createElement("li");
  li.className = role === "user" ? "turn user" : `turn echo-turn ${extra.status ?? ""}`;
  li.innerHTML = `<div class="who">${role === "user" ? "You" : "ECHO"}</div>
    <p>${esc(text)}</p>${quoteList(extra.citations)}`;
  $("conversation").append(li);
  li.scrollIntoView({ block: "end" });
  state.history.push({ role, text });
  state.history = state.history.slice(-MAX_TURNS);
}

export async function ask(question) {
  if (!state.topicId || state.busy) return;
  stopSpeaking();
  const history = state.history.slice();
  addTurn("user", question);
  await converse(() => postJson(`${API}/topics/${state.topicId}/questions`, {
    question, history, user_name: userName(),
  }), (r) => ({ text: r.answer, status: r.status, citations: r.citations }));
}

async function catchUp() {
  if (!state.topicId || state.busy) return;
  stopSpeaking();
  await converse(() => postJson(`${API}/topics/${state.topicId}/briefing`, { user_name: userName() }),
    (r) => ({ text: r.briefing, status: "answered", citations: r.citations }));
}

async function converse(call, pick) {
  state.busy = true;
  setPresence("thinking");
  $("latency").textContent = "";
  try {
    const result = await call();
    const turn = pick(result);
    addTurn("echo", turn.text, turn);
    $("latency").textContent = `Answer ${seconds(result.elapsed_ms)}`;
    if ($("speak-toggle").checked) await speak(turn.text, performance.now());
    else setPresence(resting());
  } catch (error) {
    addTurn("echo", error.message, { status: "not_discussed" });
    setPresence(resting());
  } finally {
    state.busy = false;
  }
}

async function speak(text, started) {
  try {
    const blob = await postForAudio(`${API}/voice/speech`, { text });
    $("latency").textContent += `, voice ${seconds(performance.now() - started)}`;
    const audio = new Audio(URL.createObjectURL(blob));
    state.audio = audio;
    state.speechText = text;
    audio.addEventListener("ended", stopSpeaking);
    setPresence("speaking");
    $("stop-btn").hidden = false;
    state.busy = false; // the user may talk over ECHO (barge-in) while it speaks
    await audio.play();
  } catch (error) {
    toast(`Could not play the answer: ${error.message}`);
    stopSpeaking();
  }
}

export function stopSpeaking() {
  if (state.audio) {
    state.audio.pause();
    URL.revokeObjectURL(state.audio.src);
    state.audio = null;
  }
  state.speechText = "";
  $("stop-btn").hidden = true;
  if (!state.busy) setPresence(resting());
}

export function isSpeaking() {
  return Boolean(state.audio);
}

export function speakingText() {
  return state.speechText;
}

export function isBusy() {
  return state.busy;
}

// ---------- events ----------

document.addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) {
    if (event.target === $("drawer")) closeDrawer();
    return;
  }
  if (target.dataset.topic) selectTopic(Number(target.dataset.topic)).catch((e) => toast(e.message));
  else if (target.dataset.openMeeting) openTranscript(Number(target.dataset.openMeeting));
  else if (target.dataset.meeting) openTranscript(Number(target.dataset.meeting), Number(target.dataset.line));
  else if ("build" in target.dataset) refreshBoard();
  else if (target.dataset.suggest) ask(target.dataset.suggest);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("drawer").hidden) closeDrawer();
});

$("drawer-close").addEventListener("click", closeDrawer);
$("catchup-btn").addEventListener("click", catchUp);
$("stop-btn").addEventListener("click", stopSpeaking);
$("rebuild-btn").addEventListener("click", () => {
  if (confirm("Re-read every meeting from scratch? This uses more LLM tokens than a normal update.")) refreshBoard(true);
});

$("topic-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("topic-name").value.trim();
  if (!name) return;
  try {
    const topic = await postJson(`${API}/topics`, { name });
    $("topic-name").value = "";
    await loadTopics(topic.id);
  } catch (error) {
    toast(error.message);
  }
});

$("upload-input").addEventListener("change", async (event) => {
  const files = [...event.target.files];
  event.target.value = "";
  if (!state.topicId) return toast("Add a topic first.");
  await uploadFiles(files);
});

$("ask-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const question = $("ask-input").value.trim();
  if (!question) return;
  $("ask-input").value = "";
  ask(question);
});

$("user-name").value = localStorage.getItem("echo.userName") ?? "";
$("user-name").addEventListener("change", () => {
  localStorage.setItem("echo.userName", $("user-name").value.trim());
  if (state.topicId) loadBoard().catch((e) => toast(e.message));
});

loadTopics().catch((error) => toast(`Could not reach the ECHO server: ${error.message}`));
