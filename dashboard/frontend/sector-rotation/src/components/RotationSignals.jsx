import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/solid';

function RotationSignals({ apiBase }) {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSignals();
  }, []);

  const loadSignals = async () => {
    try {
      const response = await axios.get(`${apiBase}/api/sector-rotation/rotation-signals`);
      setSignals(response.data.signals);
    } catch (error) {
      console.error('Error loading signals:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-slate-400">Loading signals...</div>;
  }

  return (
    <div className="space-y-3">
      {signals.length === 0 ? (
        <div className="text-slate-400 text-center py-8">
          No rotation signals available
        </div>
      ) : (
        signals.map((signal, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-lg ${
              signal.signal === 'ROTATION_IN'
                ? 'bg-green-900/30 border border-green-600'
                : 'bg-red-900/30 border border-red-600'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                {signal.signal === 'ROTATION_IN' ? (
                  <ArrowTrendingUpIcon className="h-5 w-5 text-green-400 mr-2" />
                ) : (
                  <ArrowTrendingDownIcon className="h-5 w-5 text-red-400 mr-2" />
                )}
                <div>
                  <div className="font-semibold text-white">{signal.theme}</div>
                  <div className="text-sm text-slate-400">{signal.date}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-300">Fiedler: {signal.fiedler?.toFixed(2)}</div>
                <div className="text-xs text-slate-400">
                  Δ: {signal.fiedler_change?.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default RotationSignals;

