import React from 'react';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';

function ThemeList({ themes }) {
  const sortedThemes = [...themes].sort((a, b) => b.enhancement_score - a.enhancement_score);

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-6">Theme Cohesion Rankings</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-3 px-4 text-slate-300">Rank</th>
              <th className="text-left py-3 px-4 text-slate-300">Theme</th>
              <th className="text-right py-3 px-4 text-slate-300">Fiedler</th>
              <th className="text-right py-3 px-4 text-slate-300">Change</th>
              <th className="text-right py-3 px-4 text-slate-300">% Change</th>
              <th className="text-right py-3 px-4 text-slate-300">Stocks</th>
              <th className="text-right py-3 px-4 text-slate-300">Score</th>
            </tr>
          </thead>
          <tbody>
            {sortedThemes.slice(0, 20).map((theme, idx) => (
              <tr
                key={idx}
                className="border-b border-slate-700/50 hover:bg-slate-700/30"
              >
                <td className="py-3 px-4 text-slate-400">{idx + 1}</td>
                <td className="py-3 px-4 text-white font-medium">{theme.theme}</td>
                <td className="py-3 px-4 text-right text-slate-300">
                  {theme.current_fiedler?.toFixed(2) || '-'}
                </td>
                <td className="py-3 px-4 text-right">
                  <div className="flex items-center justify-end">
                    {theme.fiedler_change > 0 ? (
                      <ArrowTrendingUpIcon className="h-4 w-4 text-green-400 mr-1" />
                    ) : (
                      <ArrowTrendingDownIcon className="h-4 w-4 text-red-400 mr-1" />
                    )}
                    <span className={theme.fiedler_change > 0 ? 'text-green-400' : 'text-red-400'}>
                      {theme.fiedler_change?.toFixed(2) || '-'}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4 text-right text-slate-300">
                  {theme.pct_change?.toFixed(1) || '-'}%
                </td>
                <td className="py-3 px-4 text-right text-slate-300">
                  {theme.n_stocks || '-'}
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="bg-blue-600 text-white px-2 py-1 rounded text-sm">
                    {theme.enhancement_score?.toFixed(1) || '-'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ThemeList;

