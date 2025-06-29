import os
import json
from supabase import create_client, Client

# These are read from the Netlify environment variables you will set
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def handler(event, context):
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get user_id from the request, e.g., /api/get_files?user_id=123
        user_id = event["queryStringParameters"].get("user_id")

        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"error": "user_id is required"})}

        # Query Supabase, select all links for that user, order by newest first
        response = supabase.table("files").select("file_link", "created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        return {
            "statusCode": 200,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps(response.data)
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}