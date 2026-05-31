# Gym Assistant AI — Claude Code Instructions

## Project Overview

We are building a mobile-first AI movement-analysis application for gymgoers, physiotherapists, trainers, and gyms.

The app helps users record or upload exercise videos, receive form feedback, understand whether their movement likely matches the intended muscle target, and track movement-quality progress over time. Physiotherapists and trainers should eventually be able to assign exercises, review client videos, monitor adherence, track pain/recovery signals, and comment on form.

Core positioning:

> We close the gap between the workout plan and the actual rep.

Most fitness apps tell users what workout to do. This product helps users know whether they are doing the movement correctly, safely, and effectively for their goal.

## Founding Context

The team has two founders:

* Business founder: PR, marketing, sales, partnerships, pitch, LAU Engine LAUNCH application, customer discovery, and business strategy.
* Technical co-founder: engineering, architecture, AI implementation, testing, deployment, and technical execution.

Short-term goal:

Build a focused, demo-ready MVP strong enough to support an application to LAU Engine LAUNCH. The product must look credible, differentiated, technically feasible, and testable with real gymgoers and physiotherapists.

## Product Principle

This is not a generic AI workout app.

Prioritize movement quality, form correction, target-muscle execution, and professional review over broad workout/nutrition features.

The MVP should prove one core loop:

1. User selects an exercise.
2. User selects the intended target muscle or goal.
3. User uploads or records a short video.
4. App analyzes the movement using pose estimation, rule-based logic, or prototype analysis.
5. App returns a Form Score, Target-Muscle Match estimate, and 2–3 corrective cues.
6. User can save the result and compare progress over time.
7. Optional: physiotherapist/trainer can review the video and comment.

## MVP Priorities

Build now:

* User onboarding with goal, experience level, height, weight, age, pain/injury warning, and equipment access.
* Exercise selection.
* Target muscle selection.
* Video upload or recording flow.
* Prototype movement-analysis result screen.
* Form Score.
* Target-Muscle Match estimate.
* Range-of-motion feedback.
* Tempo/control feedback.
* Exercise-specific corrective cues.
* Saved analysis history.
* Simple physiotherapist/trainer review page.

Test manually first:

* Human expert review of form videos.
* Physiotherapist dashboard workflows.
* Pain-aware training recommendations.
* Exercise substitution logic.
* Quality-adjusted training volume.

Keep for later:

* Full live real-time AI coaching.
* Full nutrition/calorie tracker.
* Large exercise library.
* Wearable integrations.
* Social network.
* Marketplace for expert reviews.
* Advanced custom ML models.

Cut for now:

* Medical diagnosis.
* Claims that the app treats or cures injuries.
* Claims that video alone directly measures muscle activation.
* Overbuilt AI architecture before product validation.

## First Exercises to Support

Start with a small number of high-value movements:

1. Squat or goblet squat
2. Lunge
3. Romanian deadlift or hip hinge
4. Push-up
5. Row
6. Plank
7. Shoulder external rotation or simple rehab/prehab movement

For the first demo, prioritize squat/goblet squat before expanding.

## AI and Movement Analysis Rules

For the MVP, prefer simple and testable analysis over advanced but fragile AI.

Acceptable MVP approaches:

* Existing pose-estimation library.
* Rule-based joint angle thresholds.
* Rep counting.
* Range-of-motion scoring.
* Tempo scoring.
* Stability/symmetry checks.
* Mocked analysis clearly labeled in code.
* Semi-automated analysis supported by human review.

Important limitation:

Video analysis can estimate movement mechanics and likely exercise emphasis, but it cannot directly measure muscle activation. Do not claim direct muscle activation measurement unless future validated hardware or methods support it.

Use careful wording:

* Good: "Likely shifts emphasis toward glutes."
* Good: "Movement pattern may reduce quad emphasis."
* Bad: "Your quads activated 72%."
* Bad: "This diagnoses your knee problem."

## Safety and Medical Claim Rules

Do not present the app as diagnosing, treating, curing, or preventing medical conditions.

Use safe language:

* Form feedback
* Movement quality
* Exercise education
* Professional review
* Pain-aware training
* Recovery exercise tracking
* Consult a licensed professional for pain, injury, or rehab decisions

If a user reports pain, injury, numbness, instability, sharp pain, post-surgical status, or worsening symptoms, the app should recommend professional evaluation instead of giving aggressive training advice.

For physiotherapy features, position the product as support for adherence, monitoring, education, and communication — not as a replacement for a licensed clinician.

## Technical Direction

When starting a task:

1. Inspect the existing project structure.
2. Identify the framework, package manager, and build/test commands.
3. Explain the relevant files.
4. Propose a small implementation plan.
5. Implement in small steps.
6. Run relevant checks.
7. Summarize what changed.

Prefer:

* Modular architecture.
* Small components.
* Clear service boundaries.
* Replaceable prototype analysis logic.
* Typed data models where possible.
* Simple UI that is demo-ready.
* Explicit mock/real boundaries.
* No unnecessary dependencies.

Avoid:

* Massive rewrites.
* Hidden mock behavior.
* Fake AI claims.
* Hardcoded secrets.
* Premature custom ML infrastructure.
* Overly complex databases before validation.
* Features that do not support the LAUNCH demo.

## Repository Structure

```
gym-assistant/
├── CLAUDE.md                        # This file
├── requirements.txt                 # Python dependencies
├── server.py                        # FastAPI WebSocket server (real-time pose streaming)
├── pushup_analyzer.py               # CLI entry point (standalone video analysis)
├── run.bat                          # Convenience launcher script
├── gym_assistant/                   # Core Python package
│   ├── __init__.py                  # Exports run()
│   ├── main.py                      # Main exercise tracking loop + MediaPipe integration
│   ├── counter.py                   # Rep counting logic
│   ├── evaluation.py                # Form/posture evaluation
│   ├── geometry.py                  # Geometric helpers for pose analysis
│   ├── pose_utils.py                # Keypoint building, angle calculations
│   ├── ui.py                        # On-frame text overlay and color helpers
│   ├── csv_logger.py                # Session data logging to CSV
│   ├── movement_memory.py           # Per-rep movement history for pattern detection
│   └── exercises/
│       ├── __init__.py              # EXERCISES registry dict
│       ├── pushup.py                # Push-up config (keypoints, thresholds, form checks)
│       └── squat.py                 # Squat config (keypoints, thresholds, form checks)
└── gym-ui/                          # React + Vite frontend
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx                 # React entry point
        ├── App.jsx                  # Root component
        ├── GymDashboard.jsx         # Main dashboard (WebSocket client, live metrics)
        ├── App.css
        └── index.css
```

### Key architectural notes

* Exercise configs live in `gym_assistant/exercises/` as plain dicts. Each config declares keypoints, rep thresholds, memory metrics, and form checks — the engine in `main.py` / `evaluation.py` drives all exercises generically from these configs. Add a new exercise by adding a new config file and registering it in `exercises/__init__.py`.
* The backend streams pose analysis over WebSocket (`server.py`). The React dashboard (`GymDashboard.jsx`) is the WebSocket client.
* `movement_memory.py` accumulates per-frame metrics across a rep, then `evaluation.py` runs form checks against the aggregated values after the rep completes.
* CSV logging in `csv_logger.py` writes session data to `sessions/` (git-ignored).

## Build Commands

### Python backend

Package manager: **pip**

```bash
# Install dependencies
pip install -r requirements.txt

# Run the WebSocket server (backend)
python server.py

# Run standalone CLI analysis
python pushup_analyzer.py

# Convenience launcher
run.bat
```

### React frontend

Package manager: **npm** (located in `gym-ui/`)

```bash
cd gym-ui

# Install dependencies
npm install

# Run dev server
npm run dev

# Run lint
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

No test runner is currently configured. Add pytest (backend) or Vitest (frontend) when test coverage becomes a priority.

## Suggested App Modules

Adapt to the actual stack after inspecting the repo.

Possible modules:

* `onboarding` — user profile, goals, experience, pain/injury warning.
* `exercise-library` — supported exercises, target muscles, cues.
* `video-upload` — upload/recording flow.
* `movement-analysis` — pose/rule/mock analysis logic.
* `analysis-results` — Form Score, Target-Muscle Match, cues.
* `progress-history` — saved sessions and comparison.
* `professional-review` — trainer/physio comments and client view.
* `safety` — pain flags, medical disclaimers, escalation rules.

## Data Model Concepts

Use or adapt these concepts as needed:

User:

* id
* name
* age
* height
* weight
* training goal
* experience level
* equipment access
* pain/injury notes
* createdAt

Exercise:

* id
* name
* movement pattern
* primary muscles
* secondary muscles
* common mistakes
* setup cues
* safety notes

AnalysisSession:

* id
* userId
* exerciseId
* targetMuscle
* videoUrl or local video reference
* formScore
* targetMuscleMatchScore
* rangeOfMotionScore
* tempoScore
* stabilityScore
* correctiveCues
* safetyFlags
* analysisType: mock | rule_based | pose_estimation | human_review
* createdAt

ProfessionalReview:

* id
* analysisSessionId
* reviewerId
* reviewerRole: physiotherapist | trainer | coach
* comments
* recommendedAction
* createdAt

## Result Screen Requirements

A movement-analysis result should be understandable in less than 10 seconds.

Show:

* Exercise name
* Target muscle
* Form Score from 0–100
* Target-Muscle Match estimate
* 2–3 most important corrective cues
* Safety note if needed
* Save result button
* Option to compare with previous result
* Option to request professional review later

Do not overload the user with too much technical biomechanical detail in the first screen.

## Product Voice

The app should sound:

* Scientific
* Clear
* Calm
* Practical
* Safety-aware
* Not gimmicky
* Not bro-science
* Not overconfident

Example cue style:

Good:
"Your knees appear to move inward during the lowering phase. Try reducing load and keeping the knees aligned with the toes."

Bad:
"Terrible squat. Your form is dangerous."

Good:
"Your torso angle suggests this rep may shift more load toward the hips and lower back than intended."

Bad:
"Your lower back is injured."

## Coding Rules

* Make the smallest useful change.
* Prefer readable code over clever code.
* Do not hardcode secrets.
* Use environment variables for API keys.
* Clearly label mock data and prototype logic.
* Keep analysis logic separate from UI.
* Add tests or verification steps for important logic.
* Run lint, typecheck, test, or build commands when available.
* If a command fails, explain why and fix the root cause instead of suppressing errors.
* Do not add a dependency without explaining why it is needed.
* Do not change unrelated files unless necessary.

## Design Requirements

For MVP screens:

* Mobile-first.
* Clean, modern, minimal.
* Demo-ready for accelerator pitch.
* Clear CTA on every screen.
* Avoid clutter.
* Make the analysis result feel trustworthy.
* Use plain language and concise cues.
* Do not make the product feel like a medical device.

Accessibility:

* Use readable font sizes.
* Maintain good contrast.
* Avoid relying only on color to communicate risk.
* Use clear labels for buttons and forms.

## LAU Engine LAUNCH Demo Goal

The demo should prove:

1. We understand a real gym/physio problem.
2. The product is not another generic workout app.
3. A user can upload or record a movement.
4. The app gives useful form feedback.
5. The feedback is clear and safe.
6. Progress can be tracked.
7. A physiotherapist/trainer workflow is possible.
8. The product can be piloted with gyms, trainers, or physiotherapists.

Prioritize features that make the demo stronger.

## Current Roadmap

Phase 0 — Project setup

* Confirm stack. (done: Python/FastAPI + React/Vite)
* Confirm package manager. (done: pip + npm)
* Confirm build/test commands. (done: see Build Commands above)
* Create basic structure. (done)

Phase 1 — Demo user flow

* Onboarding.
* Exercise selection.
* Target muscle selection.
* Video upload.
* Mock analysis result screen.
* Save analysis result.

Phase 2 — Movement analysis prototype

* Add pose-estimation or rule-based analysis.
* Start with squat/goblet squat.
* Add range-of-motion, tempo, and knee-tracking feedback if feasible.
* Keep mock fallback clearly labeled.

Phase 3 — Professional review

* Add simple reviewer dashboard.
* Allow reviewer comments.
* Allow client analysis history.
* Track adherence and pain feedback.

Phase 4 — Pilot readiness

* Add basic analytics.
* Add privacy-safe user/video handling.
* Add exportable demo data.
* Improve onboarding and result UX.
* Prepare app for testing with real users.

## Definition of Done

A feature is done only when:

* The user flow works.
* The UI is understandable.
* Mocked parts are clearly labeled.
* Safety wording is appropriate.
* Relevant checks pass or failures are explained.
* The feature supports the MVP and LAUNCH demo.
* The implementation is modular enough to improve later.

## When to Ask Before Acting

Ask before:

* Major architecture changes.
* Adding paid APIs.
* Adding large dependencies.
* Changing authentication strategy.
* Changing database provider.
* Deleting files.
* Making irreversible data changes.
* Making medical or regulatory assumptions.

Proceed without asking for small, clearly scoped implementation improvements.

## Do Not Modify This File Unnecessarily

Do not update `CLAUDE.md` after every session.

Update it only when:

* The project stack is confirmed.
* Build/test commands are discovered.
* A permanent architecture decision is made.
* The MVP scope changes.
* A repeated Claude mistake needs to be prevented.
* A safety/product rule must become permanent.
