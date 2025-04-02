#!/bin/bash
# Setup script for the hardware monitoring frontend

# Create project directory
mkdir -p hardware-monitor-frontend
cd hardware-monitor-frontend

# Initialize Vite React project
npm create vite@latest . -- --template react

# Install dependencies
npm install axios react-router-dom recharts @mantine/core @mantine/hooks @emotion/react @mantine/charts chart.js @tabler/icons-react

# Create directory structure
mkdir -p src/api
mkdir -p src/components
mkdir -p src/pages

# Copy files from provided code
# Note: You should have the source files in a directory accessible to this script
# or manually create each file with the content from the provided code

echo "Setup complete! You can now run 'npm run dev' to start the development server."