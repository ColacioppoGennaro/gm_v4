import React, { useState } from 'react';
import { Icons } from './Icons';

interface OnboardingProps {
  onComplete: () => void;
}

const Onboarding: React.FC<OnboardingProps> = ({ onComplete }) => {
  const [step, setStep] = useState(0);

  const steps = [
    {
      icon: <span className="text-5xl">👋</span>,
      title: 'Benvenuto!',
      description: "SmartLife ti aiuta a organizzare la tua vita con l'intelligenza artificiale.",
    },
    {
      icon: <Icons.Calendar className="h-14 w-14 text-blue-400" />,
      title: 'Sincronizza Calendario',
      description: 'Collega Google Calendar per avere tutti gli eventi in un unico posto.',
      action: 'Connetti Google',
    },
    {
      icon: <span className="text-5xl">🎨</span>,
      title: 'Le Tue Categorie',
      description: 'Organizza gli eventi per ambito. Puoi personalizzarle quando vuoi!',
    },
    {
      icon: <Icons.Sparkles className="h-14 w-14 text-primary" />,
      title: 'Il Tuo Assistente',
      description: 'Scrivi o fotografa documenti, l\'AI crea eventi e promemoria per te!',
    },
  ];

  const currentStep = steps[step];

  return (
    <div className="fixed inset-0 bg-background flex flex-col items-center justify-center p-6 text-center">
      <div className="w-full max-w-sm flex flex-col items-center">
        <div className="mb-8">{currentStep.icon}</div>
        <h2 className="text-3xl font-bold mb-4">{currentStep.title}</h2>
        <p className="text-text-secondary mb-12 h-16">{currentStep.description}</p>
        
        <div className="flex items-center gap-2 mb-12">
            {steps.map((_, index) => (
                <div key={index} className={`h-2 rounded-full transition-all ${index === step ? 'w-6 bg-primary' : 'w-2 bg-surface'}`}></div>
            ))}
        </div>

        <div className="w-full flex items-center justify-between">
            <button 
                onClick={() => step > 0 ? setStep(s => s - 1) : null}
                className={`font-semibold transition-opacity ${step === 0 ? 'opacity-0 cursor-default' : 'opacity-100 hover:text-primary'}`}
                disabled={step === 0}
            >
                Indietro
            </button>
            {step < steps.length - 1 ? (
                 <button onClick={() => setStep(s => s + 1)} className="bg-primary text-white font-bold py-3 px-6 rounded-lg hover:bg-violet-700">
                    {currentStep.action || 'Avanti'}
                </button>
            ) : (
                <button onClick={onComplete} className="bg-secondary text-white font-bold py-3 px-6 rounded-lg hover:bg-emerald-700">
                    Inizia! 🚀
                </button>
            )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
