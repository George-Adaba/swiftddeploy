import os
import time
import random
import asyncio
'''basically calling the FastAPI class from the fastapi library, fastapi is a webframework for building apis'''
from fastapi import FastAPI,Response,HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


app = FastAPI()
'''here we created an instance of the fast api class and assigned it to the variable app from this variable 
 we wll call all our routes '''

start_time = time.time()

chaos_config = {
    "mode" : "recover", 
    "duration" : 0,
    "rate" : 0.5
}

class ChaosConfig(BaseModel):
    mode : str
    duration : Optional[int]= 0
    rate : Optional[float]= 0.0



@app.get('/')
async def read_root(response : Response):
    mode_env = os.getenv('MODE' , 'stable')
    version = os.getenv('APP_VERSION' , '0.0.0')

    if mode_env == "canary":
        response.headers["X-mode"] = "canary"

        if chaos_config["mode"] == "slow":
            await asyncio.sleep(chaos_config["duration"])

        elif chaos_config["mode"] == "error":
            if random.random() < chaos_config["rate"]:
                raise HTTPException(status_code=500, detail="chaos error injected")

    return {
        "message" : "wlecome to the swiftdeploy api",
        "mode" : mode_env,
        "version" : version,
        "timestamp" : datetime.now(timezone.utc).isoformat()
    }

@app.get('/healthz')
def health_check():
    uptime = int(time.time() - start_time)
    return {
        "status" : "ok",
        "uptime" : uptime
    }

@app.post('/chaos')
def set_chaos(command : ChaosConfig):
    if os.getenv('MODE') != "canary":
        raise HTTPException(status_code=400, detail="chaos configuration can only be set in canary mode")
    
    if command.mode == "recover":
        chaos_config["mode"] = "recover"
        chaos_config["duration"] = 0
        chaos_config["rate"] = 0.0
    else:
        chaos_config["mode"] = command.mode
        chaos_config["duration"] = command.duration or 0
        chaos_config["rate"] = command.rate or 0.0

    return {
        "message" : f"chaos configuration set to {command.mode}",
        "config" : chaos_config
    }


if __name__ == "__main__":
    import uvicorn
    app_port = int(os.getenv('APP_PORT', '8000'))
    uvicorn.run(app, host="0.0.0.0", port=app_port)