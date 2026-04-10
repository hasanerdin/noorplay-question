"""
Pytest configuration and shared fixtures.

Patches Streamlit before any test module imports shared/database.py,
so the database layer can run outside a live Streamlit app.

Integration tests are auto-skipped when SUPABASE_URL / SUPABASE_KEY
are absent from the environment (populated by run_tests.sh).
"""
from __future__ import annotations
import os


# ── Streamlit mock (must run before database.py is first imported) ──

def pytest_configure(config):  # noqa: ARG001
    """Replace Streamlit runtime deps with lightweight fakes.

    database.py is decorated with @st.cache_resource and reads
    st.secrets — both require a live Streamlit runtime.  Replacing
    them here (before collection-time imports) lets the module load
    cleanly in plain pytest.
    """
    import streamlit as st

    # @st.cache_resource  →  transparent pass-through decorator
    st.cache_resource = lambda fn=None, **kwargs: (
        fn if callable(fn) else lambda f: f
    )

    # st.secrets  →  plain dict backed by environment variables
    st.secrets = {
        "SUPABASE_URL":   os.environ.get("SUPABASE_URL", ""),
        "SUPABASE_KEY":   os.environ.get("SUPABASE_KEY", ""),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
    }


# ── Skip guard for integration tests ─────────────────────────────

import pytest  # noqa: E402  (must come after the stdlib imports above)


@pytest.fixture(scope="session")
def requires_db():
    """Attach to any integration test; skips when DB credentials are absent."""
    if not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY")):
        pytest.skip(
            "Integration tests require SUPABASE_URL and SUPABASE_KEY env vars. "
            "Run via ./run_tests.sh or export them manually."
        )
