import React, { useState, useEffect } from 'react';
import {
  ShieldCheck, Cpu, User, ChevronDown, RefreshCw, AlertCircle, Sparkles,
  PieChart, MessageSquare, ShieldAlert, Landmark, Compass, Award,
  BookOpen, TrendingUp, CheckCircle, Database
} from 'lucide-react';
import { Persona } from '../types';
import { api } from '../api';

interface NavbarProps {
  currentPersona: Persona | null;
  onSelectPersona: (persona: Persona) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  aiStatus: { online: boolean; model: string };
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentPersona,
  onSelectPersona,
  activeTab,
  setActiveTab,
  aiStatus,
  onRefreshHealth
}) => {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [showPersonaMenu, setShowPersonaMenu] = useState(false);

  useEffect(() => {
    api.getPersonas().then(setPersonas).catch(console.error);
  }, []);

  const navItems = [
    { id: 'chat', label: 'AI Banking Chat', icon: MessageSquare, badge: 'Llama 3.1' },
    { id: 'dashboard', label: 'Spending & Cashflow', icon: PieChart },
    { id: 'fraud', label: 'Fraud Centre', icon: ShieldAlert, badge: 'Hero' },
    { id: 'loans', label: 'Loan Navigator', icon: Landmark },
    { id: 'guidance', label: '50/30/20 Guidance', icon: Compass },
    { id: 'products', label: 'Product Matches', icon: Award },
    { id: 'rag', label: 'Regulatory RAG', icon: BookOpen },
    { id: 'investments', label: 'Investment Hub', icon: TrendingUp },
    { id: 'quality', label: 'Quality & Evals', icon: CheckCircle, badge: '10/10' },
    { id: 'audit', label: 'Audit Trail', icon: Database }
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      {/* Top Bar */}
      <div className="max-w-7xl mx-auto px-4 py-2.5 flex flex-wrap items-center justify-between gap-4">
        {/* Logo & Tagline */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white">Antigravity Banking</span>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                10/10 Verified
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Private by design • Correct by construction • Explainable by default
            </p>
          </div>
        </div>

        {/* Status Indicators & Persona Switcher */}
        <div className="flex items-center space-x-3">
          {/* AI Status Badge */}
          <button
            onClick={onRefreshHealth}
            title="Click to check Ollama connectivity"
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              aiStatus.online
                ? 'bg-emerald-950/50 border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/40'
                : 'bg-amber-950/50 border-amber-500/30 text-amber-300 hover:bg-amber-900/40'
            }`}
          >
            <div className={`w-2 h-2 rounded-full ${aiStatus.online ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            <Cpu className="w-3.5 h-3.5" />
            <span>
              {aiStatus.online ? `Ollama (${aiStatus.model})` : 'AI Offline (Rule Fallback)'}
            </span>
            <RefreshCw className="w-3 h-3 text-slate-400 ml-1 hover:rotate-180 transition-transform" />
          </button>

          {/* Persona Switcher Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowPersonaMenu(!showPersonaMenu)}
              className="flex items-center space-x-2.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-slate-200 transition-colors"
            >
              <div className="w-5 h-5 rounded-full bg-emerald-600/30 text-emerald-400 flex items-center justify-center font-bold text-[10px]">
                {currentPersona?.name.charAt(0) || 'U'}
              </div>
              <div className="text-left">
                <span className="font-semibold block leading-tight">{currentPersona?.name || 'Select Persona'}</span>
                <span className="text-[10px] text-slate-400 block">{currentPersona?.persona_type || 'User'}</span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {showPersonaMenu && (
              <div className="absolute right-0 mt-2 w-72 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 py-1.5 overflow-hidden animate-in fade-in slide-in-from-top-2">
                <div className="px-3 py-2 border-b border-slate-800">
                  <p className="text-xs font-semibold text-slate-300">Switch Demo Persona</p>
                  <p className="text-[11px] text-slate-400">Instantly inspect 12-month transaction mix & risk baselines</p>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {personas.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        onSelectPersona(p);
                        setShowPersonaMenu(false);
                      }}
                      className={`w-full px-3 py-2.5 text-left text-xs flex items-center justify-between hover:bg-slate-800/80 transition-colors ${
                        currentPersona?.id === p.id ? 'bg-emerald-950/40 border-l-2 border-emerald-500' : ''
                      }`}
                    >
                      <div>
                        <div className="font-medium text-slate-200">{p.name}</div>
                        <div className="text-[10px] text-slate-400">{p.persona_type} • Score: {p.credit_score}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-emerald-400 text-xs">₹{(p.balance).toLocaleString('en-IN')}</div>
                        <div className="text-[10px] text-slate-400">{p.account_number}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Module Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 flex space-x-1 overflow-x-auto scrollbar-none py-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-2 px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
              {item.badge && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${
                  isActive ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </header>
  );
};
