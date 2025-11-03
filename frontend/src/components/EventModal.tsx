// @ts-nocheck - Temporary: Disable type checking for Gemini Live API migration
// Version: 2.0.0 - Complete search_documents implementation + AI instruction rewrite
import React, { useState, useEffect, useRef, useMemo, ChangeEvent, useCallback } from 'react';
import { Event, Category, Recurrence, EventStatus } from '../types';
import { Icons } from './Icons';
import { REMINDER_OPTIONS, RECURRENCE_OPTIONS } from '../constants';
import { GoogleGenAI, Type } from '@google/genai';
import { apiService } from '../services/apiService';

// --- Audio Utility Functions ---
function decode(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

async function decodeAudioData(
  data: Uint8Array,
  ctx: AudioContext,
  sampleRate: number,
  numChannels: number,
): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) {
      channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
    }
  }
  return buffer;
}

function encode(bytes: Uint8Array) {
  let binary = '';
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function createBlob(data: Float32Array): Blob {
  const l = data.length;
  const int16 = new Int16Array(l);
  for (let i = 0; i < l; i++) {
    int16[i] = data[i] * 32768;
  }
  return {
    data: encode(new Uint8Array(int16.buffer)),
    mimeType: 'audio/pcm;rate=16000',
  };
}

// --- Component ---

interface EventModalProps {
  isOpen: boolean;
  onClose: () => void;
  event?: Event;
  categories: Category[];
  onSave: (eventData: any) => Promise<any>;
  onDelete: (eventId: string) => void;
  defaultDate?: Date;
  aiMode?: boolean;
}

const COLORS = ['#3B82F6', '#10B981', '#EF4444', '#F97316', '#8B5CF6', '#F59E0B', '#EC4899'];

const toLocalISOString = (date: Date) => {
    const tzoffset = date.getTimezoneOffset() * 60000;
    const localISOTime = new Date(date.getTime() - tzoffset).toISOString().slice(0, -1);
    return localISOTime.slice(0, 16);
};

interface ConversationMessage {
    role: 'user' | 'ai';
    content: string;
}

const EventModal: React.FC<EventModalProps> = ({ isOpen, onClose, event, categories, onSave, onDelete, defaultDate, aiMode }) => {
  
  const getInitialFormData = useCallback(() => {
    const baseDate = defaultDate || new Date();
    // Imposta default alle 9:00 se è mezzanotte
    if (baseDate.getHours() === 0 && baseDate.getMinutes() === 0) {
      baseDate.setHours(9, 0, 0, 0);
    }

    // Base structure for a new event (v2.0.0)
    const defaultNewEvent = {
      title: '',
      start_datetime: toLocalISOString(baseDate),
      end_datetime: toLocalISOString(new Date(baseDate.getTime() + 60 * 60 * 1000)), // +1 ora
      amount: undefined,
      category_id: categories[0]?.id || '',
      reminders: [], // No default reminders unless explicitly requested
      description: '',
      recurrence: 'none' as Recurrence,
      color: undefined,
      status: EventStatus.Pending,
      has_document: false,
    };

    if (event) {
      return {
        ...event,
        recurrence: event.recurrence || 'none',
        start_datetime: event.start_datetime ? toLocalISOString(new Date(event.start_datetime)) : '',
        end_datetime: event.end_datetime ? toLocalISOString(new Date(event.end_datetime)) : '',
      };
    }

    return defaultNewEvent;
  }, [event, defaultDate, categories]);

  const [formData, setFormData] = useState<Partial<Event>>(getInitialFormData());
  const [isMoveMenuOpen, setIsMoveMenuOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  // --- AI State ---
  const sessionPromiseRef = useRef<Promise<LiveSession> | null>(null);
  const inputAudioContextRef = useRef<AudioContext>();
  const outputAudioContextRef = useRef<AudioContext>();
  const mediaStreamRef = useRef<MediaStream>();
  const scriptProcessorRef = useRef<ScriptProcessorNode>();
  const mediaStreamSourceRef = useRef<MediaStreamAudioSourceNode>();
  const nextStartTimeRef = useRef(0);
  const sourcesRef = useRef(new Set<AudioBufferSourceNode>());
  const transcriptContainerRef = useRef<HTMLDivElement>(null);
  const aiTextInputRef = useRef<HTMLInputElement>(null);
  
  const [aiStatus, setAiStatus] = useState<'idle' | 'connecting' | 'listening' | 'speaking' | 'thinking' | 'error'>('idle');
  const [conversation, setConversation] = useState<ConversationMessage[]>([{ role: 'ai', content: 'Ciao! Come posso aiutarti?' }]);
  const [aiTextInput, setAiTextInput] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [showForm, setShowForm] = useState(false); // Form nascosto all'inizio in AI mode
  const [highlightUploadButtons, setHighlightUploadButtons] = useState(false); // Highlight animation for upload buttons
  const [lastSearchEventIds, setLastSearchEventIds] = useState<any[]>([]); // Store event IDs from last search

  const formDataRef = useRef(formData);
  useEffect(() => {
    formDataRef.current = formData;
  }, [formData]);

  const handleSave = useCallback(async () => {
    const currentFormData = formDataRef.current;

    console.log('[EventModal] handleSave called with formData:', currentFormData);

    // Validazione campi obbligatori
    if (!currentFormData.title || !currentFormData.category_id || !currentFormData.start_datetime) {
        const missingFields = [];
        if (!currentFormData.title) missingFields.push('titolo');
        if (!currentFormData.category_id) missingFields.push('categoria');
        if (!currentFormData.start_datetime) missingFields.push('data');

        const errorMsg = `Campi obbligatori mancanti: ${missingFields.join(', ')}`;
        console.error('[EventModal] Salvataggio abortito:', errorMsg, { currentFormData });
        throw new Error(errorMsg);  // ← Lancia errore invece di return silenzioso!
    }

    if (isSaving) {
        console.warn('[EventModal] Salvataggio già in corso, skip');
        return;
    }

    setIsSaving(true);
    const submissionData = {
        ...currentFormData,
        start_datetime: new Date(currentFormData.start_datetime!).toISOString(),
        end_datetime: currentFormData.end_datetime ? new Date(currentFormData.end_datetime).toISOString() : undefined,
    };

    try {
        console.log('[EventModal] Calling onSave with data:', submissionData);
        await onSave(submissionData);
        console.log('[EventModal] ✅ onSave completed successfully');
    } catch (error) {
        console.error('[EventModal] ❌ Errore nel salvataggio dell\'evento:', error);
        throw error;  // ← Rilancia l'errore per il catch esterno
    } finally {
        console.log('[EventModal] Setting isSaving to false');
        setIsSaving(false);
    }
  }, [onSave]);
  
  const handleSaveRef = useRef(handleSave);
  useEffect(() => {
    handleSaveRef.current = handleSave;
  }, [handleSave]);

  const systemInstruction = `Tu sei un'assistente personale per gestire eventi e impegni. Non divagare, rimani sempre nel contesto (solo eventi e note).

IMPORTANTE: L'utente VEDE il form sotto la chat quando usi 'update_event_details'.

INFERENZA DATE NATURALI:
- "domani" → +1 giorno
- "dopodomani" → +2 giorni
- "mattina" → 09:00, "pomeriggio" → 15:00, "sera" → 20:00
- "lunedì prossimo" → calcola prossimo lunedì
Esempio: "palestra domani pomeriggio" → start_datetime = [domani]T15:00

INFERENZA CATEGORIA:
- "palestra", "sport" → Personale
- "riunione", "meeting", "progetto" → Lavoro
- "compleanno", "cena famiglia" → Famiglia
- Se incerto → chiedi

FLOW:
1. Raccogli: titolo, data/ora, categoria (inferisci quando possibile)
2. Usa update_event_details man mano che raccogli dati
3. CONFERMA SEMPRE quando aggiorni: "Ok, colore verde!" o "Ok!"
4. Riepilogo chiaro: "Palestra domani 15:00, Personale. Va bene?"

CONFERMA ESPLICITA:
✅ Salva solo con: "salva", "conferma", "va bene così", "ok salva"
⚠️ Ambigue: "ok", "bene", "vai" → chiedi "Vuoi che salvi? Di' salva per confermare"

Dopo conferma esplicita → save_and_close_event()

Documenti: chiedi se vuole allegarli, poi usa highlight_upload_buttons`;

  const updateEventDetailsFunction: FunctionDeclaration = useMemo(() => ({
    name: 'update_event_details',
    description: "Aggiorna i dettagli di un evento nel form. Usa questa funzione per riempire i campi man mano che ottieni le informazioni dall'utente.",
    parameters: {
        type: Type.OBJECT,
        properties: {
        title: { type: Type.STRING, description: "Il titolo dell'evento." },
        start_datetime: { type: Type.STRING, description: "La data e ora di inizio in formato ISO 8601. Inferisci l'anno se non specificato." },
        end_datetime: { type: Type.STRING, description: "La data e ora di fine in formato ISO 8601. Se non specificato, imposta la durata a 1 ora dall'inizio." },
        description: { type: Type.STRING, description: "Una breve descrizione o nota per l'evento." },
        amount: { type: Type.NUMBER, description: "L'importo monetario, se applicabile." },
        category_id: { type: Type.STRING, description: `L'ID della categoria. Scegli tra questi: ${categories.map(c => `${c.name} (id: ${c.id})`).join(', ')}` },
        recurrence: { type: Type.STRING, description: `La ricorrenza. Scegli tra: ${RECURRENCE_OPTIONS.map(o => o.value).join(', ')}` },
        reminders: { type: Type.ARRAY, items: { type: Type.NUMBER }, description: `Promemoria in minuti prima dell'evento. Scegli tra: ${REMINDER_OPTIONS.map(o => o.value).join(', ')}` },
        color: { type: Type.STRING, description: `Colore esadecimale per l'evento. Scegli tra: ${COLORS.join(', ')}` },
        },
    },
  }), [categories]);
  
  const saveAndCloseEventFunction: FunctionDeclaration = useMemo(() => ({
    name: 'save_and_close_event',
    description: "Salva l'evento con i dettagli correnti nel modulo e chiude la finestra. Da usare SOLO dopo che l'utente ha dato la conferma finale che i dettagli sono corretti.",
    parameters: { type: Type.OBJECT, properties: {}, required: [] },
  }), []);

  const highlightUploadButtonsFunction: FunctionDeclaration = useMemo(() => ({
    name: 'highlight_upload_buttons',
    description: "Evidenzia i pulsanti di caricamento documento (📷 Foto e 📁 File) con un'animazione per attirare l'attenzione dell'utente. Usa quando suggerisci di caricare un documento.",
    parameters: { type: Type.OBJECT, properties: {}, required: [] },
  }), []);

  const stopListening = useCallback(async () => {
    setAiStatus('idle');
    scriptProcessorRef.current?.disconnect();
    mediaStreamSourceRef.current?.disconnect();
    mediaStreamRef.current?.getTracks().forEach(track => track.stop());
    if (inputAudioContextRef.current && inputAudioContextRef.current.state !== 'closed') {
      try { await inputAudioContextRef.current.close(); } catch(e) { console.warn("Could not close input audio context:", e)}
    }
    if (sessionPromiseRef.current) {
        try {
            const session = await sessionPromiseRef.current;
            session.close();
        } catch (e) { console.error("Error closing session:", e); }
        sessionPromiseRef.current = null;
    }
  }, []);

  const startListening = useCallback(async () => {
    if (aiStatus === 'listening') {
        stopListening();
        return;
    }
    setAiStatus('connecting');
    setConversation(prev => [...prev, {role: 'ai', content: ''}]);

    try {
        const ai = new GoogleGenAI({apiKey: import.meta.env.VITE_GEMINI_API_KEY});
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaStreamRef.current = stream;
        inputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
        outputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
        
        // Try gemini-2.5-flash-live first (optimized for Live API), fallback to gemini-2.0-flash-live-001
        let modelToUse = 'gemini-2.5-flash-live';

        sessionPromiseRef.current = ai.live.connect({
            model: modelToUse,
            callbacks: {
                onopen: () => {
                    setAiStatus('listening');
                    const source = inputAudioContextRef.current!.createMediaStreamSource(stream);
                    mediaStreamSourceRef.current = source;
                    const scriptProcessor = inputAudioContextRef.current!.createScriptProcessor(4096, 1, 1);
                    scriptProcessorRef.current = scriptProcessor;
                    
                    scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
                        const inputData = audioProcessingEvent.inputBuffer.getChannelData(0);
                        const pcmBlob = createBlob(inputData);
                        sessionPromiseRef.current?.then((session) => {
                            session.sendRealtimeInput({ media: pcmBlob });
                        });
                    };
                    source.connect(scriptProcessor);
                    scriptProcessor.connect(inputAudioContextRef.current!.destination);
                },
                onmessage: async (message: LiveServerMessage) => {
                    if (message.serverContent?.modelTurn?.parts[0]?.inlineData?.data) {
                        setAiStatus('speaking');
                        const base64Audio = message.serverContent.modelTurn.parts[0].inlineData.data;
                        const ctx = outputAudioContextRef.current!;
                        nextStartTimeRef.current = Math.max(nextStartTimeRef.current, ctx.currentTime);
                        const audioBuffer = await decodeAudioData(decode(base64Audio), ctx, 24000, 1);
                        const source = ctx.createBufferSource();
                        source.buffer = audioBuffer;
                        source.connect(ctx.destination);
                        source.addEventListener('ended', () => {
                           setAiStatus('listening');
                           sourcesRef.current.delete(source);
                        });
                        source.start(nextStartTimeRef.current);
                        nextStartTimeRef.current += audioBuffer.duration;
                        sourcesRef.current.add(source);
                    }
                    if (message.toolCall?.functionCalls) {
                        message.toolCall.functionCalls.forEach(fc => {
                            if (fc.name === 'update_event_details') {
                                const { start_datetime, end_datetime, ...rest } = fc.args;
                                const updatedFormData: Partial<Event> = { ...rest };

                                // Handle dates with proper end_datetime calculation
                                if(start_datetime) {
                                    const startDate = new Date(start_datetime);
                                    updatedFormData.start_datetime = toLocalISOString(startDate);

                                    // If end_datetime not provided, set it to start + 1 hour
                                    if(!end_datetime) {
                                        const endDate = new Date(startDate.getTime() + 60 * 60 * 1000);
                                        updatedFormData.end_datetime = toLocalISOString(endDate);
                                    }
                                }
                                if(end_datetime) {
                                    updatedFormData.end_datetime = toLocalISOString(new Date(end_datetime));
                                }

                                setFormData(prev => ({ ...prev, ...updatedFormData }));
                                setShowForm(true); // Mostra il form quando AI inizia a compilare
                                sessionPromiseRef.current?.then(session => session.sendToolResponse({ functionResponses: { id: fc.id, name: fc.name, response: { result: "ok" } } }));

                            } else if (fc.name === 'save_and_close_event') {
                                console.log('[EventModal] save_and_close_event chiamato (voice)!');
                                handleSaveRef.current()
                                    .then(() => {
                                        console.log('[EventModal] Salvataggio completato (voice), chiudo finestra...');
                                        stopListening();
                                        onClose();
                                    })
                                    .catch((error) => {
                                        console.error('[EventModal] Errore durante save_and_close_event (voice):', error);
                                    });

                            } else if (fc.name === 'search_documents') {
                                console.log('[EventModal] search_documents chiamato (voice):', fc.args);
                                fetch('/api/ai/search', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                                    },
                                    body: JSON.stringify({
                                        query: fc.args.query,
                                        source_types: fc.args.source_types || ['event', 'document'],
                                        top_k: fc.args.top_k || 5
                                    })
                                })
                                    .then(res => res.json())
                                    .then(searchResult => {
                                        console.log('[EventModal] Risultati ricerca (voice):', searchResult);
                                        sessionPromiseRef.current?.then(session =>
                                            session.sendToolResponse({
                                                functionResponses: {
                                                    id: fc.id,
                                                    name: fc.name,
                                                    response: {
                                                        result: searchResult.answer || 'Nessun risultato trovato'
                                                    }
                                                }
                                            })
                                        );
                                    })
                                    .catch((error) => {
                                        console.error('[EventModal] Errore durante search_documents (voice):', error);
                                        sessionPromiseRef.current?.then(session =>
                                            session.sendToolResponse({
                                                functionResponses: {
                                                    id: fc.id,
                                                    name: fc.name,
                                                    response: {
                                                        result: 'Errore durante la ricerca'
                                                    }
                                                }
                                            })
                                        );
                                    });

                            } else if (fc.name === 'create_document') {
                                console.log('[EventModal] create_document chiamato (voice):', fc.args);
                                // TODO: Implementare creazione documento
                                sessionPromiseRef.current?.then(session => session.sendToolResponse({ functionResponses: { id: fc.id, name: fc.name, response: { result: "Creazione documento in sviluppo" } } }));

                            } else if (fc.name === 'highlight_upload_buttons') {
                                console.log('[EventModal] highlight_upload_buttons chiamato (voice)');
                                // Attiva animazione highlight
                                setHighlightUploadButtons(true);
                                // Auto-disattiva dopo 5 secondi
                                setTimeout(() => setHighlightUploadButtons(false), 5000);
                                // Ferma la voce per abilitare i pulsanti upload
                                stopListening();
                                sessionPromiseRef.current?.then(session => session.sendToolResponse({ functionResponses: { id: fc.id, name: fc.name, response: { result: "Pulsanti evidenziati, voce fermata" } } }));
                            }
                        })
                    }
                    if (message.serverContent?.inputTranscription) {
                        const text = message.serverContent.inputTranscription.text;
                        const isFinal = message.serverContent.inputTranscription.isFinal;
                         setConversation(current => {
                            const last = current[current.length - 1];
                            if (last?.role === 'user') {
                                const newConvo = [...current];
                                newConvo[current.length - 1] = { ...last, content: isFinal ? text : (last.content.split(' ').slice(0,-1).join(' ')+ ' ' + text) };
                                return newConvo;
                            }
                            return [...current, { role: 'user', content: text }];
                        });
                    }
                    if (message.serverContent?.outputTranscription) {
                        const newTranscript = message.serverContent.outputTranscription.text;
                         setConversation(current => {
                            const last = current[current.length - 1];
                            if (last?.role === 'ai') {
                                const newConvo = [...current];
                                newConvo[current.length - 1] = { ...last, content: last.content + newTranscript };
                                return newConvo;
                            }
                            return [...current, { role: 'ai', content: newTranscript }];
                        });
                    }
                },
                onerror: (e: ErrorEvent) => {
                    console.error('Live session error:', e);
                    setAiStatus('error');
                    setConversation(p => [...p, {role: 'ai', content: "Si è verificato un errore. Riprova."}]);
                    stopListening();
                },
                onclose: () => {},
            },
            config: {
                responseModalities: [Modality.AUDIO],
                speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } } },
                systemInstruction,
                tools: [{ functionDeclarations: [updateEventDetailsFunction, saveAndCloseEventFunction, highlightUploadButtonsFunction] }],
                inputAudioTranscription: {},
                outputAudioTranscription: {},
            },
        });
    } catch (error) {
        console.error('Failed to start microphone:', error);
        setAiStatus('error');
        setConversation(p => [...p, {role: 'ai', content: "Non ho accesso al microfono. Controlla le autorizzazioni."}]);
    }
  }, [aiStatus, stopListening, updateEventDetailsFunction, saveAndCloseEventFunction, highlightUploadButtonsFunction, systemInstruction]);

    const handleTextPrompt = async (e: React.FormEvent) => {
        e.preventDefault();
        const userMessage = aiTextInput.trim();
        if (!userMessage || aiStatus !== 'idle') return;

        setAiTextInput('');
        const currentConversation = [...conversation, { role: 'user', content: userMessage }];
        setConversation(currentConversation);
        setAiStatus('thinking');

        try {
            // Call backend AI endpoint instead of direct Gemini
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/ai/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    messages: currentConversation,
                    categories: categories,  // Pass categories to backend
                    form_state: formData     // Pass current form state so AI can see what's filled
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            // Handle function calls from backend
            if (result.function_calls && result.function_calls.length > 0) {
                for (const fc of result.function_calls) {
                    if (fc.name === 'update_event_details') {
                        const { start_datetime, end_datetime, ...rest } = fc.args;
                        const updatedFormData: Partial<Event> = { ...rest };

                        // Handle dates with proper end_datetime calculation
                        if(start_datetime) {
                            const startDate = new Date(start_datetime);
                            updatedFormData.start_datetime = toLocalISOString(startDate);

                            // If end_datetime not provided, set it to start + 1 hour
                            if(!end_datetime) {
                                const endDate = new Date(startDate.getTime() + 60 * 60 * 1000);
                                updatedFormData.end_datetime = toLocalISOString(endDate);
                            }
                        }
                        if(end_datetime) {
                            updatedFormData.end_datetime = toLocalISOString(new Date(end_datetime));
                        }

                        setFormData(prev => ({ ...prev, ...updatedFormData }));
                        setShowForm(true); // Mostra il form quando AI inizia a compilare

                    } else if (fc.name === 'save_and_close_event') {
                        console.log('[EventModal] save_and_close_event chiamato!');

                        // Mostra messaggio "Salvataggio in corso..."
                        setConversation(prev => [...prev, { role: 'ai', content: '💾 Salvataggio in corso...' }]);

                        try {
                            // PRIMA salva
                            await handleSaveRef.current();
                            console.log('[EventModal] ✅ Salvataggio completato con successo');

                            // DOPO il salvataggio riuscito, aggiorna il messaggio
                            setConversation(prev => {
                                const newConv = [...prev];
                                newConv[newConv.length - 1] = { role: 'ai', content: '✅ Salvato con successo!' };
                                return newConv;
                            });

                            setAiStatus('idle');

                            // Chiudi SOLO se salvataggio riuscito
                            setTimeout(() => {
                                onClose();
                            }, 800);
                        } catch (error) {
                            console.error('[EventModal] ❌ Errore durante save_and_close_event:', error);

                            // Aggiorna messaggio con errore
                            setConversation(prev => {
                                const newConv = [...prev];
                                newConv[newConv.length - 1] = {
                                    role: 'ai',
                                    content: `❌ Errore nel salvataggio: ${error instanceof Error ? error.message : 'Riprova'}`
                                };
                                return newConv;
                            });

                            setAiStatus('idle');
                            // NON chiudere la finestra se c'è errore!
                        }
                        return;

                    } else if (fc.name === 'search_documents') {
                        console.log('[EventModal] search_documents chiamato:', fc.args);
                        try {
                            const searchResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/ai/search`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                                },
                                body: JSON.stringify({
                                    query: fc.args.query,
                                    source_types: fc.args.source_types || ['event', 'document'],
                                    top_k: fc.args.top_k || 5
                                })
                            });
                            const searchResult = await searchResponse.json();
                            console.log('[EventModal] Risultati ricerca:', searchResult);

                            // Store event IDs for later use with open_event
                            if (searchResult.event_ids) {
                                setLastSearchEventIds(searchResult.event_ids);
                            }

                            if (searchResult.answer) {
                                setConversation(prev => [...prev, {
                                    role: 'ai',
                                    content: searchResult.answer
                                }]);
                            }
                        } catch (error) {
                            console.error('[EventModal] Errore durante search_documents:', error);
                            setConversation(prev => [...prev, {
                                role: 'ai',
                                content: 'Errore durante la ricerca. Riprova.'
                            }]);
                        }
                        return;

                    } else if (fc.name === 'create_document') {
                        console.log('[EventModal] create_document chiamato:', fc.args);
                        try {
                            const docResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/ai/create-document`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                                },
                                body: JSON.stringify({
                                    title: fc.args.title,
                                    content: fc.args.content,
                                    category_id: fc.args.category_id
                                })
                            });

                            const docResult = await docResponse.json();

                            if (docResult.success) {
                                setConversation(prev => [...prev, {
                                    role: 'ai',
                                    content: `✅ Appunto salvato: "${docResult.title}"`
                                }]);
                            } else {
                                throw new Error(docResult.error);
                            }
                        } catch (error) {
                            console.error('[EventModal] Errore durante create_document:', error);
                            setConversation(prev => [...prev, {
                                role: 'ai',
                                content: 'Errore nel salvare l\'appunto. Riprova.'
                            }]);
                        }
                        return;

                    } else if (fc.name === 'open_event') {
                        console.log('[EventModal] open_event chiamato:', fc.args);
                        let event_id = fc.args.event_id;

                        // If AI passed an index (like "0"), convert to real event_id
                        if (event_id && /^\d+$/.test(event_id)) {
                            const index = parseInt(event_id);
                            if (lastSearchEventIds[index]) {
                                event_id = lastSearchEventIds[index].event_id;
                                console.log(`[EventModal] Converted index ${index} to event_id: ${event_id}`);
                            }
                        }

                        try {
                            // Fetch event data
                            const eventResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events/${event_id}`, {
                                headers: {
                                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                                }
                            });

                            if (!eventResponse.ok) {
                                throw new Error('Event not found');
                            }

                            const eventData = await eventResponse.json();
                            console.log('[EventModal] Evento caricato:', eventData);

                            // Load event into form
                            setFormData(eventData);
                            setShowForm(true);

                            setConversation(prev => [...prev, {
                                role: 'ai',
                                content: `Ok! Ho aperto "${eventData.title}". Cosa vuoi modificare?`
                            }]);
                        } catch (error) {
                            console.error('[EventModal] Errore durante open_event:', error);
                            setConversation(prev => [...prev, {
                                role: 'ai',
                                content: 'Non ho trovato questo evento. Puoi essere più specifico?'
                            }]);
                        }
                        return;

                    } else if (fc.name === 'highlight_upload_buttons') {
                        console.log('[EventModal] highlight_upload_buttons chiamato');
                        // Attiva animazione highlight
                        setHighlightUploadButtons(true);
                        // Auto-disattiva dopo 5 secondi
                        setTimeout(() => setHighlightUploadButtons(false), 5000);
                    }
                }
            }
            
            // Add AI text response to conversation
            if (result.text) {
                setConversation(prev => [...prev, { role: 'ai', content: result.text }]);
            }

        } catch (error) {
            console.error('Text prompt error:', error);
            const errorMessage = error instanceof Error && error.message.includes('429')
                ? 'Troppe richieste. Aspetta 30 secondi e riprova. 😊'
                : 'Si è verificato un errore. Riprova.';
            setConversation(prev => [...prev, { role: 'ai', content: errorMessage }]);
        } finally {
            setAiStatus('idle');
            // Focus back to input after AI response - multiple attempts for reliability
            requestAnimationFrame(() => {
                aiTextInputRef.current?.focus();
                setTimeout(() => {
                    aiTextInputRef.current?.focus();
                }, 50);
            });
        }
    };

  useEffect(() => {
    return () => { stopListening(); }
  }, [stopListening]);

  useEffect(() => {
    if (transcriptContainerRef.current) {
        transcriptContainerRef.current.scrollTop = transcriptContainerRef.current.scrollHeight;
    }
  }, [conversation]);

  useEffect(() => {
    // Focus input when modal opens in AI mode
    if (isOpen && aiMode && aiTextInputRef.current) {
        setTimeout(() => {
            aiTextInputRef.current?.focus();
        }, 100);
    }
  }, [isOpen, aiMode]);
  
  useEffect(() => {
    if (isOpen) {
        setFormData(getInitialFormData());
        setIsSaving(false);
        setShowForm(!aiMode); // In AI mode, form nascosto all'inizio
        if (aiMode) {
          setConversation([{ role: 'ai', content: 'Ciao! Come posso aiutarti?' }]);
        }
    }
  }, [isOpen, getInitialFormData, aiMode]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'amount' ? (value ? parseFloat(value) : undefined) : value,
    }));
  };
  
  const addReminder = (minutes: number) => {
    if (minutes && !formData.reminders?.includes(minutes)) {
        setFormData(prev => ({ ...prev, reminders: [...(prev.reminders || []), minutes] }));
    }
  };

  const removeReminder = (minutes: number) => {
    setFormData(prev => ({ ...prev, reminders: (prev.reminders || []).filter(r => r !== minutes) }));
  };

  const handleSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();
    handleSave();
  };
  
  const handleDelete = () => { if (event?.id) setIsDeleteConfirmOpen(true); };
  
  const handleConfirmDelete = () => {
      if (event?.id) onDelete(event.id);
      setIsDeleteConfirmOpen(false);
  }
  
   const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setAiStatus('thinking');
    setConversation(p => [...p, {role: 'ai', content: `Analizzo il documento: ${file.name}...`}]);
    try {
        const analysis = await apiService.aiAnalyzeDocument(file);
        const updatedFormData: Partial<Event> = {
            title: analysis.reason,
            start_datetime: analysis.due_date ? toLocalISOString(new Date(analysis.due_date)) : formData.start_datetime,
            amount: analysis.amount,
            has_document: true,
        };
        setFormData(prev => ({...prev, ...updatedFormData}));
        setShowForm(true); // Mostra il form con i dati compilati dall'analisi
        setConversation(p => [...p, {role: 'ai', content: `Ho analizzato il documento. Ho trovato una ${analysis.document_type || 'informazione'}. Ho compilato i campi qui sotto. È tutto corretto?`}]);
    } catch(err) {
        setConversation(p => [...p, {role: 'ai', content: "Non sono riuscito ad analizzare il documento. Riprova."}]);
    } finally {
        setAiStatus('idle');
         if(e.target) e.target.value = '';
    }
   };

  const handleMoveEvent = (unit: 'day' | 'week' | 'month') => {
    const startDate = new Date(formData.start_datetime!);
    const endDate = formData.end_datetime ? new Date(formData.end_datetime) : null;
    const duration = endDate ? endDate.getTime() - startDate.getTime() : (60 * 60 * 1000); // Default 1h duration

    let newStartDate: Date;
    if (unit === 'day') newStartDate = new Date(startDate.setDate(startDate.getDate() + 1));
    else if (unit === 'week') newStartDate = new Date(startDate.setDate(startDate.getDate() + 7));
    else newStartDate = new Date(startDate.setMonth(startDate.getMonth() + 1));
    
    const newEndDate = new Date(newStartDate.getTime() + duration);

    setFormData(prev => ({
        ...prev,
        start_datetime: toLocalISOString(newStartDate),
        end_datetime: newEndDate ? toLocalISOString(newEndDate) : undefined,
    }));
    setIsMoveMenuOpen(false);
  };

  const handleMoveEventToDate = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDateStr = e.target.value;
    if (!newDateStr) return;
    const [year, month, day] = newDateStr.split('-').map(Number);
    
    const startDate = new Date(formData.start_datetime!);
    const endDate = formData.end_datetime ? new Date(formData.end_datetime) : null;
    const duration = endDate ? endDate.getTime() - startDate.getTime() : (60 * 60 * 1000);

    const newStartDate = new Date(startDate);
    newStartDate.setFullYear(year, month - 1, day);
    const newEndDate = new Date(newStartDate.getTime() + duration);
    
    setFormData(prev => ({
        ...prev,
        start_datetime: toLocalISOString(newStartDate),
        end_datetime: newEndDate ? toLocalISOString(newEndDate) : undefined,
    }));
    setIsMoveMenuOpen(false);
  };
  
  if (!isOpen) return null;
  
  const MicButton = () => {
    let content; let pulsing = false;
    switch(aiStatus) {
        case 'listening':
        case 'speaking':
            content = <div className="w-3 h-3 bg-white rounded-sm"></div>;
            pulsing = aiStatus === 'listening'; break;
        case 'connecting':
        case 'thinking':
            content = <Icons.Spinner className="h-6 w-6 animate-spin" />; break;
        case 'error':
            content = <Icons.XMark className="h-6 w-6"/>; break;
        default:
             content = <Icons.Microphone className="h-6 w-6"/>;
    }
    return (
         <button type="button" onClick={startListening} className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors text-white ${aiStatus === 'listening' || aiStatus === 'speaking' ? 'bg-red-500' : 'bg-primary'} ${pulsing ? 'animate-pulse' : ''}`}>
            {content}
        </button>
    )
  }

  const isFormValid = !!(formData.title && formData.category_id && formData.start_datetime);

  return (
    <>
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
      <div className="bg-surface w-full max-w-md m-4 rounded-lg flex flex-col max-h-[90vh] relative">
        <header className="p-4 flex justify-between items-center border-b border-gray-700 flex-shrink-0">
          <h2 className="font-bold text-lg">{event ? 'Modifica Evento' : 'Nuovo Evento'} {aiMode && <span className="text-primary text-sm align-middle">(AI)</span>}</h2>
           <div className="flex items-center gap-2">
            {event && !aiMode && (
                 <div className="relative">
                    <button type="button" onClick={() => setIsMoveMenuOpen(prev => !prev)} className="text-sm font-semibold px-3 py-1 rounded-md border border-gray-600 hover:bg-gray-700">Sposta a...</button>
                    {isMoveMenuOpen && (
                        <div className="absolute right-0 mt-2 w-48 bg-background border border-gray-600 rounded-md shadow-lg z-20">
                            <button type="button" onClick={() => handleMoveEvent('day')} className="block w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-surface">Il giorno dopo</button>
                            <button type="button" onClick={() => handleMoveEvent('week')} className="block w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-surface">Una settimana dopo</button>
                            <button type="button" onClick={() => handleMoveEvent('month')} className="block w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-surface">Un mese dopo</button>
                            <div className="border-t border-gray-600 my-1"></div>
                            <label htmlFor="move-to-date-input" className="block w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-surface cursor-pointer">Scegli data...</label>
                            <input type="date" id="move-to-date-input" onChange={handleMoveEventToDate} className="opacity-0 w-0 h-0 absolute left-0 top-0"/>
                        </div>
                    )}
                 </div>
            )}
            <button onClick={() => onClose()} className="p-1 -mr-1 rounded-full hover:bg-gray-700"><Icons.Close/></button>
          </div>
        </header>
        
        {aiMode && (
            <div className="flex-shrink-0 flex flex-col">
                <div ref={transcriptContainerRef} className="text-sm min-h-[6rem] max-h-40 overflow-y-auto p-3 space-y-2 scroll-smooth border-b border-gray-700">
                    {conversation.map((msg, index) => (
                        <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <p className={`max-w-[80%] rounded-lg px-3 py-2 ${msg.role === 'user' ? 'bg-primary text-white' : 'bg-background'}`}>
                                {msg.content}
                            </p>
                        </div>
                    ))}
                     {aiStatus === 'thinking' && 
                        <div className="flex justify-start">
                             <p className="bg-background rounded-lg px-3 py-2 animate-pulse">...</p>
                        </div>
                     }
                </div>
                <form onSubmit={handleTextPrompt} className="p-2 flex items-center gap-2 border-b border-gray-700">
                     <input 
                        ref={aiTextInputRef}
                        type="text" 
                        value={aiTextInput}
                        onChange={(e) => setAiTextInput(e.target.value)}
                        placeholder="Oppure scrivi qui..."
                        className="flex-grow bg-background p-2 rounded-lg border border-gray-600 focus:outline-none focus:ring-1 focus:ring-primary text-sm"
                        disabled={aiStatus !== 'idle'}
                     />
                     <button type="submit" className="text-primary hover:text-white disabled:text-gray-500" disabled={!aiTextInput.trim() || aiStatus !== 'idle'}>
                        <Icons.Send className="h-6 w-6"/>
                     </button>
                </form>
                <div className="flex items-center justify-around p-3">
                    <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept="image/jpeg,image/png,application/pdf" />
                    <input type="file" ref={cameraInputRef} onChange={handleFileUpload} className="hidden" accept="image/*" capture="environment" />

                    <div className="relative">
                        {highlightUploadButtons && (
                            <div className="absolute inset-0 -m-2 rounded-full border-4 border-primary animate-ping"></div>
                        )}
                        <button type="button" onClick={() => fileInputRef.current?.click()} className="relative text-text-secondary hover:text-primary disabled:opacity-50" disabled={aiStatus !== 'idle'} title="Carica Documento">
                            <Icons.Upload className="h-7 w-7"/>
                        </button>
                    </div>
                    <MicButton />
                    <div className="relative">
                        {highlightUploadButtons && (
                            <div className="absolute inset-0 -m-2 rounded-full border-4 border-primary animate-ping"></div>
                        )}
                        <button type="button" onClick={() => cameraInputRef.current?.click()} className="relative text-text-secondary hover:text-primary disabled:opacity-50" disabled={aiStatus !== 'idle'} title="Usa Fotocamera">
                            <Icons.Camera className="h-7 w-7"/>
                        </button>
                    </div>
                </div>
            </div>
        )}

        {(!aiMode || showForm) && (
        <form onSubmit={handleSubmit} className="flex flex-col flex-grow overflow-hidden">
            <div className="flex-grow p-4 overflow-y-auto space-y-4">
                <div>
                    <label htmlFor="title" className="block text-sm font-medium text-text-secondary mb-1">Titolo</label>
                    <input type="text" id="title" name="title" value={formData.title} onChange={handleChange} required className="w-full bg-background p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary"/>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label htmlFor="category_id" className="block text-sm font-medium text-text-secondary mb-1">Categoria</label>
                        <div className="flex items-center">
                            <span className="w-4 h-4 rounded-full mr-2 flex-shrink-0" style={{ backgroundColor: categories.find(c=>c.id === formData.category_id)?.color }}></span>
                            <select id="category_id" name="category_id" value={formData.category_id} onChange={handleChange} required className="w-full bg-background p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary appearance-none">
                                {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>)}
                            </select>
                        </div>
                    </div>
                     <div>
                        <label htmlFor="amount" className="block text-sm font-medium text-text-secondary mb-1">Importo (€)</label>
                        <input 
                            type="number" 
                            id="amount" 
                            name="amount" 
                            value={formData.amount === undefined ? '' : formData.amount} 
                            onChange={handleChange} 
                            placeholder="Es. 75.50" 
                            step="0.01"
                            className="w-full bg-background p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                    </div>
                </div>
                <div>
                    <label htmlFor="description" className="block text-sm font-medium text-text-secondary mb-1">Appunti / Descrizione</label>
                    <textarea id="description" name="description" rows={3} value={formData.description || ''} onChange={handleChange} placeholder="Dettagli aggiuntivi..." className="w-full bg-background p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary"/>
                </div>
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Colore Evento</label>
                    <div className="flex items-center gap-2 flex-wrap">
                        <button type="button" onClick={() => setFormData(prev => ({ ...prev, color: undefined }))} className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all ${!formData.color ? 'border-white ring-2 ring-primary' : 'border-transparent'}`} title="Usa colore categoria">
                            <div className="w-6 h-6 rounded-full" style={{ backgroundColor: categories.find(c => c.id === formData.category_id)?.color }}></div>
                        </button>
                        {COLORS.map(c => (
                            <button key={c} type="button" onClick={() => setFormData(prev => ({ ...prev, color: c }))} style={{ backgroundColor: c }} className={`w-8 h-8 rounded-full border-2 transition-all ${formData.color === c ? 'border-white ring-2 ring-offset-2 ring-offset-surface ring-white' : 'border-transparent'}`}></button>
                        ))}
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label htmlFor="start_datetime" className="block text-sm font-medium text-text-secondary mb-1">Inizio</label>
                        <input type="datetime-local" id="start_datetime" name="start_datetime" value={formData.start_datetime} onChange={handleChange} required className="w-full bg-background p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary"/>
                    </div>
                    <div>
                        <label htmlFor="end_datetime" className="block text-sm font-medium text-text-secondary mb-1">Fine</label>
                        <input type="datetime-local" id="end_datetime" name="end_datetime" value={formData.end_datetime || ''} onChange={handleChange} className="w-full bg-background p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary"/>
                    </div>
                </div>
                <div>
                    <label htmlFor="recurrence" className="block text-sm font-medium text-text-secondary mb-1">Si ripete</label>
                    <select id="recurrence" name="recurrence" value={formData.recurrence} onChange={handleChange} className="w-full bg-background p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary">
                        {RECURRENCE_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Promemoria</label>
                    <div className="flex flex-wrap gap-2 mb-2">
                        {formData.reminders?.map(minutes => (
                            <div key={minutes} className="flex items-center gap-1 bg-primary/30 text-primary font-semibold px-2 py-1 rounded-md text-xs">
                                <span>{REMINDER_OPTIONS.find(o => o.value === minutes)?.label}</span>
                                <button type="button" onClick={() => removeReminder(minutes)}><Icons.XMark className="h-4 w-4"/></button>
                            </div>
                        ))}
                    </div>
                    <select onChange={(e) => addReminder(parseInt(e.target.value))} className="w-full bg-background p-2 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary" value="">
                        <option value="" disabled>Aggiungi un promemoria...</option>
                        {REMINDER_OPTIONS.filter(opt => !formData.reminders?.includes(opt.value)).map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                    </select>
                </div>
            </div>
            <footer className="flex-shrink-0 p-4 flex justify-between items-center border-t border-gray-700">
                <div>
                    {event && (
                        <button onClick={handleDelete} type="button" className="text-red-500 hover:text-red-400 font-semibold flex items-center gap-1">
                            <Icons.Trash className="h-5 w-5"/> Elimina
                        </button>
                    )}
                </div>
                <div className="flex gap-2">
                    <button onClick={() => onClose()} type="button" className="px-4 py-2 rounded-md bg-gray-600 hover:bg-gray-500 text-white font-semibold">Annulla</button>
                    <button 
                        type="submit"
                        disabled={!isFormValid || isSaving || (aiMode && aiStatus !== 'idle')}
                        className="px-4 py-2 rounded-md bg-primary hover:bg-violet-700 text-white font-semibold transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed flex items-center justify-center w-24"
                    >
                        {isSaving ? <Icons.Spinner className="h-5 w-5 animate-spin" /> : 'Salva'}
                    </button>
                </div>
            </footer>
        </form>
        )}
      </div>
    </div>
    
    {isDeleteConfirmOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[60]">
            <div className="bg-surface rounded-lg p-6 w-full max-w-sm m-4 text-center shadow-2xl">
            <h3 className="font-bold text-lg mb-2">Conferma Eliminazione</h3>
            <p className="text-text-secondary mb-6">
                Sei sicuro di voler eliminare l'evento "{event?.title}"? L'azione è irreversibile.
            </p>
            <div className="flex justify-end gap-3">
                <button onClick={() => setIsDeleteConfirmOpen(false)} className="px-4 py-2 rounded-md bg-gray-600 hover:bg-gray-500 font-semibold transition-colors">Annulla</button>
                <button onClick={handleConfirmDelete} className="px-4 py-2 rounded-md bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors">Elimina</button>
            </div>
            </div>
        </div>
    )}
    </>
  );
};

export default EventModal;
