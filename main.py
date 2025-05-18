from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from openai import OpenAI
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

class CaseInput(BaseModel):
    patient_description: str

class CaseUpdate(BaseModel):
    id: str
    updates: Dict[str, Any]

@app.post("/create-case")
async def create_case(case_input: CaseInput):
    gpt_prompt = f"""
    You are a clinical assistant AI using the Neurosemiotic Psychiatry (NSP) model. 
    Parse this freeform input into JSON with the following fields:

    Required fields: 
    patient_name, national_id, age, address, email, phone_number, diagnoses, signs, symptoms, allergies, 
    past_medical_history, past_surgical_history, medications, nsp_notes, summary, 
    risk_level (High/Medium/Low), research_potential (true/false), research_notes, 
    court_related (true/false), team_members.

    Use null or empty strings where data is missing.
    Return raw JSON only.

    Input: "{case_input.patient_description}"
    """

    try:
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a CortexAI clinical case parser using the NSP framework."},
                {"role": "user", "content": gpt_prompt}
            ]
        )
        raw_response = gpt_response.choices[0].message.content
        print("🧠 GPT RAW RESPONSE:")
        print(f"START>>> {raw_response} <<<END")

        if not raw_response or not raw_response.strip().startswith("{"):
            raise HTTPException(status_code=500, detail=f"GPT returned invalid or empty JSON: START>>> {raw_response} <<<END")

        try:
            structured_data = json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"GPT parsing error: {str(e)} | Raw: {raw_response}")

        structured_data["created_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT response failure: {str(e)}")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/cases",
            headers=headers,
            json=structured_data
        )
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase insert error: {str(e)}")

    return {"message": "Case created successfully", "data": structured_data}

@app.get("/cases")
def get_cases():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/cases?select=*",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cases: {str(e)}")

@app.get("/cases/{case_id}")
def get_case_by_id(case_id: str):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/cases?id=eq.{case_id}&select=*",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            raise HTTPException(status_code=404, detail="Case not found")
        return data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching case: {str(e)}")

@app.patch("/update-case")
def update_case(update: CaseUpdate):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    update_data = update.updates
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/cases?id=eq.{update.id}",
            headers=headers,
            json=update_data
        )
        response.raise_for_status()
        return {"message": "Case updated successfully", "data": update_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")
