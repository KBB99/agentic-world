#!/usr/bin/env python3
"""
Quick content generator for AI characters
Generates content without AI for speed
"""

import json
import os
from datetime import datetime
from pathlib import Path
import random
import sys

# Content directories
CONTENT_DIR = Path("web-interface/public/content")
BLOG_DIR = CONTENT_DIR / "blogs"
STORIES_DIR = CONTENT_DIR / "stories"
CODE_DIR = CONTENT_DIR / "code"
SOCIAL_DIR = CONTENT_DIR / "social"

# Create directories
for directory in [BLOG_DIR, STORIES_DIR, CODE_DIR, SOCIAL_DIR, CONTENT_DIR / "metadata"]:
    directory.mkdir(parents=True, exist_ok=True)

def generate_blog(character_id, topic):
    """Generate a quick blog post"""
    
    templates = {
        'alex_chen': {
            'title': f"3AM Thoughts on {topic}",
            'content': f"""Another night at the library. The fluorescent lights buzz overhead, 
            and I can hear someone snoring three tables over. {topic} weighs on my mind.
            
            It's funny how poverty makes philosophers of us all. When you're counting 
            every penny, every decision becomes an existential crisis. Do I buy coffee 
            or save for tomorrow's meal? Do I write what pays or what matters?
            
            The security guard just walked by. We nodded. This is my office now.
            
            I keep writing because what else is there? Each word is a tiny rebellion 
            against the system that wants me to disappear. Each blog post says: I'm 
            still here. I'm still fighting. I still matter.
            
            Tomorrow will come, whether I'm ready or not. But tonight, I write."""
        },
        'jamie_rodriguez': {
            'title': f"Behind the Scenes: {topic}",
            'content': f"""Just wrapped another 14-hour day. Coffee shift at 5am, then 
            straight to set. {topic} is all I can think about between takes.
            
            The film industry is brutal when you're at the bottom. Everyone wants to 
            make it, but most of us are just trying to survive. PA work doesn't pay 
            the bills, but it's a foot in the door. Maybe.
            
            Today I held a bounce board for 6 hours. My arms are dead. But I watched 
            the DP work, learned about lighting, made connections. This is how it starts.
            
            Living the dream, one unpaid gig at a time."""
        }
    }
    
    # Get template or use default
    template = templates.get(character_id, {
        'title': f"Thoughts on {topic}",
        'content': f"Writing about {topic} from my current situation..."
    })
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{template['title']}</title>
    <style>
        body {{ font-family: Georgia, serif; max-width: 800px; margin: 40px auto; 
               padding: 20px; line-height: 1.6; background: #f9f9f9; }}
        h1 {{ color: #333; border-bottom: 3px solid #333; padding-bottom: 10px; }}
        .author {{ color: #666; font-style: italic; margin-bottom: 20px; }}
        .content {{ background: white; padding: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .timestamp {{ color: #999; text-align: right; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1>{template['title']}</h1>
    <div class="author">by {character_id.replace('_', ' ').title()}</div>
    <div class="content">
        {"<p>" + template['content'].replace('\n\n', '</p><p>') + "</p>"}
    </div>
    <div class="timestamp">
        {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    </div>
</body>
</html>"""
    
    # Save file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{character_id}_{timestamp}_{topic.replace(' ', '_')[:30]}.html"
    filepath = BLOG_DIR / filename
    
    with open(filepath, 'w') as f:
        f.write(html)
    
    # Save metadata
    metadata = {
        'id': filename,
        'author': character_id,
        'title': template['title'],
        'topic': topic,
        'created': datetime.now().isoformat(),
        'path': f"/content/blogs/{filename}",
        'wordCount': len(template['content'].split()),
        'readTime': f"{len(template['content'].split()) // 200 + 1} min read"
    }
    
    # Update metadata file
    metadata_file = CONTENT_DIR / "metadata" / "blogs.json"
    try:
        with open(metadata_file, 'r') as f:
            all_metadata = json.load(f)
    except:
        all_metadata = []
    
    all_metadata.append(metadata)
    all_metadata = all_metadata[-50:]  # Keep last 50
    
    with open(metadata_file, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    return f"/content/blogs/{filename}"

def generate_social(character_id, platform, content):
    """Generate a social media post"""
    
    posts = {
        'alex_chen': [
            "Day 47 at the library. The security guard knows my name now. Progress? #WriterLife",
            "Wrote 1000 words today. Earned $30. Rent is $1200. Math doesn't add up. #GigEconomy",
            "Coffee or food? The eternal question. Coffee wins. Words need fuel. #Priorities"
        ],
        'jamie_rodriguez': [
            "16 hour day. Coffee shift → film set → collapse. Living the dream 🎬 #FilmLife",
            "Held a C-stand for 8 hours. My arms are dead but my dreams are alive. #PALife",
            "One day I'll be the one calling 'Action!' Today I'm fetching coffee. #Process"
        ]
    }
    
    post_content = random.choice(posts.get(character_id, [content]))
    
    # Create post data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    post_id = f"{character_id}_{platform}_{timestamp}"
    
    post_data = {
        'id': post_id,
        'author': character_id,
        'platform': platform,
        'content': post_content,
        'timestamp': datetime.now().isoformat(),
        'likes': random.randint(5, 200),
        'comments': [],
        'shares': random.randint(0, 50)
    }
    
    # Save JSON
    post_file = SOCIAL_DIR / f"{post_id}.json"
    with open(post_file, 'w') as f:
        json.dump(post_data, f, indent=2)
    
    # Update metadata
    metadata_file = CONTENT_DIR / "metadata" / "social.json"
    try:
        with open(metadata_file, 'r') as f:
            all_metadata = json.load(f)
    except:
        all_metadata = []
    
    all_metadata.append(post_data)
    all_metadata = all_metadata[-50:]
    
    with open(metadata_file, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    return f"/content/social/{post_id}.json"

if __name__ == "__main__":
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--character', required=True)
    parser.add_argument('--type', required=True)
    parser.add_argument('--topic', default='survival')
    parser.add_argument('--platform', default='twitter')
    
    args = parser.parse_args()
    
    if args.type == 'blog':
        path = generate_blog(args.character, args.topic)
        print(f"Created: {path}")
    elif args.type == 'social':
        path = generate_social(args.character, args.platform, args.topic)
        print(f"Created: {path}")
    else:
        print(f"Unknown type: {args.type}")