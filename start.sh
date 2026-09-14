#!/bin/bash

# Start FastAPI backend on internal port 8000
uvicorn src.api:app --host 0.0.0.0 --port 8000 &

# Wait 3 seconds for backend to warm up
sleep 3

# Start Streamlit on default Hugging Face Spaces port 7860
streamlit run app.py --server.port 7860 --server.address 0.0.0.0