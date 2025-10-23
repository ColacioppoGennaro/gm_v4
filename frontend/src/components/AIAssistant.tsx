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
}

type AssistantMode = 'idle' | 'chat' | 'voice' | 'photo' | 'document';
type IntentType = 'create_event' | 'upload_document' | 'question' | 'unknown';

const AIAssistant: React.FC<AIAssistantProps> = ({
  isOpen,
  onClose,
  onOpenEventForm,
  onOpenDocumentUpload
}) => {
  const [mode, setMode] = useState<AssistantMode>('idle');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [detectedIntent, setDetectedIntent] = useState<IntentType | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dragStartY = useRef<number>(0);
  const currentSheetY = useRef<number>(0);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when mode changes to chat
  useEffect(() => {
    if (mode === 'chat' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [mode]);

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
      // Send to AI chat endpoint
      const response = await apiService.aiChat([...messages, userMessage]);

      const aiMessage: Message = {
        role: 'ai',
        content: response.text || 'Mi dispiace, non ho capito.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);

      // Check for function calls (intent recognition)
      if (response.function_calls && response.function_calls.length > 0) {
        const functionCall = response.function_calls[0];

        if (functionCall.name === 'update_event_details') {
          setDetectedIntent('create_event');
          // Open event form with AI data
          if (onOpenEventForm) {
            onOpenEventForm(functionCall.args || {});
          }
        } else if (functionCall.name === 'save_and_close_event') {
          // Event saved, close assistant
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

  const handleVoiceStart = () => {
    setMode('voice');
    setIsRecording(true);
    // TODO: Implement Gemini Live Voice
    console.log('🎤 Voice recording started');
  };

  const handleVoiceStop = () => {
    setIsRecording(false);
    console.log('🎤 Voice recording stopped');
  };

  const handlePhotoCapture = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setMode('photo');
    setIsLoading(true);

    try {
      // Upload and analyze photo
      const response = await apiService.aiAnalyzeDocument(file);

      const aiMessage: Message = {
        role: 'ai',
        content: `Ho analizzato la foto. Tipo: ${response.document_type}. ${response.reason}`,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
      setMode('chat');

    } catch (error) {
      console.error('Photo analysis error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDocumentUpload = () => {
    setMode('document');
    if (onOpenDocumentUpload) {
      onOpenDocumentUpload();
    }
  };

  const resetAssistant = () => {
    setMode('idle');
    setMessages([]);
    setInputText('');
    setDetectedIntent(null);
    setIsLoading(false);
    setIsRecording(false);
  };

  const handleDragStart = (e: React.TouchEvent | React.MouseEvent) => {
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    dragStartY.current = clientY;
    currentSheetY.current = clientY;
  };

  const handleDragMove = (e: React.TouchEvent | React.MouseEvent) => {
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    const deltaY = clientY - dragStartY.current;

    // Only allow dragging down to close
    if (deltaY > 0) {
      currentSheetY.current = clientY;
    }
  };

  const handleDragEnd = () => {
    const deltaY = currentSheetY.current - dragStartY.current;

    // If dragged down more than 100px, close
    if (deltaY > 100) {
      onClose();
      resetAssistant();
    }
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

      {/* Bottom Sheet */}
      <div
        className={`fixed left-0 right-0 max-w-2xl mx-auto bg-surface rounded-t-3xl shadow-2xl z-50 transition-all duration-300 ${
          detectedIntent === 'create_event' ? 'top-[20%] bottom-0' : 'top-[40%] bottom-0'
        }`}
        onTouchStart={handleDragStart}
        onTouchMove={handleDragMove}
        onTouchEnd={handleDragEnd}
        onMouseDown={handleDragStart}
        onMouseMove={handleDragMove}
        onMouseUp={handleDragEnd}
      >
        {/* Drag Handle */}
        <div className="flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing">
          <div className="w-12 h-1.5 bg-gray-600 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
              <Icons.Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-lg">AI Assistant</h2>
              <p className="text-xs text-text-secondary">
                {mode === 'idle' && 'Come posso aiutarti?'}
                {mode === 'chat' && 'Chatta con me'}
                {mode === 'voice' && isRecording ? 'Sto ascoltando...' : 'Voice mode'}
                {mode === 'photo' && 'Analizza foto'}
                {mode === 'document' && 'Carica documento'}
              </p>
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

        {/* Content Area */}
        <div className="flex-1 overflow-hidden flex flex-col">

          {/* Idle State - Show 4 Buttons */}
          {mode === 'idle' && (
            <div className="flex-1 flex items-center justify-center p-6">
              <div className="grid grid-cols-2 gap-4 w-full max-w-md">

                {/* Chat Button */}
                <button
                  onClick={() => setMode('chat')}
                  className="flex flex-col items-center justify-center p-6 bg-background rounded-2xl hover:bg-gray-700 transition-colors gap-3"
                >
                  <div className="w-14 h-14 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <Icons.MessageCircle className="h-7 w-7 text-blue-400" />
                  </div>
                  <span className="font-semibold">Chat</span>
                  <span className="text-xs text-text-secondary text-center">Scrivi un messaggio</span>
                </button>

                {/* Voice Button */}
                <button
                  onClick={handleVoiceStart}
                  className="flex flex-col items-center justify-center p-6 bg-background rounded-2xl hover:bg-gray-700 transition-colors gap-3"
                >
                  <div className="w-14 h-14 bg-green-500/20 rounded-full flex items-center justify-center">
                    <Icons.Mic className="h-7 w-7 text-green-400" />
                  </div>
                  <span className="font-semibold">Voce</span>
                  <span className="text-xs text-text-secondary text-center">Parla in tempo reale</span>
                </button>

                {/* Photo Button */}
                <label className="flex flex-col items-center justify-center p-6 bg-background rounded-2xl hover:bg-gray-700 transition-colors gap-3 cursor-pointer">
                  <div className="w-14 h-14 bg-purple-500/20 rounded-full flex items-center justify-center">
                    <Icons.Camera className="h-7 w-7 text-purple-400" />
                  </div>
                  <span className="font-semibold">Foto</span>
                  <span className="text-xs text-text-secondary text-center">Scatta o carica</span>
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="hidden"
                    onChange={handlePhotoCapture}
                  />
                </label>

                {/* Document Button */}
                <button
                  onClick={handleDocumentUpload}
                  className="flex flex-col items-center justify-center p-6 bg-background rounded-2xl hover:bg-gray-700 transition-colors gap-3"
                >
                  <div className="w-14 h-14 bg-orange-500/20 rounded-full flex items-center justify-center">
                    <Icons.Upload className="h-7 w-7 text-orange-400" />
                  </div>
                  <span className="font-semibold">Documento</span>
                  <span className="text-xs text-text-secondary text-center">Carica PDF/immagine</span>
                </button>

              </div>
            </div>
          )}

          {/* Chat Mode */}
          {mode === 'chat' && (
            <div className="flex-1 flex flex-col min-h-0">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3 max-w-2xl w-full mx-auto">
                {messages.length === 0 && (
                  <div className="text-center text-text-secondary py-8">
                    <Icons.Sparkles className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Inizia a chattare! Posso aiutarti a:</p>
                    <ul className="text-sm mt-2 space-y-1">
                      <li>• Creare eventi nel calendario</li>
                      <li>• Analizzare documenti</li>
                      <li>• Rispondere a domande sui tuoi dati</li>
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

              {/* Chat Input */}
              <div className="flex-shrink-0 p-4 border-t border-gray-700 safe-area-inset-bottom">
                <div className="flex items-center gap-2 max-w-2xl w-full mx-auto">
                  <button
                    onClick={() => setMode('idle')}
                    className="p-3 bg-background rounded-full hover:bg-gray-700 transition-colors"
                  >
                    <Icons.ChevronLeft className="h-5 w-5" />
                  </button>

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
            </div>
          )}

          {/* Voice Mode */}
          {mode === 'voice' && (
            <div className="flex-1 flex flex-col items-center justify-center p-6 space-y-6">
              <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all ${
                isRecording
                  ? 'bg-red-500/20 animate-pulse'
                  : 'bg-green-500/20'
              }`}>
                <Icons.Mic className={`h-16 w-16 ${isRecording ? 'text-red-400' : 'text-green-400'}`} />
              </div>

              <div className="text-center">
                <p className="text-lg font-semibold mb-2">
                  {isRecording ? 'Sto ascoltando...' : 'Premi per parlare'}
                </p>
                <p className="text-sm text-text-secondary">
                  {inputText || 'Dì qualcosa...'}
                </p>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => setMode('idle')}
                  className="px-6 py-3 bg-background rounded-full hover:bg-gray-700 transition-colors"
                >
                  Annulla
                </button>

                <button
                  onClick={isRecording ? handleVoiceStop : handleVoiceStart}
                  className={`px-6 py-3 rounded-full transition-colors ${
                    isRecording
                      ? 'bg-red-500 hover:bg-red-600 text-white'
                      : 'bg-green-500 hover:bg-green-600 text-white'
                  }`}
                >
                  {isRecording ? 'Ferma' : 'Registra'}
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  );
};

export default AIAssistant;
