// Fix: Provide full content for the Calendar component to resolve module errors.
import React, { useState, useMemo } from 'react';
import { Event, User } from '../types';
import { Icons } from './Icons';
import YearMonthPicker from './YearMonthPicker';

interface CalendarViewProps {
  events: Event[];
  onEventSelect: (event: Event) => void;
  onAddEvent: (date: Date) => void;
  user: User;
}

const CalendarView: React.FC<CalendarViewProps> = ({ events, onEventSelect, onAddEvent, user }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  
  const today = new Date();
  today.setHours(0,0,0,0);

  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
  const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

  const daysInMonth = useMemo(() => {
    const days = [];
    const startingDay = firstDayOfMonth.getDay(); // 0 = Sunday, 1 = Monday...
    
    // Add blank days for the first week
    for (let i = 0; i < startingDay; i++) {
      days.push(null);
    }
    // Add days of the month
    for (let i = 1; i <= lastDayOfMonth.getDate(); i++) {
      days.push(new Date(currentDate.getFullYear(), currentDate.getMonth(), i));
    }
    return days;
  }, [currentDate]);

  const eventsByDate = useMemo(() => {
    const filteredEvents = user.google_calendar_connected ? events : events.filter(e => e.source === 'local');
    return filteredEvents.reduce((acc, event) => {
        const dateKey = new Date(event.start_datetime).toDateString();
        if (!acc[dateKey]) {
            acc[dateKey] = [];
        }
        acc[dateKey].push(event);
        return acc;
    }, {} as Record<string, Event[]>);
  }, [events, user.google_calendar_connected]);
  
  const selectedDayEvents = useMemo(() => {
    const key = selectedDate.toDateString();
    return (eventsByDate[key] || []).sort((a,b) => new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime());
  }, [selectedDate, eventsByDate]);

  const changeMonth = (amount: number) => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() + amount, 1));
  };
  
  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDate(new Date());
  };

  const handleDateSelect = (date: Date) => {
      setIsPickerOpen(false);
      setCurrentDate(date);
      setSelectedDate(date);
  }

  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <div className="h-full flex flex-col relative">
      {/* Header */}
      <header className="flex-shrink-0 p-4 md:p-6 lg:px-8 flex justify-between items-center border-b border-surface">
        <div className="max-w-6xl mx-auto w-full flex justify-between items-center">
          <button onClick={() => setIsPickerOpen(true)} className="flex items-center gap-1">
            <h1 className="text-xl font-bold">{currentDate.toLocaleString('it-IT', { month: 'long', year: 'numeric' })}</h1>
            <Icons.ChevronDown className="h-5 w-5"/>
          </button>
        <div className="flex items-center gap-2">
          <button onClick={goToToday} className="px-3 py-1 text-sm border border-gray-600 rounded-md hover:bg-surface">Oggi</button>
          <button onClick={() => changeMonth(-1)} className="p-1 hover:bg-surface rounded-full"><Icons.ChevronLeft className="h-6 w-6" /></button>
          <button onClick={() => changeMonth(1)} className="p-1 hover:bg-surface rounded-full"><Icons.ChevronRight className="h-6 w-6" /></button>
        </div>
        </div>
      </header>

      {/* Calendar Grid */}
      <div className="px-2 md:px-4 lg:px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-7 text-center text-xs font-bold text-text-secondary border-b border-surface">
            {['DOM', 'LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB'].map(day => (
              <div key={day} className="py-2">{day}</div>
            ))}
          </div>

          <div className="grid grid-cols-7">
        {daysInMonth.map((day, index) => (
          <div key={index} onClick={() => day && setSelectedDate(day)} className="h-16 border-b border-r border-surface p-1 text-sm text-center cursor-pointer hover:bg-surface/50 transition-colors">
            {day && (
              <div
                className={`w-7 h-7 flex items-center justify-center rounded-full mx-auto 
                  ${day.toDateString() === today.toDateString() ? 'bg-secondary text-white' : ''}
                  ${day.toDateString() === selectedDate.toDateString() ? 'bg-primary text-white' : ''}
                `}
              >
                {day.getDate()}
              </div>
            )}
            {day && eventsByDate[day.toDateString()] && (
                <div className="flex justify-center mt-1">
                    {eventsByDate[day.toDateString()].slice(0, 3).map(event => (
                        <div key={event.id} className="w-1.5 h-1.5 rounded-full mx-0.5" style={{ backgroundColor: event.color || event.category?.color }}></div>
                    ))}
                </div>
            )}
          </div>
        ))}
          </div>
        </div>
      </div>

      {/* Agenda/Timeline View */}
      <div className="flex-shrink-0 h-[45%] flex flex-col border-t-2 border-primary px-2 md:px-4 lg:px-6">
        <div className="max-w-6xl mx-auto w-full flex flex-col h-full">
          <h2 className="p-2 text-center font-bold text-sm bg-surface rounded-t-lg">{selectedDate.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' })}</h2>
          <div className="flex-grow overflow-y-auto relative">
          {/* Hour Grid Background */}
          <div className="absolute top-0 left-0 w-full h-full grid grid-rows-24">
            {hours.map(hour => (
              <div key={hour} className="h-12 border-b border-surface/50 flex items-start">
                  <span className="text-xs text-text-secondary -mt-2 ml-2">{`${hour.toString().padStart(2, '0')}:00`}</span>
              </div>
            ))}
          </div>
          {/* Events */}
          <div className="relative h-full">
            {selectedDayEvents.map(event => {
                const start = new Date(event.start_datetime);
                const end = event.end_datetime ? new Date(event.end_datetime) : new Date(start.getTime() + 60 * 60 * 1000); // Default 1h duration
                const top = (start.getHours() + start.getMinutes() / 60) * 3; // 3rem (h-12) per hour
                const height = Math.max(((end.getTime() - start.getTime()) / (1000 * 60 * 60)) * 3, 1.5); // Min height 0.75rem

                return (
                    <div 
                        key={event.id}
                        onClick={() => onEventSelect(event)}
                        className="absolute left-12 right-2 p-1 rounded-md text-white text-xs z-10 cursor-pointer"
                        style={{ top: `${top}rem`, height: `${height}rem`, backgroundColor: event.color || event.category?.color }}
                    >
                        <p className="font-bold truncate">{event.title}</p>
                        <p className="opacity-80 truncate">{start.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })} - {end.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}</p>
                        {event.source === 'google' && <Icons.Google className="absolute top-1 right-1 h-3 w-3 bg-white rounded-full p-0.5" />}
                    </div>
                )
            })}
             {selectedDayEvents.length === 0 && (
                <p className="text-center text-text-secondary pt-10">Nessun evento per questo giorno.</p>
            )}
          </div>
          </div>
        </div>
      </div>
      
       <button 
        onClick={() => onAddEvent(selectedDate)}
        className="absolute bottom-24 right-4 bg-primary text-white rounded-full p-4 shadow-lg hover:bg-violet-700 transition-colors z-40"
        aria-label="Aggiungi Evento"
      >
        <Icons.Plus className="h-8 w-8" />
      </button>

      {isPickerOpen && (
        <YearMonthPicker 
            currentDate={currentDate}
            onClose={() => setIsPickerOpen(false)}
            onDateSelect={handleDateSelect}
        />
      )}
    </div>
  );
};

export default CalendarView;
