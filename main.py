from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

class CaseInput(BaseModel):
    patient_description: str

@app.post("/create-case")
async def create_case(case_input: CaseInput):
    gpt_prompt = f"""
    You are a clinical assistant AI. Parse the following clinical input into structured JSON.

    ONLY return the JSON body. Do NOT include markdown, explanations, or text outside of the JSON.
    
    Input: "{case_input.patient_description}"

    JSON fields: patient_name, national_id, age, address, email, phone_number, diagnoses,
    signs, symptoms, allergies, past_medical_history, past_surgical_history, medications, 
    nsp_notes, summary, risk_level, research_potential, research_notes, court_related, team_members.
    """

    try:
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a clinical case parser."},
                {"role": "user", "content": gpt_prompt}
            ]
        )
        raw_response = gpt_response.choices[0].message.content
        structured_data = json.loads(raw_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT parsing error: {str(e)}")

    structured_data["created_at"] = datetime.utcnow().isoformat()

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
