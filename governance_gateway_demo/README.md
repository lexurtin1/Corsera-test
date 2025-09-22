# Governance Gateway Demo

A minimal Flask demonstration app that simulates a GS DAP pre-clearance workflow. Upload a PDF, watch the compliance checks complete on a timer-driven circular progress ring, then download a generated compliance packet (JSON + CSV) and send it to a stubbed GS DAP rail.

## Requirements

- Python 3.9+
- pip

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Running the app

```bash
flask --app app run --debug
```

Alternatively, run `python app.py` while inside the `governance_gateway_demo/` folder.

The development server will be available at http://127.0.0.1:5000/.

## Demo flow

1. Navigate to `/` and upload any PDF (max 10MB).
2. Watch the circular progress ring complete each quarter as KYC, AML/Sanctions, Ownership & PEP, and Governance checks finish.
3. Once complete, download the generated JSON and CSV compliance packet.
4. Click **Send to GS DAP** to log delivery to the stubbed rail and view the confirmation receipt.

## Project structure

```
app.py
models.py
utils.py
static/
  css/style.css
  js/progress.js
templates/
  base.html
  index.html
  progress.html
  sent.html
  sample_uploads/Onboarding_Template.csv
uploads/
exports/
logs/
tmp/
```

Uploads, exports, and logs directories are created automatically at runtime. The session store is persisted in `tmp/session_store.json`.
