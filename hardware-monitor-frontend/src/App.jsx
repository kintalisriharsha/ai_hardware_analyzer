/* eslint-disable no-unused-vars */
// File: src/App.jsx
import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MantineProvider, createTheme, useComputedColorScheme, useMantineColorScheme } from '@mantine/core';
import '@mantine/core/styles.css';
import '@mantine/charts/styles.css';

import AppShell from './components/AppShell';
import Dashboard from './pages/Dashboard';
import Metrics from './pages/Metrics';
import SystemAnalysis from './pages/SystemAnalysis';
import Settings from './pages/Settings';

// Create theme
const theme = createTheme({
  // Your theme customizations can go here
});

function App() {
  const [colorScheme, setColorScheme] = useState('light');
  
  const toggleColorScheme = () => {
    setColorScheme(colorScheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <MantineProvider theme={theme} defaultColorScheme={colorScheme}>
      <Router>
        <AppShell toggleColorScheme={toggleColorScheme}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/metrics" element={<Metrics />} />
            <Route path="/analysis" element={<SystemAnalysis />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </AppShell>
      </Router>
    </MantineProvider>
  );
}

export default App;