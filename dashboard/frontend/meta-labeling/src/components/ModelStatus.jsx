import React from 'react';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';

function ModelStatus({ status }) {
  if (!status) {
    return (
      <div className="flex items-center text-slate-400">
        <XCircleIcon className="h-5 w-5 mr-2" />
        Status Unknown
      </div>
    );
  }

  if (!status.available) {
    return (
      <div className="flex items-center text-yellow-400">
        <XCircleIcon className="h-5 w-5 mr-2" />
        Not Available
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-4">
      <div className="flex items-center text-green-400">
        <CheckCircleIcon className="h-5 w-5 mr-2" />
        Active
      </div>
      <div className="text-sm text-slate-400">
        {status.model_type} • {status.n_features} features
      </div>
    </div>
  );
}

export default ModelStatus;

