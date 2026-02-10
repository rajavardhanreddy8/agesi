import httpx
import supabase
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import json
import os
import logging
from datetime import datetime
from cryptography.fernet import Fernet
from dotenv import load_dotenv

print(f"CWD: {os.getcwd()}")
if os.path.exists('.env'):
    print(".env exists")
    with open('.env') as f:
        print(f"Content start: {f.read(50)}")
load_dotenv(override=True)
print(f"DB_HOST: {os.getenv('DB_HOST')}")
