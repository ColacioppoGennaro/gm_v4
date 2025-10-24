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

      // Check for function calls - open EventModal if AI wants to create event
      if (response.function_calls && response.function_calls.length > 0) {
        const functionCall = response.function_calls[0];

        if (functionCall.name === 'update_event_details' && onOpenEventForm) {
          // Open EventModal with AI data
          onOpenEventForm(functionCall.args || {});
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

      {/* Centered Modal - 448px wide (like prototype) */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-surface rounded-2xl shadow-2xl w-full max-w-[448px] h-[600px]"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                  <Icons.Sparkles className="h-4 w-4 text-white" />
                </div>
                <h2 className="font-semibold text-base">AI Assistant</h2>
              </div>
              <button
                onClick={() => {
                  onClose();
                  resetAssistant();
                }}
                className="p-1.5 hover:bg-gray-700 rounded-full transition-colors"
              >
                <Icons.Close className="h-4 w-4" />
              </button>
            </div>

            {/* Input at TOP */}
            <div className="p-3 border-b border-gray-700">
              <div className="flex items-center gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Scrivi un messaggio..."
                  className="flex-1 bg-background border border-gray-600 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={isLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputText.trim() || isLoading}
                  className="p-2 bg-primary rounded-full hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Icons.Send className="h-4 w-4 text-white" />
                </button>
              </div>
            </div>

            {/* Messages - scrollable */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {messages.length === 0 && (
                <div className="text-center text-text-secondary py-8">
                  <Icons.Sparkles className="h-10 w-10 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Chiedimi di creare eventi o cerca informazioni!</p>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-3 py-2 ${
                      msg.role === 'user'
                        ? 'bg-primary text-white'
                        : 'bg-background text-text-primary'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    <span className="text-xs opacity-70 mt-0.5 block">
                      {msg.timestamp.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-background rounded-2xl px-3 py-2">
                    <Icons.Spinner className="h-4 w-4 animate-spin text-primary" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Action Buttons - 3 buttons at bottom */}
            <div className="p-3 flex justify-center gap-2 border-t border-gray-700">
              <button
                onClick={() => console.log('Voice input')}
                className="flex items-center gap-1.5 px-3 py-2 bg-background hover:bg-gray-700 rounded-full transition-colors text-sm"
              >
                <Icons.Mic className="h-4 w-4 text-green-400" />
                <span>Parla</span>
              </button>

              <label className="flex items-center gap-1.5 px-3 py-2 bg-background hover:bg-gray-700 rounded-full transition-colors cursor-pointer text-sm">
                <Icons.Camera className="h-4 w-4 text-purple-400" />
                <span>Foto</span>
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={(e) => console.log('Photo:', e.target.files?.[0])}
                />
              </label>

              <button
                onClick={() => {
                  if (onOpenDocumentUpload) onOpenDocumentUpload();
                  onClose();
                }}
                className="flex items-center gap-1.5 px-3 py-2 bg-background hover:bg-gray-700 rounded-full transition-colors text-sm"
              >
                <Icons.Upload className="h-4 w-4 text-orange-400" />
                <span>File</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AIAssistant;
