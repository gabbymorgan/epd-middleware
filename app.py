from typing import Annotated
from fastapi import FastAPI, File, WebSocket

from EPaper import *

interface = EPaperInterface()
app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.websocket("/screen_interaction")
async def screen_interaction_stream(
    *,
    websocket: WebSocket
):
    await websocket.accept()
    while True:
        screen_data = interface.detect_screen_interaction()
        await websocket.send_json(screen_data)
        time.sleep(0.02)

@app.get("/screen_interaction")
async def detect_screen_interaction():
    try:
        screen_data = interface.detect_screen_interaction()
        return {"success": True, "screen_data": screen_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/shutdown")
async def shutdown():
    try:
        interface.shutdown()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/sleep")
async def sleep():
    try:
        interface.sleep()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/awaken")
async def awaken():
    try:
        interface.awaken()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/clear_screen")
async def clear_screen():
    try:
        interface.clear_screen()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/reset_canvas")
async def reset_canvas():
    try:
        interface.reset_canvas()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/request_render")
async def request_render(file: Annotated[bytes, File()]):
    try:
        interface.request_render(image_data=file)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/window")
async def get_window():
    try:
        window_data = interface.get_window()
        return {
            "success": True,
            "window_dat": window_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
