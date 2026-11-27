import React, { useState, useEffect } from 'react';
import {
  Award, ShieldCheck, CheckCircle2, XCircle, AlertCircle,
  CreditCard, Landmark, DollarSign, ChevronRight, Info
} from 'lucide-react';
import { ProductMatches, Persona } from '../types';
import { api } from '../api';

interface ProductCatalogProps {
  currentPersona: Persona | null;
}

export const ProductCatalog: React.FC<ProductCatalogProps> = ({ currentPersona }) => {
  const [matches, setMatches] = useState<ProductMatches | null>(null);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const loadMatches = async () => {
    setLoading(true);
    try {
      const res = await api.getProductRecommendations(selectedFilter === 'all' ? undefined : selectedFilter);
      setMatches(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMatches();
  }, [selectedFilter, currentPersona]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Transparent Product Recommendations</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Rule-based eligibility underwriting • Zero hidden sponsored ranking
          </p>
        </div>

        {/* Category Filters */}
        <div className="flex bg-slate-900 border border-slate-700/80 rounded-xl p-1 text-xs">
          {['all', 'credit_card', 'loan', 'fixed_deposit'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedFilter(cat)}
              className={`px-3 py-1.5 rounded-lg font-medium capitalize transition-colors ${
                selectedFilter === cat ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Recommended Products Grid */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Eligible Matches ({matches?.recommended_products.length || 0})</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {matches?.recommended_products.map((prod) => (
            <div
              key={prod.product_code}
              className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between hover:border-emerald-500/40 transition-all shadow-lg"
            >
              <div>
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-base font-bold text-white">{prod.name}</h3>
                    <span className="text-[11px] font-mono text-emerald-400 uppercase">{prod.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      Fit: {prod.fit_score}/100
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 mt-3 leading-relaxed">{prod.description}</p>

                <div className="mt-4 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Pricing / Rate:</span>
                    <span className="font-semibold text-slate-200">{prod.interest_rate_or_fee}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Reward Rate:</span>
                    <span className="font-semibold text-emerald-400">{prod.reward_rate}</span>
                  </div>
                </div>

                {/* Why it fits */}
                <div className="mt-3.5 pt-3 border-t border-slate-800/80">
                  <span className="text-[11px] font-semibold text-slate-400 block mb-1">Why this fits your profile:</span>
                  <p className="text-xs text-emerald-300/90 bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-500/20">
                    {prod.fit_reason}
                  </p>
                </div>

                {prod.caveats && (
                  <div className="mt-2 text-[10px] text-slate-400 flex items-start space-x-1.5">
                    <Info className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                    <span>Caveat: {prod.caveats}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Excluded Products (Full Transparency) */}
      {matches?.excluded_products && matches.excluded_products.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <h2 className="text-sm font-semibold text-slate-400 flex items-center space-x-2">
            <XCircle className="w-4 h-4 text-slate-500" />
            <span>Excluded Products & Underwriting Rationale ({matches.excluded_products.length})</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {matches.excluded_products.map((ex) => (
              <div key={ex.product_code} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs">
                <div className="flex justify-between items-center mb-1.5">
                  <span className="font-semibold text-slate-300">{ex.name}</span>
                  <span className="text-[10px] text-slate-500 uppercase">{ex.category}</span>
                </div>
                <div className="text-rose-400/90 text-[11px] space-y-1">
                  {ex.exclusion_reasons.map((r, idx) => (
                    <div key={idx} className="flex items-start space-x-1.5">
                      <span className="text-rose-500">•</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
