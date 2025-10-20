import React, { useState } from 'react';
import { Category } from '../types';
import { apiService } from '../services/apiService';
import { Icons } from './Icons';

interface CategoryManagerProps {
  categories: Category[];
  setCategories: React.Dispatch<React.SetStateAction<Category[]>>;
}

const CategoryManager: React.FC<CategoryManagerProps> = ({ categories, setCategories }) => {
  const [newCategoryName, setNewCategoryName] = useState('');
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleAddCategory = async () => {
    if (!newCategoryName.trim()) return;
    const newCategoryData = {
      name: newCategoryName,
      color: `#${Math.floor(Math.random()*16777215).toString(16)}`,
      icon: '🆕',
    };
    try {
        const addedCategory = await apiService.addCategory(newCategoryData);
        setCategories(prev => [...prev, addedCategory]);
        setNewCategoryName('');
    } catch (e) { console.error(e); }
  };
  
  const handleDeleteCategory = async (id: string) => {
    const categoryToDelete = categories.find(cat => cat.id === id);

    if (categoryToDelete && (categoryToDelete.event_count || 0) > 0) {
        setDeleteError('Non è possibile eliminare una categoria che contiene eventi. Per favore, sposta o elimina prima gli eventi in questa categoria.');
        return;
    }

    try {
        await apiService.deleteCategory(id);
        setCategories(prev => prev.filter(c => c.id !== id));
    } catch(e) { console.error(e); }
  }

  return (
    <div>
      <h3 className="font-bold text-lg mb-2">Le Mie Categorie</h3>
      <div className="space-y-2">
        {categories.map(cat => (
          <div key={cat.id} className="flex items-center justify-between p-3 bg-surface rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-2 h-6 rounded" style={{ backgroundColor: cat.color }}></div>
              <span>{cat.icon} {cat.name}</span>
              <span className="text-xs bg-background px-2 py-0.5 rounded-full">{cat.event_count || 0}</span>
            </div>
            <div className="flex items-center gap-2">
                <button className="text-text-secondary hover:text-primary"><Icons.Pencil className="h-5 w-5"/></button>
                <button onClick={() => handleDeleteCategory(cat.id)} className="text-text-secondary hover:text-red-500"><Icons.Trash className="h-5 w-5"/></button>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-2">
        <input 
            type="text" 
            value={newCategoryName}
            onChange={e => setNewCategoryName(e.target.value)}
            placeholder="Nuova categoria..." 
            className="flex-grow bg-surface p-2 rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <button onClick={handleAddCategory} className="bg-secondary p-2 rounded-lg text-white hover:bg-emerald-600"><Icons.Plus className="h-6 w-6"/></button>
      </div>

      {/* Error Modal */}
      {deleteError && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
          <div className="bg-surface rounded-lg p-6 w-full max-w-sm m-4 text-center shadow-2xl">
            <h3 className="font-bold text-lg mb-2 text-yellow-400">Attenzione</h3>
            <p className="text-text-secondary mb-6">
              {deleteError}
            </p>
            <div className="flex justify-center">
              <button onClick={() => setDeleteError(null)} className="px-6 py-2 rounded-md bg-primary hover:bg-violet-700 text-white font-semibold transition-colors">
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryManager;
