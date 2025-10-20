import React, { useState } from 'react';
import { User, Category } from '../types';
import CategoryManager from './CategoryManager';
import { Icons } from './Icons';
import { apiService } from '../services/apiService';

interface SettingsProps {
  user: User;
  categories: Category[];
  setCategories: React.Dispatch<React.SetStateAction<Category[]>>;
  onUserUpdate: (user: User) => void;
}

const Settings: React.FC<SettingsProps> = ({ user, categories, setCategories, onUserUpdate }) => {
  const [isSyncing, setIsSyncing] = useState(false);

  const handleGoogleSyncToggle = async () => {
    setIsSyncing(true);
    try {
        let updatedUser;
        if (user.google_calendar_connected) {
            updatedUser = await apiService.disconnectGoogleCalendar();
        } else {
            updatedUser = await apiService.connectGoogleCalendar();
        }
        onUserUpdate(updatedUser);
    } catch(e) {
        console.error("Failed to toggle Google Sync", e);
    } finally {
        setIsSyncing(false);
    }
  }

  return (
    <div className="p-4 space-y-8">
      
      {/* User Profile Section */}
      <div className="flex items-center gap-4">
        <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center text-2xl font-bold">
          {user.email.charAt(0).toUpperCase()}
        </div>
        <div>
          <h2 className="text-xl font-bold">{user.email}</h2>
          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${user.subscription_type === 'pro' ? 'bg-yellow-500 text-black' : 'bg-green-500 text-white'}`}>
            {user.subscription_type.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Subscription Section */}
      {user.subscription_type === 'free' && (
        <div className="bg-surface rounded-lg p-4 text-center">
            <h3 className="font-bold text-lg mb-2">Passa a Pro!</h3>
            <p className="text-text-secondary mb-4">Upload e query AI illimitati, senza pubblicità.</p>
            <button className="bg-primary hover:bg-violet-700 text-white font-bold py-2 px-6 rounded-lg transition-colors w-full">
                Upgrade
            </button>
        </div>
      )}

      {/* Category Management */}
      <CategoryManager categories={categories} setCategories={setCategories} />

      {/* Other Settings */}
      <div className="space-y-2">
        <h3 className="font-bold text-lg mb-2">Impostazioni</h3>
        <div className="bg-surface rounded-lg">
            <div className="flex justify-between items-center p-3">
                <span className="flex items-center gap-2">
                    <Icons.Google className="h-6 w-6" />
                    <span>Sincronizzazione Google Calendar</span>
                </span>
                <button onClick={handleGoogleSyncToggle} disabled={isSyncing} className={`text-sm font-semibold px-3 py-1 rounded-md transition-colors ${
                    user.google_calendar_connected 
                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/40' 
                    : 'bg-green-500/20 text-green-400 hover:bg-green-500/40'
                } disabled:opacity-50`}>
                    {isSyncing ? <Icons.Spinner className="h-5 w-5 animate-spin"/> : (user.google_calendar_connected ? 'Disconnetti' : 'Connetti')}
                </button>
            </div>
            <div className="border-t border-gray-700">
                <button className="w-full flex justify-between items-center p-3 hover:bg-gray-700/50 rounded-b-lg">
                    <span>Preferenze Notifiche</span>
                    <Icons.ChevronRight className="h-5 w-5"/>
                </button>
            </div>
        </div>
         <button className="w-full text-left p-3 mt-4 bg-surface rounded-lg hover:bg-gray-700/50 text-red-400 font-semibold">
            Logout
        </button>
      </div>
    </div>
  );
};

export default Settings;
