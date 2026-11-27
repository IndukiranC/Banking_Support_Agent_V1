import React, { useState, useEffect } from 'react';
import {
  Compass, ShieldCheck, Target, TrendingUp, Sliders, CheckCircle2,
  AlertCircle, DollarSign, ArrowRight
} from 'lucide-react';
import { GuidancePlan, Persona } from '../types';
import { api } from '../api';

interface GuidancePlannerProps {
  currentPersona: Persona | null;
}

export const GuidancePlanner: React.FC<GuidancePlannerProps> = ({ currentPersona }) => {
  const [plan, setPlan] = useState<GuidancePlan | null>(null);
  const [diningCut, setDiningCut] = useState(0);
  const [shoppingCut, setShoppingCut] = useState(0);
  const [loading, setLoading] = useState(true);

  const loadPlan = async () => {
    setLoading(true);
    try {
      const res = await api.getGuidancePlan(diningCut, shoppingCut);
      setPlan(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlan();
  }, [diningCut, shoppingCut, currentPersona]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Personalised 50/30/20 Financial Guidance</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Deterministic benchmarking adapted to verified cash-flow • What-if trade-off simulator
        </p>
      </div>

      {/* 50/30/20 Split Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Needs (50%) */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 relative">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Needs (Essentials)
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Target: 50%
            </span>
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-white">
            {plan?.needs_pct}%
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 mt-3 overflow-hidden">
            <div
              className={`h-2 rounded-full ${plan && plan.needs_pct > 55 ? 'bg-amber-400' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, plan?.needs_pct || 0)}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2">
            Housing, groceries, utilities, transit.
          </p>
        </div>

        {/* Wants (30%) */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 relative">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
              Wants (Discretionary)
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Target: 30%
            </span>
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-white">
            {plan?.wants_pct}%
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 mt-3 overflow-hidden">
            <div
              className={`h-2 rounded-full ${plan && plan.wants_pct > 35 ? 'bg-rose-400' : 'bg-blue-500'}`}
              style={{ width: `${Math.min(100, plan?.wants_pct || 0)}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2">
            Dining out, shopping, entertainment.
          </p>
        </div>

        {/* Savings (20%) */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 relative">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-teal-400 uppercase tracking-wider">
              Savings & Investment
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">
              Target: 20%
            </span>
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-white">
            {plan?.savings_pct}%
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 mt-3 overflow-hidden">
            <div
              className="h-2 rounded-full bg-teal-400"
              style={{ width: `${Math.min(100, plan?.savings_pct || 0)}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2">
            Emergency reserve, mutual funds, goal savings.
          </p>
        </div>
      </div>

      {/* Emergency Fund & What-If Simulator Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Emergency Fund Box */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2">
            <Target className="w-5 h-5 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">6-Month Emergency Fund Target</h2>
          </div>
          <div className="text-3xl font-bold font-mono text-emerald-400">
            {plan?.formatted_emergency_target}
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Calculated as 6 months of essential living requirements (rent, bills, groceries).
            Insulates against income disruption without liquidating long-term investments.
          </p>
          <div className="pt-2 border-t border-slate-800 text-xs text-slate-400 flex justify-between">
            <span>Verified Monthly Income:</span>
            <span className="font-mono text-slate-200">{plan?.formatted_income}</span>
          </div>
        </div>

        {/* What-If Sliders */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-5">
          <div className="flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-teal-400" />
            <h2 className="text-sm font-semibold text-white">What-If Spending Levers</h2>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Reduce Food Delivery & Dining</span>
              <span className="font-mono text-emerald-400 font-bold">-{diningCut}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="5"
              value={diningCut}
              onChange={(e) => setDiningCut(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Pause Discretionary Shopping</span>
              <span className="font-mono text-emerald-400 font-bold">-{shoppingCut}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="5"
              value={shoppingCut}
              onChange={(e) => setShoppingCut(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
          </div>

          {plan?.what_if_scenario && (
            <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300">
              <span className="font-semibold block mb-0.5">Trade-off Impact:</span>
              <span>
                Frees up <strong className="font-mono text-white">{plan.what_if_scenario.formatted_additional_savings}</strong> additional monthly capital!
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
