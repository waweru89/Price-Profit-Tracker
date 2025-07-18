from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("https://auolsufrudtjvvjcsuqf.supabase.co")
key = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1b2xzdWZydWR0anZ2amNzdXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI4NDE2MjAsImV4cCI6MjA2ODQxNzYyMH0.mLL8yr8anxLHr-s4LcV6wS02p7sIUbsB6VBjMOaTNwM")
supabase: Client = create_client(url, key)

def create_user(email, password):
    return supabase.auth.sign_up({
        "email": email,
        "password": password
    })

def sign_in_user(email, password):
    return supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
