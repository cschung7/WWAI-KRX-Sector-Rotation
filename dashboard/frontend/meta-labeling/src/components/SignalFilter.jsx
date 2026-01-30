import React, { useState } from 'react';
import axios from 'axios';
import { FunnelIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

function SignalFilter({ apiBase }) {
  const [signals, setSignals] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [filtering, setFiltering] = useState(false);
  const [result, setResult] = useState(null);

  const handleFilter = async () => {
    if (!signals.trim()) {
      alert('Please enter signals (JSON format)');
      return;
    }

    setFiltering(true);
    try {
      const signalsArray = JSON.parse(signals);
      const response = await axios.post(`${apiBase}/api/meta-labeling/filter`, {
        signals: signalsArray,
        date: date
      });
      setResult(response.data);
    } catch (error) {
      alert('Error filtering signals: ' + error.message);
    } finally {
      setFiltering(false);
    }
  };

  return (
    <div>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Analysis Date
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Signals (JSON Array)
          </label>
          <textarea
            value={signals}
            onChange={(e) => setSignals(e.target.value)}
            placeholder='[{"theme": "반도체", "signal_type": "tier", "signal_strength": 2.5, ...}]'
            rows={6}
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white font-mono text-sm"
          />
        </div>

        <button
          onClick={handleFilter}
          disabled={filtering}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-semibold py-2 px-4 rounded-lg flex items-center justify-center"
        >
          {filtering ? (
            'Filtering...'
          ) : (
            <>
              <FunnelIcon className="h-5 w-5 mr-2" />
              Filter Signals
            </>
          )}
        </button>
      </div>

      {result && (
        <div className="mt-6 p-4 bg-slate-700 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Filtering Results</h3>
            <div className="text-sm text-slate-400">
              {result.original_count} → {result.filtered_count} signals
            </div>
          </div>
          <div className="text-sm text-slate-300">
            <div>Reduction: {result.reduction_pct.toFixed(1)}%</div>
            <div className="mt-2 text-xs text-slate-400">
              {result.filtered_count} signals passed meta-labeling filter
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SignalFilter;

