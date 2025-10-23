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
          // Open EventModal directly with AI data
          if (onOpenEventForm) {
            onOpenEventForm(functionCall.args || {});
          }
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
          className="bg-surface rounded-2xl shadow-2xl w-full max-w-2xl h-[70vh]"
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

            {/* Chat Section */}
            <div className="flex flex-col flex-1">
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
          </div>
        </div>
      </div>
    </>
  );
};

export default AIAssistant;
