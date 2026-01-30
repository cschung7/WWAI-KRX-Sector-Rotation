import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

function FiedlerChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
        <XAxis 
          dataKey="date" 
          stroke="#94a3b8"
          tick={{ fill: '#94a3b8', fontSize: 12 }}
        />
        <YAxis 
          stroke="#94a3b8"
          tick={{ fill: '#94a3b8', fontSize: 12 }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #475569',
            borderRadius: '8px',
            color: '#fff'
          }}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="fiedler" 
          stroke="#3b82f6" 
          strokeWidth={2}
          name="Fiedler Value"
          dot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default FiedlerChart;

