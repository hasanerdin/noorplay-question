#!/bin/bash
export SUPABASE_URL=$(grep SUPABASE_URL .streamlit/secrets.toml | cut -d'"' -f2)
export SUPABASE_KEY=$(grep SUPABASE_KEY .streamlit/secrets.toml | cut -d'"' -f2)
export OPENAI_API_KEY=$(grep OPENAI_API_KEY .streamlit/secrets.toml | cut -d'"' -f2)
pytest tests/ -v --tb=short
