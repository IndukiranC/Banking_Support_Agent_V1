import React, { useState, useEffect } from 'react';
import {
  TrendingDown, TrendingUp, Download, RefreshCw, AlertCircle,
  Send, CheckCircle2, AlertTriangle, ShieldCheck, CreditCard, ArrowRight, UserCheck
} from 'lucide-react';
import {
  PieChart as RePieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip
} from 'recharts';
import { SpendingSummary, CashFlowForecast, Persona } from '../types';
import { api } from '../api';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b'];

interface SpendingDashboardProps {
  currentPersona: Persona | null;
}

export const SpendingDashboard: React.FC<SpendingDashboardProps> = ({ currentPersona }) => {
  const [spending, setSpending] = useState<SpendingSummary | null>(null);
  const [forecast, setForecast] = useState<CashFlowForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('current_month');

  // Transfer State
  const [recipient, setRecipient] = useState('Kishan Kumar');
  const [transferAmount, setTransferAmount] = useState('5000');
  const [transferChannel, setTransferChannel] = useState('UPI');
  const [isCheckingTransfer, setIsCheckingTransfer] = useState(false);
  const [transferAlert, setTransferAlert] = useState<any | null>(null);
  const [transferSuccess, setTransferSuccess] = useState<any | null>(null);
  const [transferError, setTransferError] = useState<string | null>(null);

  const demoContacts = [
    { name: 'Kishan Kumar', role: 'Freelancer', upi: 'kishan@upi' },
    { name: 'Manasa Rao', role: 'FinTech PM', upi: 'manasa@upi' },
    { name: 'Indukiran Reddy', role: 'Tech Lead', upi: 'indukiran@upi' },
    { name: 'Manjunath Hegde', role: 'Director', upi: 'manjunath@upi' }
  ].filter(c => !currentPersona?.name.includes(c.name.split(' ')[0]));

  const loadData = async () => {
    setLoading(true);
    try {
      const [spendRes, forecastRes] = await Promise.all([
        api.getSpendingSummary(undefined, selectedPeriod),
        api.getCashflowForecast()
      ]);
      setSpending(spendRes);
      setForecast(forecastRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    setTransferAlert(null);
    setTransferSuccess(null);
    setTransferError(null);
  }, [currentPersona, selectedPeriod]);

  const handleInitiateTransfer = async () => {
    const amt = parseFloat(transferAmount);
    if (isNaN(amt) || amt <= 0) {
      setTransferError('Please enter a valid positive transfer amount.');
      return;
    }
    if (!recipient.trim()) {
      setTransferError('Please enter or select a recipient name.');
      return;
    }

    setTransferError(null);
    setTransferSuccess(null);
    setIsCheckingTransfer(true);

    try {
      const checkRes = await api.checkTransfer(recipient, amt);
      if (checkRes.is_repeated) {
        // Trigger advisory alert without restricting
        setTransferAlert(checkRes);
      } else {
        // Clear to execute directly
        await executeTransferNow(recipient, amt);
      }
    } catch (err: any) {
      setTransferError('Failed to verify payee history. Please retry.');
    } finally {
      setIsCheckingTransfer(false);
    }
  };

  const executeTransferNow = async (recName: string, amt: number) => {
    try {
      setIsCheckingTransfer(true);
      const res = await api.executeTransfer(recName, amt, transferChannel);
      if (res.success) {
        setTransferSuccess(res);
        setTransferAlert(null);
        await loadData(); // refresh spending and balance
      } else {
        setTransferError(res.error || 'Transfer failed.');
      }
    } catch (err: any) {
      setTransferError('Transfer failed due to network error.');
    } finally {
      setIsCheckingTransfer(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2 text-slate-400 text-sm">
          <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
          <span>Loading verified spending analytics...</span>
        </div>
      </div>
    );
  }

  const pieData = (spending?.category_breakdown || []).map(c => ({
    name: c.category,
    value: c.amount
  }));

  const momPositive = (spending?.month_over_month_change_pct || 0) > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center space-x-2">
            <span>Spending Analytics & Instant Pay</span>
            <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Deterministic Python Accounting
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            100% verified against SQLite financial ledger • {spending?.data_window}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex bg-slate-900 border border-slate-700/80 rounded-xl p-1 text-xs">
            <button
              onClick={() => setSelectedPeriod('current_month')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                selectedPeriod === 'current_month' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Current Month
            </button>
            <button
              onClick={() => setSelectedPeriod('last_month')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                selectedPeriod === 'last_month' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Last Month
            </button>
          </div>

          <a
            href={`/api/v1/spending/export-csv?period=${selectedPeriod}`}
            className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors shadow-sm"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Spent */}
        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 relative overflow-hidden backdrop-blur shadow-lg">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
          <span className="text-xs font-medium text-slate-400 block">Total Outlays ({spending?.data_window})</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-white">
              {spending?.formatted_total_spent}
            </span>
            <div className={`flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${
              momPositive ? 'text-rose-400 bg-rose-950/40 border border-rose-500/20' : 'text-emerald-400 bg-emerald-950/40 border border-emerald-500/20'
            }`}>
              {momPositive ? <TrendingUp className="w-3.5 h-3.5 mr-1" /> : <TrendingDown className="w-3.5 h-3.5 mr-1" />}
              <span>{Math.abs(spending?.month_over_month_change_pct || 0)}% MoM</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            vs {spending?.formatted_last_month_spent} in prior month
          </p>
        </div>

        {/* Card 2: Account Balance */}
        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur shadow-lg">
          <span className="text-xs font-medium text-slate-400 block">Liquid Account Balance</span>
          <div className="mt-2 text-2xl font-bold font-mono text-emerald-400">
            ₹{(currentPersona?.balance || 0).toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
            <span>{currentPersona?.name}</span>
            <span className="text-slate-400 font-mono text-[10px]">{currentPersona?.account_number}</span>
          </p>
        </div>

        {/* Card 3: Daily Run Rate */}
        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur shadow-lg">
          <span className="text-xs font-medium text-slate-400 block">Daily Average Burn Rate</span>
          <div className="mt-2 text-2xl font-bold font-mono text-white">
            {forecast?.formatted_daily_burn_rate || '₹0'}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            {forecast?.days_remaining} days remaining in cycle
          </p>
        </div>

        {/* Card 4: Projected Month-End */}
        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur shadow-lg">
          <span className="text-xs font-medium text-slate-400 block">Projected Net Surplus</span>
          <div className="mt-2 text-2xl font-bold font-mono text-teal-300">
            {forecast?.formatted_projected_savings || '₹0'}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Projected total: {forecast?.formatted_projected_total}
          </p>
        </div>
      </div>

      {/* FEATURE SPOTLIGHT: Instant Money Transfer with Repeated Transaction Advisory */}
      <div className="p-6 rounded-3xl bg-gradient-to-b from-slate-900/95 to-slate-950 border border-slate-800 shadow-2xl relative overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-inner">
              <Send className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <span>Instant Transfer & Payee Advisory</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300">
                  Feature Active
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Transfers alert on recent duplicates to prevent double-charging, without restricting authorized transactions.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/60 px-3 py-1.5 rounded-xl border border-slate-700/60">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Advisory Window: 72 Hours</span>
          </div>
        </div>

        {/* Transfer Form Controls */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Column 1: Payee Selection */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 block">Select or Enter Recipient</label>
            <div className="relative">
              <input
                type="text"
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                placeholder="e.g. Kishan Kumar"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {demoContacts.map((c, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setRecipient(c.name)}
                  className={`text-[11px] px-2.5 py-1 rounded-lg border transition-all ${
                    recipient.toLowerCase().includes(c.name.toLowerCase().split(' ')[0])
                      ? 'bg-emerald-950/70 border-emerald-500/60 text-emerald-300'
                      : 'bg-slate-800/60 border-slate-700/60 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {c.name.split(' ')[0]} ({c.role})
                </button>
              ))}
            </div>
          </div>

          {/* Column 2: Amount & Quick Chips */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 block">Amount (₹ INR)</label>
            <div className="relative">
              <span className="absolute left-3.5 top-2.5 text-slate-500 font-semibold">₹</span>
              <input
                type="number"
                value={transferAmount}
                onChange={(e) => setTransferAmount(e.target.value)}
                placeholder="5000"
                className="w-full pl-8 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm font-mono text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {['1000', '2500', '5000', '10000'].map((amt) => (
                <button
                  key={amt}
                  type="button"
                  onClick={() => setTransferAmount(amt)}
                  className={`text-[11px] px-2.5 py-1 rounded-lg border font-mono transition-all ${
                    transferAmount === amt
                      ? 'bg-emerald-950/70 border-emerald-500/60 text-emerald-300'
                      : 'bg-slate-800/60 border-slate-700/60 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  ₹{parseInt(amt).toLocaleString('en-IN')}
                </button>
              ))}
            </div>
          </div>

          {/* Column 3: Channel & Action */}
          <div className="space-y-2 flex flex-col justify-between">
            <div>
              <label className="text-xs font-semibold text-slate-300 block">Transfer Mode</label>
              <div className="grid grid-cols-3 gap-2">
                {['UPI', 'IMPS', 'NEFT'].map((ch) => (
                  <button
                    key={ch}
                    type="button"
                    onClick={() => setTransferChannel(ch)}
                    className={`py-2 rounded-xl text-xs font-semibold border transition-all ${
                      transferChannel === ch
                        ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm'
                        : 'bg-slate-950 border-slate-700 text-slate-400 hover:text-white'
                    }`}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleInitiateTransfer}
              disabled={isCheckingTransfer || !recipient.trim() || !transferAmount}
              className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-semibold text-sm flex items-center justify-center space-x-2 transition-all shadow-lg shadow-emerald-950/50"
            >
              {isCheckingTransfer ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Verifying Payee History...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Send ₹{Number(transferAmount || 0).toLocaleString('en-IN')}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* ERROR MESSAGE */}
        {transferError && (
          <div className="mt-4 p-3 rounded-xl bg-rose-950/50 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2 animate-in fade-in">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{transferError}</span>
          </div>
        )}

        {/* SUCCESS CONFIRMATION RECEIPT */}
        {transferSuccess && (
          <div className="mt-4 p-4 rounded-2xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-200 text-xs space-y-2 animate-in fade-in">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="font-bold text-sm text-white">Payment Successful</span>
              </div>
              <span className="font-mono text-[11px] text-slate-400">Ref: #{transferSuccess.transaction_id}</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-emerald-900/60 font-mono text-[11px]">
              <div>
                <span className="text-slate-400 block text-[10px]">Recipient</span>
                <span className="text-white font-semibold">{transferSuccess.recipient}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Amount Sent</span>
                <span className="text-emerald-300 font-bold">{transferSuccess.formatted_amount}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Updated Balance</span>
                <span className="text-white">{transferSuccess.formatted_balance}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Mode</span>
                <span className="text-slate-300">{transferSuccess.channel}</span>
              </div>
            </div>
            <p className="text-[10px] text-emerald-400/80 pt-1">
              * Try transferring to {transferSuccess.recipient} again right now to see the automated repeated transaction advisory alert!
            </p>
          </div>
        )}

        {/* REPEATED TRANSACTION ADVISORY ALERT (CONFIRMS FEATURE: ALERTS BUT DOES NOT RESTRICT) */}
        {transferAlert && transferAlert.is_repeated && (
          <div className="mt-4 p-4 rounded-2xl bg-amber-950/70 border-2 border-amber-500/60 shadow-xl shadow-amber-950/40 animate-in fade-in slide-in-from-top-2">
            <div className="flex items-start space-x-3">
              <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0 mt-0.5">
                <AlertTriangle className="w-5 h-5" />
              </div>

              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-amber-200 flex items-center space-x-2">
                    <span>Repeated Transaction Alert</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      Advisory Notice Only
                    </span>
                  </h3>
                  <span className="text-[10px] text-amber-400/80 font-mono">Payee Frequency Guard</span>
                </div>

                <p className="text-xs text-amber-100/90 leading-relaxed">
                  {transferAlert.message}
                </p>

                {transferAlert.prior_transaction && (
                  <div className="p-2.5 rounded-xl bg-slate-950/70 border border-amber-500/30 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Prior Payee</span>
                      <span className="text-white font-medium">{transferAlert.prior_transaction.recipient}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Prior Amount</span>
                      <span className="text-amber-300 font-bold">{transferAlert.prior_transaction.formatted_amount}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Timestamp</span>
                      <span className="text-slate-300">{transferAlert.prior_transaction.timestamp}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Elapsed Time</span>
                      <span className="text-slate-300">{transferAlert.prior_transaction.time_ago}</span>
                    </div>
                  </div>
                )}

                {/* ADVISORY GUARANTEE: NEVER RESTRICTED */}
                <div className="p-2 rounded-lg bg-amber-900/40 border border-amber-500/20 text-[11px] text-amber-200/90 flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>
                    <strong>Non-Restrictive Guarantee:</strong> This notification is strictly informational to help avoid accidental double-taps. You retain full freedom to proceed with this transfer immediately.
                  </span>
                </div>

                {/* ACTION BUTTONS: PROCEED ANYWAY OR CANCEL */}
                <div className="flex items-center space-x-3 pt-2">
                  <button
                    onClick={() => executeTransferNow(recipient, parseFloat(transferAmount))}
                    disabled={isCheckingTransfer}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow-md shadow-emerald-950/50 transition-colors"
                  >
                    <span>Proceed Anyway (Send ₹{Number(transferAmount).toLocaleString('en-IN')})</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => setTransferAlert(null)}
                    className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-medium text-xs border border-slate-700 transition-colors"
                  >
                    Cancel Transfer
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Analytics & Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Donut */}
        <div className="lg:col-span-1 p-5 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col shadow-xl">
          <h3 className="text-sm font-semibold text-white mb-2">Category Breakdown</h3>
          <div className="h-60 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <RePieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip
                  formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Amount']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
              </RePieChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 space-y-2 max-h-40 overflow-y-auto pr-1">
            {spending?.category_breakdown.map((cat, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                  <span className="text-slate-300">{cat.category}</span>
                </div>
                <div className="font-mono text-slate-200">
                  {cat.formatted_amount} <span className="text-slate-500 text-[10px]">({cat.percentage}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Merchants & Subscriptions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Top Merchants */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl">
            <h3 className="text-sm font-semibold text-white mb-3">Top Spending Merchants</h3>
            <div className="space-y-2.5">
              {spending?.top_merchants.map((m, idx) => (
                <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center space-x-3">
                    <span className="w-6 h-6 rounded-lg bg-emerald-500/10 text-emerald-400 font-mono text-xs flex items-center justify-center font-bold">
                      {idx + 1}
                    </span>
                    <span className="text-xs font-medium text-slate-200">{m.name}</span>
                  </div>
                  <span className="text-xs font-mono font-semibold text-emerald-400">
                    {m.formatted_amount}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Recurring & Subscriptions */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl">
            <h3 className="text-sm font-semibold text-white mb-1">Detected Recurring Subscriptions</h3>
            <p className="text-xs text-slate-400 mb-3">Automatically isolated by periodic calendar intervals</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {spending?.recurring_items.map((r, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-medium text-slate-200 block">{r.merchant}</span>
                    <span className="text-[10px] text-slate-500">{r.category} • Monthly</span>
                  </div>
                  <span className="text-xs font-mono font-semibold text-white">
                    {r.formatted_amount}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
