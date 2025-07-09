#!/bin/bash

# Advisory ETL UI Application Setup Script
echo "Setting up Advisory ETL UI Application..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.8 or later."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed. Please install Node.js 16 or later."
    exit 1
fi

# Create project directory structure
mkdir -p ui-application/backend/logs
mkdir -p ui-application/frontend/build

# Backend Setup
echo "Setting up backend..."
cd ui-application/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment variables
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template. Please update with your actual values."
fi

cd ../..

# Frontend Setup
echo "Setting up frontend..."
cd ui-application/frontend

# Install Node.js dependencies
npm install

# Copy environment variables
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created frontend .env file from template."
fi

cd ../..

# Create startup scripts
cat > ui-application/start-backend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
python app.py
EOF

cat > ui-application/start-frontend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
npm start
EOF

cat > ui-application/start-all.sh << 'EOF'
#!/bin/bash
echo "Starting Advisory ETL UI Application..."

# Start backend in background
echo "Starting backend server..."
cd "$(dirname "$0")"
./start-backend.sh &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend
echo "Starting frontend development server..."
./start-frontend.sh &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Application URLs:"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000/api"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
EOF

# Make scripts executable
chmod +x ui-application/start-backend.sh
chmod +x ui-application/start-frontend.sh
chmod +x ui-application/start-all.sh

echo ""
echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update ui-application/backend/.env with your database connection details"
echo "2. Update ui-application/frontend/.env if needed"
echo "3. Ensure your PostgreSQL database is running with the schema from sql/schema.sql"
echo "4. Run './ui-application/start-all.sh' to start both backend and frontend"
echo ""
echo "Application will be available at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:5000/api"
