import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

function PerformanceChart({ performance }) {
  const { baseline, filtered } = performance;

  const data = [
    {
      name: 'Win Rate',
      Baseline: baseline.win_rate,
      Filtered: filtered.win_rate
    },
    {
      name: 'Avg Return',
      Baseline: baseline.avg_return,
      Filtered: filtered.avg_return
    },
    {
      name: 'Sharpe',
      Baseline: baseline.sharpe_ratio,
      Filtered: filtered.sharpe_ratio
    }
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
        <XAxis dataKey="name" stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #475569',
            borderRadius: '8px'
          }}
        />
        <Legend />
        <Bar dataKey="Baseline" fill="#64748b" />
        <Bar dataKey="Filtered" fill="#3b82f6" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default PerformanceChart;

