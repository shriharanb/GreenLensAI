#!/bin/bash

# Get the project root directory (where this script lives)
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXEC="$PROJECT_DIR/GreenLensEnv/bin/python3"

# Colors for better visibility
export BLUE='\033[0;34m'
export GREEN='\033[0;32m'
export RED='\033[0;31m'
export YELLOW='\033[1;33m'
export NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting GreenLensAI System...${NC}"

# Cleanup function to stop everything when the script exits
cleanup() {
    echo -e "\n${RED}🛑 Stopping GreenLensAI Services...${NC}"
    [ ! -z "$DJANGO_PID" ] && kill $DJANGO_PID 2>/dev/null
    [ ! -z "$HTTP_SERVER_PID" ] && kill $HTTP_SERVER_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# 1. Check if PostgreSQL is running
echo -e "${YELLOW}🐘 Checking PostgreSQL...${NC}"
MAX_DB_RETRIES=30
DB_RETRY_COUNT=0

until pg_isready -q; do
    if [ $DB_RETRY_COUNT -eq $MAX_DB_RETRIES ]; then
        echo -e "${RED}❌ PostgreSQL is not ready after $MAX_DB_RETRIES seconds.${NC}"
        echo -e "${YELLOW}Please start it manually with: sudo systemctl start postgresql${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi
    printf "${YELLOW}⌛ Waiting for PostgreSQL... ($DB_RETRY_COUNT/$MAX_DB_RETRIES)${NC}\r"
    sleep 1
    DB_RETRY_COUNT=$((DB_RETRY_COUNT+1))
done
echo -e "\n${GREEN}✅ PostgreSQL is ready.${NC}"

# 2. Free up ports if they are in use
echo -e "${YELLOW}🧹 Clearing ports 8000 (Django) and 3000 (Frontend)...${NC}"
fuser -k 8000/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null

# 3. Clean up stale Qdrant lock file
if [ -f "$PROJECT_DIR/backend_django/vectordb/.lock" ]; then
    echo -e "${YELLOW}🧹 Removing stale Qdrant lock file...${NC}"
    rm "$PROJECT_DIR/backend_django/vectordb/.lock"
fi

# 4. Start Django Server
echo -e "${YELLOW}⚙️  Starting Django Backend on port 8000...${NC}"
cd "$PROJECT_DIR/backend_django"
$PYTHON_EXEC manage.py runserver 0.0.0.0:8000 > /tmp/django_server.log 2>&1 &
DJANGO_PID=$!

# 5. Start Frontend HTTP Server (to avoid file:// CORS issues)
echo -e "${YELLOW}🌐 Starting Frontend Server on port 3000...${NC}"
cd "$PROJECT_DIR/frontend"
python3 -m http.server 3000 > /tmp/frontend_server.log 2>&1 &
HTTP_SERVER_PID=$!

# Wait for servers to wake up
echo -e "${BLUE}⏳ Waiting for backend to initialize...${NC}"

# Health check loop for Django backend
MAX_RETRIES=30
RETRY_COUNT=0
HEALTH_URL="http://127.0.0.1:8000/api/health/"

until $(curl --output /dev/null --silent --head --fail "$HEALTH_URL"); do
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Backend failed to start after $MAX_RETRIES seconds.${NC}"
        echo -e "${YELLOW}🔍 Check /tmp/django_server.log for details:${NC}"
        tail -n 20 /tmp/django_server.log
        kill $DJANGO_PID 2>/dev/null
        kill $HTTP_SERVER_PID 2>/dev/null
        exit 1
    fi

    printf '.'
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT+1))
done

echo -e "\n${GREEN}✅ Backend is healthy!${NC}"

# 6. Open Browser
LOGIN_URL="http://localhost:3000/Pages/login.html"
echo -e "${GREEN}🌐 Opening GreenLensAI Login: $LOGIN_URL${NC}"

if command -v xdg-open &> /dev/null; then
    xdg-open "$LOGIN_URL"
elif command -v gnome-open &> /dev/null; then
    gnome-open "$LOGIN_URL"
else
    echo -e "${YELLOW}⚠️  Could not auto-open browser. Please open: $LOGIN_URL${NC}"
fi

echo -e "${GREEN}✅ System is LIVE!${NC}"
echo -e "   - Backend: http://localhost:8000"
echo -e "   - Frontend: http://localhost:3000"
echo -e "   Press ${RED}Ctrl+C${NC} to stop all services."

# Keep script alive and monitor processes
wait $DJANGO_PID $HTTP_SERVER_PID
