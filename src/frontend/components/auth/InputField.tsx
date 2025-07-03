import React from 'react';
import { LucideIcon } from 'lucide-react';

interface InputFieldProps {
  id: string;
  label: string;
  type: string;
  name: string;
  value: string;
  placeholder: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  Icon?: LucideIcon;
  className?: string;
}

const InputField: React.FC<InputFieldProps> = ({
  id,
  label,
  type,
  name,
  value,
  placeholder,
  onChange,
  error,
  Icon,
  className = "",
}) => {
  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-medium text-white/90 mb-2">
        {label}
      </label>
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        )}
        <input 
          id={id}
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          className={`w-full py-3 px-3 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent text-white bg-white/10 backdrop-blur-sm border-white/20 placeholder-gray-400
            ${Icon ? 'pl-10' : ''} ${error ? 'border-red-500 focus:ring-red-500' : 'border-white/20'}`}
          placeholder={placeholder}
        />
      </div>
      {error && (
        <p className="text-red-400 text-xs mt-1">{error}</p>
      )}
    </div>
  );
};

export default InputField;