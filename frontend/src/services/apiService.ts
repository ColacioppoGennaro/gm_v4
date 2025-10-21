// import { Type } from "@google/genai"; // For future AI features
import { Category, Document, DocumentAnalysis, Event, User } from '../types';

// Helper to get auth token
const getAuthToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

// Helper to get headers with auth token
const getAuthHeaders = (): HeadersInit => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

// Helper to convert file to base64 for Gemini API (future use)
/* const fileToGenerativePart = async (file: File) => {
  const base64EncodedDataPromise = new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
    reader.readAsDataURL(file);
  });
  return {
    inlineData: { data: await base64EncodedDataPromise, mimeType: file.type },
  };
} */

/* const documentAnalysisSchema = {
    type: Type.OBJECT,
    properties: {
        document_type: { type: Type.STRING, description: 'Tipo di documento (es. Fattura, Bolletta, Ricevuta).' },
        reason: { type: Type.STRING, description: 'Il titolo dell\'evento o la ragione del documento (es. Pagamento Utenza Elettrica).' },
        due_date: { type: Type.STRING, description: 'La data di scadenza in formato ISO 8601.' },
        amount: { type: Type.NUMBER, description: 'L\'importo monetario, se presente.' },
    },
}; */


export const apiService = {
  // Authentication
  register: async (email: string, password: string, passwordConfirm: string): Promise<{ message: string }> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, password_confirm: passwordConfirm })
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Registration failed');
    }
    return data;
  },

  login: async (email: string, password: string): Promise<{ token: string; user: User }> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }
    
    // Store token
    localStorage.setItem('auth_token', data.data.token);
    
    return data.data;
  },

  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('onboardingComplete');
    window.location.reload();
  },

  // Data fetching
  getEvents: async (): Promise<Event[]> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to fetch events');
    return data.data.events || [];
  },

  getCategories: async (): Promise<Category[]> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events/categories`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to fetch categories');
    return data.data.categories || [];
  },

  getUser: async (): Promise<User> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/me`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to fetch user');
    return data.data.user;
  },

  getDocuments: async (): Promise<Document[]> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events/documents`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to fetch documents');
    return data.data.documents || [];
  },

  // Event Management
  addEvent: async (eventData: Omit<Event, 'id'>): Promise<Event> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(eventData)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to create event');
    return data.data; // Backend ritorna { data: {...evento...}, success: true }
  },

  updateEvent: async (eventData: Event): Promise<Event> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events/${eventData.id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(eventData)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to update event');
    return data.data; // Backend ritorna { data: {...evento...}, success: true }
  },
  
  deleteEvent: async (eventId: string): Promise<void> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events/${eventId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'Failed to delete event');
    }
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
  addCategory: async (categoryData: { name: string; color: string; icon: string; }): Promise<Category> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events/categories`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(categoryData)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to create category');
    return data.data.category;
  },

  deleteCategory: async (id: string): Promise<void> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/events/categories/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'Failed to delete category');
    }
  },

  // User settings - REAL API CALLS
  connectGoogleCalendar: async (): Promise<void> => {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/google/connect`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to get authorization URL');
    }
    
    const data = await response.json();
    
    // Save current location to return after OAuth
    localStorage.setItem('oauth_return_path', window.location.pathname);
    
    // Redirect to Google OAuth (full page redirect instead of popup)
    window.location.href = data.data.authorization_url;
  },
  
  disconnectGoogleCalendar: async (): Promise<User> => {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/google/disconnect`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to disconnect Google Calendar');
    }
    
    const data = await response.json();
    return data.data.user;
  }
};
