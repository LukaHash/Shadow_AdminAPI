from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from app.stream import generate_frames
from app.executor import allowcommand
from app.schemas import CommandRequest, CommandResponse
from app.security import get_user_auth_token
from dotenv import  load_dotenv
from os import getenv
import soundcard
import asyncio
import numpy as np
load_dotenv()
app = FastAPI()



@app.get("/ping")
async def ping():
    return {"status": "online","service":"Shadow_Admin"}


@app.get("/")
async def get_client():
    return FileResponse("client.html")




@app.get("/http-header-auth")
async def auth_http_header(
    status: str =Depends(get_user_auth_token)
):
    return status



@app.post("/execute")
async def execute_command(user_req: CommandRequest, token: str = Depends(get_user_auth_token)):
    try:
        return allowcommand(user_req)
    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))


@app.websocket("/ws/execute")
async def ws(websocket: WebSocket, token: str):

    if getenv("API_SECRET_KEY") != token:
        await websocket.close(code=1008)
        return

    await websocket.accept()


    while True:
        try:
            data =  await websocket.receive_json()
            cmd = CommandRequest(**data) # В класс CommandRequest закидываем всё что нам пришо в data
            try:
                allowcommand(cmd)
                res = await websocket.send_json({"status": "success", "message": "completed"})
            except Exception as e:
                await websocket.send_json({"status": "error", "message": str(e)})
        except Exception as e:
            print(e)
            break

@app.get("/stream")
async def show_stream(token: str):
    if getenv("API_SECRET_KEY") != token:
        raise HTTPException(status_code=401,detail="Unauthorized")
    return StreamingResponse(generate_frames(),media_type="multipart/x-mixed-replace; boundary=frame")







@app.websocket("/ws/audio")
async def ws_audio(websocket: WebSocket, token: str):
    if getenv("API_SECRET_KEY") != token:
        await websocket.close(code=1008)
        return "error"


    await websocket.accept()

    SAMPLERATE = 48000
    CHUNK_SIZE = 1024
    # Получаем дефолтный динамик
    default_speaker = soundcard.default_speaker()
    # получаем все микрофоны в виде объекта с микрофонами с глобальным прослушиванием loopback
    mics = soundcard.all_microphones(include_loopback=True)
    mic = None
    for m in mics:
        if m.name == default_speaker.name:
            mic = m
            break

    if not mic:
        await websocket.close(code=1011)
        return
    # Открываем микрофон для записи
    with mic.recorder(samplerate=SAMPLERATE,channels=1) as rec:
        while True:
            try:
                # data - массив numpy float32
                data = await asyncio.to_thread(rec.record,numframes=CHUNK_SIZE)
                data_int16 = (data * 32767).astype(np.int16)
                audio_bytes = data_int16.tobytes()
                await  websocket.send_bytes(audio_bytes)
            except WebSocketDisconnect as e:
                print(e)
                break

            except Exception as e:
                print(e)
                break








