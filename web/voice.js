// Live voice loop: microphone -> backend WebSocket (Deepgram) -> question -> spoken answer.
// Barge-in: when the user starts talking while ECHO speaks, ECHO stops at once.

import { ask, isBusy, isSpeaking, setListening, speakingText, stopSpeaking, toast } from "./app.js";

const FRAME_MS = 250; // how often the recorder hands audio to the socket
const BARGE_IN_WORDS = 2; // words heard before ECHO stops talking (ignores coughs and noise)
const OWN_VOICE_OVERLAP = 0.7; // share of heard words that match ECHO's current answer
const $ = (id) => document.getElementById(id);

const mic = {
  stream: null,
  recorder: null,
  socket: null,
  heard: [], // final pieces of the current utterance
};

function socketUrl() {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${location.host}/api/v1/voice/transcribe`;
}

function micError(error) {
  if (error.name === "NotAllowedError") {
    return "Microphone access is blocked. Allow it from the icon in the address bar, then tap the circle again.";
  }
  if (error.name === "NotFoundError") return "No microphone was found. Plug one in or type your question.";
  return `The microphone could not start: ${error.message}`;
}

async function start() {
  try {
    mic.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
  } catch (error) {
    toast(micError(error));
    return;
  }
  mic.heard = [];
  mic.socket = new WebSocket(socketUrl());
  mic.socket.binaryType = "arraybuffer";
  mic.socket.onopen = () => {
    const type = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : "";
    mic.recorder = new MediaRecorder(mic.stream, type ? { mimeType: type } : undefined);
    mic.recorder.ondataavailable = (event) => {
      if (event.data.size && mic.socket?.readyState === WebSocket.OPEN) mic.socket.send(event.data);
    };
    mic.recorder.start(FRAME_MS);
    setButton(true);
    setListening(true);
  };
  mic.socket.onmessage = (message) => handle(JSON.parse(message.data));
  mic.socket.onerror = () => toast("Lost the connection to the speech service.");
  mic.socket.onclose = () => stop(false);
}

function stop(sendStop = true) {
  if (mic.recorder?.state === "recording") mic.recorder.stop();
  mic.stream?.getTracks().forEach((track) => track.stop());
  if (sendStop && mic.socket?.readyState === WebSocket.OPEN) {
    mic.socket.send(JSON.stringify({ type: "stop" }));
  }
  mic.recorder = null;
  mic.stream = null;
  mic.socket = null;
  mic.heard = [];
  $("caption").textContent = "";
  setButton(false);
  setListening(false);
}

function setButton(on) {
  const button = $("mic-btn");
  button.setAttribute("aria-pressed", String(on));
  button.setAttribute("aria-label", on ? "Stop talking to ECHO" : "Start talking to ECHO");
  $("mic-hint").textContent = on ? "Listening. Tap again to turn the mic off." : "Tap the circle and ask out loud";
}

/** True when the mic most likely picked up ECHO's own voice from the speakers. */
function isOwnVoice(text) {
  const spoken = new Set(words(speakingText()));
  const heard = words(text);
  if (!spoken.size || !heard.length) return false;
  return heard.filter((w) => spoken.has(w)).length / heard.length >= OWN_VOICE_OVERLAP;
}

function words(text) {
  return text.toLowerCase().match(/[a-z0-9']+/g) ?? [];
}

function handle(event) {
  if ((event.type === "partial" || event.type === "final") && isOwnVoice(event.text)) return;
  switch (event.type) {
    case "partial": {
      if (isSpeaking() && words(event.text).length >= BARGE_IN_WORDS) stopSpeaking(); // barge-in
      $("caption").textContent = [...mic.heard, event.text].join(" ");
      break;
    }
    case "final":
      if (isSpeaking()) stopSpeaking();
      mic.heard.push(event.text);
      $("caption").textContent = mic.heard.join(" ");
      if (event.speech_final) submit();
      break;
    case "utterance_end":
      submit();
      break;
    case "error":
      toast(event.message);
      break;
    default:
      break;
  }
}

function submit() {
  const question = mic.heard.join(" ").trim();
  mic.heard = [];
  if (!question) return;
  if (isBusy()) {
    toast("ECHO is still answering. Ask again in a moment.");
    return;
  }
  $("caption").textContent = "";
  ask(question);
}

$("mic-btn").addEventListener("click", () => (mic.socket ? stop() : start()));
window.addEventListener("beforeunload", () => stop());
