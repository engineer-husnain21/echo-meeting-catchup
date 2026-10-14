"""Voice endpoints: live transcription over a WebSocket and text-to-speech."""

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, Response, WebSocket, WebSocketDisconnect

from app.core.dependencies import get_voice_service
from app.core.exceptions import EchoError
from app.schemas.speak_request import SpeakRequest
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])
VoiceServiceDep = Annotated[VoiceService, Depends(get_voice_service)]


@router.post("/speech", response_class=Response)
async def speak(request: SpeakRequest, service: VoiceServiceDep) -> Response:
    """Return the text as spoken MP3 audio."""
    return Response(content=await service.speak(request.text), media_type="audio/mpeg")


@router.websocket("/transcribe")
async def transcribe(websocket: WebSocket, service: VoiceServiceDep) -> None:
    """Browser sends binary audio frames (and {"type": "stop"} to finish).

    Server sends JSON SpeechEvents, then {"type": "closed"}, or {"type": "error"} on failure.
    """
    await websocket.accept()
    with suppress(WebSocketDisconnect, RuntimeError):  # the browser may leave at any time
        try:
            async for event in service.transcribe(_audio_from(websocket)):
                await websocket.send_json(event.model_dump())
            await websocket.send_json({"type": "closed"})
        except EchoError as error:
            await websocket.send_json({"type": "error", "message": error.message})
        await websocket.close()


async def _audio_from(websocket: WebSocket) -> AsyncIterator[bytes]:
    """Yield audio frames until the browser sends a text message or disconnects."""
    while True:
        message = await websocket.receive()
        if message["type"] == "websocket.disconnect":
            return
        if message.get("bytes"):
            yield message["bytes"]
        elif message.get("text") is not None:
            return  # {"type": "stop"} or any text ends the stream
