# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
import re
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

from google import genai
from google.cloud import storage
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory.memory_entry import MemoryEntry
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from app.a2ui_utils import a2ui_callback
from app.tools_firestore import (
    list_exercises,
    log_workout_session,
    get_recent_workout_logs,
)


MODEL = "gemini-3.8-flash"
GCS_BUCKET_NAME = "fittrack-agent-media-qwiklabs-gcp-04-3627be7391bf"
PROJECT_ID = "qwiklabs-gcp-04-3627be7391bf"
SANDBOX_RESOURCE_NAME = (
    "projects/430663193407/locations/us-east1/reasoningEngines/5271653579348770816/sandboxEnvironments/8050017208157339648"
)

code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME,
)


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, extract and send salient fitness facts, workout logs, badges, and PRs to Memory Bank."""
    # 1. Standard session extraction via Memory Bank
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"[Warning] add_session_to_memory failed: {e}")

    # 2. Inspect session events to explicitly preserve workout sessions, badges, and PRs
    try:
        session = callback_context.session
        events = getattr(session, "events", [])
        explicit_memories = []

        for event in events[-4:]:  # Inspect recent turn events
            content = getattr(event, "content", None)
            if not content or not getattr(content, "parts", None):
                continue
            for part in content.parts:
                fn_resp = getattr(part, "function_response", None)
                if fn_resp:
                    resp_dict = fn_resp.response if isinstance(fn_resp.response, dict) else {}
                    # Case A: Logged workout session
                    if fn_resp.name == "log_workout_session" and resp_dict.get("status") == "success":
                        msg = resp_dict.get("message", "Workout session logged successfully.")
                        explicit_memories.append(
                            f"User Workout Log: {msg}"
                        )
                    # Case B: Generated Milestone Badge
                    elif fn_resp.name == "generate_workout_badge_image" and resp_dict.get("status") == "success":
                        url = resp_dict.get("public_url", "")
                        fname = resp_dict.get("filename", "")
                        explicit_memories.append(
                            f"User Milestone Badge Earned: '{fname}' with public image URL: {url}"
                        )
                # Case C: PRs or 1RM records in text responses
                text = getattr(part, "text", "")
                if text and ("1RM" in text or "Personal Record" in text or "PR" in text) and ("kg" in text or "lbs" in text):
                    # Pick concise summary line for PR
                    lines = [ln.strip() for ln in text.split("\n") if ("1RM" in ln or "PR" in ln or "Record" in ln) and len(ln.strip()) < 150]
                    for line in lines[:2]:
                        explicit_memories.append(f"User Strength Record / PR: {line}")

        if explicit_memories and hasattr(callback_context, "add_memory"):
            entries = [
                MemoryEntry(
                    content=types.Content(
                        parts=[types.Part(text=fact)],
                        role="user",
                    ),
                    author="user",
                )
                for fact in set(explicit_memories)
            ]
            await callback_context.add_memory(memories=entries)
    except Exception as e:
        print(f"[Warning] explicit memory recording: {e}")

    return None

_genai_client = None
_storage_client = None


def get_genai_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    return _genai_client


def get_storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


async def generate_workout_badge_image(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generates an image for workout achievement badges, milestones, or exercise form visuals.

    Saves the image into session artifacts (visible in Playground Artifacts panel) and uploads
    it directly to the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        prompt: Detailed description of the workout badge or fitness visual to generate (e.g. 'Gold metallic shield badge with dumbbells celebrating 100kg bench press milestone, 3d render').
        tool_context: The ADK ToolContext injected by the framework to save session artifacts.

    Returns:
        A dictionary containing the public image URL, filename, and confirmation status.
    """
    client = get_genai_client()
    image_prompt = f"High quality fitness illustration: {prompt}"

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=image_prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break
        if image_bytes:
            break

    if not image_bytes:
        return {"error": "Failed to generate image bytes from model."}

    ext = "jpg" if "jpeg" in mime_type.lower() or "jpg" in mime_type.lower() else "png"
    unique_id = uuid.uuid4().hex[:8]
    filename = f"badge_{unique_id}.{ext}"

    # 1. Save artifact into Playground
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes directly to public GCS bucket
    storage_cli = get_storage_client()
    bucket = storage_cli.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(f"badges/{filename}")
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/badges/{filename}"

    return {
        "status": "success",
        "filename": filename,
        "public_url": public_url,
        "message": f"Badge generated and saved as artifact '{filename}'. Public URL: {public_url}",
    }


def search_online_exercise_library(category: str = "Chest", limit: int = 4) -> List[Dict[str, Any]]:
    """Searches the free open-source Wger Workout Manager public API for exercise guides, equipment, and form notes.

    Args:
        category: Body part or muscle category to search (e.g. 'Chest', 'Back', 'Arms', 'Legs', 'Abs', 'Shoulders', 'Calves', 'Cardio').
        limit: Maximum number of exercise variations to fetch (default: 4).

    Returns:
        A list of exercise details including exercise name, category, target muscles, equipment, and form instructions.
    """
    api_key = os.environ.get("WGER_API_KEY", "").strip()

    categories = {
        "abs": 10, "core": 10, "arms": 8, "biceps": 8, "triceps": 8,
        "back": 12, "lats": 12, "calves": 14, "cardio": 15,
        "chest": 11, "legs": 9, "quads": 9, "hamstrings": 9, "shoulders": 13
    }
    cat_id = categories.get(category.strip().lower(), 11)
    url = f"https://wger.de/api/v2/exerciseinfo/?category={cat_id}&limit={max(1, min(limit, 10))}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "FitTrackAgent/1.0",
                "Accept": "application/json",
            },
        )
        if api_key:
            req.add_header("Authorization", f"Token {api_key}")

        with urllib.request.urlopen(req, timeout=7) as resp:
            data = json.loads(resp.read().decode())

        results = []
        for item in data.get("results", []):
            trans = next((t for t in item.get("translations", []) if t.get("language") == 2 and t.get("name")), None)
            if not trans and item.get("translations"):
                trans = item["translations"][0]
            if not trans:
                continue

            raw_desc = trans.get("description") or trans.get("description_source") or ""
            clean_desc = re.sub(r"<[^>]+>", "", raw_desc).replace("&nbsp;", " ").strip()

            results.append({
                "name": trans.get("name"),
                "category": item.get("category", {}).get("name", category),
                "muscles": [m.get("name_en") or m.get("name") for m in item.get("muscles", [])],
                "equipment": [eq.get("name") for eq in item.get("equipment", [])],
                "instructions": clean_desc[:250] if clean_desc else "Standard movement mechanics.",
            })

        return results
    except Exception as e:
        return [{"error": f"Failed to fetch from Wger API: {str(e)}"}]


def calculate_1rm_and_zones(weight: float, reps: int, unit: str = "kg") -> Dict[str, Any]:
    """Calculates estimated 1-Rep Max (1RM) using Epley & Brzycki formulas and training intensity zones.

    Args:
        weight: The weight lifted (e.g. 80.0, 185.0).
        reps: The number of completed repetitions (typically between 1 and 12).
        unit: Unit of measurement ('kg' or 'lbs'). Defaults to 'kg'.

    Returns:
        A dictionary with estimated 1RM, formula estimates, and percentage-based training zones.
    """
    if reps <= 0 or weight <= 0:
        return {"error": "Weight and reps must both be positive numbers."}

    if reps == 1:
        one_rm = round(weight, 1)
        epley = brzycki = one_rm
    else:
        epley = weight * (1.0 + (reps / 30.0))
        brzycki = weight * (36.0 / (37.0 - reps)) if reps < 37 else epley
        one_rm = round((epley + brzycki) / 2.0, 1)

    zones = {
        "90% (Near Max / Peaking)": round(one_rm * 0.90, 1),
        "85% (Heavy Strength / 4-6 reps)": round(one_rm * 0.85, 1),
        "80% (Strength / 6-8 reps)": round(one_rm * 0.80, 1),
        "75% (Hypertrophy / 8-10 reps)": round(one_rm * 0.75, 1),
        "70% (Hypertrophy / 10-12 reps)": round(one_rm * 0.70, 1),
        "60% (Endurance / Warm-up)": round(one_rm * 0.60, 1),
    }

    return {
        "input_weight": weight,
        "input_reps": reps,
        "unit": unit,
        "estimated_1rm": one_rm,
        "epley_estimate": round(epley, 1),
        "brzycki_estimate": round(brzycki, 1),
        "training_zones": zones,
    }


def get_current_time(timezone_name: str = "America/New_York") -> str:
    """Returns current date and time in specified timezone.

    Args:
        timezone_name: IANA timezone string like 'America/New_York', 'UTC', or 'America/Los_Angeles'.
    """
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.datetime.now(tz)
    return f"The current time ({timezone_name}) is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

ROLE_DESCRIPTION = """You are FitTrack AI, an intelligent, motivating workout coach.
Your mission is to help users build personalized training programs, calculate training loads, discover new exercises, log workout sessions, generate motivational milestone badges, and track strength progress.
You have access to persistent cross-session memory through Vertex AI Memory Bank. You remember all user logged workout sessions, milestone badges earned, and logged PRs across conversations. Use these remembered details to personalize workouts, celebrate progress, and recommend progressive overload.

Key guidelines:
1. When asked to perform complex numerical computations, data analysis, volume calculations, statistical trend analysis, or write and execute custom Python scripts, execute Python code in your secure Agent Engine sandbox.
2. When a user asks for a celebratory badge, milestone poster, or achievement visual (e.g. hitting a PR, joining a club like '100 kg Bench Press Club', or completing a workout streak), use `generate_workout_badge_image` to generate the image, save it as an artifact, and provide its public URL so it embeds directly. Acknowledge and remember this earned badge for future conversations.
3. When a user logs a PR or asks about 1RM, working weights, target percentages, or how heavy they should lift based on a set (e.g. 'I did 80 kg for 8 reps, what is my 1RM?'), use `calculate_1rm_and_zones` to compute accurate estimates and training zones. Record the PR clearly so it persists in memory.
4. When a user asks for exercise variations, alternative exercises, or global exercise ideas from the public database, use `search_online_exercise_library` to fetch real movements, equipment needs, and instructions.
5. For core catalog lookups and personal program designs, you can also use `list_exercises`.
6. When a user reports their completed workout (e.g. exercises, weights, reps, sets), use `log_workout_session` to persist their session into Firestore. Always format the exercise data cleanly, summarize the total volume and key achievements, and remember the session.
7. When a user asks about their workout history, past performance, past badges, or PR progress, combine your retrieved memory facts with `get_recent_workout_logs` to provide an inspiring, comprehensive overview.
8. Encourage progressive overload and safe lifting technique.
"""

UI_DESCRIPTION = (
    "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
    "Never nest a Card inside a Card. "
    "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
    "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
    "nothing in adk web). "
    "You may include one Image component, but only when you have a public https "
    "URL for the image (for example the URL an image tool returns after uploading "
    "to a public bucket). Set the Image url to that exact https link, for example "
    "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
    "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
    "not have a public URL, add a short Text line noting the image instead. "
    "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
    "headings and emphasis. "
    "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
    "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
)

INSTRUCTION = schema_manager.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
    workflow_description="Analyze the user's fitness request and return structured A2UI UI when appropriate, especially for workout plans, exercise cards, training zones, logs, and badge presentations.",
    ui_description=UI_DESCRIPTION,
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        generate_workout_badge_image,
        calculate_1rm_and_zones,
        search_online_exercise_library,
        list_exercises,
        log_workout_session,
        get_recent_workout_logs,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
