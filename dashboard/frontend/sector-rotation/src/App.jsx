import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline';
import FiedlerChart from './components/FiedlerChart';
import TierClassification from './components/TierClassification';
import RotationSignals from './components/RotationSignals';
import ThemeList from './components/ThemeList';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [themes, setThemes] = useState([]);
  const [tiers, setTiers] = useState(null);
  const [selectedTheme, setSelectedTheme] = useState(null);
  const [fiedlerData, setFiedlerData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedTheme) {
      loadFiedlerData(selectedTheme);
    }
  }, [selectedTheme]);

  const loadData = async () => {
    try {
      // Load themes
      const themesRes = await axios.get(`${API_BASE}/api/sector-rotation/themes`);
      setThemes(themesRes.data.themes);

      // Load tier classification
      const tiersRes = await axios.get(`${API_BASE}/api/sector-rotation/tier-classification`);
      setTiers(tiersRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFiedlerData = async (theme) => {
    try {
      const response = await axios.get(`${API_BASE}/api/sector-rotation/fiedler-timeseries`, {
        params: { theme }
      });
      setFiedlerData(response.data.timeseries);
    } catch (error) {
      console.error('Error loading Fiedler data:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-white">Sector Rotation Dashboard</h1>
          <p className="text-slate-400 mt-1">Fiedler Values, Rotation Signals & Sector Analysis</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tier Classification */}
        {tiers && (
          <TierClassification tiers={tiers} />
        )}

        {/* Charts Grid */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Fiedler Chart */}
          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <ChartBarIcon className="h-6 w-6 mr-2" />
              Fiedler Value Time Series
            </h2>
            <div className="mb-4">
              <select
                value={selectedTheme || ''}
                onChange={(e) => setSelectedTheme(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white"
              >
                <option value="">Select Theme...</option>
                {themes.map((theme, idx) => (
                  <option key={idx} value={theme.theme}>
                    {theme.theme}
                  </option>
                ))}
              </select>
            </div>
            {fiedlerData.length > 0 && (
              <FiedlerChart data={fiedlerData} />
            )}
          </div>

          {/* Rotation Signals */}
          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <ArrowTrendingUpIcon className="h-6 w-6 mr-2" />
              Rotation Signals
            </h2>
            <RotationSignals apiBase={API_BASE} />
          </div>
        </div>

        {/* Theme List */}
        <div className="mt-8">
          <ThemeList themes={themes} />
        </div>
      </main>
    </div>
  );
}

export default App;

