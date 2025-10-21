/**
 * Real API Service - Calls backend endpoints
 * Replace mock implementation in apiService.ts with this
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://gruppogea.net/gm_v4';

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * Helper function to make API requests with authentication
 */
async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = localStorage.getItem('auth_token');
  
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  
  // Add auth token if available
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  // Add Content-Type for JSON if body is not FormData
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(errorData.error || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Real API Service Implementation
 */
export const realApiService = {
  // Auth
  login: async (email: string, password: string) => {
    const response = await apiRequest('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    if (response.data?.token) {
      localStorage.setItem('auth_token', response.data.token);
    }
    
    return response.data.user;
  },
  
  register: async (email: string, password: string, password_confirm: string) => {
    const response = await apiRequest('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, password_confirm }),
    });
    
    return response;
  },
  
  getCurrentUser: async () => {
    const response = await apiRequest('/api/auth/me', {
      method: 'GET',
    });
    
    return response.data.user;
  },
  
  // Events
  getEvents: async () => {
    const response = await apiRequest('/api/events', {
      method: 'GET',
    });
    
    return response.data.events || [];
  },
  
  createEvent: async (eventData: any) => {
    const response = await apiRequest('/api/events', {
      method: 'POST',
      body: JSON.stringify(eventData),
    });
    
    return response.data;
  },
  
  updateEvent: async (eventId: string, eventData: any) => {
    const response = await apiRequest(`/api/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify(eventData),
    });
    
    return response.data;
  },
  
  deleteEvent: async (eventId: string) => {
    await apiRequest(`/api/events/${eventId}`, {
      method: 'DELETE',
    });
  },
  
  // Categories
  getCategories: async () => {
    const response = await apiRequest('/api/categories', {
      method: 'GET',
    });
    
    return response.data.categories || [];
  },
  
  addCategory: async (categoryData: { name: string; color: string; icon: string }) => {
    const response = await apiRequest('/api/categories', {
      method: 'POST',
      body: JSON.stringify(categoryData),
    });
    
    return response.data;
  },
  
  deleteCategory: async (categoryId: string) => {
    await apiRequest(`/api/categories/${categoryId}`, {
      method: 'DELETE',
    });
  },
  
  // Google Calendar
  connectGoogleCalendar: async () => {
    const response = await apiRequest('/api/auth/google/connect', {
      method: 'GET',
    });
    
    // Open OAuth popup
    const authWindow = window.open(
      response.data.authorization_url,
      'google_auth',
      'width=600,height=700,left=100,top=100'
    );
    
    // Listen for OAuth callback
    return new Promise((resolve, reject) => {
      const handleMessage = (event: MessageEvent) => {
        if (event.data.type === 'google_auth') {
          window.removeEventListener('message', handleMessage);
          
          if (event.data.success) {
            // Refresh user data
            realApiService.getCurrentUser()
              .then((user) => resolve(user))
              .catch(reject);
          } else {
            reject(new Error(event.data.error || 'Google authentication failed'));
          }
        }
      };
      
      window.addEventListener('message', handleMessage);
      
      // Check if window was closed
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed);
          window.removeEventListener('message', handleMessage);
          reject(new Error('Authentication cancelled'));
        }
      }, 500);
    });
  },
  
  disconnectGoogleCalendar: async () => {
    const response = await apiRequest('/api/auth/google/disconnect', {
      method: 'POST',
    });
    
    return response.data.user;
  },
  
  // AI Services
  aiAnalyzeDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiRequest('/api/ai/analyze-document', {
      method: 'POST',
      body: formData,
    });
    
    return response.data;
  },
  
  aiChat: async (messages: Array<{ role: string; content: string }>) => {
    const response = await apiRequest('/api/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ messages }),
    });
    
    return response.data;
  },
};

export { apiRequest };
