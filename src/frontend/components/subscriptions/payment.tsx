import React, { useState } from 'react';
import { CreditCard, Lock, Check, AlertCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface PaymentFormData {
  cardNumber: string;
  cardName: string;
  expiryDate: string;
  cvv: string;
  amount: string;
}

interface FormErrors {
  cardNumber?: string;
  cardName?: string;
  expiryDate?: string;
  cvv?: string;
  amount?: string;
}

export default function PaymentGateway() {
  const router = useRouter();
  const [formData, setFormData] = useState<PaymentFormData>({
    cardNumber: '',
    cardName: '',
    expiryDate: '',
    cvv: '',
    amount: '20.00'
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);

  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\s/g, '');
    const match = cleaned.match(/.{1,4}/g);
    return match ? match.join(' ') : cleaned;
  };

  const formatExpiryDate = (value: string) => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length >= 2) {
      return cleaned.slice(0, 2) + '/' + cleaned.slice(2, 4);
    }
    return cleaned;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    let formattedValue = value;

    if (name === 'cardNumber') {
      formattedValue = formatCardNumber(value.replace(/\s/g, '').slice(0, 16));
    } else if (name === 'expiryDate') {
      formattedValue = formatExpiryDate(value.slice(0, 5));
    } else if (name === 'cvv') {
      formattedValue = value.replace(/\D/g, '').slice(0, 4);
    }

    setFormData(prev => ({ ...prev, [name]: formattedValue }));
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (formData.cardNumber.replace(/\s/g, '').length !== 16) {
      newErrors.cardNumber = 'Card number must be 16 digits';
    }

    if (formData.cardName.trim().length < 3) {
      newErrors.cardName = 'Please enter a valid name';
    }

    const expiryMatch = formData.expiryDate.match(/^(\d{2})\/(\d{2})$/);
    if (!expiryMatch) {
      newErrors.expiryDate = 'Invalid expiry date';
    } else {
      const month = parseInt(expiryMatch[1]);
      if (month < 1 || month > 12) {
        newErrors.expiryDate = 'Invalid month';
      }
    }

    if (formData.cvv.length < 3) {
      newErrors.cvv = 'CVV must be 3-4 digits';
    }

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      newErrors.amount = 'Invalid amount';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validateForm()) return;

    setIsProcessing(true);

    // Simulate payment processing
    setTimeout(() => {
      setIsProcessing(false);
      setPaymentSuccess(true);
      
      // Redirect to dashboard after showing success message for 3 seconds
      setTimeout(() => {
        router.push('/dashboard');
      }, 3000);
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  if (paymentSuccess) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Check className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Payment Successful!</h2>
          <p className="text-gray-600 mb-4">Your transaction has been processed successfully.</p>
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-500">Amount Paid</p>
            <p className="text-3xl font-bold text-gray-800">${formData.amount}</p>
          </div>
          <p className="text-sm text-gray-500 mb-4">Transaction ID: TXN{Math.random().toString(36).substr(2, 9).toUpperCase()}</p>
          <p className="text-sm text-indigo-600 font-medium animate-pulse">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
        <div className="flex items-center justify-center mb-6">
          <div className="bg-indigo-600 p-3 rounded-full">
            <CreditCard className="w-8 h-8 text-white" />
          </div>
        </div>
        
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">Secure Payment</h1>
        <p className="text-center text-gray-600 mb-8 flex items-center justify-center gap-2">
          <Lock className="w-4 h-4" />
          Your information is encrypted and secure
        </p>

        <div className="space-y-6" onKeyPress={handleKeyPress}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-lg">$</span>
              <input
                type="text"
                name="amount"
                value="20.00"
                // onChange={handleInputChange}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none text-lg font-semibold bg-white text-gray-800"
                placeholder="0.00"
              />
            </div>
            {errors.amount && (
              <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {errors.amount}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Card Number
            </label>
            <input
              type="text"
              name="cardNumber"
              value={formData.cardNumber}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none bg-white text-gray-800"
              placeholder="1234 5678 9012 3456"
            />
            {errors.cardNumber && (
              <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {errors.cardNumber}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cardholder Name
            </label>
            <input
              type="text"
              name="cardName"
              value={formData.cardName}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none bg-white text-gray-800"
              placeholder="John Doe"
            />
            {errors.cardName && (
              <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {errors.cardName}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Expiry Date
              </label>
              <input
                type="text"
                name="expiryDate"
                value={formData.expiryDate}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none bg-white text-gray-800"
                placeholder="MM/YY"
              />
              {errors.expiryDate && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.expiryDate}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                CVV
              </label>
              <input
                type="password"
                name="cvv"
                value={formData.cvv}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none bg-white text-gray-800"
                placeholder="123"
              />
              {errors.cvv && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.cvv}
                </p>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={isProcessing}
            className="w-full bg-yellow-500 text-white py-4 rounded-lg font-semibold text-lg hover:bg-yellow-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Lock className="w-5 h-5" />
                Pay ${formData.amount}
              </>
            )}
          </button>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-center text-gray-500">
            Protected by 256-bit SSL encryption
          </p>
        </div>
      </div>
    </div>
  );
}