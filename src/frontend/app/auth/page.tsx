'use client';
import Image from 'next/image';
import React, { useState } from 'react';
import { Mail, User, TrendingUp, BarChart3, Shield } from 'lucide-react';

import InputField from '../../components/auth/InputField';
import PasswordInput from '../../components/auth/PasswordInput';

interface FormData {
  email: string;
  password: string;
  confirmPassword?: string;
  firstName?: string;
  lastName?: string;
}

const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: ''
  });
  const [errors, setErrors] = useState<Partial<FormData>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormData]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
    setMessage(null);
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<FormData> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (!isLogin) {
      if (!formData.firstName) {
        newErrors.firstName = 'First name is required';
      }
      if (!formData.lastName) {
        newErrors.lastName = 'Last name is required';
      }
      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Please confirm your password';
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    setMessage(null);
    if (!validateForm()) return;

    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      console.log(isLogin ? 'Login data:' : 'Signup data:', formData);
      setMessage({
        type: 'success',
        text: `${isLogin ? 'Login' : 'Account creation'} successful! Welcome to trading!`
      });
      setIsLoading(false);
      
      // Redirect to dashboard on success
      if (typeof window !== 'undefined') {
        window.location.href = '/dashboard';
      }
    }, 1500);
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({
      email: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: ''
    });
    setErrors({});
    setMessage(null);
  };

  return (
    <div className="min-h-screen bg-black grid grid-cols-[1fr_min-content_1fr] font-['Inter']">
      {/* Left Side - Branding */}
      <div className="bg-black relative overflow-hidden flex items-center justify-center pl-30">
        {/* Content */}
        <div className="relative z-10 text-center text-white max-w-md">
          {/* Logo */}
          <div className="mb-8">
            <Image
              src="/images/blueLogo.png"
              alt="Alphintra Logo"
              width={192}
              height={192}
              className="w-48 h-48 object-contain mx-auto mb-6 animate-float"
            />
          </div>

          {/* Title */}
          <h1 className="text-5xl font-bold mb-4 text-white">
            ALPHINTRA
          </h1>

          {/* Subtitle */}
          <p className="text-xl text-white/80 mb-4 font-medium">
            Let the Bot do the Hustle.
          </p>

          {/* Description */}
          <p className="text-xs text-white/70 mb-0 leading-relaxed">
            Professional trading platform with advanced tools, real-time data, and secure transactions. Start your trading journey today.
          </p>
        </div>
      </div>
          
      {/* Gradient Separator Line */}
      <div className="w-[2px] h-full bg-gradient-to-b from-black via-yellow-500 to-black"></div>

      {/* Right Side - Form */}
      <div className="flex items-center justify-center pr-20">
        <div className="w-full max-w-md bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-xl border border-white/20">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">
              {isLogin ? 'Welcome back' : 'Welcome'}
            </h2>
            <p className="text-white/80">
              {isLogin ? 'Sign in to your account' : 'Create your trading account'}
            </p>
          </div>

          {/* Form Container */}
          <div>
            {/* Mode Toggle Buttons */}
            <div className="flex bg-white/20 rounded-xl p-1 mb-6">
              <button
                type="button"
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${
                  isLogin
                    ? 'bg-yellow-500 text-black shadow-lg'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${
                  !isLogin
                    ? 'bg-yellow-500 text-black shadow-lg'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Sign Up
              </button>
            </div>

            {/* Message Display */}
            {message && (
              <div
                className={`p-4 mb-6 rounded-xl text-sm font-medium ${
                  message.type === 'success'
                    ? 'bg-green-500/20 text-green-200 border border-green-400/50'
                    : 'bg-red-500/20 text-red-200 border border-red-400/50'
                }`}
              >
                {message.text}
              </div>
            )}

            <div className="space-y-5">
              {/* Name Fields (Signup Only) */}
              {!isLogin && (
                <div className="grid grid-cols-2 gap-4">
                  <InputField
                    id="firstName"
                    label="First Name"
                    type="text"
                    name="firstName"
                    value={formData.firstName || ''}
                    onChange={handleInputChange}
                    placeholder="John"
                    error={errors.firstName}
                    Icon={User}
                  />
                  <InputField
                    id="lastName"
                    label="Last Name"
                    type="text"
                    name="lastName"
                    value={formData.lastName || ''}
                    onChange={handleInputChange}
                    placeholder="Doe"
                    error={errors.lastName}
                    Icon={User}
                  />
                </div>
              )}

              {/* Email Input */}
              <InputField
                id="email"
                label="Email Address"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="john.doe@example.com"
                error={errors.email}
                Icon={Mail}
              />

              {/* Password Input */}
              <PasswordInput
                id="password"
                label="Password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                error={errors.password}
              />

              {/* Confirm Password Input (Signup Only) */}
              {!isLogin && (
                <PasswordInput
                  id="confirmPassword"
                  label="Confirm Password"
                  name="confirmPassword"
                  value={formData.confirmPassword || ''}
                  onChange={handleInputChange}
                  placeholder="Confirm your password"
                  error={errors.confirmPassword}
                />
              )}

              {/* Forgot Password Link (Login Only) */}
              {isLogin && (
                <div className="text-right">
                  <button
                    type="button"
                    className="text-sm text-yellow-400 hover:text-yellow-300 font-medium transition-colors"
                  >
                    Forgot your password?
                  </button>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 disabled:from-yellow-400 disabled:to-yellow-500 text-black font-semibold py-3 px-6 rounded-lg text-sm transition-all duration-200 flex items-center justify-center shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-black border-t-transparent"></div>
                ) : (
                  isLogin ? 'Sign In' : 'Create Account'
                )}
              </button>

              {/* Terms & Privacy (Signup Only) */}
              {!isLogin && (
                <p className="text-xs text-gray-300 text-center mt-4">
                  By creating an account, you agree to our{' '}
                  <button type="button" className="text-yellow-400 hover:text-yellow-300 transition-colors">
                    Terms of Service
                  </button>{' '}
                  and{' '}
                  <button type="button" className="text-yellow-400 hover:text-yellow-300 transition-colors">
                    Privacy Policy
                  </button>
                </p>
              )}
            </div>
          </div>

          {/* Switch Mode Section */}
          <div className="text-center mt-6">
            <p className="text-sm text-white/80">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              <button
                type="button"
                onClick={toggleMode}
                className="ml-2 text-yellow-400 hover:text-yellow-300 font-medium transition-colors"
              >
                {isLogin ? 'Create one' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;