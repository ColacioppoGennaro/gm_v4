// Fix: Provide full implementation for the main App component.
// Fix: Imported useState and useEffect from React to fix "Cannot find name" errors.
import React, { useState, useEffect, useCallback } from 'react';
import { Category, Document, Event, User, EventStatus } from './types';
import { apiService } from './services/apiService';
import { Icons } from './components/Icons';
import Auth from './components/Auth';
import Onboarding from './components/Onboarding';
import Dashboard from './components/Dashboard';
import CalendarView from './components/Calendar';
import Documents from './components/Documents';
import Settings from './components/Settings';
import EventModal from './components/EventModal';

type View = 'dashboard' | 'calendar' | 'documents' | 'settings';

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [eventToEdit, setEventToEdit] = useState<Event | undefined>(undefined);
  const [newEventDate, setNewEventDate] = useState<Date | undefined>(undefined);
  const [isAiMode, setIsAiMode] = useState(false);

  // App Data State
  const [user, setUser] = useState<User | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for Google OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const googleAuth = urlParams.get('google_auth');
    
    if (googleAuth === 'success') {
      // Remove query params and reload user data
      window.history.replaceState({}, '', window.location.pathname);
      setCurrentView('settings'); // Navigate to settings to show success
    } else if (googleAuth === 'error') {
      const message = urlParams.get('message') || 'Unknown error';
      console.error('Google OAuth error:', message);
      window.history.replaceState({}, '', window.location.pathname);
    }
    
    // Check if user is authenticated
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setIsLoading(false);
      setIsAuthenticated(false);
      return;
    }

    setIsAuthenticated(true);

    const onboardingComplete = localStorage.getItem('onboardingComplete') === 'true';
    if (!onboardingComplete) {
      setShowOnboarding(true);
    }

    const loadData = async () => {
        try {
            const [userData, eventsData, categoriesData, documentsData] = await Promise.all([
                apiService.getUser(),
                apiService.getEvents(),
                apiService.getCategories(),
                apiService.getDocuments(),
            ]);
            setUser(userData);
            setEvents(eventsData.map(e => ({...e, category: categoriesData.find(c => c.id === e.category_id)})));
            setCategories(categoriesData);
            setDocuments(documentsData);
        } catch (error) {
            console.error("Failed to load initial data", error);
            // If load fails, might be invalid token
            if ((error as any)?.message?.includes('401') || (error as any)?.message?.includes('Authentication')) {
              localStorage.removeItem('auth_token');
              setIsAuthenticated(false);
            }
        } finally {
            setIsLoading(false);
        }
    };
    loadData();
  }, []);

  const handleLoginSuccess = (userData: User) => {
    setUser(userData);
    setIsAuthenticated(true);
    
    // Check onboarding
    const onboardingComplete = localStorage.getItem('onboardingComplete') === 'true';
    if (!onboardingComplete && !userData.onboarding_completed) {
      setShowOnboarding(true);
    }
  };

  const handleOnboardingComplete = () => {
    localStorage.setItem('onboardingComplete', 'true');
    setShowOnboarding(false);
  };

  const handleOpenEventModal = (event?: Event, date?: Date, aiMode = false) => {
    setEventToEdit(event);
    setNewEventDate(date);
    setIsAiMode(aiMode);
    setIsEventModalOpen(true);
  };
  
  const handleAddEvent = useCallback(async (eventData: Omit<Event, 'id'>) => {
    console.log('[handleAddEvent] Starting...', eventData);
    const newEvent = await apiService.addEvent(eventData);
    console.log('[handleAddEvent] Event created:', newEvent);
    const category = categories.find(c => c.id === newEvent.category_id);
    setEvents(prev => [...prev, {...newEvent, category}].sort((a,b) => new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime()));
    setCategories(prev => prev.map(c => c.id === newEvent.category_id ? { ...c, event_count: (c.event_count || 0) + 1 } : c));
    console.log('[handleAddEvent] Closing modal...');
    setIsEventModalOpen(false);
    setEventToEdit(undefined);
    setNewEventDate(undefined);
    setIsAiMode(false);
    console.log('[handleAddEvent] Done!');
  }, [categories]);

  const handleUpdateEvent = useCallback(async (eventData: Event) => {
    const updatedEvent = await apiService.updateEvent(eventData);
    const category = categories.find(c => c.id === updatedEvent.category_id);
    setEvents(prev => prev.map(e => e.id === updatedEvent.id ? {...updatedEvent, category} : e));
    setIsEventModalOpen(false);
    setEventToEdit(undefined);
  }, [categories]);

  const handleToggleEventStatus = async (event: Event) => {
    const newStatus = event.status === EventStatus.Completed ? EventStatus.Pending : EventStatus.Completed;
    const updatedEvent = { ...event, status: newStatus };
    const returnedEvent = await apiService.updateEvent(updatedEvent);
    const category = categories.find(c => c.id === returnedEvent.category_id);
    setEvents(prev => prev.map(e => e.id === returnedEvent.id ? {...returnedEvent, category} : e));
  }

  const handleDeleteEvent = async (eventId: string) => {
    await apiService.deleteEvent(eventId);
    const deletedEvent = events.find(e => e.id === eventId);
    setEvents(prev => prev.filter(e => e.id !== eventId));
     if(deletedEvent) {
        setCategories(prev => prev.map(c => c.id === deletedEvent.category_id ? { ...c, event_count: Math.max(0, (c.event_count || 1) - 1) } : c));
    }
    setIsEventModalOpen(false);
    setEventToEdit(undefined);
  };
  
  const handleCloseEventModal = useCallback(() => {
    setIsEventModalOpen(false);
    setEventToEdit(undefined);
    setNewEventDate(undefined);
    setIsAiMode(false);
  }, []);


  const renderView = () => {
    if (isLoading || !user) {
        return <div className="h-full flex items-center justify-center"><Icons.Spinner className="h-8 w-8 animate-spin text-primary" /></div>;
    }
    switch (currentView) {
      case 'dashboard':
        return <Dashboard events={events} onToggleStatus={handleToggleEventStatus} categories={categories} onEditEvent={handleOpenEventModal} />;
      case 'calendar':
        return <CalendarView events={events} onEventSelect={handleOpenEventModal} onAddEvent={(date) => handleOpenEventModal(undefined, date)} user={user}/>;
      case 'documents':
        return <Documents documents={documents} />;
      case 'settings':
        return <Settings user={user} categories={categories} setCategories={setCategories} onUserUpdate={setUser} />;
      default:
        return <Dashboard events={events} onToggleStatus={handleToggleEventStatus} categories={categories} onEditEvent={handleOpenEventModal} />;
    }
  };

  // Show auth screen if not authenticated
  if (!isAuthenticated && !isLoading) {
    return <Auth onSuccess={handleLoginSuccess} />;
  }

  if (showOnboarding) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }
  
  return (
    <div className="h-screen w-screen bg-background text-text-primary flex flex-col font-sans">
      <main className="flex-grow overflow-y-auto">
        {renderView()}
      </main>

      {/* AI Assistant FAB */}
      {currentView !== 'calendar' && 
        <button 
          onClick={() => handleOpenEventModal(undefined, undefined, true)}
          className="absolute bottom-24 right-4 bg-primary text-white rounded-full p-4 shadow-lg hover:bg-violet-700 transition-colors z-40"
          aria-label="Open AI Assistant"
        >
          <Icons.Sparkles className="h-8 w-8" />
        </button>
      }


      {/* Bottom Navigation */}
      <nav className="flex-shrink-0 bg-surface border-t border-gray-700 flex justify-around items-center">
        {navItems.map(item => (
          <button 
            key={item.view}
            onClick={() => setCurrentView(item.view)}
            className={`flex flex-col items-center justify-center p-3 w-full transition-colors ${currentView === item.view ? 'text-primary' : 'text-text-secondary hover:text-white'}`}
          >
            <item.icon className="h-6 w-6 mb-1" />
            <span className="text-xs font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      {isEventModalOpen && (
        <EventModal
          isOpen={isEventModalOpen}
          onClose={handleCloseEventModal}
          event={eventToEdit}
          categories={categories}
          onSave={eventToEdit ? handleUpdateEvent : handleAddEvent}
          onDelete={handleDeleteEvent}
          defaultDate={newEventDate}
          aiMode={isAiMode}
        />
      )}
    </div>
  );
};

const navItems: { view: View; label: string; icon: React.FC<any> }[] = [
    { view: 'dashboard', label: 'Home', icon: Icons.Home },
    { view: 'calendar', label: 'Calendario', icon: Icons.Calendar },
    { view: 'documents', label: 'Documenti', icon: Icons.Document },
    { view: 'settings', label: 'Impostazioni', icon: Icons.Settings },
];

export default App;
