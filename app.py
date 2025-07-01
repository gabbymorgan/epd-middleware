from typing import Annotated
from fastapi import FastAPI, File, UploadFile

from EPaper import *

interface = EPaperInterface()
app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/detect_screen_interaction")
async def detect_screen_interaction():
    try:
        screen_data = interface.detect_screen_interaction()
        return {"success": True, "screen_data": screen_data}
    except Exception as e:
        return {"success": False}


@app.post("/shutdown")
async def shutdown():
    try:
        interface.sleep()
        return {"success": True}
    except Exception as e:
        return {"success": False}


@app.post("/sleep")
async def sleep():
    try:
        interface.sleep()
        return {"success": True}
    except Exception as e:
        return {"success": False}


@app.post("/awaken")
async def awaken():
    try:
        interface.awaken()
        return {"success": True}
    except Exception as e:
        return {"success": False}


@app.post("/clear_screen")
async def clear_screen():
    try:
        interface.clear_screen()
        return {"success": True}
    except Exception as e:
        return {"success": False}


@app.post("/reset_canvas")
async def reset_canvas():
    try:
        interface.reset_canvas()
        return {"success": True}
    except Exception as e:
        return {"success": False}


@app.post("/render")
async def render(file: Annotated[bytes, File()]):
    try:
        print(len(file))
        interface.request_render(image_data=file)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/request_render")
async def request_render():
    try:
        interface.request_render()
        return {"success": True}
    except Exception as e:
        return {"success": False}


@app.post("/get_alignment")
async def get_alignment():
    try:
        alignment_data = interface.get_alignment()
        return {
            "success": True,
            "alignment_data": alignment_data
        }
    except Exception as e:
        return {"success": False}
