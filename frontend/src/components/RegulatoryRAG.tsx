import React, { useState, useEffect } from 'react';
import {
  BookOpen, Search, ShieldCheck, ExternalLink, CheckCircle2,
  AlertCircle, FileText, ChevronRight, CornerDownLeft
} from 'lucide-react';
import { RegulatoryResult } from '../types';
import { api } from '../api';

export const RegulatoryRAG: React.FC = () => {
  const [query, setQuery] = useState('What are valid KYC documents under RBI rules?');
  const [result, setResult] = useState<RegulatoryResult | null>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const executeSearch = async (searchQuery?: string) => {
    const q = (searchQuery || query).trim();
    if (!q) return;

    setLoading(true);
    try {
      const res = await api.searchKnowledge(q);
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeSearch();
    api.getKnowledgeDocuments().then(setDocuments).catch(console.error);
  }, []);

  const sampleQueries = [
    "What are Officially Valid Documents (OVD) for KYC?",
    "How frequently does RBI mandate periodic KYC updation?",
    "What is the deposit insurance limit under DICGC?",
    "What is the bank grievance redressal timeline before Ombudsman?",
    "What is the Cash Transaction Report CTR threshold?"
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Regulatory Clarity & Official RAG Corpus</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Authoritative retrieval over curated RBI Master Directions, PMLA, DICGC, and Ombudsman frameworks
        </p>
      </div>

      {/* Search Input Box */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-700/80 shadow-xl space-y-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            executeSearch();
          }}
          className="relative flex items-center"
        >
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search RBI KYC guidelines, AML/PMLA thresholds, DICGC limits..."
            className="w-full py-3 pl-10 pr-24 bg-slate-950 border border-slate-700 rounded-xl text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {/* Quick query chips */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {sampleQueries.map((sq, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(sq);
                executeSearch(sq);
              }}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* RAG Search Results */}
      {result && (
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-400">Search Confidence & Grounding</span>
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                result.is_grounded
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
              }`}>
                {result.is_grounded ? `Grounded (${result.confidence * 100}%)` : 'Out of Corpus / Refused'}
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">{result.official_source_notice}</p>
          </div>

          {/* Citations List */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-white">Statutory Citations & Source Sections</h3>
            {result.citations.map((cite, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold text-white">{cite.document}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-emerald-300">
                    {cite.section}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                  "{cite.text}"
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Curated Documents Directory */}
      <div className="pt-4 border-t border-slate-800 space-y-3">
        <h3 className="text-sm font-semibold text-white">Curated Regulatory Statutory Library</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {documents.map((doc) => (
            <div key={doc.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
              <div className="flex justify-between items-start">
                <h4 className="font-semibold text-slate-200">{doc.title}</h4>
                <span className="text-[10px] text-slate-500 shrink-0 font-mono">v{doc.version}</span>
              </div>
              <div className="text-[11px] text-slate-400 flex items-center justify-between">
                <span>Effective Date: {doc.effective_date}</span>
                {doc.source_url && (
                  <a href={doc.source_url} target="_blank" rel="noreferrer" className="text-emerald-400 flex items-center space-x-1 hover:underline">
                    <span>RBI Portal</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
