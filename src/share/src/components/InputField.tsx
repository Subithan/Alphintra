import React from 'react';
import { LucideIcon } from 'lucide-react'; // Importing LucideIcon type

// Define props for the InputField component
interface InputFieldProps {
  id: string;
  label: string;
  type: string;
  name: string;
  value: string;
  placeholder: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string; // Optional error message
  Icon?: LucideIcon; // Optional icon component from lucide-react
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
  Icon, // Destructure the Icon prop
}) => {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
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
          className={`w-full py-2.5 px-3 border rounded-md text-sm  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700
            ${Icon ? 'pl-10' : ''} ${error ? 'border-red-500' : 'border-gray-300'}`}
          placeholder={placeholder}
        />
      </div>
      {error && (
        <p className="text-red-600 text-xs mt-1">{error}</p>
      )}
    </div>
  );
};

export default InputField;
