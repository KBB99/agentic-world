const serverless = require('serverless-http');
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const AWS = require('aws-sdk');
const path = require('path');

// Create Express app
const app = express();

// Configure AWS SDK
AWS.config.update({ region: process.env.AWS_REGION || 'us-east-1' });

// Middleware
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true
}));

// Additional CORS headers for all responses
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static files
app.use('/assets', express.static(path.join(__dirname, 'public/assets')));
app.use('/content', express.static(path.join(__dirname, 'public/content')));

// Import routes from server.js logic
const dynamodb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();

// Helper function to fetch S3 content
async function fetchS3Content() {
    const bucketName = process.env.CONTENT_BUCKET;
    const cloudfrontDomain = process.env.CLOUDFRONT_DOMAIN;
    
    if (!bucketName) {
        return { error: 'S3 bucket not configured' };
    }
    
    try {
        const listParams = {
            Bucket: bucketName,
            Prefix: 'content/'
        };
        
        const objects = await s3.listObjectsV2(listParams).promise();
        
        const characterContent = {};
        
        for (const obj of objects.Contents || []) {
            const key = obj.Key;
            const parts = key.split('/');
            
            if (parts.length >= 4) {
                const characterId = parts[1];
                const contentType = parts[2];
                const filename = parts[parts.length - 1];
                
                if (!characterContent[characterId]) {
                    characterContent[characterId] = { content: {} };
                }
                
                if (!characterContent[characterId].content[contentType]) {
                    characterContent[characterId].content[contentType] = [];
                }
                
                characterContent[characterId].content[contentType].push({
                    s3_key: key,
                    filename: filename,
                    url: `https://${bucketName}.s3.amazonaws.com/${key}`,
                    cloudfrontUrl: cloudfrontDomain ? `https://${cloudfrontDomain}/${key}` : null,
                    created: obj.LastModified,
                    size: obj.Size
                });
            }
        }
        
        return {
            characters: characterContent,
            cloudfrontDomain: cloudfrontDomain,
            bucketName: bucketName
        };
    } catch (error) {
        console.error('Error fetching S3 content:', error);
        return { error: error.message };
    }
}

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/dashboard', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'dashboard.html'));
});

app.get('/content-hub.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'content-hub.html'));
});

app.get('/s3-content-viewer.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 's3-content-viewer.html'));
});

// API Routes
app.get('/agents', async (req, res) => {
    try {
        const params = {
            TableName: process.env.AGENTS_TABLE || 'agentic-demo-agent-contexts'
        };
        console.log('Scanning DynamoDB table:', params.TableName);
        const data = await dynamodb.scan(params).promise();
        console.log('Found items:', data.Items ? data.Items.length : 0);
        res.json(data.Items || []);
    } catch (error) {
        console.error('Error fetching agents:', error);
        // Check if it's a permissions error
        if (error.code === 'AccessDeniedException' || error.statusCode === 403) {
            res.status(500).json({ 
                error: 'Database access error',
                details: error.message,
                table: process.env.AGENTS_TABLE || 'agentic-demo-agent-contexts'
            });
        } else {
            res.status(500).json({ error: error.message });
        }
    }
});

app.get('/world', async (req, res) => {
    try {
        const params = {
            TableName: process.env.WORLD_TABLE || 'agentic-demo-world-state',
            Key: { worldId: 'main' }
        };
        const data = await dynamodb.get(params).promise();
        res.json(data.Item || {});
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/memories/:agentId', async (req, res) => {
    try {
        const params = {
            TableName: process.env.MEMORIES_TABLE || 'agentic-demo-character-memories',
            Key: { characterId: req.params.agentId }
        };
        const data = await dynamodb.get(params).promise();
        res.json(data.Item?.memories || []);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/content-hub', async (req, res) => {
    try {
        // Fetch S3 content
        const s3Content = await fetchS3Content();
        
        // Also include local content metadata
        const fs = require('fs').promises;
        let blogs = [];
        try {
            const blogsData = await fs.readFile(path.join(__dirname, 'public/content/metadata/blogs.json'), 'utf8');
            blogs = JSON.parse(blogsData);
        } catch (e) {
            console.log('No local blogs metadata');
        }
        
        res.json({
            s3Content: s3Content,
            blogs: blogs
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/s3-content/:characterId', async (req, res) => {
    try {
        const bucketName = process.env.CONTENT_BUCKET;
        const cloudfrontDomain = process.env.CLOUDFRONT_DOMAIN;
        const characterId = req.params.characterId;
        
        const listParams = {
            Bucket: bucketName,
            Prefix: `character-content/${characterId}/`
        };
        
        const objects = await s3.listObjectsV2(listParams).promise();
        
        const content = {};
        
        for (const obj of objects.Contents || []) {
            const key = obj.Key;
            const parts = key.split('/');
            
            if (parts.length >= 3) {
                const contentType = parts[2];
                const filename = parts[parts.length - 1];
                
                if (!content[contentType]) {
                    content[contentType] = [];
                }
                
                content[contentType].push({
                    s3_key: key,
                    filename: filename,
                    url: `https://${bucketName}.s3.amazonaws.com/${key}`,
                    cloudfrontUrl: cloudfrontDomain ? `https://${cloudfrontDomain}/${key}` : null,
                    created: obj.LastModified,
                    size: obj.Size
                });
            }
        }
        
        res.json({ content: content });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/run-turn', async (req, res) => {
    try {
        const lambda = new AWS.Lambda();
        
        const params = {
            FunctionName: process.env.SIMULATION_FUNCTION || 'agentic-demo-simulation-runner',
            InvocationType: 'RequestResponse',
            Payload: JSON.stringify(req.body)
        };
        
        const result = await lambda.invoke(params).promise();
        const payload = JSON.parse(result.Payload);
        
        res.json(payload);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Export the serverless handler
module.exports.handler = serverless(app);