import React, { useState, useEffect } from 'react';
import {
  Landmark, Calculator, ShieldCheck, CheckCircle2, AlertTriangle,
  ArrowRight, Percent, Calendar, DollarSign, Layers
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { LoanPackage, Persona } from '../types';
import { api } from '../api';

interface LoanNavigatorProps {
  currentPersona: Persona | null;
}

export const LoanNavigator: React.FC<LoanNavigatorProps> = ({ currentPersona }) => {
  const [principal, setPrincipal] = useState(4000000); // 40 Lakhs default
  const [rate, setRate] = useState(8.5);
  const [tenureYears, setTenureYears] = useState(20);
  const [loanPackage, setLoanPackage] = useState<LoanPackage | null>(null);
  const [amortisation, setAmortisation] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const calculate = async () => {
    setLoading(true);
    try {
      const tenureMonths = tenureYears * 12;
      const [pkg, sched] = await Promise.all([
        api.calculateLoan(principal, rate, tenureMonths),
        api.getAmortisationSchedule(principal, rate, tenureMonths, 36)
      ]);
      setLoanPackage(pkg);
      setAmortisation(sched);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    calculate();
  }, [principal, rate, tenureYears, currentPersona]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Loan & Mortgage Navigator</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Precision Decimal arithmetic • Verified against reference bank golden vectors
        </p>
      </div>

      {/* Calculator Controls & Primary Result Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sliders Box */}
        <div className="lg:col-span-1 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-5">
          <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
            <Calculator className="w-4 h-4 text-emerald-400" />
            <span>Loan Parameters</span>
          </h2>

          {/* Principal Slider */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Principal Amount</span>
              <span className="font-mono font-bold text-emerald-400">
                ₹{(principal).toLocaleString('en-IN')}
              </span>
            </div>
            <input
              type="range"
              min="500000"
              max="15000000"
              step="100000"
              value={principal}
              onChange={(e) => setPrincipal(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>₹5 Lakh</span>
              <span>₹1.5 Crore</span>
            </div>
          </div>

          {/* Interest Rate Slider */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Annual Interest Rate</span>
              <span className="font-mono font-bold text-emerald-400">{rate}% p.a.</span>
            </div>
            <input
              type="range"
              min="6.5"
              max="14.0"
              step="0.1"
              value={rate}
              onChange={(e) => setRate(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>6.5%</span>
              <span>14.0%</span>
            </div>
          </div>

          {/* Tenure Slider */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Tenure (Years)</span>
              <span className="font-mono font-bold text-emerald-400">
                {tenureYears} Years ({tenureYears * 12} mos)
              </span>
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
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>1 Year</span>
              <span>30 Years</span>
            </div>
          </div>

          {/* Affordability assessment badge */}
          {loanPackage && (
            <div className={`p-4 rounded-xl border text-xs ${
              loanPackage.is_affordable
                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                : 'bg-amber-950/40 border-amber-500/40 text-amber-300'
            }`}>
              <div className="flex items-center space-x-1.5 font-semibold mb-1">
                {loanPackage.is_affordable ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-amber-400" />}
                <span>FOIR Obligation Ratio: {loanPackage.foir_pct}%</span>
              </div>
              <p className="text-[11px] leading-relaxed opacity-90">
                {loanPackage.affordability_notes}
              </p>
            </div>
          )}
        </div>

        {/* Results Metrics & Amortisation Chart */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
              <span className="text-xs text-slate-400 block">Monthly Equated Instalment</span>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1.5">
                {loanPackage?.formatted_emi || '₹0'}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Accurate to the paisa</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
              <span className="text-xs text-slate-400 block">Total Interest Payable</span>
              <div className="text-2xl font-bold font-mono text-amber-300 mt-1.5">
                {loanPackage?.formatted_total_interest || '₹0'}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Over {tenureYears} years</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
              <span className="text-xs text-slate-400 block">Total Amount Payable</span>
              <div className="text-2xl font-bold font-mono text-white mt-1.5">
                {loanPackage?.formatted_total_payment || '₹0'}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Principal + Interest</span>
            </div>
          </div>

          {/* Amortisation Chart */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800">
            <h3 className="text-sm font-semibold text-white mb-1">Amortisation Schedule (First 36 Months)</h3>
            <p className="text-xs text-slate-400 mb-4">Visualizing remaining loan balance reduction over time</p>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={amortisation}>
                  <defs>
                    <linearGradient id="balanceGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#64748b" tickFormatter={(m) => `M${m}`} />
                  <YAxis stroke="#64748b" tickFormatter={(v) => `₹${(v/100000).toFixed(0)}L`} />
                  <RechartsTooltip
                    formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Balance']}
                    labelFormatter={(m) => `Month ${m}`}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  />
                  <Area type="monotone" dataKey="remaining_balance" stroke="#10b981" fillOpacity={1} fill="url(#balanceGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Prepayment & Balance Transfer What-If Box */}
          {loanPackage?.prepayment_options && (
            <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-xs font-semibold text-emerald-400 block mb-1">
                  Prepayment Scenario (₹2 Lakh at Month 12)
                </span>
                <p className="text-xs text-slate-300">
                  Option A: Save <strong className="text-white font-mono">{loanPackage.prepayment_options.reduced_tenure_option.formatted_interest_saved}</strong> and cut tenure by <strong className="text-white font-mono">{loanPackage.prepayment_options.reduced_tenure_option.years_saved} years</strong>.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-xs font-semibold text-teal-400 block mb-1">
                  Balance Transfer (0.5% lower rate)
                </span>
                <p className="text-xs text-slate-300">
                  Refinancing saves <strong className="text-white font-mono">{loanPackage.balance_transfer?.formatted_net_total_savings}</strong> net with break-even in <strong className="text-white font-mono">{loanPackage.balance_transfer?.break_even_months} months</strong>.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
