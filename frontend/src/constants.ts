import { Recurrence } from "./types";

export const REMINDER_OPTIONS = [
  { value: 5, label: '5 minuti prima' },
  { value: 15, label: '15 minuti prima' },
  { value: 30, label: '30 minuti prima' },
  { value: 60, label: '1 ora prima' },
  { value: 120, label: '2 ore prima' },
  { value: 1440, label: '1 giorno prima' },
  { value: 2880, label: '2 giorni prima' },
];

export const RECURRENCE_OPTIONS: { value: Recurrence; label: string }[] = [
    { value: 'none', label: 'Non si ripete' },
    { value: 'daily', label: 'Ogni giorno' },
    { value: 'weekly', label: 'Ogni settimana' },
    { value: 'monthly', label: 'Ogni mese' },
    { value: 'yearly', label: 'Ogni anno' },
];
