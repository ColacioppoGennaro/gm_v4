// Fix: Provide full content for types.ts to define all application types.
export enum EventStatus {
  Pending = 'pending',
  Completed = 'completed',
}

export type Recurrence = 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly';

export interface Category {
  id: string;
  name: string;
  color: string;
  icon: string;
  event_count?: number;
}

export interface Event {
  id: string;
  title: string;
  start_datetime: string;
  end_datetime?: string;
  amount?: number;
  category_id: string;
  category?: Category;
  status: EventStatus;
  has_document: boolean;
  reminders: number[]; // Array of minutes before event
  source?: 'local' | 'google';
  description?: string;
  recurrence?: Recurrence;
  color?: string;
}

export interface User {
  id: string;
  email: string;
  subscription_type: 'free' | 'pro';
  google_calendar_connected: boolean;
  onboarding_completed?: boolean;
}

export interface Document {
    id: string;
    filename: string;
    upload_date: string;
    ai_summary?: string;
    extracted_amount?: number;
    event_id?: string;
    event?: {
        title: string;
    }
}

export enum AiConversationType {
    Greeting = 'greeting',
    UploadPrompt = 'upload_prompt',
    Question = 'question',
    Confirmation = 'confirmation',
}
  
export interface AiResponse {
    message: string;
    type: AiConversationType;
    extracted_data?: Partial<Event>;
}
  
export interface DocumentAnalysis {
    document_type: string;
    reason?: string;
    due_date?: string;
    amount?: number;
}
