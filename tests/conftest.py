import pytest, os
from supabase import create_client

@pytest.fixture(scope="session")
def sb():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)

@pytest.fixture
def test_book_id():
    return "book_test_pytest"

@pytest.fixture
def test_chapter_id():
    return "chapter_test_pytest"

@pytest.fixture
def test_page_id():
    return "page_test_pytest"
