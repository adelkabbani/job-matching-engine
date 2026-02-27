@echo off
echo Starting Backend...
start cmd /k "cd backend && title Backend && python run_server.py"

echo Starting Frontend...
start cmd /k "cd frontend && title Frontend && npm run dev"

echo Both servers are starting up in new windows.
