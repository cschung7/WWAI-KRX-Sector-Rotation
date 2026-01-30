import React from 'react';
import { BuildingOfficeIcon } from '@heroicons/react/24/outline';

function TierClassification({ tiers }) {
  const tierColors = {
    tier1: 'bg-green-600',
    tier2: 'bg-blue-600',
    tier3: 'bg-yellow-600',
    tier4: 'bg-slate-600'
  };

  const tierLabels = {
    tier1: 'TIER 1: Buy NOW',
    tier2: 'TIER 2: Accumulate 6-12mo',
    tier3: 'TIER 3: Research 12-18mo',
    tier4: 'TIER 4: Monitor 18-24mo'
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-6 flex items-center">
        <BuildingOfficeIcon className="h-6 w-6 mr-2" />
        4-Tier Investment Classification
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Object.keys(tierLabels).map((tierKey) => {
          const tierThemes = tiers.tiers[tierKey] || [];
          return (
            <div key={tierKey} className={`${tierColors[tierKey]} rounded-lg p-4`}>
              <div className="text-white font-semibold mb-2">{tierLabels[tierKey]}</div>
              <div className="text-3xl font-bold text-white">{tierThemes.length}</div>
              <div className="text-sm text-white/80 mt-1">themes</div>
            </div>
          );
        })}
      </div>

      {/* Tier Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.keys(tierLabels).map((tierKey) => {
          const tierThemes = tiers.tiers[tierKey] || [];
          return (
            <div key={tierKey} className="bg-slate-700 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-3">{tierLabels[tierKey]}</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {tierThemes.slice(0, 10).map((theme, idx) => (
                  <div key={idx} className="text-sm text-slate-300">
                    {theme.theme}
                  </div>
                ))}
                {tierThemes.length > 10 && (
                  <div className="text-xs text-slate-400">
                    +{tierThemes.length - 10} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TierClassification;

