// Small fetch helpers. Every error carries the API's own message.

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json();
      if (body.message) message = body.message;
      else if (Array.isArray(body.detail)) message = body.detail[0]?.msg ?? message;
      else if (body.detail) message = body.detail;
    } catch {
      // not JSON: keep the generic message
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return response;
}

export async function getJson(path) {
  return (await request(path)).json();
}

export async function postJson(path, body = {}) {
  const response = await request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

export async function postFile(path, file) {
  const form = new FormData();
  form.append("file", file);
  return (await request(path, { method: "POST", body: form })).json();
}

export async function postForAudio(path, body) {
  const response = await request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.blob();
}
