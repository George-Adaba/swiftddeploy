# SwiftDeploy

A declarative infrastructure automation tool that generates deployment configs
from a single `manifest.yaml` and manages the full container lifecycle.

## Requirements

- Python 3.8+
- Docker Desktop
- Docker Compose v2

Install Python dependencies:
pip install pyyaml


## Quick Start

# 1. Build the image first
docker build -t swift-deploy-1-node:latest .

# 2. Deploy
python swiftdeploy deploy

# 3. Test it
curl http://localhost:8080/
curl http://localhost:8080/healthz

## manifest.yaml

The manifest is the single source of truth for your deployment:
```
services:
  image: swift-deploy-1-node:latest   # Docker image name
  port: 8000                          # App port (internal only)
  version: "1.0.2"                    # App version
  restart_policy: unless-stopped
  health_check:
    path: /healthz
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 5s

nginx:
  image: nginx:alpine
  port: 8080                          # Public port (only exposed port)
  proxy_timeout: 30

network:
  name: swiftdeploy-net
  driver_type: bridge

mode: stable                          # stable or canary
```
## Subcommand Walkthrough

### init
Parses manifest.yaml and generates all config files.
Does NOT start any containers.

python swiftdeploy init

Generates:
- templates/nginx.conf
- docker-compose.yml
- .env

### validate
Runs 5 pre-flight checks before deployment:
1. manifest.yaml exists and is valid YAML
2. All required fields present and non-empty
3. Docker image exists locally
4. Nginx port is not already bound
5. Generated nginx.conf is syntactically valid

python swiftdeploy validate

### deploy
Runs init, brings up the full stack, and waits for health checks to pass.

python swiftdeploy deploy

What it does:
1. Generates all configs from manifest.yaml
2. Runs docker-compose up --build -d
3. Polls /healthz through Nginx until healthy (60s timeout)

### promote
Switches the deployment between stable and canary modes without downtime.

python swiftdeploy promote canary
python swiftdeploy promote stable

What it does:
1. Updates mode in manifest.yaml
2. Regenerates docker-compose.yml and .env
3. Recreates the app container with new environment variables
4. Verifies the service is healthy through Nginx

Canary mode adds X-Mode: canary header to every response.
Stable mode runs without the X-Mode header.

### teardown
Stops and removes all containers, networks, and volumes.

# Keep generated files
python swiftdeploy teardown

# Also delete generated configs
python swiftdeploy teardown --clean

## API Endpoints

`/GET     Welcome message with mode, version, timestamp`
`/healthz Liveness check with status and uptime` 
`/chaos   Inject failure modes for testing` 

### Chaos modes

# Slow mode — adds N second delay to all requests
```
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "slow", "duration": 5}'
```

# Error mode — returns 500 on X% of requests
```
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "error", "rate": 0.5}'
```
# Recover — cancels any active chaos
```
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "recover"}'
```
## Security

- App container runs as non-root user (appuser)
- All Linux capabilities dropped (cap_drop: ALL)
- App port never exposed directly — all traffic routes through Nginx
- Internal Docker network isolates the app from the public network
