
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types





load_dotenv(".env")


def extract_resume_with_ai(resume_text):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Gemini API key missing")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=20000,
            retry_options=types.HttpRetryOptions(attempts=1)
        )
    )

    prompt = f"""
Extract structured information from the resume below.

Return a JSON object with these keys:
- skills
- education
- experience
- projects
- certifications
- awards
- languages

Each key must contain a list.
Use only information present in the resume.
Do not invent missing details.
Return empty lists for missing sections.

RESUME:
{resume_text}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response")

    import json
    result = json.loads(response.text)

    expected_keys = [
        "skills", "education", "experience",
        "projects", "certifications", "awards", "languages"
    ]

    if not isinstance(result, dict):
        raise ValueError("Gemini returned invalid JSON structure")

    for key in expected_keys:
        if key not in result or not isinstance(result[key], list):
            raise ValueError(f"Invalid or missing field: {key}")

    return {key: result[key] for key in expected_keys}
