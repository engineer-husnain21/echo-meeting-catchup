# Resource setup guide

ECHO needs four free accounts. Every key goes only into `.env` (never commit it).
`.env.example` lists every setting with a safe default.

## 1. Groq (LLM)

1. Sign up at https://console.groq.com and open **API Keys**, then **Create API Key**.
2. In `.env`:
   ```
   LLM_BASE_URL=https://api.groq.com/openai/v1
   LLM_API_KEY=<your Groq key>
   LLM_MODEL=openai/gpt-oss-120b
   LLM_REASONING_EFFORT=medium
   ```
3. The free tier has per-minute and per-day token limits. Building the board for the five sample
   meetings uses roughly 15k to 40k tokens. Use **Re-read all meetings** only when needed.

Any OpenAI-compatible provider works by changing these lines only.

## 2. Jina AI (embeddings)

1. Get a free key at https://jina.ai/embeddings (no card needed).
2. In `.env`:
   ```
   EMBEDDING_BASE_URL=https://api.jina.ai/v1/
   EMBEDDING_API_KEY=<your Jina key>
   EMBEDDING_MODEL=jina-embeddings-v3
   EMBEDDING_DIMENSIONS=768
   EMBEDDING_PASSAGE_TASK=retrieval.passage
   EMBEDDING_QUERY_TASK=retrieval.query
   ```

If you change the model or dimensions later, also change `QDRANT_COLLECTION` (or delete the old
collection), because a collection keeps the vector size it was created with.

## 3. Qdrant Cloud (vector store)

1. Sign up at https://cloud.qdrant.io and create a **free cluster** (any region).
2. Copy the cluster URL and create an API key for it.
3. In `.env`, keep `:443` at the end of the URL:
   ```
   QDRANT_URL=https://<cluster-id>.<region>.cloud.qdrant.io:443
   QDRANT_API_KEY=<your Qdrant key>
   QDRANT_COLLECTION=echo_chunks
   ```
   Many office and home networks block Qdrant's default port 6333. Check with:
   ```powershell
   Test-NetConnection <cluster-id>.<region>.cloud.qdrant.io -Port 443
   ```
4. ECHO creates the collection and its payload indexes on the first upload.

Leave `QDRANT_URL` empty to use an in-memory store (data is lost when the server stops).

## 4. Deepgram (speech to text and text to speech)

1. Sign up at https://console.deepgram.com. New accounts get $200 free credit.
   If the signup page returns 403 on your network, try mobile data.
2. Create an API key with **Member** rights.
3. In `.env`:
   ```
   DEEPGRAM_API_KEY=<your Deepgram key>
   DEEPGRAM_STT_MODEL=nova-3
   DEEPGRAM_TTS_MODEL=aura-2-thalia-en
   ```
4. If you see `getaddrinfo failed` in the server log, your network's DNS cannot resolve
   `api.deepgram.com`. Check:
   ```powershell
   Resolve-DnsName api.deepgram.com
   Resolve-DnsName api.deepgram.com -Server 8.8.8.8
   ```
   If only the second works, set the WiFi adapter DNS to `8.8.8.8` and `1.1.1.1`
   (Settings, Network, WiFi, DNS server assignment, Manual), then `ipconfig /flushdns`.
   A mobile hotspot also works.

## 5. Check everything

```powershell
uvicorn app.main:app --reload
```

- http://127.0.0.1:8000/api/v1/health returns `ok`.
- Upload one sample meeting in the UI: it shows "Added ... (N lines)" (Jina and Qdrant work).
- The board appears after the upload (Groq works).
- Tap the circle, allow the microphone, and ask a question: you see a live caption and hear the
  answer (Deepgram works). Use Chrome or Edge on `127.0.0.1` or `localhost`; browsers only allow
  the microphone on secure origins, and these two count as secure.

## Costs

Everything above runs on free tiers. Deepgram uses the free credit (a demo session costs a few
cents). No card is needed for Groq, Jina or Qdrant.
