import React from 'react';
import { Document } from '../types';
import { Icons } from './Icons';

interface DocumentsProps {
  documents: Document[];
}

const Documents: React.FC<DocumentsProps> = ({ documents }) => {
  return (
    <div className="p-4 space-y-4">
      <div className="flex gap-2">
        <input 
          type="text" 
          placeholder="Cerca documenti..."
          className="flex-grow bg-surface p-2 rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <button className="bg-surface p-2 rounded-lg">Filtri</button>
      </div>
      {documents.length === 0 ? (
        <div className="text-center py-10">
            <p className="text-text-secondary">Nessun documento caricato.</p>
        </div>
      ) : (
        <div className="space-y-3">
            {documents.map(doc => (
                <div key={doc.id} className="bg-surface p-3 rounded-lg">
                    <div className="flex justify-between items-start">
                        <h4 className="font-bold text-text-primary flex items-center gap-2"><Icons.Document className="h-5 w-5 text-accent"/> {doc.filename}</h4>
                        {doc.extracted_amount && <span className="font-semibold text-primary">€{doc.extracted_amount.toFixed(2)}</span>}
                    </div>
                    <p className="text-sm text-text-secondary mt-1 line-clamp-2">{doc.ai_summary}</p>
                    <div className="text-xs text-gray-400 mt-2 flex justify-between">
                        <span>Caricato: {new Date(doc.upload_date).toLocaleDateString()}</span>
                        {doc.event && <span>Associato a: {doc.event.title}</span>}
                    </div>
                </div>
            ))}
        </div>
      )}
    </div>
  );
};

export default Documents;
