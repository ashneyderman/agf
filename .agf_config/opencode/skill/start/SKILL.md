---
name: start
description: Start the project services
params: []
---

# Start

Start the project services or development environment.

## Instructions

This skill takes no parameters. It starts any services required by the project.

1. **Check for Start Script**: Look for a start script in the project (e.g., `bin/start.sh`, `scripts/start.sh`, or package.json start script)
2. **Execute Start Command**: Run the appropriate start command for the project
   - Default: `sh bin/start.sh` with a 300-second timeout
   - Adjust based on project configuration found in README.md or package.json
3. **Verify Services**: Check that services started successfully
4. **Report Status**: Report which services were started and their status

## Common Start Patterns

The skill should detect and use the appropriate start method:

- Shell script: `sh bin/start.sh` or `bash scripts/start.sh`
- Node.js: `npm start` or `yarn start`
- Python: `python manage.py runserver` or `uvicorn main:app`
- Docker: `docker-compose up`
- Make: `make start`

## Report Format

After starting services, report:

- Command executed
- Services started
- Ports listening (if applicable)
- Any errors or warnings
- How to stop the services

## Example Output

```
Started services:
- Web server on http://localhost:8000
- Background worker process
- Redis cache on localhost:6379

Command: sh bin/start.sh
Status: Running (PID 12345)

To stop: Press Ctrl+C or run `sh bin/stop.sh`
```
