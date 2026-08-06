from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from app.executor import allowcommand
from app.schemas import CommandRequest, CommandResponse
from app.security import get_user_auth_token
from dotenv import  load_dotenv
from os import getenv
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
        return allowcommand(user_req.action,user_req.parameter)
    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))


@app.websocket("/ws/execute")
async def ws(websocket: WebSocket, token: str):

    if getenv("API_SECRET_KEY") != token:
        await websocket.close(code=1008)
        return "error"

    await websocket.accept()


    while True:
        try:
            data =  await websocket.receive_json()
            try:
                allowcommand(data["action"],data["parameter"])
                res = await websocket.send_json({"status": "success", "message": "completed"})
            except Exception as e:
                await websocket.send_json({f"status": "error", "message": str(e)})
        except Exception as e:
            print(e)
            break




