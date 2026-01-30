import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ChartBarIcon,
  FilterIcon,
  TrendingUpIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import PerformanceMetrics from './components/PerformanceMetrics';
import SignalFilter from './components/SignalFilter';
import PerformanceChart from './components/PerformanceChart';
import ModelStatus from './components/ModelStatus';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [status, setStatus] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load status
      const statusRes = await axios.get(`${API_BASE}/api/meta-labeling/status`);
      setStatus(statusRes.data);

      // Load performance
      const perfRes = await axios.get(`${API_BASE}/api/meta-labeling/performance`);
      setPerformance(perfRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">Meta-Labeling Dashboard</h1>
              <p className="text-slate-400 mt-1">Signal Filtering & Performance Monitoring</p>
            </div>
            <ModelStatus status={status} />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Performance Metrics */}
        {performance && (
          <PerformanceMetrics performance={performance} />
        )}

        {/* Charts */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <TrendingUpIcon className="h-6 w-6 mr-2" />
              Performance Comparison
            </h2>
            {performance && (
              <PerformanceChart performance={performance} />
            )}
          </div>

          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <FilterIcon className="h-6 w-6 mr-2" />
              Signal Filtering
            </h2>
            <SignalFilter apiBase={API_BASE} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

