#!/usr/bin/env python3
"""
Publish AI character content to the EXISTING S3 bucket
"""

import boto3
import json
import os
from datetime import datetime
from pathlib import Path

# Use the EXISTING bucket from stack-outputs.json
with open('aws/out/stack-outputs.json', 'r') as f:
    outputs = json.load(f)

S3_BUCKET = outputs['viewerBucketName']
CLOUDFRONT_DOMAIN = outputs['cloudfrontDomainName']
REGION = outputs['region']

s3_client = boto3.client('s3', region_name=REGION)

def publish_character_content(character_id, content_type, local_file):
    """Publish character content to existing S3 bucket"""
    
    # Read the local file
    with open(local_file, 'r') as f:
        content = f.read()
    
    # Create S3 key under /content/ to avoid conflicts with viewer
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = Path(local_file).name
    s3_key = f"content/{character_id}/{content_type}/{timestamp}_{filename}"
    
    # Upload to S3
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=content,
        ContentType='text/html',
        CacheControl='max-age=3600'
    )
    
    # Return CloudFront URL
    url = f"https://{CLOUDFRONT_DOMAIN}/{s3_key}"
    
    print(f"✅ Published to CloudFront: {url}")
    
    # Also update a content index
    update_content_index(character_id, content_type, {
        'url': url,
        's3_key': s3_key,
        'title': filename,
        'created': datetime.now().isoformat()
    })
    
    return url

def update_content_index(character_id, content_type, metadata):
    """Update content index in S3"""
    
    index_key = f"content/{character_id}/index.json"
    
    # Try to get existing index
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=index_key)
        index = json.loads(response['Body'].read())
    except:
        index = {
            'character_id': character_id,
            'content': {}
        }
    
    # Add new content
    if content_type not in index['content']:
        index['content'][content_type] = []
    
    index['content'][content_type].append(metadata)
    
    # Keep last 50 items
    index['content'][content_type] = index['content'][content_type][-50:]
    
    # Upload updated index
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=index_key,
        Body=json.dumps(index, indent=2),
        ContentType='application/json'
    )
    
    print(f"✅ Updated {character_id}'s content index")
    print(f"   View at: https://{CLOUDFRONT_DOMAIN}/content/{character_id}/index.json")

def create_content_hub():
    """Create a content hub page in the existing S3 bucket"""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Character Content Hub</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        h1 {{ color: #333; }}
        .character-section {{
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .content-item {{
            background: #f5f5f5;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            transition: transform 0.3s;
        }}
        .content-item:hover {{
            transform: translateX(5px);
            background: #e9ecef;
        }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 AI Character Generated Content</h1>
        <p>All content created by AI characters in the simulation</p>
        
        <div class="character-section">
            <h2>Alex Chen - Struggling Writer</h2>
            <div id="alex-content">
                <p>Loading Alex's content...</p>
            </div>
        </div>
        
        <div class="character-section">
            <h2>Jamie Rodriguez - Film PA</h2>
            <div id="jamie-content">
                <p>Loading Jamie's content...</p>
            </div>
        </div>
        
        <p style="text-align: center; margin-top: 40px; color: #666;">
            Content updates automatically as characters create new work
        </p>
    </div>
    
    <script>
        async function loadCharacterContent(characterId, elementId) {{
            try {{
                const response = await fetch(`/content/${{characterId}}/index.json`);
                const data = await response.json();
                
                const element = document.getElementById(elementId);
                let html = '';
                
                // Show blogs
                if (data.content.blogs) {{
                    html += '<h3>📝 Blog Posts</h3>';
                    data.content.blogs.forEach(blog => {{
                        html += `<div class="content-item">
                            <a href="${{blog.url}}">${{blog.title}}</a>
                            <span style="color: #999; font-size: 0.9em;"> - ${{blog.created}}</span>
                        </div>`;
                    }});
                }}
                
                // Show stories
                if (data.content.stories) {{
                    html += '<h3>📚 Stories</h3>';
                    data.content.stories.forEach(story => {{
                        html += `<div class="content-item">
                            <a href="${{story.url}}">${{story.title}}</a>
                        </div>`;
                    }});
                }}
                
                element.innerHTML = html || '<p>No content yet</p>';
            }} catch (e) {{
                document.getElementById(elementId).innerHTML = '<p style="color: #999;">No content published yet</p>';
            }}
        }}
        
        // Load content for each character
        loadCharacterContent('alex_chen', 'alex-content');
        loadCharacterContent('jamie_rodriguez', 'jamie-content');
        
        // Refresh every 30 seconds
        setInterval(() => {{
            loadCharacterContent('alex_chen', 'alex-content');
            loadCharacterContent('jamie_rodriguez', 'jamie-content');
        }}, 30000);
    </script>
</body>
</html>"""
    
    # Upload hub to S3
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key='content/index.html',
        Body=html,
        ContentType='text/html'
    )
    
    url = f"https://{CLOUDFRONT_DOMAIN}/content/index.html"
    print(f"✅ Content Hub created: {url}")
    return url

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--character', help='Character ID')
    parser.add_argument('--type', help='Content type')
    parser.add_argument('--file', help='Local file to upload')
    parser.add_argument('--create-hub', action='store_true', help='Create content hub')
    
    args = parser.parse_args()
    
    if args.create_hub:
        hub_url = create_content_hub()
        print(f"\n🌐 View Content Hub at: {hub_url}")
    elif args.character and args.type and args.file:
        url = publish_character_content(args.character, args.type, args.file)
        print(f"\n📄 View content at: {url}")
    else:
        print("Usage:")
        print("  Create hub: python3 publish-to-existing-s3.py --create-hub")
        print("  Publish: python3 publish-to-existing-s3.py --character alex_chen --type blog --file blog.html")