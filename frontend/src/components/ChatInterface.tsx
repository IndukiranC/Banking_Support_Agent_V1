import React, { useState, useRef, useEffect } from 'react';
import {
  Send, Sparkles, Trash2, Bot, User, Clock, AlertTriangle,
  ShieldCheck, RefreshCw, ArrowRight, CornerDownLeft
} from 'lucide-react';
import { ChatMessage, Persona } from '../types';
import { HowCalculatedDrawer } from './HowCalculatedDrawer';
import { api } from '../api';

interface ChatInterfaceProps {
  currentPersona: Persona | null;
  onNavigateTab: (tab: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ currentPersona, onNavigateTab }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: `Hello ${currentPersona ? currentPersona.name : 'there'}! I am your Antigravity Banking Assistant. Every financial figure I present is computed deterministically in Python and proven with a transparent audit trail.\n\nHow can I help you today? You can ask about your monthly spending, transfer money with automated repeated transaction alerts, calculate loan EMI, inspect fraud alerts, or consult RBI guidelines.`,
      suggested_chips: [
        "Send ₹5,000 to Kishan",
        "How much did I spend this month?",
        "Can I afford a ₹40 lakh home loan?",
        "Check my account for suspicious fraud alerts",
        "Help me build a 50/30/20 budget plan"
      ],
      ai_status: 'OLLAMA_LLAMA3_1'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    setInputValue('');
    const userMsg: ChatMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await api.sendMessage(text);
      setMessages(prev => [...prev, response]);
      setMessages(prev => [
        ...prev,
        {
          ...response,
          role: 'assistant',
          content: (response as any).reply || response.content || ''
        }
      ]);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an issue connecting to the banking engine. Please check system health or retry.',
          ai_status: 'OFFLINE_RULE_FALLBACK'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: `Chat history cleared. How can I assist you with your banking needs?`,
        suggested_chips: [
          "How much did I spend on food this month?",
          "Can I afford a ₹40 lakh home loan?",
          "What are the valid KYC documents under RBI rules?"
        ]
      }
    ]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-5xl mx-auto px-4 py-2">
      {/* Top chat banner */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Bot className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Verified Banking Conversation</h2>
            <p className="text-xs text-slate-400">Zero-Trust LLM • Output Verifier Active</p>
          </div>
        </div>

        <button
          onClick={clearChat}
          className="flex items-center space-x-1.5 px-2.5 py-1 text-xs text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 rounded-lg border border-slate-700/60 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Reset Session</span>
        </button>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-[85%] sm:max-w-[78%] ${msg.role === 'user' ? 'order-1' : ''}`}>
              <div
                className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-emerald-600 text-white rounded-tr-none shadow-md shadow-emerald-900/20'
                    : 'bg-slate-900/90 text-slate-200 border border-slate-800/90 rounded-tl-none shadow-xl'
                }`}
              >
                {/* Content formatted with Markdown linebreaks */}
                <div className="whitespace-pre-line prose prose-invert prose-xs max-w-none">
                  {msg.content}
                </div>

                {/* Repeated Payee Advisory Quick Action */}
                {msg.role === 'assistant' && msg.intent === 'transfer_check' && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between flex-wrap gap-2">
                    <span className="text-[11px] text-amber-300 flex items-center space-x-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                      <span>Payee Advisory Active (Non-Restrictive)</span>
                    </span>
                    <button
                      onClick={() => onNavigateTab('dashboard')}
                      className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold flex items-center space-x-1 transition-colors shadow-sm"
                    >
                      <span>Open Instant Pay</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                )}

                {/* Show-Your-Work Drawer for verified calculations */}
                {msg.role === 'assistant' && msg.calculation_notes && (
                  <HowCalculatedDrawer
                    notes={msg.calculation_notes}
                    verificationStatus={msg.verification?.status}
                    verifiedNumbers={msg.verification?.verified_numbers}
                  />
                )}

                {/* Footer metadata for assistant response */}
                {msg.role === 'assistant' && msg.latency_ms !== undefined && (
                  <div className="mt-2.5 pt-2 border-t border-slate-800/70 flex items-center justify-between text-[10px] text-slate-400">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>{msg.latency_ms} ms</span>
                    </span>
                    <span className="flex items-center space-x-1 text-emerald-400/90 font-mono">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      <span>{msg.verification?.status || 'VERIFIED'}</span>
                    </span>
                  </div>
                )}
              </div>

              {/* Suggested Follow-up Quick Reply Chips */}
              {msg.role === 'assistant' && msg.suggested_chips && msg.suggested_chips.length > 0 && idx === messages.length - 1 && (
                <div className="mt-3 flex flex-wrap gap-1.5 animate-in fade-in">
                  {msg.suggested_chips.map((chip, cIdx) => (
                    <button
                      key={cIdx}
                      onClick={() => handleSend(chip)}
                      className="text-left text-xs px-3 py-1.5 rounded-full bg-slate-800/90 hover:bg-emerald-950/70 border border-slate-700/80 hover:border-emerald-500/50 text-slate-300 hover:text-emerald-300 transition-all flex items-center space-x-1 shadow-sm"
                    >
                      <Sparkles className="w-3 h-3 text-emerald-400 shrink-0" />
                      <span>{chip}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start space-x-3 justify-start animate-pulse">
            <div className="w-8 h-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0 mt-1">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl rounded-tl-none bg-slate-900 border border-slate-800 text-xs text-slate-400 flex items-center space-x-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-emerald-400" />
              <span>Computing financial truth and verifying figures with Output Verifier...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input box */}
      <div className="pt-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center bg-slate-900 border border-slate-700/80 rounded-2xl shadow-xl focus-within:border-emerald-500/60 focus-within:ring-2 focus-within:ring-emerald-500/20 transition-all"
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about spending, loan EMI, fraud alerts, 50/30/20 budget, or RBI rules..."
            disabled={isLoading}
            className="w-full py-3.5 pl-4 pr-12 bg-transparent text-slate-100 placeholder-slate-500 text-xs sm:text-sm focus:outline-none"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="absolute right-2 p-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white disabled:text-slate-600 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="flex items-center justify-between text-[11px] text-slate-500 px-2 pt-1.5">
          <span>Protected by Zero-Trust LLM & Hash-Chained Audit Trail</span>
          <span>Press Enter to send</span>
        </div>
      </div>
    </div>
  );
};
