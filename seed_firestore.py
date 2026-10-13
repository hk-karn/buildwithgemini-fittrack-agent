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

"""Seed script to populate comprehensive workout catalog (5-6 exercises per major muscle group)."""

import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-3627be7391bf"

EXERCISES = [
    # --- CHEST (6 exercises) ---
    {
        "id": "barbell-bench-press",
        "name": "Barbell Bench Press",
        "target_muscle": "Chest",
        "secondary_muscles": ["Triceps", "Anterior Deltoids"],
        "equipment": "Barbell, Flat Bench",
        "difficulty": "Intermediate",
        "instructions": "Lie flat on bench, grip bar slightly wider than shoulder width. Lower bar smoothly to mid-chest, then drive up.",
    },
    {
        "id": "incline-dumbbell-press",
        "name": "Incline Dumbbell Press",
        "target_muscle": "Chest",
        "secondary_muscles": ["Anterior Deltoids", "Triceps"],
        "equipment": "Dumbbells, Incline Bench (30-45 deg)",
        "difficulty": "Intermediate",
        "instructions": "Set bench to 30-45 degrees. Press dumbbells up overhead with palms angled slightly inward; lower until elbows reach 90 degrees.",
    },
    {
        "id": "cable-chest-flye",
        "name": "Cable Chest Flye",
        "target_muscle": "Chest",
        "secondary_muscles": ["Anterior Deltoids"],
        "equipment": "Cable Crossover Machine",
        "difficulty": "Beginner",
        "instructions": "Stand in center with slight forward lean. Bring handles together in front of chest in a hugging motion, squeezing pecs.",
    },
    {
        "id": "chest-dips",
        "name": "Weighted / Bodyweight Chest Dips",
        "target_muscle": "Chest",
        "secondary_muscles": ["Triceps", "Front Deltoids"],
        "equipment": "Dip Station / Parallel Bars",
        "difficulty": "Intermediate",
        "instructions": "Lean torso forward roughly 30 degrees and flare elbows slightly outward. Lower until elbows reach 90 degrees, then push back up.",
    },
    {
        "id": "dumbbell-pullover",
        "name": "Dumbbell Pullover",
        "target_muscle": "Chest",
        "secondary_muscles": ["Lats", "Serratus Anterior", "Triceps"],
        "equipment": "Dumbbell, Flat Bench",
        "difficulty": "Intermediate",
        "instructions": "Lie perpendicular across a bench with upper back supported. Lower dumbbell back over head in a slow arc, feeling chest and serratus stretch.",
    },
    {
        "id": "push-up",
        "name": "Push-Up",
        "target_muscle": "Chest",
        "secondary_muscles": ["Triceps", "Anterior Deltoids", "Core"],
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "instructions": "Maintain rigid plank line. Lower chest to floor with elbows angled back 45 degrees, then press through the palms to full lockout.",
    },

    # --- BACK / LATS (6 exercises) ---
    {
        "id": "pull-up",
        "name": "Pull-Up",
        "target_muscle": "Lats",
        "secondary_muscles": ["Biceps", "Upper Back", "Forearms"],
        "equipment": "Pull-up Bar",
        "difficulty": "Intermediate",
        "instructions": "Overhand grip wider than shoulder width. Pull elbows down and back towards hips until chin clears bar.",
    },
    {
        "id": "barbell-bent-over-row",
        "name": "Barbell Bent-Over Row",
        "target_muscle": "Back",
        "secondary_muscles": ["Lats", "Rhomboids", "Rear Delts", "Biceps"],
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "instructions": "Hinge at hips to a 45-degree torso angle with a flat back. Row bar toward lower ribcage / navel, driving through elbows.",
    },
    {
        "id": "lat-pulldown",
        "name": "Wide-Grip Lat Pulldown",
        "target_muscle": "Lats",
        "secondary_muscles": ["Biceps", "Rear Delts", "Middle Back"],
        "equipment": "Cable Lat Pulldown Machine",
        "difficulty": "Beginner",
        "instructions": "Grip bar wide, sit upright with slight backward lean. Pull bar down toward upper collarbone while depressing shoulder blades.",
    },
    {
        "id": "seated-cable-row",
        "name": "Seated Cable Row",
        "target_muscle": "Back",
        "secondary_muscles": ["Rhomboids", "Lats", "Biceps"],
        "equipment": "Cable Row Machine / V-bar handle",
        "difficulty": "Beginner",
        "instructions": "Sit upright with neutral spine. Pull handle into lower abdomen, retracting and squeezing shoulder blades tightly.",
    },
    {
        "id": "single-arm-dumbbell-row",
        "name": "Single-Arm Dumbbell Row",
        "target_muscle": "Back",
        "secondary_muscles": ["Lats", "Rear Deltoids", "Biceps"],
        "equipment": "Dumbbell, Flat Bench",
        "difficulty": "Beginner",
        "instructions": "Place one knee and hand on bench for support. Pull dumbbell up towards hip pocket keeping elbow close to side.",
    },
    {
        "id": "t-bar-row",
        "name": "T-Bar Row",
        "target_muscle": "Back",
        "secondary_muscles": ["Lats", "Traps", "Rear Delts", "Spinal Erectors"],
        "equipment": "T-Bar Machine or Landmine attachment",
        "difficulty": "Intermediate",
        "instructions": "Straddle the bar with knees slightly bent. Pull bar into upper abdomen with chest elevated, squeezing middle back.",
    },

    # --- LEGS / QUADRICEPS (6 exercises) ---
    {
        "id": "barbell-squat",
        "name": "Barbell Back Squat",
        "target_muscle": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings", "Lower Back", "Core"],
        "equipment": "Barbell, Squat Rack",
        "difficulty": "Intermediate",
        "instructions": "Bar rested across traps. Squat down with chest tall and knees tracking over toes until thighs are at or below parallel.",
    },
    {
        "id": "front-squat",
        "name": "Barbell Front Squat",
        "target_muscle": "Quadriceps",
        "secondary_muscles": ["Upper Back", "Core", "Glutes"],
        "equipment": "Barbell, Squat Rack",
        "difficulty": "Advanced",
        "instructions": "Rest bar across front deltoids with clean grip or cross-arm grip, elbows high. Squat deep keeping torso upright.",
    },
    {
        "id": "leg-press",
        "name": "45-Degree Leg Press",
        "target_muscle": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings"],
        "equipment": "Leg Press Machine",
        "difficulty": "Beginner",
        "instructions": "Position feet hip-width on sled. Lower weight sled until knees are bent to 90 degrees; press through whole foot without locking knees violently.",
    },
    {
        "id": "bulgarian-split-squat",
        "name": "Bulgarian Split Squat",
        "target_muscle": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings", "Calves"],
        "equipment": "Dumbbells, Bench",
        "difficulty": "Intermediate",
        "instructions": "Elevate rear foot on bench behind you. Lower hips until front thigh is parallel to ground, driving through front heel to return.",
    },
    {
        "id": "walking-lunges",
        "name": "Dumbbell Walking Lunges",
        "target_muscle": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings", "Core"],
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Take controlled step forward, dropping back knee gently toward ground. Drive up into next step maintaining posture.",
    },
    {
        "id": "leg-extension",
        "name": "Seated Leg Extension",
        "target_muscle": "Quadriceps",
        "secondary_muscles": [],
        "equipment": "Leg Extension Machine",
        "difficulty": "Beginner",
        "instructions": "Position shin pad above ankles. Extend knees fully, pausing for 1 second at top contraction before lowering with control.",
    },

    # --- HAMSTRINGS & GLUTES (6 exercises) ---
    {
        "id": "conventional-deadlift",
        "name": "Conventional Deadlift",
        "target_muscle": "Hamstrings",
        "secondary_muscles": ["Glutes", "Lower Back", "Lats", "Forearms"],
        "equipment": "Barbell, Bumper Plates",
        "difficulty": "Advanced",
        "instructions": "Hips back, grip bar outside legs, engage lats, push through the floor keeping spine neutral throughout.",
    },
    {
        "id": "romanian-deadlift",
        "name": "Romanian Deadlift (RDL)",
        "target_muscle": "Hamstrings",
        "secondary_muscles": ["Glutes", "Lower Back"],
        "equipment": "Barbell or Dumbbells",
        "difficulty": "Intermediate",
        "instructions": "Slight knee bend fixed in place. Hinge hips back as bar slides down thighs until deep hamstring stretch is felt; contract glutes to return.",
    },
    {
        "id": "lying-leg-curl",
        "name": "Lying Hamstring Leg Curl",
        "target_muscle": "Hamstrings",
        "secondary_muscles": ["Calves"],
        "equipment": "Leg Curl Machine",
        "difficulty": "Beginner",
        "instructions": "Lie face down with pad behind ankles. Curl heels toward glutes, pausing briefly at peak contraction before lowering smoothly.",
    },
    {
        "id": "barbell-hip-thrust",
        "name": "Barbell Hip Thrust",
        "target_muscle": "Glutes",
        "secondary_muscles": ["Hamstrings", "Adductors"],
        "equipment": "Barbell, Bench, Pad",
        "difficulty": "Intermediate",
        "instructions": "Upper back against bench, barbell cushioned over hips. Drive through heels to full hip extension, squeezing glutes hard at top.",
    },
    {
        "id": "nordic-hamstring-curl",
        "name": "Nordic Hamstring Curl",
        "target_muscle": "Hamstrings",
        "secondary_muscles": ["Calves", "Glutes"],
        "equipment": "Ankle anchor or Partner",
        "difficulty": "Advanced",
        "instructions": "Kneel with ankles anchored. Lower torso forward slowly resisting gravity purely with hamstrings; push off lightly with hands to return.",
    },
    {
        "id": "standing-calf-raise",
        "name": "Standing Calf Raise",
        "target_muscle": "Calves",
        "secondary_muscles": ["Gastrocnemius", "Soleus"],
        "equipment": "Calf Raise Machine or Step + Dumbbell",
        "difficulty": "Beginner",
        "instructions": "Balls of feet on edge of platform. Lower heels for deep stretch, then rise onto toes into full plantarflexion.",
    },

    # --- SHOULDERS (6 exercises) ---
    {
        "id": "overhead-press",
        "name": "Overhead Barbell Press",
        "target_muscle": "Shoulders",
        "secondary_muscles": ["Triceps", "Upper Chest", "Core"],
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "instructions": "Press bar overhead from collarbone while bracing core and glutes. Lock out overhead with head slightly forward.",
    },
    {
        "id": "dumbbell-lateral-raise",
        "name": "Dumbbell Lateral Raise",
        "target_muscle": "Shoulders",
        "secondary_muscles": ["Traps"],
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Stand with slight forward torso tilt. Raise dumbbells out to sides leading with elbows until parallel to floor; control negative.",
    },
    {
        "id": "seated-dumbbell-shoulder-press",
        "name": "Seated Dumbbell Shoulder Press",
        "target_muscle": "Shoulders",
        "secondary_muscles": ["Triceps", "Upper Chest"],
        "equipment": "Dumbbells, Adjustable Bench",
        "difficulty": "Beginner",
        "instructions": "Sit with back supported. Press dumbbells overhead until arms are nearly straight; lower under control to ear height.",
    },
    {
        "id": "face-pull",
        "name": "Cable Face Pull",
        "target_muscle": "Shoulders",
        "secondary_muscles": ["Rear Deltoids", "Rotator Cuff", "Rhomboids"],
        "equipment": "Cable Machine, Rope Attachment",
        "difficulty": "Beginner",
        "instructions": "Set pulley at eye height. Pull rope toward forehead/eyes while separating ends and externally rotating shoulders.",
    },
    {
        "id": "rear-delt-flye",
        "name": "Reverse Pec Deck / Rear Delt Flye",
        "target_muscle": "Shoulders",
        "secondary_muscles": ["Rear Deltoids", "Rhomboids", "Traps"],
        "equipment": "Reverse Pec Deck Machine or Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Chest against machine pad. Sweep handles outwards in wide horizontal arc without bending elbows excessively.",
    },
    {
        "id": "arnold-press",
        "name": "Arnold Press",
        "target_muscle": "Shoulders",
        "secondary_muscles": ["Triceps", "Anterior Deltoids"],
        "equipment": "Dumbbells",
        "difficulty": "Intermediate",
        "instructions": "Start with dumbbells at chin level, palms facing you. As you press overhead, rotate wrists so palms face forward at top.",
    },

    # --- ARMS: BICEPS & TRICEPS (6 exercises) ---
    {
        "id": "barbell-bicep-curl",
        "name": "Barbell Bicep Curl",
        "target_muscle": "Biceps",
        "secondary_muscles": ["Forearms", "Brachialis"],
        "equipment": "Barbell / EZ-Curl Bar",
        "difficulty": "Beginner",
        "instructions": "Stand tall, elbows pinned to sides. Curl bar up toward shoulders contracting biceps; lower slowly.",
    },
    {
        "id": "incline-dumbbell-curl",
        "name": "Incline Dumbbell Curl",
        "target_muscle": "Biceps",
        "secondary_muscles": ["Brachialis"],
        "equipment": "Dumbbells, Incline Bench (45 deg)",
        "difficulty": "Intermediate",
        "instructions": "Lie back on incline bench letting arms hang straight down for maximum long-head stretch. Curl dumbbells with supination.",
    },
    {
        "id": "hammer-curl",
        "name": "Dumbbell Hammer Curl",
        "target_muscle": "Biceps",
        "secondary_muscles": ["Brachioradialis", "Brachialis"],
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Hold dumbbells with neutral grip (palms facing each other). Curl up keeping palms facing inward throughout movement.",
    },
    {
        "id": "skull-crushers",
        "name": "EZ-Bar Skull Crushers (Lying Triceps Extension)",
        "target_muscle": "Triceps",
        "secondary_muscles": ["Forearms"],
        "equipment": "EZ-Bar, Flat Bench",
        "difficulty": "Intermediate",
        "instructions": "Lie on bench holding bar over forehead. Hinge only at elbows to lower bar toward forehead/crown; extend elbows back to start.",
    },
    {
        "id": "triceps-rope-pushdown",
        "name": "Triceps Rope Pushdown",
        "target_muscle": "Triceps",
        "secondary_muscles": ["Forearms"],
        "equipment": "Cable Pulley, Rope Attachment",
        "difficulty": "Beginner",
        "instructions": "Pin elbows to ribs. Push rope downward and spread ends apart at bottom for peak triceps contraction.",
    },
    {
        "id": "overhead-dumbbell-triceps-extension",
        "name": "Overhead Dumbbell Triceps Extension",
        "target_muscle": "Triceps",
        "secondary_muscles": ["Shoulders"],
        "equipment": "Dumbbell",
        "difficulty": "Beginner",
        "instructions": "Hold dumbbell overhead with both hands cupping the top plate. Lower dumbbell behind head by bending elbows, then press back up.",
    },

    # --- CORE / ABDOMINALS (5 exercises) ---
    {
        "id": "hanging-leg-raise",
        "name": "Hanging Leg Raise",
        "target_muscle": "Core",
        "secondary_muscles": ["Hip Flexors", "Forearms"],
        "equipment": "Pull-up Bar or Captain's Chair",
        "difficulty": "Intermediate",
        "instructions": "Hang from bar without swinging. Raise straight legs up until parallel to floor or higher by tucking pelvis upward.",
    },
    {
        "id": "cable-woodchopper",
        "name": "Cable Woodchopper",
        "target_muscle": "Core",
        "secondary_muscles": ["Obliques", "Shoulders"],
        "equipment": "Cable Machine",
        "difficulty": "Beginner",
        "instructions": "Rotate torso across body in diagonal cutting motion from high to low (or low to high), keeping arms extended.",
    },
    {
        "id": "ab-wheel-rollout",
        "name": "Ab Wheel Rollout",
        "target_muscle": "Core",
        "secondary_muscles": ["Lats", "Shoulders", "Lower Back"],
        "equipment": "Ab Wheel",
        "difficulty": "Advanced",
        "instructions": "Kneel with wheel under shoulders. Roll forward extending body as far as possible while keeping core braced; pull back with abs.",
    },
    {
        "id": "plank",
        "name": "Forearm Plank",
        "target_muscle": "Core",
        "secondary_muscles": ["Shoulders", "Glutes", "Transverse Abdominis"],
        "equipment": "Bodyweight, Mat",
        "difficulty": "Beginner",
        "instructions": "Rest on forearms and toes. Maintain a straight, rigid line from head to heels while pulling belly button into spine.",
    },
    {
        "id": "pallof-press",
        "name": "Pallof Press (Anti-Rotation)",
        "target_muscle": "Core",
        "secondary_muscles": ["Obliques", "Glutes"],
        "equipment": "Cable Machine or Resistance Band",
        "difficulty": "Beginner",
        "instructions": "Stand perpendicular to cable. Hold handle at chest and press straight out, resisting the rotational pull of the cable.",
    },
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connecting to Firestore for project: {PROJECT_ID}")
    print(f"Total exercises to seed: {len(EXERCISES)}")

    for ex in EXERCISES:
        doc_id = ex["id"]
        db.collection("exercises").document(doc_id).set(ex)
        print(f"Seeded: [{ex['target_muscle']}] {ex['name']}")

    print(f"\nSuccessfully seeded {len(EXERCISES)} exercises across all major muscle groups!")


if __name__ == "__main__":
    seed_database()
