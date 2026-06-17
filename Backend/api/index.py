import os
import sys

# main.py болон бусад модулиуд эх (Backend) фолдерт байгаа тул import замд нэмнэ.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: E402  (Vercel Python runtime энэ ASGI `app`-ийг ажиллуулна)
