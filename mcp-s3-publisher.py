#!/usr/bin/env python3
"""
MCP S3 Publisher - Allows AI characters to publish content to S3
"""

import boto3
import json
import os
from datetime import datetime
from pathlib import Path
import mimetypes

# AWS S3 configuration
S3_BUCKET = os.environ.get('CONTENT_BUCKET', 'agentic-character-content')
S3_REGION = os.environ.get('AWS_REGION', 'us-east-1')
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', '')

# Initialize S3 client
s3_client = boto3.client('s3', region_name=S3_REGION)

def ensure_bucket_exists():
    """Create S3 bucket if it doesn't exist"""
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"✅ Bucket {S3_BUCKET} exists")
    except:
        try:
            if S3_REGION == 'us-east-1':
                s3_client.create_bucket(Bucket=S3_BUCKET)
            else:
                s3_client.create_bucket(
                    Bucket=S3_BUCKET,
                    CreateBucketConfiguration={'LocationConstraint': S3_REGION}
                )
            
            # Enable public read for content
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{S3_BUCKET}/*"
                }]
            }
            
            s3_client.put_bucket_policy(
                Bucket=S3_BUCKET,
                Policy=json.dumps(bucket_policy)
            )
            
            # Enable website hosting
            s3_client.put_bucket_website(
                Bucket=S3_BUCKET,
                WebsiteConfiguration={
                    'IndexDocument': {'Suffix': 'index.html'},
                    'ErrorDocument': {'Key': 'error.html'}
                }
            )
            
            print(f"✅ Created bucket {S3_BUCKET} with public read access")
            
        except Exception as e:
            print(f"❌ Could not create bucket: {e}")
            raise

def upload_to_s3(local_path, s3_key, content_type=None):
    """Upload a file to S3 and return the public URL"""
    
    # Determine content type
    if not content_type:
        content_type, _ = mimetypes.guess_type(local_path)
        if not content_type:
            content_type = 'text/html'
    
    # Upload file
    with open(local_path, 'rb') as f:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=f,
            ContentType=content_type,
            CacheControl='max-age=3600',
            Metadata={
                'author': s3_key.split('/')[1] if '/' in s3_key else 'unknown',
                'created': datetime.now().isoformat()
            }
        )
    
    # Return URL
    if CLOUDFRONT_DOMAIN:
        url = f"https://{CLOUDFRONT_DOMAIN}/{s3_key}"
    else:
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
    
    return url

def publish_character_content(character_id, content_type, local_file):
    """Publish character-generated content to S3"""
    
    # Create S3 key structure
    # content/alex_chen/blogs/2024-01-01_blog_title.html
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = Path(local_file).name
    s3_key = f"content/{character_id}/{content_type}/{timestamp}_{filename}"
    
    # Upload to S3
    url = upload_to_s3(local_file, s3_key)
    
    # Update character's content index
    update_character_index(character_id, content_type, {
        'url': url,
        's3_key': s3_key,
        'title': filename,
        'created': datetime.now().isoformat(),
        'local_file': local_file
    })
    
    return url

def update_character_index(character_id, content_type, metadata):
    """Update the character's content index in S3"""
    
    index_key = f"content/{character_id}/index.json"
    
    # Try to get existing index
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=index_key)
        index = json.loads(response['Body'].read())
    except:
        index = {
            'character_id': character_id,
            'content': {
                'blogs': [],
                'stories': [],
                'code': [],
                'social': [],
                'streams': []
            }
        }
    
    # Add new content
    if content_type not in index['content']:
        index['content'][content_type] = []
    
    index['content'][content_type].append(metadata)
    
    # Keep only last 50 items per type
    index['content'][content_type] = index['content'][content_type][-50:]
    
    # Upload updated index
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=index_key,
        Body=json.dumps(index, indent=2),
        ContentType='application/json'
    )
    
    print(f"✅ Updated {character_id}'s content index")

def create_public_content_hub():
    """Create a public content hub HTML page in S3"""
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>AI Character Content Hub</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .character { border: 1px solid #ddd; padding: 20px; margin: 20px 0; }
        .content-item { background: #f5f5f5; padding: 10px; margin: 10px 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>AI Character Generated Content</h1>
    <p>All content generated by AI characters in the simulation</p>
    
    <div id="content-list">
        <p>Loading content...</p>
    </div>
    
    <script>
        // This would dynamically load content from S3
        fetch('/content/index.json')
            .then(r => r.json())
            .then(data => {
                // Display content
            });
    </script>
</body>
</html>"""
    
    # Upload hub page
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key='index.html',
        Body=html,
        ContentType='text/html'
    )
    
    hub_url = f"https://{S3_BUCKET}.s3-website-{S3_REGION}.amazonaws.com/"
    print(f"✅ Content hub available at: {hub_url}")
    return hub_url

class MCPContentPublisher:
    """MCP tool for publishing to S3"""
    
    def __init__(self):
        ensure_bucket_exists()
    
    def publish_blog(self, character_id, local_file):
        """MCP tool: Publish blog to S3"""
        return publish_character_content(character_id, 'blogs', local_file)
    
    def publish_story(self, character_id, local_file):
        """MCP tool: Publish story to S3"""
        return publish_character_content(character_id, 'stories', local_file)
    
    def publish_code(self, character_id, local_file):
        """MCP tool: Publish code project to S3"""
        return publish_character_content(character_id, 'code', local_file)
    
    def publish_social(self, character_id, platform, content):
        """MCP tool: Publish social media post to S3"""
        # Create temporary JSON file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'author': character_id,
                'platform': platform,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }, f)
            temp_file = f.name
        
        url = publish_character_content(character_id, 'social', temp_file)
        os.unlink(temp_file)
        return url
    
    def get_my_content_url(self, character_id):
        """MCP tool: Get URL to character's content"""
        if CLOUDFRONT_DOMAIN:
            return f"https://{CLOUDFRONT_DOMAIN}/content/{character_id}/index.json"
        else:
            return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/content/{character_id}/index.json"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--character', required=True, help='Character ID')
    parser.add_argument('--type', required=True, help='Content type (blog, story, code, social)')
    parser.add_argument('--file', required=True, help='Local file to upload')
    parser.add_argument('--create-hub', action='store_true', help='Create content hub')
    
    args = parser.parse_args()
    
    if args.create_hub:
        hub_url = create_public_content_hub()
        print(f"Content hub: {hub_url}")
    else:
        publisher = MCPContentPublisher()
        
        if args.type == 'blog':
            url = publisher.publish_blog(args.character, args.file)
        elif args.type == 'story':
            url = publisher.publish_story(args.character, args.file)
        elif args.type == 'code':
            url = publisher.publish_code(args.character, args.file)
        else:
            print(f"Unknown type: {args.type}")
            exit(1)
        
        print(f"Published to: {url}")