'use client';

import { useEffect, useMemo, useState } from 'react';
import { authServiceApiClient } from '@/lib/api/auth-service-api';
import {
  EMAIL_VERIFICATION_EXPIRY_MS,
  clearPendingSignup,
  generateVerificationCode,
  loadPendingSignup,
  PendingSignup,
  sendVerificationEmail,
  storePendingSignup,
} from '@/lib/email/verification';

const VerifyEmailPage = () => {
  const [code, setCode] = useState('');
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState<string>('');
  const [pending, setPending] = useState<PendingSignup | null>(null);
  const [resendLoading, setResendLoading] = useState(false);
  const [verifyLoading, setVerifyLoading] = useState(false);

  useEffect(() => {
    const data = loadPendingSignup();
    if (!data) {
      setStatus('error');
      setMessage('No verification request found. Sign up again to receive a code.');
      return;
    }
    console.log('[Verify] Loaded pending signup', data.email);
    setPending(data);
  }, []);

  const expiresInSeconds = useMemo(() => {
    if (!pending) return 0;
    const ms = pending.expiresAt - Date.now();
    return Math.max(Math.floor(ms / 1000), 0);
  }, [pending, status]);

  const handleVerify = async () => {
    if (!pending) return;
    console.log('[Verify] User submitted code', code);
    if (Date.now() > pending.expiresAt) {
      console.warn('[Verify] Code expired');
      setStatus('error');
      setMessage('Verification code expired. Please request a new one.');
      return;
    }

    if (code.trim() !== pending.code) {
      console.warn('[Verify] Invalid code entered');
      setStatus('error');
      setMessage('Invalid verification code. Check the email and try again.');
      return;
    }

    setVerifyLoading(true);

    try {
      console.log('[Verify] OTP valid, registering user');
      const response = await authServiceApiClient.register(pending.formData);
      console.log('[Verify] Registration succeeded', response.user.email);
      clearPendingSignup();

      if (typeof window !== 'undefined') {
        localStorage.setItem('alphintra_jwt_token', response.token);
        localStorage.setItem('alphintra_auth_token', response.token);
        localStorage.setItem('auth_token', response.token);
        localStorage.setItem('alphintra_jwt_user', JSON.stringify(response.user));
        localStorage.setItem('alphintra_email_verified', 'true');
      }
      setStatus('success');
      setMessage('Email verified! Redirecting to your dashboard…');
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1500);
    } catch (error: any) {
      console.error('[Verify] Registration failed', error);
      clearPendingSignup();
      setStatus('error');
      if (error?.response?.status === 409) {
        setMessage('Email already registered. Please sign in instead.');
      } else {
        setMessage('We could not complete the registration. Please try again.');
      }
    } finally {
      setVerifyLoading(false);
    }
  };

  const handleResend = async () => {
    if (!pending) return;
    setResendLoading(true);
    try {
      const newCode = generateVerificationCode();
      await sendVerificationEmail(pending.email, newCode, pending.name ?? pending.email);
      const refreshed: PendingSignup = {
        formData: pending.formData,
        email: pending.email,
        code: newCode,
        expiresAt: Date.now() + EMAIL_VERIFICATION_EXPIRY_MS,
        name: pending.name,
      };
      storePendingSignup(refreshed);
      setPending(refreshed);
      setStatus('success');
      setMessage('New verification code sent.');
    } catch (error) {
      console.error('Resend verification failed', error);
      setStatus('error');
      setMessage('Unable to resend email right now. Please try again later.');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black text-white px-4">
      <div className="max-w-md w-full border border-white/20 bg-white/10 backdrop-blur-lg rounded-2xl p-8 space-y-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Verify your email</h1>
          <p className="text-sm text-white/70">
            {pending
              ? `We sent a code to ${pending.email}. Enter it below to finish setting up your account.`
              : 'No verification details found. Return to the sign-up page to start over.'}
          </p>
          {pending && (
            <p className="text-xs text-white/50">
              The code expires in approximately {Math.ceil(expiresInSeconds / 60)} minutes.
            </p>
          )}
        </div>

        <div className="space-y-4">
          <input
            type="text"
            value={code}
            onChange={(event) => setCode(event.target.value)}
            placeholder="Enter 6-digit code"
            className="w-full rounded-lg bg-black/40 border border-white/20 px-4 py-3 text-lg tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-yellow-400"
          />
          <button
            onClick={handleVerify}
            disabled={!pending || code.trim().length === 0 || verifyLoading}
            className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-semibold py-3 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {verifyLoading ? 'Verifying…' : 'Verify Email'}
          </button>

          <button
            onClick={handleResend}
            disabled={!pending || resendLoading}
            className="w-full border border-yellow-500 text-yellow-400 hover:bg-yellow-500/10 font-medium py-3 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {resendLoading ? 'Resending…' : 'Resend Code'}
          </button>
        </div>

        {message && (
          <p
            className={`text-sm text-center ${
              status === 'success' ? 'text-green-300' : 'text-red-300'
            }`}
          >
            {message}
          </p>
        )}

        <p className="text-xs text-center text-white/40">
          Need help? Contact support@alphintra.com
        </p>
      </div>
    </div>
  );
};

export default VerifyEmailPage;
