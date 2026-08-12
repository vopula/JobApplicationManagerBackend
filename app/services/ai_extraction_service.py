import json

from app.schemas.ingestion import AIJobExtractionResponse
from openai import OpenAI

import os
from dotenv import load_dotenv

load_dotenv()

AI_EXTRACTION_ENABLED = os.getenv("ENABLE_AI_EXTRACTION", "true").lower() not in ("false", "0", "no")

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

def extract_job_data_with_AI(job_text: str) -> AIJobExtractionResponse:
    if not AI_EXTRACTION_ENABLED:
        return AIJobExtractionResponse()

    prompt = build_AI_extraction_prompt(job_text)
    
    llm_response = call_llm(prompt)
    
    return parse_llm_output(llm_response)
    

def build_AI_extraction_prompt(job_text: str) -> str:
    return f"""
    You are an information extraction system.

    Extract structured information from the job posting text below.

    Return only a valid JSON object with exactly these keys:
    - company_name
    - job_title
    - location
    - date_posted
    - job_summary
    
    job_summary must be a JSON object with exactly these keys:
    - required_experience: a string describing the required experience, such as "3+ years", or null if not clearly present
    - key_skills: a list of strings containing the key required skills, or null if not clearly present

    Rules:
    - If a field is not explicitly or clearly present, return null.
    - Do not guess or infer missing values.
    - job_title should be the actual title of the job, not a heading unrelated to the role.
    - company_name should be the employer/company, not the job portal or platform name, unless no better company is available.
    - location should be a place/location only, not work mode.
    - date_posted should be in YYYY-MM-DD format if available, otherwise null.
    - job_summary should be a concise 2-3 sentence summary of the role and responsibilities.
    - Do not return markdown.
    - Do not wrap the JSON in code fences.
    - Do not include explanations or extra text.

    Job posting text:
    {job_text}
    """.strip()


def call_llm(prompt: str):
    response = client.responses.create(
        input=prompt,
        model="openai/gpt-oss-20b",
    )

    return response.output_text


def parse_llm_output(llm_response) -> AIJobExtractionResponse:
    cleaned_response = llm_response.strip()

    # if cleaned_response.startswith("```json"):
    #     cleaned_response = cleaned_response.removeprefix("```json").strip()
    # elif cleaned_response.startswith("```"):
    #     cleaned_response = cleaned_response.removeprefix("```").strip()

    # if cleaned_response.endswith("```"):
    #     cleaned_response = cleaned_response.removesuffix("```").strip()

    start_index = cleaned_response.find("{")
    end_index = cleaned_response.rfind("}")

    if start_index == -1 or end_index == -1 or start_index > end_index:
        raise ValueError("No valid JSON object found in LLM output.")

    json_text = cleaned_response[start_index:end_index + 1]

    parsed_output = json.loads(json_text)
    return AIJobExtractionResponse(**parsed_output)

    
def merge_rule_based_and_ai_data(rule_data: dict, ai_data: AIJobExtractionResponse) -> dict:
    merged_data = rule_data.copy()

    if not merged_data.get("company_name") and ai_data.company_name:
        merged_data["company_name"] = ai_data.company_name

    if not merged_data.get("job_title") and ai_data.job_title:
        merged_data["job_title"] = ai_data.job_title

    if not merged_data.get("location") and ai_data.location:
        merged_data["location"] = ai_data.location

    if not merged_data.get("date_posted") and ai_data.date_posted:
        merged_data["date_posted"] = ai_data.date_posted

    if ai_data.job_summary:
        merged_data["job_summary"] = ai_data.job_summary

    return merged_data

