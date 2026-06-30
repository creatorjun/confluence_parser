# config.py
import os

BASE_URL = os.environ.get("CONFLUENCE_BASE_URL", "https://your-instance.atlassian.net/wiki")
EMAIL = os.environ.get("CONFLUENCE_EMAIL", "")
API_TOKEN = os.environ.get("CONFLUENCE_API_TOKEN", "")
ROOT_PAGE_ID = os.environ.get("CONFLUENCE_ROOT_PAGE_ID", "")
