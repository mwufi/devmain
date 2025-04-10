cat << EOF > request.json
{
    "endpoint": "projects/digital-seat-456019-k6/locations/us-central1/publishers/google/models/veo-2.0-generate-001",
    "instances": [
        {
            "prompt": "A time-lapse of a futuristic cityscape, where people live and work in giant, inflatable structures. The structures are constantly changing shape and color, creating a mesmerizing spectacle. The camera pans across the cityscape, revealing the intricate details of the structures and the people who live in them. Saturated, gauzy, dream-like cinematography.",
        }
    ],
    "parameters": {
        "aspectRatio": "16:9",
        "sampleCount": 4,
        "durationSeconds": "8",
        "fps": "",
        "personGeneration": "allow_adult",
        "enablePromptRewriting": true,
        "addWatermark": true,
        "includeRaiReason": true,
    }
}
EOF

PROJECT_ID="digital-seat-456019-k6"
LOCATION_ID="us-central1"
API_ENDPOINT="us-central1-aiplatform.googleapis.com"
MODEL_ID="veo-2.0-generate-001"

OPERATION_ID=$(curl \
-X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
"https://${API_ENDPOINT}/v1/projects/${PROJECT_ID}/locations/${LOCATION_ID}/publishers/google/models/${MODEL_ID}:predictLongRunning" -d '@request.json' | grep '"name": .*'| sed 's|"name":\ ||g')

echo "OPERATION_ID: ${OPERATION_ID}"