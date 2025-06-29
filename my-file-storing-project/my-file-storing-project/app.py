import os
from flask import Flask, jsonify, request, render_template
from supabase import create_client, Client
from flask_cors import CORS

# Initialize the Flask App
app = Flask(__name__)
CORS(app) # This is important for allowing requests

# Get Supabase credentials from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# This is the route for your main web page (the Mini App)
@app.route('/')
def index():
    # It will find and serve your index.html file
    return render_template('index.html')

# This is the route for your API to get the files
@app.route('/api/get_files')
def get_files():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        # The same Supabase query as before
        response = supabase.table("files").select("file_link", "created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500