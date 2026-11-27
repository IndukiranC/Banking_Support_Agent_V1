import React, { useState, useEffect } from 'react';
import {
  Database, ShieldCheck, RefreshCw, Key, CheckCircle2,
  Lock, AlertTriangle, Hash, ExternalLink
} from 'lucide-react';
import { AuditLogItem } from '../types';
import { api } from '../api';

export const AuditLogView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [verifyResult, setVerifyResult] = useState<any>(null);
  const [verifying, setVerifying] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs(50);
      setLogs(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const runVerification = async () => {
    setVerifying(true);
    try {
      const res = await api.verifyAuditChain();
      setVerifyResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white">Append-Only Hash-Chained Audit Trail</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              SHA-256 Chained
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable, tamper-evident cryptographic provenance for all banking queries and actions
          </p>
        </div>

        <button
          onClick={runVerification}
          disabled={verifying}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-900/20 transition-all disabled:bg-slate-800"
        >
          {verifying ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
          <span>Verify Cryptographic Chain</span>
        </button>
      </div>

      {/* Verification status card */}
      {verifyResult && (
        <div className={`p-4 rounded-2xl border text-xs flex items-center justify-between ${
          verifyResult.valid
            ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
            : 'bg-rose-950/40 border-rose-500/40 text-rose-300'
        }`}>
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <span className="font-bold block text-sm">
                Cryptographic Integrity Status: {verifyResult.status}
              </span>
              <span className="text-[11px] text-slate-400">
                Verified {verifyResult.total_entries} records from Genesis block. Latest Tip Hash: {verifyResult.latest_hash?.slice(0, 24)}...
              </span>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full font-mono text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            TAMPER_PROOF
          </span>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-sm font-semibold text-white">Cryptographic Log Records ({logs.length})</h2>
          <button
            onClick={loadLogs}
            className="text-xs text-slate-400 hover:text-white flex items-center space-x-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
              <tr>
                <th className="pb-3 font-semibold">ID</th>
                <th className="pb-3 font-semibold">Timestamp</th>
                <th className="pb-3 font-semibold">Action Type</th>
                <th className="pb-3 font-semibold">Intent</th>
                <th className="pb-3 font-semibold">Verification</th>
                <th className="pb-3 font-semibold">Current Block Hash</th>
                <th className="pb-3 font-semibold">Previous Hash Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 text-slate-400">#{log.id}</td>
                  <td className="py-3 font-sans text-slate-300 whitespace-nowrap">{log.timestamp}</td>
                  <td className="py-3 font-sans font-medium text-white">{log.action_type}</td>
                  <td className="py-3 text-emerald-400">{log.intent || '—'}</td>
                  <td className="py-3">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-sans font-semibold ${
                      log.verification_status === 'PASSED'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {log.verification_status || 'N/A'}
                    </span>
                  </td>
                  <td className="py-3 text-slate-300" title={log.curr_hash}>
                    {log.curr_hash.slice(0, 16)}...
                  </td>
                  <td className="py-3 text-slate-500" title={log.prev_hash}>
                    {log.prev_hash.slice(0, 16)}...
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
