#Requires -Version 5.1
<#
.SYNOPSIS
  Start the Unreal MCP → WebSocket telemetry bridge on Windows.

.DESCRIPTION
  Connects to an Unreal MCP Server over TCP JSON-RPC (127.0.0.1:32123 by default)
  and forwards succinct overlay telemetry to the API Gateway WebSocket.

.PARAMETER Wss
  API Gateway WebSocket WSS URL (e.g., wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod)

.PARAMETER Host
  Unreal MCP TCP host (default: 127.0.0.1)

.PARAMETER Port
  Unreal MCP TCP port (default: 32123)

.PARAMETER Verbose
  Enable verbose logging from the bridge.

.EXAMPLE
  .\start-bridge.ps1 -Wss "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod" -Host "127.0.0.1" -Port 32123 -Verbose
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Wss,

  [string]$Host = "127.0.0.1",

  [int]$Port = 32123,

  [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Validate Node.js availability
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  Write-Error "Node.js is not installed or not on PATH. Install Node.js 18+ and retry."
  exit 1
}

# Resolve project paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$indexJs   = Join-Path $scriptDir "index.js"

if (-not (Test-Path $indexJs)) {
  Write-Error "Cannot find index.js at: $indexJs. Ensure you are running this from the mcp-bridge directory."
  exit 1
}

# Ensure dependencies are installed
$nodeModules = Join-Path $scriptDir "node_modules"
if (-not (Test-Path $nodeModules)) {
  Write-Host "Installing npm dependencies in $scriptDir ..."
  Push-Location $scriptDir
  try {
    npm install --no-fund --loglevel=error
  } finally {
    Pop-Location
  }
}

# Build CLI args for the bridge
$cli = @("`"$indexJs`"", "--wss", $Wss, "--mcp-host", $Host, "--mcp-port", $Port)
if ($Verbose.IsPresent) { $cli += "--verbose" }

Write-Host "Starting MCP bridge:"
Write-Host "  MCP (TCP): $Host`:$Port"
Write-Host "  Telemetry WSS: $Wss"
Write-Host ""

# Execute the bridge
& node @cli