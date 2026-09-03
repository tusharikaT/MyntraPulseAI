import os
import subprocess
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

class SyncResponse(BaseModel):
    status: str
    message: str

def run_sync_pipeline():
    # Trigger the ETL pipeline script in the background
    script_path = os.path.join(os.path.dirname(__file__), "../../scripts/run_pipeline.py")
    try:
        subprocess.run(["python", script_path], check=True)
    except Exception as e:
        print(f"Sync Pipeline Error: {e}")

@router.post("/sync", response_model=SyncResponse)
def trigger_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync_pipeline)
    return SyncResponse(
        status="success",
        message="Review synchronization pipeline has been triggered in the background."
    )
