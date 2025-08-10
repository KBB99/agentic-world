# Windows Setup Guide for MCP Server Bridge

This guide provides step-by-step instructions for setting up and running the MCP Server bridge on a Windows machine.

## Prerequisites

### 1. Install Git for Windows
- Download from: https://git-scm.com/download/win
- During installation, select "Git from the command line and also from 3rd-party software"
- Choose "Use Windows' default console window"

### 2. Install Node.js
- Download LTS version from: https://nodejs.org/
- Version 18 or higher required
- Verify installation:
  ```cmd
  node --version
  npm --version
  ```

### 3. Install Python (for AI agent scripts)
- Download from: https://www.python.org/downloads/windows/
- Version 3.8 or higher
- **IMPORTANT**: Check "Add Python to PATH" during installation
- Verify installation:
  ```cmd
  python --version
  pip --version
  ```

### 4. Install AWS CLI
- Download MSI installer from: https://aws.amazon.com/cli/
- Run the installer and follow prompts
- Configure AWS credentials:
  ```cmd
  aws configure
  ```
  Enter your AWS Access Key ID, Secret Access Key, and region (us-east-1)

## Clone the Repository

1. Open Command Prompt or PowerShell
2. Navigate to your desired directory:
   ```cmd
   cd C:\Users\YourUsername\Documents
   ```
3. Clone the repository:
   ```cmd
   git clone https://github.com/kentonblacutt/agentic-world.git
   cd agentic-world
   ```

## Install Dependencies

### Node.js Dependencies
```cmd
npm install
```

### Python Dependencies
```cmd
pip install boto3 decimal
```

### MCP SDK Installation
```cmd
npm install @modelcontextprotocol/sdk
```

## Configure MCP Server Bridge

### 1. Get WebSocket Endpoint
First, check if AWS infrastructure is deployed:
```cmd
type aws\out\telemetry.outputs.json
```

If the file doesn't exist, deploy the infrastructure:
```cmd
set REGION=us-east-1
set PROJECT=agentic-demo
set BUCKET=your-unique-bucket-name
bash aws\scripts\deploy-all.sh
```

### 2. Start MCP Bridge (Basic)
```cmd
node mcp-bridge\index.js --wss wss://your-api-gateway.execute-api.region.amazonaws.com/prod
```

### 3. Start AI-Enhanced MCP Bridge
For AI agent integration:
```cmd
node mcp-bridge\index-ai.js --wss wss://your-api-gateway.execute-api.region.amazonaws.com/prod --agent-id npc_001
```

## Running the MCP Server Bridge

### Basic MCP Bridge (Telemetry Only)

1. Open Command Prompt
2. Navigate to project directory:
   ```cmd
   cd C:\path\to\agentic-world
   ```
3. Start the bridge:
   ```cmd
   node mcp-bridge\index.js --wss wss://your-websocket-url/prod
   ```

The bridge will:
- Listen on TCP port 32123 for Unreal Engine connections
- Forward telemetry to AWS WebSocket API Gateway
- Auto-reconnect on connection loss

### AI-Enhanced MCP Bridge

For full AI agent functionality:

1. Ensure AWS Bedrock is configured in your region
2. Start the enhanced bridge:
   ```cmd
   node mcp-bridge\index-ai.js ^
     --wss wss://your-websocket-url/prod ^
     --agent-id alex_chen
   ```

### Real MCP Server Connections

To connect characters to real MCP servers:

1. Install required MCP servers:
   ```cmd
   npm install -g @modelcontextprotocol/server-filesystem
   npm install -g @modelcontextprotocol/server-github
   ```

2. Run character with MCP access:
   ```cmd
   python real-mcp-turn.py
   ```

## Windows-Specific Considerations

### Path Separators
Windows uses backslashes (`\`) instead of forward slashes (`/`):
- Linux/Mac: `/Users/name/project`
- Windows: `C:\Users\name\project`

### Line Endings
Git may convert line endings. Configure Git for Windows:
```cmd
git config --global core.autocrlf true
```

### Firewall Configuration
Windows Firewall may block connections:
1. Open Windows Defender Firewall
2. Click "Allow an app or feature"
3. Add Node.js to allowed applications
4. Ensure port 32123 is open for TCP connections

### PowerShell Execution Policy
If scripts won't run in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Environment Variables
Set persistent environment variables:
```cmd
setx AWS_REGION us-east-1
setx PROJECT agentic-demo
```

## Testing the Setup

### 1. Test MCP Bridge Connection
```cmd
node test-mcp-connection.js
```

### 2. Test WebSocket Connection
```cmd
python aws\scripts\post-telemetry.py ^
  --ws wss://your-websocket-url/prod ^
  --table your-table-name ^
  --goal "Test from Windows" ^
  --action "Testing setup"
```

### 3. Test Character Simulation
```cmd
python run-narrative-turns.py
```

## Troubleshooting

### Node.js Issues
- **"node is not recognized"**: Add Node.js to PATH
  - Control Panel → System → Advanced → Environment Variables
  - Add `C:\Program Files\nodejs\` to PATH

### Python Issues
- **"python is not recognized"**: Use `python3` or `py` instead
- **Module not found**: Install with `pip install module-name`

### AWS CLI Issues
- **"aws is not recognized"**: Reinstall AWS CLI and restart Command Prompt
- **Credentials error**: Run `aws configure` again

### MCP Connection Issues
- **Port 32123 in use**: Find and kill the process:
  ```cmd
  netstat -ano | findstr :32123
  taskkill /PID <process-id> /F
  ```
- **WebSocket connection failed**: Check firewall and AWS credentials

### Character File Issues
- **Permission denied**: Run Command Prompt as Administrator
- **Path not found**: Create directories manually:
  ```cmd
  mkdir character_files\alex_chen
  ```

## Running as a Service (Optional)

To run the MCP bridge continuously:

1. Install PM2 globally:
   ```cmd
   npm install -g pm2
   npm install -g pm2-windows-startup
   ```

2. Start the bridge with PM2:
   ```cmd
   pm2 start mcp-bridge\index-ai.js -- --wss wss://your-url/prod --agent-id alex_chen
   pm2 save
   ```

3. Configure auto-start:
   ```cmd
   pm2 startup
   pm2 save
   ```

## Cost Management

Monitor AWS costs:
```cmd
python cost-status.py
```

Stop expensive services when not in use:
```cmd
bash aws\scripts\stop-medialive-channel.sh
python pause-ai.py
```

## Next Steps

1. Configure OBS Studio for streaming to MediaLive
2. Set up Unreal Engine with MCP server connection
3. Deploy AI agents with different economic tiers
4. Monitor telemetry at CloudFront viewer URL

## Support

- Check logs: `type mcp-bridge.log`
- View AWS CloudWatch logs for Lambda functions
- Test individual components before full integration
- Use verbose mode for debugging: `node mcp-bridge\index.js --verbose`

## Security Notes

- Never commit AWS credentials to Git
- Use AWS IAM roles when possible
- Keep API keys in environment variables, not code
- Regularly rotate credentials
- Monitor AWS billing alerts

---

For issues specific to Windows, check:
- Windows Event Viewer for system errors
- `%APPDATA%\npm` for global npm packages
- `%USERPROFILE%\.aws` for AWS configuration