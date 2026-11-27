import React, { useState, useEffect } from 'react';
import {
  TrendingUp, ShieldAlert, PieChart as PieIcon, Calculator,
  AlertCircle, CheckCircle2, DollarSign, Layers
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip
} from 'recharts';
import { InvestmentPortfolio, Persona } from '../types';
import { api } from '../api';

const ASSET_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#06b6d4'];

interface InvestmentHubProps {
  currentPersona: Persona | null;
}

export const InvestmentHub: React.FC<InvestmentHubProps> = ({ currentPersona }) => {
  const [portfolio, setPortfolio] = useState<InvestmentPortfolio | null>(null);
  const [monthlySip, setMonthlySip] = useState(10000);
  const [returnPct, setReturnPct] = useState(12.0);
  const [tenureYears, setTenureYears] = useState(10);
  const [sipResult, setSipResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [portRes, sipRes] = await Promise.all([
        api.getInvestmentPortfolio(),
        api.calculateSip(monthlySip, returnPct, tenureYears)
      ]);
      setPortfolio(portRes);
      setSipResult(sipRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentPersona]);

  const recalculateSip = async () => {
    try {
      const res = await api.calculateSip(monthlySip, returnPct, tenureYears);
      setSipResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    recalculateSip();
  }, [monthlySip, returnPct, tenureYears]);

  const allocData = portfolio?.recommended_allocation
    ? Object.entries(portfolio.recommended_allocation).map(([name, pct]) => ({
        name,
        value: pct * 100
      }))
    : [];

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Investment Awareness & Portfolio Benchmarks</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Educational asset allocation models • Guaranteed SEBI compliance policy
        </p>
      </div>

      {/* Mandatory Regulatory Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-300 text-xs flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">Statutory Educational Notice:</span>
          <p className="text-amber-200/90 leading-relaxed text-[11px]">
            {portfolio?.disclaimer}
          </p>
        </div>
      </div>

      {/* Grid: Recommended Asset Mix & SIP Calculator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recommended Asset Allocation */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-semibold text-white">
                Assessed Profile Model: <span className="text-emerald-400">{portfolio?.risk_profile}</span>
              </h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300">
                Standard Benchmark
              </span>
            </div>

            <div className="h-56 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={allocData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {allocData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={ASSET_COLORS[index % ASSET_COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    formatter={(val: any) => [`${val}%`, 'Allocation']}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-2 mt-4">
              {allocData.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center text-xs">
                  <div className="flex items-center space-x-2">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ASSET_COLORS[idx % ASSET_COLORS.length] }} />
                    <span className="text-slate-300">{item.name}</span>
                  </div>
                  <span className="font-mono font-semibold text-white">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Compound SIP Wealth Simulator */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2">
            <Calculator className="w-5 h-5 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Systematic Investment Plan (SIP) Simulator</h2>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Monthly Contribution</span>
              <span className="font-mono font-bold text-emerald-400">₹{(monthlySip).toLocaleString('en-IN')}</span>
            </div>
            <input
              type="range"
              min="1000"
              max="100000"
              step="1000"
              value={monthlySip}
              onChange={(e) => setMonthlySip(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Expected Annual Growth</span>
              <span className="font-mono font-bold text-emerald-400">{returnPct}% p.a.</span>
            </div>
            <input
              type="range"
              min="6.0"
              max="18.0"
              step="0.5"
              value={returnPct}
              onChange={(e) => setReturnPct(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Time Horizon</span>
              <span className="font-mono font-bold text-emerald-400">{tenureYears} Years</span>
            </div>
            <input
              type="range"
              min="1"
              max="30"
              step="1"
              value={tenureYears}
              onChange={(e) => setTenureYears(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
          </div>

          {/* SIP Outcome Card */}
          {sipResult && (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-400 text-[10px] block">Invested Principal</span>
                <span className="font-mono font-semibold text-slate-200">{sipResult.formatted_invested}</span>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] block">Estimated Wealth Gain</span>
                <span className="font-mono font-semibold text-emerald-400">+{sipResult.formatted_gain}</span>
              </div>
              <div className="col-span-2 pt-2 border-t border-slate-800 flex justify-between items-baseline">
                <span className="text-slate-300 font-medium">Estimated Maturity Value:</span>
                <span className="text-lg font-bold font-mono text-emerald-400">{sipResult.formatted_maturity}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
