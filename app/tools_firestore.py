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

"""Firestore tools for FitTrack AI agent."""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-3627be7391bf"

_db: Optional[firestore.Client] = None


def get_firestore_client() -> firestore.Client:
    """Returns a singleton Firestore client with the explicit project ID."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def list_exercises(muscle_group: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists available exercises from the exercise library, optionally filtered by target muscle.

    Args:
        muscle_group: Optional target muscle to filter by (e.g. 'Chest', 'Quadriceps', 'Lats', 'Shoulders', 'Hamstrings').

    Returns:
        A list of exercise details including name, target muscles, equipment, difficulty, and form instructions.
    """
    db = get_firestore_client()
    collection_ref = db.collection("exercises")

    results = []
    if muscle_group:
        docs = collection_ref.stream()
        for doc in docs:
            data = doc.to_dict()
            if muscle_group.lower() in data.get("target_muscle", "").lower():
                results.append(data)
    else:
        for doc in collection_ref.stream():
            results.append(doc.to_dict())

    return results


def log_workout_session(
    session_name: str,
    exercises_data: str,
    duration_minutes: int = 45,
    notes: str = "",
    date: Optional[str] = None,
    user_id: str = "default_user",
) -> str:
    """Logs a completed workout session with exercises, sets, reps, and weights to Firestore.

    Args:
        session_name: Name or focus of the workout session (e.g., 'Push Day A', 'Leg Day Heavy').
        exercises_data: JSON string or description detailing the exercises performed and sets/reps/weight_kg.
                        Example: '[{"exercise": "Barbell Bench Press", "sets": [{"reps": 8, "weight_kg": 80.0}]}]'
        duration_minutes: Duration of the workout session in minutes.
        notes: Personal observations, RPE, or feelings on performance.
        date: Date of workout in YYYY-MM-DD format (defaults to current date if not provided).
        user_id: Identifier for the user (default: 'default_user').

    Returns:
        A confirmation message with the generated log ID and summary.
    """
    import json

    db = get_firestore_client()
    log_id = f"log-{uuid.uuid4().hex[:8]}"

    if not date:
        date = datetime.date.today().isoformat()

    parsed_exercises = []
    total_volume = 0.0

    try:
        parsed_exercises = json.loads(exercises_data)
        if isinstance(parsed_exercises, list):
            for item in parsed_exercises:
                for s in item.get("sets", []):
                    reps = float(s.get("reps", 0))
                    weight = float(s.get("weight_kg", 0.0))
                    total_volume += reps * weight
    except Exception:
        parsed_exercises = [{"raw_entry": exercises_data}]

    log_doc = {
        "id": log_id,
        "user_id": user_id,
        "session_name": session_name,
        "date": date,
        "duration_minutes": duration_minutes,
        "exercises": parsed_exercises,
        "total_volume_kg": total_volume,
        "notes": notes,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    db.collection("workout_logs").document(log_id).set(log_doc)
    return f"Successfully logged workout session '{session_name}' on {date} (ID: {log_id}). Total calculated volume: {total_volume} kg."


def get_recent_workout_logs(limit: int = 5, user_id: str = "default_user") -> List[Dict[str, Any]]:
    """Retrieves recent workout logs for the user to review history, performance, and volume trends.

    Args:
        limit: Maximum number of recent sessions to fetch (default: 5).
        user_id: User identifier (default: 'default_user').

    Returns:
        A list of recent workout sessions sorted by date.
    """
    db = get_firestore_client()
    query = (
        db.collection("workout_logs")
        .where(filter=firestore.FieldFilter("user_id", "==", user_id))
        .limit(limit)
    )

    logs = []
    for doc in query.stream():
        logs.append(doc.to_dict())

    logs.sort(key=lambda x: x.get("date", ""), reverse=True)
    return logs
