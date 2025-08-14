#!/usr/bin/env python3
"""
Content Generation System
Makes AI characters actually create viewable content (blogs, stories, code, art)
"""

import json
import boto3
import os
from datetime import datetime
from pathlib import Path
import random

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Content directories
CONTENT_DIR = Path("web-interface/public/content")
BLOG_DIR = CONTENT_DIR / "blogs"
STORIES_DIR = CONTENT_DIR / "stories"
CODE_DIR = CONTENT_DIR / "code"
SOCIAL_DIR = CONTENT_DIR / "social"
PORTFOLIO_DIR = CONTENT_DIR / "portfolios"

# Create directories if they don't exist
for directory in [BLOG_DIR, STORIES_DIR, CODE_DIR, SOCIAL_DIR, PORTFOLIO_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class ContentGenerator:
    def __init__(self, character_id, character_data):
        self.character_id = character_id
        self.character = character_data
        self.portfolio_dir = PORTFOLIO_DIR / character_id
        self.portfolio_dir.mkdir(exist_ok=True)
        
    def generate_blog_post(self, topic, client_requirements=None):
        """Generate an actual blog post HTML file"""
        
        prompt = f"""You are {self.character['personality']}.
Background: {self.character['background']}
Current situation: {self.character['current_situation']}

Write a 1000-word blog post about: {topic}

Requirements: {client_requirements or 'Engaging, well-researched, SEO-friendly'}

Write in your authentic voice based on your background and current life situation.
Format the response as JSON with 'title', 'subtitle', and 'content' fields."""

        try:
            # Generate content with AI
            response = bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2000,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content_text = response_body['content'][0]['text']
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
            if json_match:
                post_data = json.loads(json_match.group())
            else:
                # Fallback content
                post_data = {
                    'title': f'Thoughts on {topic}',
                    'subtitle': f'By {self.character_id}',
                    'content': content_text
                }
                
        except Exception as e:
            print(f"Bedrock error: {e}, using fallback")
            # Fallback blog post
            post_data = self.generate_fallback_blog(topic)
        
        # Create HTML file
        html_content = self.create_blog_html(post_data)
        
        # Save the blog post
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.character_id}_{timestamp}_{topic.replace(' ', '_')[:30]}.html"
        filepath = BLOG_DIR / filename
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        # Also save to portfolio
        portfolio_path = self.portfolio_dir / f"blog_{timestamp}.html"
        with open(portfolio_path, 'w') as f:
            f.write(html_content)
        
        # Create metadata
        metadata = {
            'id': filename,
            'author': self.character_id,
            'title': post_data['title'],
            'topic': topic,
            'created': datetime.now().isoformat(),
            'path': f"/content/blogs/{filename}",
            'wordCount': len(post_data['content'].split()),
            'readTime': f"{len(post_data['content'].split()) // 200} min read"
        }
        
        # Save metadata
        self.save_metadata('blogs', metadata)
        
        return metadata
    
    def create_blog_html(self, post_data):
        """Create a styled HTML blog post"""
        
        # Simple paragraph conversion (replace markdown module)
        content_html = '<p>' + post_data['content'].replace('\n\n', '</p><p>').replace('\n', '<br>') + '</p>'
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post_data['title']}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.6;
            color: #333;
            background: #f9f9f9;
        }}
        h1 {{
            color: #222;
            font-size: 2.5em;
            margin-bottom: 10px;
            border-bottom: 3px solid #333;
            padding-bottom: 10px;
        }}
        .subtitle {{
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .author-info {{
            background: #fff;
            padding: 15px;
            border-left: 4px solid #0066cc;
            margin: 30px 0;
        }}
        .author-name {{
            font-weight: bold;
            color: #0066cc;
        }}
        .content {{
            background: white;
            padding: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .content p:first-letter {{
            font-size: 3em;
            float: left;
            line-height: 1;
            margin-right: 5px;
            font-weight: bold;
            color: #0066cc;
        }}
        .timestamp {{
            color: #999;
            font-size: 0.9em;
            margin-top: 30px;
            text-align: right;
        }}
    </style>
</head>
<body>
    <article>
        <h1>{post_data['title']}</h1>
        <div class="subtitle">{post_data.get('subtitle', '')}</div>
        
        <div class="author-info">
            <div class="author-name">{self.character_id.replace('_', ' ').title()}</div>
            <div>{self.character.get('current_situation', 'Freelance Writer')}</div>
        </div>
        
        <div class="content">
            {content_html}
        </div>
        
        <div class="timestamp">
            Written on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </article>
</body>
</html>"""
        
        return html
    
    def generate_story(self, prompt, genre="literary fiction"):
        """Generate a short story"""
        
        story_prompt = f"""You are {self.character['personality']}.
Write a 2000-word short story in the {genre} genre.
Prompt: {prompt}
Draw from your experiences: {self.character['background']}

Format as JSON with 'title', 'story', and 'excerpt' fields."""

        try:
            response = bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 3000,
                    'messages': [{
                        'role': 'user',
                        'content': story_prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            story_text = response_body['content'][0]['text']
            
            # Parse JSON
            import re
            json_match = re.search(r'\{.*\}', story_text, re.DOTALL)
            if json_match:
                story_data = json.loads(json_match.group())
            else:
                story_data = {
                    'title': 'Untitled Story',
                    'story': story_text,
                    'excerpt': story_text[:200] + '...'
                }
                
        except Exception as e:
            print(f"Error generating story: {e}")
            story_data = {
                'title': 'Digital Ghosts',
                'story': self.generate_fallback_story(),
                'excerpt': 'A story about connection in the digital age...'
            }
        
        # Create HTML
        html = self.create_story_html(story_data)
        
        # Save story
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.character_id}_story_{timestamp}.html"
        filepath = STORIES_DIR / filename
        
        with open(filepath, 'w') as f:
            f.write(html)
        
        metadata = {
            'id': filename,
            'author': self.character_id,
            'title': story_data['title'],
            'genre': genre,
            'excerpt': story_data['excerpt'],
            'created': datetime.now().isoformat(),
            'path': f"/content/stories/{filename}",
            'wordCount': len(story_data['story'].split())
        }
        
        self.save_metadata('stories', metadata)
        
        return metadata
    
    def create_story_html(self, story_data):
        """Create styled story HTML"""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{story_data['title']}</title>
    <style>
        body {{
            font-family: 'Garamond', 'Georgia', serif;
            max-width: 700px;
            margin: 0 auto;
            padding: 60px 20px;
            background: #fafafa;
            color: #333;
            line-height: 1.8;
        }}
        h1 {{
            font-size: 3em;
            text-align: center;
            margin-bottom: 10px;
            font-weight: normal;
            letter-spacing: 2px;
        }}
        .author {{
            text-align: center;
            color: #666;
            margin-bottom: 50px;
            font-style: italic;
        }}
        .story {{
            text-align: justify;
            font-size: 1.1em;
        }}
        .story p {{
            margin-bottom: 20px;
            text-indent: 40px;
        }}
        .story p:first-of-type {{
            text-indent: 0;
        }}
        .story p:first-of-type:first-letter {{
            font-size: 4em;
            float: left;
            line-height: 0.8;
            margin: 10px 5px 0 0;
            font-family: 'Georgia', serif;
        }}
    </style>
</head>
<body>
    <h1>{story_data['title']}</h1>
    <div class="author">by {self.character_id.replace('_', ' ').title()}</div>
    <div class="story">
        {''.join(f'<p>{p}</p>' for p in story_data['story'].split('\\n\\n') if p)}
    </div>
</body>
</html>"""
        
        return html
    
    def generate_code_project(self, project_type="web app", description=""):
        """Generate actual code files"""
        
        if self.character_id == "alex_chen":
            # Alex writes more literary/artistic code
            code_style = "clean, poetic variable names, lots of comments"
        elif self.character_id == "ashley_kim":
            # Ashley writes enterprise-style code
            code_style = "professional, well-documented, design patterns"
        else:
            code_style = "functional"
        
        # Generate a simple web app
        if project_type == "web app":
            # Create project directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            project_name = f"{self.character_id}_project_{timestamp}"
            project_dir = CODE_DIR / project_name
            project_dir.mkdir(exist_ok=True)
            
            # Generate HTML
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{description or 'My Project'}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Created by {self.character_id.replace('_', ' ').title()}</h1>
    <p>{description}</p>
    <div id="app"></div>
    <script src="app.js"></script>
</body>
</html>"""
            
            # Generate CSS
            css = """body {
    font-family: 'Arial', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 40px;
}
#app {
    background: rgba(255,255,255,0.1);
    padding: 20px;
    border-radius: 10px;
}"""
            
            # Generate JavaScript
            js = f"""// Project by {self.character_id}
// {self.character.get('current_situation', '')}

class App {{
    constructor() {{
        this.messages = [];
        this.init();
    }}
    
    init() {{
        console.log('App initialized by {self.character_id}');
        this.render();
    }}
    
    render() {{
        const app = document.getElementById('app');
        app.innerHTML = `
            <h2>Interactive Demo</h2>
            <button onclick="alert('Created by {self.character_id}!')">Click Me</button>
        `;
    }}
}}

// Initialize app
const app = new App();"""
            
            # Save files
            with open(project_dir / "index.html", 'w') as f:
                f.write(html)
            with open(project_dir / "style.css", 'w') as f:
                f.write(css)
            with open(project_dir / "app.js", 'w') as f:
                f.write(js)
            
            metadata = {
                'id': project_name,
                'author': self.character_id,
                'type': project_type,
                'description': description,
                'created': datetime.now().isoformat(),
                'path': f"/content/code/{project_name}/index.html",
                'files': ['index.html', 'style.css', 'app.js']
            }
            
            self.save_metadata('code', metadata)
            
            return metadata
    
    def create_social_post(self, platform, content):
        """Create a social media post"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        post_id = f"{self.character_id}_{platform}_{timestamp}"
        
        post_data = {
            'id': post_id,
            'author': self.character_id,
            'platform': platform,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'likes': random.randint(0, 100),
            'comments': [],
            'shares': random.randint(0, 20)
        }
        
        # Save as JSON
        post_file = SOCIAL_DIR / f"{post_id}.json"
        with open(post_file, 'w') as f:
            json.dump(post_data, f, indent=2)
        
        # Also create viewable HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>@{self.character_id} on {platform}</title>
    <style>
        body {{ font-family: Arial; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .post {{ border: 1px solid #ddd; padding: 20px; border-radius: 10px; }}
        .author {{ font-weight: bold; color: #0066cc; }}
        .content {{ margin: 20px 0; font-size: 1.2em; }}
        .stats {{ color: #666; }}
    </style>
</head>
<body>
    <div class="post">
        <div class="author">@{self.character_id}</div>
        <div class="content">{content}</div>
        <div class="stats">❤️ {post_data['likes']} | 💬 {len(post_data['comments'])} | 🔄 {post_data['shares']}</div>
    </div>
</body>
</html>"""
        
        html_file = SOCIAL_DIR / f"{post_id}.html"
        with open(html_file, 'w') as f:
            f.write(html)
        
        return post_data
    
    def save_metadata(self, content_type, metadata):
        """Save metadata for content discovery"""
        
        metadata_dir = CONTENT_DIR / "metadata"
        metadata_dir.mkdir(exist_ok=True)
        
        metadata_file = metadata_dir / f"{content_type}.json"
        
        # Load existing metadata
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                all_metadata = json.load(f)
        else:
            all_metadata = []
        
        # Add new metadata
        all_metadata.append(metadata)
        
        # Keep only last 100 items
        all_metadata = all_metadata[-100:]
        
        # Save
        with open(metadata_file, 'w') as f:
            json.dump(all_metadata, f, indent=2)
    
    def generate_fallback_blog(self, topic):
        """Fallback blog content when AI fails"""
        
        if self.character_id == "alex_chen":
            return {
                'title': f'Late Night Thoughts on {topic}',
                'subtitle': 'Written at 3am from the library',
                'content': f"""It's 3am and I'm still at the library. The security guard has stopped bothering me - 
                we have an understanding now. I nod, he nods, we both pretend I'm not essentially living here.

                {topic} has been on my mind lately. Maybe it's the exhaustion talking, but everything feels 
                connected when you haven't slept in 48 hours. The fluorescent lights buzz overhead, and I 
                can hear someone snoring softly three tables over. Another writer, probably. Or another person 
                with nowhere else to go.

                I should be working on my novel, but freelance deadlines don't care about artistic ambitions. 
                So here I am, churning out content about {topic}, trying to hit that word count that translates 
                to just enough dollars to buy tomorrow's coffee. The coffee that keeps me awake to write more 
                content to buy more coffee.

                But there's something beautiful in this cycle, this midnight solidarity of the desperate and 
                driven. We're all here, creating things that might matter, or might just pay the bills. And 
                maybe that's enough. Maybe the act of creation itself, even at 3am in a public library, even 
                for $0.03 a word, is its own form of resistance.

                The sunrise is coming soon. I can feel it even though there are no windows here. Another day, 
                another chance, another blank page. And yes, another deadline. But I'm still here, still 
                writing, still fighting.

                That has to count for something."""
            }
        else:
            return {
                'title': f'Thoughts on {topic}',
                'subtitle': f'By {self.character_id}',
                'content': f'This is a blog post about {topic}...'
            }
    
    def generate_fallback_story(self):
        """Fallback story content"""
        return """The coffee shop WiFi cut out again. Sarah stared at the "No Internet Connection" message, 
        her half-finished article mocking her from the screen. $47 in her account. Rent due in three days.
        
        She refreshed the connection. Nothing. The barista gave her that look - the one that said she'd 
        been here too long on one small coffee. But where else could she go? The library closed at 6.
        
        Her phone buzzed. A notification from the freelance platform: "Your proposal was not selected."
        The thirty-seventh rejection this week. She closed her laptop and put her head in her hands.
        
        "Rough day?" 
        
        Sarah looked up. An older woman at the next table, expensive laptop, designer bag. Everything 
        Sarah used to have, before the layoffs, before the industry collapsed, before...
        
        "Something like that," Sarah managed.
        
        The woman nodded, turned back to her screen. But a moment later, she spoke again: "The WiFi 
        password for the business center upstairs is 'prosperity2024'. They never change it."
        
        Sarah looked up, surprised.
        
        The woman was already packing up to leave. "I used to sit where you're sitting," she said 
        quietly. "Took me three years to get to this side of the table. The WiFi upstairs is faster. 
        And they don't kick you out."
        
        Then she was gone, leaving only the faint scent of expensive perfume and something else - hope, 
        maybe. Or just the possibility that tomorrow might be different.
        
        Sarah packed up her things and headed for the stairs."""


def demonstrate_content_generation():
    """Demo: Generate actual content from characters"""
    
    print("="*80)
    print("CONTENT GENERATION DEMONSTRATION")
    print("="*80)
    
    # Load Alex Chen
    alex_data = {
        'personality': 'Exhausted writer, talented but desperate',
        'background': '28yo writer, MFA graduate, couchsurfing',
        'current_situation': 'Writing at library for wifi, skipping meals',
        'skills': ['creative writing', 'blog posts', 'SEO content'],
        'money': 53.09
    }
    
    alex = ContentGenerator('alex_chen', alex_data)
    
    # Generate blog post
    print("\n📝 Alex writes a blog post...")
    blog = alex.generate_blog_post(
        topic="digital nomad lifestyle",
        client_requirements="SEO-optimized, 1000 words, include personal experience"
    )
    print(f"   Created: {blog['path']}")
    print(f"   Word count: {blog['wordCount']}")
    
    # Generate story
    print("\n📚 Alex writes a short story...")
    story = alex.generate_story(
        prompt="Someone discovers that their digital assistant has been lying to them",
        genre="literary fiction"
    )
    print(f"   Created: {story['path']}")
    print(f"   Title: {story['title']}")
    
    # Generate code project
    print("\n💻 Alex creates a web project...")
    project = alex.generate_code_project(
        project_type="web app",
        description="A minimalist writing tracker"
    )
    print(f"   Created: {project['path']}")
    print(f"   Files: {', '.join(project['files'])}")
    
    # Create social post
    print("\n📱 Alex posts on social media...")
    post = alex.create_social_post(
        platform="twitter",
        content="Day 47 of writing from the library. The security guard and I are basically best friends now. He doesn't even check my bag anymore. Living the dream. #WriterLife #Exhausted"
    )
    print(f"   Posted: {post['content']}")
    print(f"   Engagement: {post['likes']} likes")
    
    print("\n" + "="*80)
    print("All content saved to: web-interface/public/content/")
    print("View in browser at: http://localhost:3001/content/")
    print("="*80)


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate content for AI characters')
    parser.add_argument('--character', type=str, help='Character ID')
    parser.add_argument('--type', type=str, help='Content type (blog, story, code, social)')
    parser.add_argument('--topic', type=str, default='general', help='Topic or prompt')
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    
    args = parser.parse_args()
    
    if args.demo or (not args.character and not args.type):
        demonstrate_content_generation()
    else:
        # Generate specific content
        character_data = {
            'alex_chen': {
                'personality': 'Exhausted writer, talented but desperate',
                'background': '28yo writer, MFA graduate, couchsurfing',
                'current_situation': 'Writing at library for wifi, skipping meals',
                'skills': ['creative writing', 'blog posts', 'SEO content'],
                'money': 53.09
            },
            'jamie_rodriguez': {
                'personality': 'Film school dropout, PA on indie films, optimistic but wearing down',
                'background': '26yo, part-time barista, sleeps in shared studio',
                'current_situation': '5am coffee shifts, evening film gigs for experience',
                'skills': ['video editing', 'social media', 'film production'],
                'money': 43
            },
            'ashley_kim': {
                'personality': 'Tech PM, organized, stressed but maintaining',
                'background': '29yo tech worker, $47K salary, student loans',
                'current_situation': 'Managing three projects, working 60-hour weeks',
                'skills': ['project management', 'technical writing', 'coding'],
                'money': 47000
            },
            'victoria_sterling': {
                'personality': 'CEO, confident, disconnected from reality',
                'background': '42yo executive, inherited wealth, MBA from Harvard',
                'current_situation': 'Running tech startup, multiple homes',
                'skills': ['business strategy', 'leadership', 'public speaking'],
                'money': 25000000
            }
        }
        
        if args.character in character_data:
            char_data = character_data[args.character]
            generator = ContentGenerator(args.character, char_data)
            
            if args.type == 'blog':
                result = generator.generate_blog_post(args.topic)
                print(f"Created: {result['path']}")
            elif args.type == 'story':
                result = generator.generate_story(args.topic)
                print(f"Created: {result['path']}")
            elif args.type == 'code':
                result = generator.generate_code_project('web app', args.topic)
                print(f"Created: {result['path']}")
            elif args.type == 'social':
                result = generator.create_social_post('twitter', args.topic)
                print(f"Created: /content/social/{result['id']}.html")
            else:
                print(f"Unknown content type: {args.type}")
        else:
            print(f"Unknown character: {args.character}")