import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from fastapi import APIRouter
from pydantic import BaseModel
from rag.copilot import query_copilot
from api.schemas import CopilotResponse

router = APIRouter()

PREFETCH_FILE = os.path.join(os.path.dirname(__file__), '../../data/prefetched_copilot.json')
prefetched_data = {}
if os.path.exists(PREFETCH_FILE):
    with open(PREFETCH_FILE, 'r', encoding='utf-8') as f:
        prefetched_data = json.load(f)

class CopilotRequest(BaseModel):
    question: str
    platform: str = None
    top_k: int = 10

@router.post("/copilot/ask", response_model=CopilotResponse)
def ask_copilot(req: CopilotRequest):
    # Check if the exact question exists in prefetched data
    if req.question in prefetched_data:
        return CopilotResponse(**prefetched_data[req.question])
    
    filters = {}
    if req.platform:
        filters["platform"] = req.platform
        
    result_dict = query_copilot(req.question, top_k=req.top_k, filters=filters)
    
    return CopilotResponse(**result_dict)
