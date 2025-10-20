// Fix: Provide placeholder content for the YearMonthPicker component.
import React, { useState } from 'react';
import { Icons } from './Icons';

interface YearMonthPickerProps {
    currentDate: Date;
    onClose: () => void;
    onDateSelect: (date: Date) => void;
}

const YearMonthPicker: React.FC<YearMonthPickerProps> = ({ currentDate, onClose, onDateSelect }) => {
    const [year, setYear] = useState(currentDate.getFullYear());
    const months = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"];

    const selectMonth = (monthIndex: number) => {
        onDateSelect(new Date(year, monthIndex, 1));
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
            <div className="bg-surface rounded-lg w-72" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center p-2 border-b border-gray-700">
                    <button onClick={() => setYear(y => y-1)} className="p-2 rounded-full hover:bg-gray-700"><Icons.ChevronLeft className="h-5 w-5"/></button>
                    <span className="font-bold text-lg">{year}</span>
                    <button onClick={() => setYear(y => y+1)} className="p-2 rounded-full hover:bg-gray-700"><Icons.ChevronRight className="h-5 w-5"/></button>
                </div>
                <div className="grid grid-cols-4 gap-2 p-2">
                    {months.map((month, index) => (
                        <button 
                            key={month} 
                            onClick={() => selectMonth(index)}
                            className={`p-2 rounded-md text-center hover:bg-primary/50 transition-colors ${currentDate.getFullYear() === year && currentDate.getMonth() === index ? 'bg-primary' : ''}`}
                        >
                            {month}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default YearMonthPicker;
