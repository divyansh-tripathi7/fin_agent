#!/bin/bash

# Start the backend server in the background
echo "Starting the backend server..."
cd "$(dirname "$0")"
python main.py --api-only &
BACKEND_PID=$!

# Wait for the backend to start
echo "Waiting for backend to start..."
sleep 5

# Start the React frontend in the background
echo "Starting the React frontend..."
cd frontend
npm start &
FRONTEND_PID=$!

# Function to handle script termination
cleanup() {
    echo "Shutting down servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Register the cleanup function for when the script is terminated
trap cleanup SIGINT SIGTERM

echo "All servers are running!"
echo "Backend API: http://localhost:8080"
echo "React Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop all servers."

# Keep the script running
wait
