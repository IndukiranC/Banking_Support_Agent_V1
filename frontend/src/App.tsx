import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { ChatInterface } from './components/ChatInterface';
import { SpendingDashboard } from './components/SpendingDashboard';
import { FraudCentre } from './components/FraudCentre';
import { LoanNavigator } from './components/LoanNavigator';
import { GuidancePlanner } from './components/GuidancePlanner';
import { ProductCatalog } from './components/ProductCatalog';
import { RegulatoryRAG } from './components/RegulatoryRAG';
import { InvestmentHub } from './components/InvestmentHub';
import { QualityAdmin } from './components/QualityAdmin';
import { AuditLogView } from './components/AuditLogView';
import { Persona } from './types';
import { api } from './api';

export const App: React.FC = () => {
  const [currentPersona, setCurrentPersona] = useState<Persona | null>(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [aiStatus, setAiStatus] = useState({ online: true, model: 'llama3.1:latest' });

  const checkHealth = async () => {
    try {
      const data = await api.getHealth();
      setAiStatus({
        online: data.ai_engine?.ollama_available || false,
        model: data.ai_engine?.target_model || 'llama3.1:latest'
      });
    } catch {
      setAiStatus({ online: false, model: 'Offline' });
    }
  };

  const initPersona = async () => {
    try {
      const personas = await api.getPersonas();
      if (personas.length > 0) {
        const defaultPersona = personas[0]; // Rajesh Sharma (Salaried)
        setCurrentPersona(defaultPersona);
        await api.switchPersona(defaultPersona.id);
      }
    } catch (e) {
      console.error('Error loading default persona:', e);
    }
  };

  useEffect(() => {
    checkHealth();
    initPersona();
  }, []);

  const handleSelectPersona = async (persona: Persona) => {
    setCurrentPersona(persona);
    await api.switchPersona(persona.id);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        currentPersona={currentPersona}
        onSelectPersona={handleSelectPersona}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        aiStatus={aiStatus}
        onRefreshHealth={checkHealth}
      />

      <main className="flex-1 overflow-x-hidden">
        {activeTab === 'chat' && (
          <ChatInterface currentPersona={currentPersona} onNavigateTab={setActiveTab} />
        )}
        {activeTab === 'dashboard' && (
          <SpendingDashboard currentPersona={currentPersona} />
        )}
        {activeTab === 'fraud' && (
          <FraudCentre currentPersona={currentPersona} />
        )}
        {activeTab === 'loans' && (
          <LoanNavigator currentPersona={currentPersona} />
        )}
        {activeTab === 'guidance' && (
          <GuidancePlanner currentPersona={currentPersona} />
        )}
        {activeTab === 'products' && (
          <ProductCatalog currentPersona={currentPersona} />
        )}
        {activeTab === 'rag' && (
          <RegulatoryRAG />
        )}
        {activeTab === 'investments' && (
          <InvestmentHub currentPersona={currentPersona} />
        )}
        {activeTab === 'quality' && (
          <QualityAdmin />
        )}
        {activeTab === 'audit' && (
          <AuditLogView />
        )}
      </main>
    </div>
  );
};

export default App;
