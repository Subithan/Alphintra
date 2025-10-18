'use client';

import emailjs from 'emailjs-com';

export interface SignupFormPayload {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface PendingSignup {
  formData: SignupFormPayload;
  email: string;
  code: string;
  expiresAt: number;
  name?: string;
}

const EMAILJS_SERVICE_ID =
  process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID ?? 'service_hd0x07j';
const EMAILJS_TEMPLATE_ID =
  process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID ?? 'template_bm1j6uo';
const EMAILJS_PUBLIC_KEY =
  process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY ?? 'QuWnJl-wEWqo6qnoL';

export const EMAIL_VERIFICATION_EXPIRY_MS = 10 * 60 * 1000; // 10 minutes
const PENDING_SIGNUP_STORAGE_KEY = 'alphintra_pending_signup';

export const generateVerificationCode = (): string =>
  Math.floor(100000 + Math.random() * 900000).toString();

export async function sendVerificationEmail(
  email: string,
  code: string,
  name?: string
): Promise<void> {
  console.log('[Email] Sending verification email', { email, code });
  await emailjs.send(
    EMAILJS_SERVICE_ID,
    EMAILJS_TEMPLATE_ID,
    {
      to_email: email,
      to_name: name ?? email,
      verification_code: code,
    },
    EMAILJS_PUBLIC_KEY
  );
  console.log('[Email] Verification email sent successfully');
}

export function storePendingSignup(payload: PendingSignup): void {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(
    PENDING_SIGNUP_STORAGE_KEY,
    JSON.stringify(payload)
  );
  console.log('[Email] Stored pending signup payload', payload.email);
}

export function loadPendingSignup(): PendingSignup | null {
  if (typeof window === 'undefined') return null;
  const raw = sessionStorage.getItem(PENDING_SIGNUP_STORAGE_KEY);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as PendingSignup;
    return parsed;
  } catch (error) {
    console.error('[Email] Failed to parse pending signup payload', error);
    return null;
  }
}

export function clearPendingSignup(): void {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem(PENDING_SIGNUP_STORAGE_KEY);
  console.log('[Email] Cleared pending signup payload');
}
