import React, { useState, useMemo, useRef } from 'react';
import { Event, Category, EventStatus } from '../types';
import EventCard from './EventCard';
// import { Icons } from './Icons';

interface DashboardProps {
  events: Event[];
  onToggleStatus: (event: Event) => void;
  categories: Category[];
  onEditEvent: (event: Event) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ events, onToggleStatus, categories, onEditEvent }) => {
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [visibleCount, setVisibleCount] = useState(15);
  const todayRef = useRef<HTMLDivElement>(null);
  const [eventToConfirm, setEventToConfirm] = useState<Event | null>(null);

  const filteredEvents = useMemo(() => {
    return events
      .filter(event => {
        if (filterCategory !== 'all' && event.category_id !== filterCategory) {
          return false;
        }
        if (filterStatus === 'completed' && event.status !== EventStatus.Completed) {
          return false;
        }
        if (filterStatus === 'pending' && event.status !== EventStatus.Pending) {
          return false;
        }
        return true;
      })
      .sort((a, b) => new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime());
  }, [events, filterCategory, filterStatus]);

  const groupedEvents = useMemo(() => {
    const groups: Record<string, Event[]> = {};
    filteredEvents.slice(0, visibleCount).forEach(event => {
        const date = new Date(event.start_datetime);
        const dateKey = new Date(date.getFullYear(), date.getMonth(), date.getDate()).toISOString();
        if (!groups[dateKey]) {
            groups[dateKey] = [];
        }
        groups[dateKey].push(event);
    });
    return groups;
  }, [filteredEvents, visibleCount]);

  const sortedDateKeys = Object.keys(groupedEvents).sort((a,b) => new Date(a).getTime() - new Date(b).getTime());

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayDateString = today.toDateString();

  // FIX: Replace findLastIndex with a compatible loop to support older environments.
  let lastPastDayIndex = -1;
  for (let i = sortedDateKeys.length - 1; i >= 0; i--) {
    if (new Date(sortedDateKeys[i]) < today) {
      lastPastDayIndex = i;
      break;
    }
  }

  const scrollToToday = () => {
    todayRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleRequestToggleStatus = (event: Event) => {
    setEventToConfirm(event);
  };

  const handleConfirmToggle = () => {
    if (eventToConfirm) {
      onToggleStatus(eventToConfirm);
    }
    setEventToConfirm(null);
  };


  return (
    <div className="h-full flex flex-col">
      {/* Filters */}
      <div className="flex-shrink-0 p-2 bg-surface/50 backdrop-blur-sm sticky top-0 z-10 border-b border-gray-700">
        <div className="flex items-center justify-between gap-2">
            <div className="flex space-x-2 flex-grow">
                <select
                    value={filterCategory}
                    onChange={e => setFilterCategory(e.target.value)}
                    className="bg-background border border-gray-600 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-1/2"
                >
                    <option value="all">Tutte le categorie</option>
                    {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
                </select>
                <select
                    value={filterStatus}
                    onChange={e => setFilterStatus(e.target.value)}
                    className="bg-background border border-gray-600 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-1/2"
                >
                    <option value="all">Tutti gli stati</option>
                    <option value="pending">Da fare</option>
                    <option value="completed">Completati</option>
                </select>
            </div>
             <button onClick={scrollToToday} className="flex-shrink-0 bg-accent text-white font-semibold text-sm py-1 px-3 rounded-md hover:bg-blue-600 transition-colors">
                Oggi
            </button>
        </div>
      </div>

      <div className="flex-grow overflow-y-auto p-3 space-y-4">
        {filteredEvents.length === 0 ? (
          <div className="text-center py-10">
              <p className="text-text-secondary">Nessun evento corrisponde ai filtri.</p>
          </div>
        ) : (
            sortedDateKeys.map((dateKey, index) => {
                const isToday = new Date(dateKey).toDateString() === todayDateString;

                return (
                    <React.Fragment key={dateKey}>
                        <div ref={isToday ? todayRef : null}>
                            <h2 className="font-bold text-lg mb-1 pl-1 sticky top-0 bg-background py-1.5">
                                {new Date(dateKey).toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' })}
                            </h2>
                            <div className="space-y-2">
                                {groupedEvents[dateKey].map(event => (
                                    <EventCard 
                                        key={event.id} 
                                        event={event} 
                                        onRequestToggleStatus={() => handleRequestToggleStatus(event)} 
                                        onEditEvent={() => onEditEvent(event)}
                                    />
                                ))}
                            </div>
                        </div>
                        {index === lastPastDayIndex && lastPastDayIndex < sortedDateKeys.length - 1 && (
                            <div className="flex items-center my-2" aria-hidden="true">
                                <div className="flex-grow border-t border-dashed border-gray-600"></div>
                                <span className="flex-shrink mx-4 text-xs font-bold uppercase text-text-secondary">Futuro</span>
                                <div className="flex-grow border-t border-dashed border-gray-600"></div>
                            </div>
                        )}
                    </React.Fragment>
                )
            })
        )}
        {visibleCount < filteredEvents.length && (
            <div className="text-center mt-6">
                <button onClick={() => setVisibleCount(c => c + 15)} className="bg-surface hover:bg-gray-700 text-text-secondary font-semibold py-2 px-4 rounded-lg">
                    Carica altro
                </button>
            </div>
        )}
      </div>
      
      {/* Confirmation Modal */}
      {eventToConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
          <div className="bg-surface rounded-lg p-6 w-full max-w-sm m-4 text-center shadow-2xl">
            <h3 className="font-bold text-lg mb-2">Conferma azione</h3>
            <p className="text-text-secondary mb-6">
              Sei sicuro di voler {eventToConfirm.status === EventStatus.Completed ? 'contrassegnare come "Da Fare"' : 'contrassegnare come "Completato"'} l'evento "{eventToConfirm.title}"?
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setEventToConfirm(null)} className="px-4 py-2 rounded-md bg-gray-600 hover:bg-gray-500 font-semibold transition-colors">Annulla</button>
              <button onClick={handleConfirmToggle} className="px-4 py-2 rounded-md bg-primary hover:bg-violet-700 text-white font-semibold transition-colors">Conferma</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
