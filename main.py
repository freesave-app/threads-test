import requests
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # এটি তোমার ওয়েবসাইটকে এই এপিআই ব্যবহার করার অনুমতি দেবে

# --- তোমার দেওয়া লজিক অংশ শুরু ---

def extract_post_id(url):
    """URL থেকে Post ID বের করা"""
    patterns = [
        r"threads\.net/@[\w.]+/post/([\w-]+)",
        r"threads\.net/t/([\w-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def parse_video_data(data):
    """API রেসপন্স থেকে ভিডিও URL বের করা"""
    try:
        items = data["data"]["data"]["edges"][0]["node"]["thread_items"]
        for item in items:
            post = item.get("post", {})
            media_type = post.get("media_type")
            
            if media_type == 2:  # Single Video
                video_versions = post.get("video_versions", [])
                if video_versions:
                    return {"url": video_versions[0]["url"]}
            
            elif media_type == 8: # Carousel Video
                carousel = post.get("carousel_media", [])
                for media in carousel:
                    if media.get("media_type") == 2:
                        v = media.get("video_versions", [])
                        if v:
                            return {"url": v[0]["url"]}
        
        return {"error": "No video found in this post"}
    except Exception as e:
        return {"error": f"Parse error: {str(e)}"}

# --- এপিআই রুট অংশ ---

@app.route('/download', methods=['GET'])
def download_threads():
    # ওয়েবসাইট থেকে পাঠানো ইউআরএল গ্রহণ করা
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({"error": "লিঙ্ক দেওয়া হয়নি!"}), 400

    post_id = extract_post_id(target_url)
    if not post_id:
        return jsonify({"error": "সঠিক থ্রেডস লিঙ্ক দিন!"}), 400

    # থ্রেডস সার্ভারে রিকোয়েস্ট পাঠানো
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
        "X-IG-App-ID": "238260118697367",
    }
    
    api_url = "https://www.threads.net/api/graphql"
    payload = {
        "lsd": "AVqbxe3J_YA",
        "variables": json.dumps({
            "postID": post_id,
            "__relay_internal__pv__BarcelonaIsLoggedInrelayprovider": False
        }),
        "doc_id": "6232751443445612",
    }
    
    try:
        response = requests.post(api_url, headers=headers, data=payload)
        if response.status_code != 200:
            return jsonify({"error": "থ্রেডস সার্ভার থেকে রেসপন্স পাওয়া যায়নি"}), 500
            
        result = parse_video_data(response.json())
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": "সার্ভারে সমস্যা হয়েছে, আবার চেষ্টা করুন"}), 500

if __name__ == "__main__":
    # Render-এর জন্য হোস্ট এবং পোর্ট সেটআপ
    app.run(host='0.0.0.0', port=5000)
