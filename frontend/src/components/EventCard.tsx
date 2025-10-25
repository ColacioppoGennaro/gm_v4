import React from 'react';
import { Event, EventStatus } from '../types';
import { Icons } from './Icons';

interface EventCardProps {
  event: Event;
  onRequestToggleStatus: () => void;
  onEditEvent: () => void;
}

const EventCard: React.FC<EventCardProps> = ({ event, onRequestToggleStatus, onEditEvent }) => {
  const { title, amount, category, start_datetime, status, document_count, reminders, color } = event;

  const eventDate = new Date(start_datetime);
  const isPast = eventDate < new Date();
  const isCompleted = status === EventStatus.Completed;
  const isExpired = isPast && !isCompleted;

  const eventTime = eventDate.toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit'
  });
  
  const eventColor = color || category?.color || '#6B7280';

  return (
    <div 
        onClick={onEditEvent}
        className={`bg-surface rounded-lg p-2 flex items-start gap-2 transition-all border-l-4 cursor-pointer hover:bg-gray-700/50 ${isCompleted ? 'opacity-50' : ''}`}
        style={{ borderColor: eventColor }}
    >
      <div className="pt-1" onClick={(e) => e.stopPropagation()}>
          <input
              type="checkbox"
              checked={isCompleted}
              onChange={onRequestToggleStatus}
              className="w-5 h-5 rounded-full bg-background border-gray-600 text-primary focus:ring-primary"
          />
      </div>
      <div className="flex-grow">
        <div className="flex justify-between items-start">
            <h3 className={`font-bold text-text-primary pr-2 ${isCompleted ? 'line-through' : ''}`}>
                {category?.icon} {title}
            </h3>
            {amount && <span className="text-lg font-semibold text-primary">€{typeof amount === 'number' ? amount.toFixed(2) : parseFloat(amount).toFixed(2)}</span>}
        </div>
        
        {isExpired && <span className="text-xs font-bold text-red-400 bg-red-500/20 px-2 py-0.5 rounded-full mt-1 inline-block">SCADUTO</span>}

        <div className="flex items-center justify-between mt-1 text-sm text-text-secondary">
          <div className="flex items-center gap-3">
            {document_count && document_count > 0 && (
              <div className="flex items-center gap-1">
                <Icons.Document className="h-5 w-5" title="Documenti allegati" />
                <span className="text-xs font-medium">{document_count}</span>
              </div>
            )}
            {reminders && reminders.length > 0 && <Icons.Bell className="h-5 w-5" title="Promemoria attivo" />}
          </div>
          <span className="font-medium">{eventTime}</span>
        </div>
      </div>
    </div>
  );
};

export default EventCard;
