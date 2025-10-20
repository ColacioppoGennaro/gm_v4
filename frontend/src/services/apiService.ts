// Fix: Provide full implementation for apiService, including Gemini integration and mock data.
// @ts-nocheck - Temporary: Disable type checking for unused code
import { Type } from "@google/genai";
import { v4 as uuidv4 } from 'uuid';
import { Category, Document, DocumentAnalysis, Event, EventStatus, User } from '../types';

// Helper function to create dates relative to today
const today = new Date();
const getRelativeDate = (dayOffset: number, hour: number, minute: number = 0): string => {
    const date = new Date(today);
    date.setDate(today.getDate() + dayOffset);
    date.setHours(hour, minute, 0, 0);
    return date.toISOString();
};


// Mock data
let MOCK_CATEGORIES: Category[] = [
  { id: 'c1', name: 'Lavoro', color: '#3B82F6', icon: '💼', event_count: 4 },
  { id: 'c2', name: 'Famiglia', color: '#10B981', icon: '👨\u200d👩\u200d👧\u200d👦', event_count: 2 },
  { id: 'c3', name: 'Personale', color: '#8B5CF6', icon: '🧘', event_count: 3 },
  { id: 'c4', name: 'Altro', color: '#6B7280', icon: '📌', event_count: 1 },
];

let MOCK_EVENTS: Event[] = [
  { id: 'e-past-1', title: 'Revisione trimestrale', start_datetime: getRelativeDate(-10, 9, 0), category_id: 'c1', status: EventStatus.Completed, has_document: false, reminders: [], recurrence: 'none' },
  { id: 'e-past-2', title: 'Pagamento Tasse', start_datetime: getRelativeDate(-5, 11, 0), category_id: 'c4', status: EventStatus.Pending, has_document: true, reminders: [], recurrence: 'none' },
  { id: 'e-past-3', title: 'Visita medica', start_datetime: getRelativeDate(-2, 16, 0), category_id: 'c3', status: EventStatus.Completed, has_document: false, reminders: [], recurrence: 'none' },
  { id: '3', title: 'Team Meeting', start_datetime: getRelativeDate(0, 9, 0), end_datetime: getRelativeDate(0, 10, 30), category_id: 'c1', status: EventStatus.Pending, has_document: false, reminders: [15], source: 'local', recurrence: 'weekly' },
  { id: '5', title: 'Palestra', start_datetime: getRelativeDate(0, 18, 0), end_datetime: getRelativeDate(0, 19, 30), category_id: 'c3', status: EventStatus.Pending, has_document: false, reminders: [60], source: 'local', recurrence: 'none'},
  { id: '1', title: 'Pagamento Bolletta Luce', start_datetime: getRelativeDate(2, 11, 0), end_datetime: getRelativeDate(2, 11, 30), amount: 75.50, category_id: 'c2', status: EventStatus.Pending, has_document: true, reminders: [1440, 60], source: 'local', recurrence: 'none' },
  { id: '4', title: 'Cena con amici', start_datetime: getRelativeDate(3, 20, 0), end_datetime: getRelativeDate(3, 22, 0), category_id: 'c2', status: EventStatus.Pending, has_document: false, reminders: [180], source: 'google', recurrence: 'none', color: '#EF4444' },
  { id: '2', title: 'Appuntamento Dentista', start_datetime: getRelativeDate(5, 15, 0), end_datetime: getRelativeDate(5, 16, 0), category_id: 'c3', status: EventStatus.Pending, has_document: false, reminders: [1440, 120], source: 'local', recurrence: 'none' },
  { id: '7', title: 'Chiamata Cliente', start_datetime: getRelativeDate(1, 14, 0), end_datetime: getRelativeDate(1, 14, 30), category_id: 'c1', status: EventStatus.Pending, has_document: false, reminders: [15], source: 'google', recurrence: 'none'},
  { id: 'e-future-1', title: 'Presentazione Progetto', start_datetime: getRelativeDate(10, 10, 0), category_id: 'c1', status: EventStatus.Pending, has_document: false, reminders: [2880], recurrence: 'none' },
];

let MOCK_USER: User = { id: 'u1', email: 'test@example.com', subscription_type: 'pro', google_calendar_connected: true };
let MOCK_DOCUMENTS: Document[] = [
    { id: 'd1', filename: 'bolletta_luce.pdf', upload_date: new Date().toISOString(), ai_summary: 'Bolletta per la fornitura di energia elettrica per il mese corrente.', extracted_amount: 75.50, event_id: '1' },
    { id: 'd2', filename: 'report_q3.pdf', upload_date: new Date().toISOString(), ai_summary: 'Report trimestrale sulle performance.', extracted_amount: undefined, event_id: '6' }
];

const mockApiCall = <T>(data: T, delay = 300): Promise<T> => 
  new Promise(resolve => setTimeout(() => {
    if (data === undefined) {
        resolve(data);
        return;
    }
    resolve(JSON.parse(JSON.stringify(data)))
  }, delay));

// Helper to convert file to base64 for Gemini API
const fileToGenerativePart = async (file: File) => {
  const base64EncodedDataPromise = new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
    reader.readAsDataURL(file);
  });
  return {
    inlineData: { data: await base64EncodedDataPromise, mimeType: file.type },
  };
}

const documentAnalysisSchema = {
    type: Type.OBJECT,
    properties: {
        document_type: { type: Type.STRING, description: 'Tipo di documento (es. Fattura, Bolletta, Ricevuta).' },
        reason: { type: Type.STRING, description: 'Il titolo dell\'evento o la ragione del documento (es. Pagamento Utenza Elettrica).' },
        due_date: { type: Type.STRING, description: 'La data di scadenza in formato ISO 8601.' },
        amount: { type: Type.NUMBER, description: 'L\'importo monetario, se presente.' },
    },
};


export const apiService = {
  // Data fetching
  getEvents: () => {
    const sortedEvents = MOCK_EVENTS.sort((a,b) => new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime());
    return mockApiCall(sortedEvents);
  },
  getCategories: () => mockApiCall(MOCK_CATEGORIES),
  getUser: () => mockApiCall(MOCK_USER),
  getDocuments: () => mockApiCall(MOCK_DOCUMENTS),

  // Event Management
  addEvent: (eventData: Omit<Event, 'id'>): Promise<Event> => {
    const newEvent: Event = {
      ...eventData,
      id: uuidv4(),
      status: EventStatus.Pending,
      has_document: eventData.has_document || false, 
      source: 'local',
      recurrence: eventData.recurrence || 'none',
    };
    MOCK_EVENTS.push(newEvent);
    return mockApiCall(newEvent);
  },

  updateEvent: (eventData: Event): Promise<Event> => {
    MOCK_EVENTS = MOCK_EVENTS.map(e => e.id === eventData.id ? eventData : e);
    return mockApiCall(eventData);
  },
  
  deleteEvent: (eventId: string): Promise<void> => {
    MOCK_EVENTS = MOCK_EVENTS.filter(e => e.id !== eventId);
    return mockApiCall(undefined);
  },

  // AI analysis - calls backend endpoint (server-side Gemini API key)
  aiAnalyzeDocument: async (file: File): Promise<DocumentAnalysis> => {
    console.log("Analyzing document via backend API:", file.name);
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/ai/analyze-document`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        return result.analysis;

    } catch(e) {
        console.error("Backend AI analysis error", e);
        throw new Error("Failed to analyze document with AI.");
    }
  },

  // Category management
  addCategory: (categoryData: { name: string; color: string; icon: string; }): Promise<Category> => {
    const newCategory: Category = { ...categoryData, id: uuidv4(), event_count: 0 };
    MOCK_CATEGORIES.push(newCategory);
    return mockApiCall(newCategory);
  },
  deleteCategory: (id: string): Promise<void> => {
    MOCK_CATEGORIES = MOCK_CATEGORIES.filter(c => c.id !== id);
    return mockApiCall(undefined);
  },

  // User settings
  connectGoogleCalendar: (): Promise<User> => {
    MOCK_USER.google_calendar_connected = true;
    return mockApiCall(MOCK_USER);
  },
  disconnectGoogleCalendar: (): Promise<User> => {
    MOCK_USER.google_calendar_connected = false;
    return mockApiCall(MOCK_USER);
  }
};
