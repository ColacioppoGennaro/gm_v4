import React, { useState, useRef, useEffect } from 'react';
import { Icons } from './Icons';
import { apiService } from '../services/apiService';

interface Message {
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

interface AIAssistantProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenEventForm?: (data: any) => void;
  onOpenDocumentUpload?: () => void;
  events?: any[];
}

const AIAssistant: React.FC<AIAssistantProps> = ({
  isOpen,
  onClose,
  onOpenEventForm,
  onOpenDocumentUpload,
  events = []
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [eventData, setEventData] = useState<any>(null);
  const [showEventForm, setShowEventForm] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await apiService.aiChat([...messages, userMessage], events);

      const aiMessage: Message = {
        role: 'ai',
        content: response.text || 'Mi dispiace, non ho capito.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);

      // Check for function calls
      if (response.function_calls && response.function_calls.length > 0) {
        const functionCall = response.function_calls[0];

        if (functionCall.name === 'update_event_details') {
          // Update event data and show form
          setEventData((prev: any) => ({
            ...prev,
            ...functionCall.args
          }));
          setShowEventForm(true);
        } else if (functionCall.name === 'save_and_close_event') {
          // Save event
          if (eventData && onOpenEventForm) {
            onOpenEventForm(eventData);
          }
          setTimeout(() => {
            onClose();
            resetAssistant();
          }, 1000);
        }
      }

    } catch (error: any) {
      const errorMessage: Message = {
        role: 'ai',
        content: 'Mi dispiace, si è verificato un errore. Riprova.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      console.error('AI Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceInput = () => {
    // TODO: Implement voice input
    console.log('Voice input');
  };

  const handlePhotoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    console.log('Photo upload:', file);
    // TODO: Implement photo analysis
  };

  const handleDocumentUpload = () => {
    if (onOpenDocumentUpload) {
      onOpenDocumentUpload();
    }
    onClose();
  };

  const resetAssistant = () => {
    setMessages([]);
    setInputText('');
    setEventData(null);
    setShowEventForm(false);
    setIsLoading(false);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
        onClick={() => {
          onClose();
          resetAssistant();
        }}
      />

      {/* Centered Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className={`bg-surface rounded-2xl shadow-2xl w-full max-w-2xl transition-all duration-300 ${
            showEventForm ? 'h-[90vh]' : 'h-[70vh]'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                  <Icons.Sparkles className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="font-bold text-lg">AI Assistant</h2>
                  <p className="text-xs text-text-secondary">Come posso aiutarti?</p>
                </div>
              </div>
              <button
                onClick={() => {
                  onClose();
                  resetAssistant();
                }}
                className="p-2 hover:bg-gray-700 rounded-full transition-colors"
              >
                <Icons.Close className="h-5 w-5" />
              </button>
            </div>

            {/* Chat Section - compresses when form shows */}
            <div className={`flex flex-col ${showEventForm ? 'h-[45%]' : 'flex-1'} border-b border-gray-700`}>
              {/* Input at TOP */}
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Scrivi un messaggio..."
                    className="flex-1 bg-background border border-gray-600 rounded-full px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary"
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputText.trim() || isLoading}
                    className="p-3 bg-primary rounded-full hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Icons.Send className="h-5 w-5 text-white" />
                  </button>
                </div>
              </div>

              {/* Messages - scrollable, max 5-6 lines visible */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 && (
                  <div className="text-center text-text-secondary py-8">
                    <Icons.Sparkles className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Inizia a chattare! Posso aiutarti a:</p>
                    <ul className="text-sm mt-2 space-y-1">
                      <li>• Creare eventi nel calendario</li>
                      <li>• Rispondere a domande sui tuoi dati</li>
                      <li>• Analizzare documenti</li>
                    </ul>
                  </div>
                )}

                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        msg.role === 'user'
                          ? 'bg-primary text-white'
                          : 'bg-background text-text-primary'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      <span className="text-xs opacity-70 mt-1 block">
                        {msg.timestamp.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-background rounded-2xl px-4 py-3">
                      <Icons.Spinner className="h-5 w-5 animate-spin text-primary" />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Action Buttons - always visible at bottom of chat section */}
              <div className="p-4 flex justify-center gap-3 border-t border-gray-700">
                <button
                  onClick={handleVoiceInput}
                  className="flex items-center gap-2 px-4 py-2 bg-background hover:bg-gray-700 rounded-full transition-colors"
                >
                  <Icons.Mic className="h-5 w-5 text-green-400" />
                  <span className="text-sm">Voce</span>
                </button>

                <label className="flex items-center gap-2 px-4 py-2 bg-background hover:bg-gray-700 rounded-full transition-colors cursor-pointer">
                  <Icons.Camera className="h-5 w-5 text-purple-400" />
                  <span className="text-sm">Foto</span>
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="hidden"
                    onChange={handlePhotoUpload}
                  />
                </label>

                <button
                  onClick={handleDocumentUpload}
                  className="flex items-center gap-2 px-4 py-2 bg-background hover:bg-gray-700 rounded-full transition-colors"
                >
                  <Icons.Upload className="h-5 w-5 text-orange-400" />
                  <span className="text-sm">File</span>
                </button>
              </div>
            </div>

            {/* Event Form - appears below when triggered */}
            {showEventForm && eventData && (
              <div className="flex-1 overflow-y-auto p-4 bg-background">
                <div className="space-y-3">
                  <div className="flex items-center gap-2 mb-3">
                    <Icons.Calendar className="h-5 w-5 text-primary" />
                    <span className="font-semibold text-primary">Creazione Evento</span>
                  </div>

                  {/* Title */}
                  <div>
                    <label className="text-xs text-text-secondary block mb-1">Titolo</label>
                    <input
                      type="text"
                      value={eventData.title || ''}
                      onChange={(e) => setEventData({...eventData, title: e.target.value})}
                      className="w-full bg-surface border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="Inserisci titolo..."
                    />
                  </div>

                  {/* Date/Time */}
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-text-secondary block mb-1">Data inizio</label>
                      <input
                        type="datetime-local"
                        value={eventData.start_datetime ? eventData.start_datetime.slice(0, 16) : ''}
                        onChange={(e) => setEventData({...eventData, start_datetime: e.target.value + ':00'})}
                        className="w-full bg-surface border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-text-secondary block mb-1">Data fine</label>
                      <input
                        type="datetime-local"
                        value={eventData.end_datetime ? eventData.end_datetime.slice(0, 16) : ''}
                        onChange={(e) => setEventData({...eventData, end_datetime: e.target.value + ':00'})}
                        className="w-full bg-surface border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      />
                    </div>
                  </div>

                  {/* Amount */}
                  <div>
                    <label className="text-xs text-text-secondary block mb-1">Importo €</label>
                    <input
                      type="number"
                      step="0.01"
                      value={eventData.amount || ''}
                      onChange={(e) => setEventData({...eventData, amount: parseFloat(e.target.value)})}
                      className="w-full bg-surface border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="0.00"
                    />
                  </div>

                  {/* Description */}
                  <div>
                    <label className="text-xs text-text-secondary block mb-1">Descrizione</label>
                    <textarea
                      value={eventData.description || ''}
                      onChange={(e) => setEventData({...eventData, description: e.target.value})}
                      className="w-full bg-surface border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                      rows={3}
                      placeholder="Inserisci descrizione..."
                    />
                  </div>

                  <div className="text-xs text-text-secondary italic">
                    Categoria, colore e promemoria li aggiungerai dopo conferma
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default AIAssistant;
