import React, { useState } from 'react';
import { Calculator, ChevronDown, ChevronUp, Code, Database, Filter, CheckCircle2, ShieldCheck } from 'lucide-react';
import { CalculationNotes } from '../types';

interface HowCalculatedDrawerProps {
  notes?: CalculationNotes;
  verificationStatus?: string;
  verifiedNumbers?: string[];
}

export const HowCalculatedDrawer: React.FC<HowCalculatedDrawerProps> = ({
  notes,
  verificationStatus,
  verifiedNumbers
}) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!notes) return null;

  return (
    <div className="mt-3 border border-slate-700/80 rounded-xl overflow-hidden bg-slate-900/60 transition-all">
      {/* Header bar that toggles the drawer */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between text-left text-xs bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Calculator className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-semibold text-slate-300">How this was calculated</span>
          <span className="text-[11px] text-slate-400 hidden sm:inline">
            ({notes.transaction_count} txs • {notes.data_window})
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1 ${
            verificationStatus === 'PASSED'
              ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
              : 'bg-amber-950/60 text-amber-400 border border-amber-500/30'
          }`}>
            <ShieldCheck className="w-3 h-3 mr-1" />
            <span>{verificationStatus === 'PASSED' ? 'Verified 100%' : 'Template Fallback'}</span>
          </span>
          {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {/* Expanded Details */}
      {isOpen && (
        <div className="p-4 space-y-3.5 text-xs text-slate-300 border-t border-slate-800 bg-slate-950/40 animate-in fade-in">
          {/* Summary */}
          <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 flex items-start space-x-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-slate-200">Calculation Summary</p>
              <p className="text-slate-400 mt-0.5 text-[11px]">{notes.calculation_summary}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Formula applied */}
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center space-x-1.5 text-slate-400 font-medium mb-1.5">
                <Code className="w-3.5 h-3.5 text-teal-400" />
                <span>Deterministic Formula</span>
              </div>
              <code className="block font-mono text-[11px] text-emerald-300 bg-slate-950 px-2 py-1.5 rounded border border-slate-800/60 break-words">
                {notes.formula}
              </code>
            </div>

            {/* Data window & filters */}
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center space-x-1.5 text-slate-400 font-medium mb-1.5">
                <Filter className="w-3.5 h-3.5 text-indigo-400" />
                <span>Data Window & Scope</span>
              </div>
              <div className="space-y-1 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-400">Date Window:</span>
                  <span className="font-medium text-slate-200">{notes.data_window}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Transactions Audited:</span>
                  <span className="font-medium text-emerald-400">{notes.transaction_count}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Breakdown parameters */}
          {notes.breakdown && (
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center space-x-1.5 text-slate-400 font-medium mb-2">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                <span>Computed Mathematical Components</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
                {Object.entries(notes.breakdown).map(([key, val]) => (
                  <div key={key} className="bg-slate-950/70 p-2 rounded border border-slate-800/80">
                    <span className="text-slate-400 text-[10px] block capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-mono font-semibold text-slate-200">
                      {typeof val === 'number' ? val.toLocaleString('en-IN') : String(val)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Source Transaction IDs */}
          {notes.source_transaction_ids && notes.source_transaction_ids.length > 0 && (
            <div className="text-[11px] text-slate-400">
              <span className="font-medium text-slate-300">Audited Transaction Records (IDs): </span>
              <span className="font-mono text-emerald-400/90">
                {notes.source_transaction_ids.slice(0, 15).map(id => `#${id}`).join(', ')}
                {notes.source_transaction_ids.length > 15 ? '...' : ''}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
