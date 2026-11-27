import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, ShieldCheck, AlertTriangle, Play, CheckCircle, XCircle,
  Clock, MapPin, Smartphone, RefreshCw, Zap, Lock
} from 'lucide-react';
import { FraudSummary, FraudAlertItem, Persona } from '../types';
import { api } from '../api';

interface FraudCentreProps {
  currentPersona: Persona | null;
}

export const FraudCentre: React.FC<FraudCentreProps> = ({ currentPersona }) => {
  const [summary, setSummary] = useState<FraudSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.getFraudSummary();
      setSummary(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [currentPersona]);

  const handleReview = async (alertId: number, feedback: 'THIS_WAS_ME' | 'THIS_WAS_NOT_ME') => {
    try {
      const res = await api.reviewFraudAlert(alertId, feedback);
      setActionNotice(feedback === 'THIS_WAS_ME'
        ? 'Verified as legitimate. Payee recorded in safe baseline.'
        : 'Confirmed fraud. Debit card temporarily frozen and dispute opened.'
      );
      loadAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSimulate = async (scenario: string) => {
    setSimulating(true);
    try {
      await api.simulateFraud(scenario);
      setActionNotice(`Live synthetic anomaly injected! Detected by rule engine.`);
      await loadAlerts();
    } catch (e) {
      console.error(e);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
        <RefreshCw className="w-5 h-5 animate-spin text-emerald-400 mr-2" />
        <span>Evaluating weighted fraud detection signals...</span>
      </div>
    );
  }

  const isHighRisk = summary?.risk_level === 'HIGH';
  const isMedRisk = summary?.risk_level === 'MEDIUM';

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header with Fraud Simulator trigger */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white">Fraud Monitoring & Alert Centre</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              Hero Module
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time explainable 7-signal behavioral scoring • Zero black-box decisions
          </p>
        </div>

        {/* Live Fraud Simulator Button Bar */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-700/80 p-1.5 rounded-xl shadow-lg">
          <div className="flex items-center space-x-1.5 px-2 text-xs font-semibold text-slate-300">
            <Zap className="w-4 h-4 text-amber-400" />
            <span className="hidden sm:inline">Fraud Simulator:</span>
          </div>
          <button
            onClick={() => handleSimulate('outlier')}
            disabled={simulating}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-rose-600/80 hover:bg-rose-600 text-white transition-colors flex items-center space-x-1"
          >
            <Play className="w-3 h-3" />
            <span>High Outlier</span>
          </button>
          <button
            onClick={() => handleSimulate('velocity')}
            disabled={simulating}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-amber-600/80 hover:bg-amber-600 text-white transition-colors flex items-center space-x-1"
          >
            <Play className="w-3 h-3" />
            <span>Velocity Spike</span>
          </button>
          <button
            onClick={() => handleSimulate('structuring')}
            disabled={simulating}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white transition-colors flex items-center space-x-1"
          >
            <Play className="w-3 h-3" />
            <span>Structuring</span>
          </button>
        </div>
      </div>

      {actionNotice && (
        <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs flex items-center justify-between">
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} className="text-emerald-400 font-bold hover:text-white">✕</button>
        </div>
      )}

      {/* Risk Standing Banner */}
      <div className={`p-6 rounded-2xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${
        isHighRisk
          ? 'bg-rose-950/40 border-rose-500/40'
          : isMedRisk
          ? 'bg-amber-950/40 border-amber-500/40'
          : 'bg-emerald-950/30 border-emerald-500/30'
      }`}>
        <div className="flex items-center space-x-4">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 ${
            isHighRisk ? 'bg-rose-600 text-white' : isMedRisk ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white'
          }`}>
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold text-white">Current Risk Assessment: {summary?.risk_level}</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-slate-900 border border-slate-700">
                Score: {summary?.risk_score}/100
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-xl">
              {summary?.recommended_action}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-6 text-right">
          <div>
            <span className="text-slate-400 text-xs block">Active Alerts</span>
            <span className="text-2xl font-bold font-mono text-white">{summary?.total_alerts || 0}</span>
          </div>
          <div>
            <span className="text-slate-400 text-xs block">High-Risk Alerts</span>
            <span className="text-2xl font-bold font-mono text-rose-400">{summary?.high_risk_alerts || 0}</span>
          </div>
        </div>
      </div>

      {/* Active Alerts List */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-white">Recent Real-Time Alerts & Review Actions</h2>

        {summary?.recent_alerts && summary.recent_alerts.length > 0 ? (
          summary.recent_alerts.map((alert) => (
            <div
              key={alert.alert_id}
              className={`p-5 rounded-2xl border transition-all ${
                alert.status === 'PENDING'
                  ? 'bg-slate-900/90 border-slate-700 shadow-xl'
                  : 'bg-slate-950/60 border-slate-800/80 opacity-75'
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold text-white">{alert.merchant}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      alert.risk_level === 'HIGH'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : alert.risk_level === 'MEDIUM'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}>
                      {alert.risk_level} ({alert.risk_score}/100)
                    </span>
                    <span className="text-xs text-slate-500">• {alert.created_at}</span>
                  </div>
                  <div className="font-mono text-base font-bold text-emerald-400">
                    {alert.formatted_amount}
                  </div>
                </div>

                {/* Feedback Action Buttons */}
                {alert.status === 'PENDING' ? (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleReview(alert.alert_id, 'THIS_WAS_ME')}
                      className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition-colors flex items-center space-x-1.5 shadow-sm"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>This was me</span>
                    </button>
                    <button
                      onClick={() => handleReview(alert.alert_id, 'THIS_WAS_NOT_ME')}
                      className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-rose-600 hover:bg-rose-500 text-white transition-colors flex items-center space-x-1.5 shadow-sm"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>This wasn't me</span>
                    </button>
                  </div>
                ) : (
                  <div className="px-3 py-1.5 rounded-xl bg-slate-800 text-xs font-medium text-slate-300 border border-slate-700">
                    Status: <span className="font-semibold text-emerald-400">{alert.status}</span>
                  </div>
                )}
              </div>

              {/* Explainable Triggered Rules Breakdown */}
              <div className="mt-4 pt-3 border-t border-slate-800/80">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Explainable Signal Audit Trail (Weights & Reasons)
                </span>
                <div className="space-y-1.5">
                  {alert.triggered_rules && alert.triggered_rules.map((rule, rIdx) => (
                    <div key={rIdx} className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs flex items-start space-x-2.5">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-200">{rule.name}</span>
                          <span className="text-[10px] font-mono text-slate-400">Weight: +{rule.weight}</span>
                        </div>
                        <p className="text-slate-400 text-[11px] mt-0.5">{rule.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="p-8 text-center rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 text-sm">
            <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
            <p className="font-semibold text-slate-200">Zero active fraud alerts</p>
            <p className="text-xs mt-1">Try clicking one of the Fraud Simulator buttons above to inject a live anomaly test!</p>
          </div>
        )}
      </div>
    </div>
  );
};
