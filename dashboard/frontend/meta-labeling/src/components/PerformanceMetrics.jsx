import React from 'react';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

function PerformanceMetrics({ performance }) {
  const { baseline, filtered, improvements } = performance;

  const metrics = [
    {
      label: 'Win Rate',
      baseline: `${baseline.win_rate.toFixed(1)}%`,
      filtered: `${filtered.win_rate.toFixed(1)}%`,
      improvement: `+${improvements.win_rate_improvement_pp.toFixed(1)} pp`,
      positive: improvements.win_rate_improvement_pp > 0
    },
    {
      label: 'Average Return',
      baseline: `${baseline.avg_return.toFixed(2)}%`,
      filtered: `${filtered.avg_return.toFixed(2)}%`,
      improvement: `+${improvements.avg_return_improvement_pct.toFixed(1)}%`,
      positive: improvements.avg_return_improvement_pct > 0
    },
    {
      label: 'Sharpe Ratio',
      baseline: baseline.sharpe_ratio.toFixed(2),
      filtered: filtered.sharpe_ratio.toFixed(2),
      improvement: `+${improvements.sharpe_improvement.toFixed(2)}`,
      positive: improvements.sharpe_improvement > 0
    },
    {
      label: 'Signals',
      baseline: baseline.n_signals.toLocaleString(),
      filtered: filtered.n_signals.toLocaleString(),
      improvement: `-${improvements.signal_reduction_pct.toFixed(1)}%`,
      positive: true // Reduction is good (quality over quantity)
    }
  ];

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-6">Performance Metrics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, idx) => (
          <div key={idx} className="bg-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm mb-2">{metric.label}</div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-slate-300 text-xs">Baseline: {metric.baseline}</div>
                <div className="text-white text-lg font-semibold mt-1">
                  {metric.filtered}
                </div>
              </div>
              <div className={`flex items-center ${metric.positive ? 'text-green-400' : 'text-red-400'}`}>
                {metric.positive ? (
                  <CheckCircleIcon className="h-5 w-5 mr-1" />
                ) : (
                  <XCircleIcon className="h-5 w-5 mr-1" />
                )}
                <span className="text-sm font-medium">{metric.improvement}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PerformanceMetrics;

