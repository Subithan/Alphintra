'use client';

import { useEffect, useMemo, useState } from 'react';
import BalanceCard from '@/components/ui/user/dashboard/BalanceCard';
import ProfileCard from '@/components/ui/user/profile/profileCard';
import { VerifyStepper } from '@/components/ui/user/profile/verifyStepper';

const TOKEN_STORAGE_KEY = 'alphintra_jwt_token';
const USER_STORAGE_KEY = 'alphintra_jwt_user';

interface StoredUser {
  id: number;
  email: string;
  username?: string | null;
  userName?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  kycStatus?: string | null;
  kyc_status?: string | null;
  roles?: string[];
  role?: string;
}

interface TokenClaims {
  sub?: string;
  roles?: string[];
  exp?: number;
  iat?: number;
  [key: string]: unknown;
}

const formatDateTime = (epochSeconds?: number) => {
  if (!epochSeconds) return null;
  try {
    return new Date(epochSeconds * 1000).toLocaleString();
  } catch {
    return null;
  }
};

export default function Profile() {
  const [token, setToken] = useState<string | null>(null);
  const [claims, setClaims] = useState<TokenClaims | null>(null);
  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
    const storedUser = localStorage.getItem(USER_STORAGE_KEY);

    if (storedToken) {
      setToken(storedToken);
      try {
        const [, payload] = storedToken.split('.');
        if (payload) {
          const decodedPayload = JSON.parse(atob(payload)) as TokenClaims;
          setClaims(decodedPayload);
        }
      } catch (error) {
        console.warn('Failed to decode JWT payload', error);
        setClaims(null);
      }
    } else {
      setToken(null);
      setClaims(null);
    }

    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser) as StoredUser;
        setUser(parsedUser);
      } catch (error) {
        console.warn('Failed to parse stored user', error);
        setUser(null);
      }
    } else {
      setUser(null);
    }
  }, []);

  const profileName = useMemo(() => {
    if (!user) return 'Guest Trader';
    const fullName = [user.firstName, user.lastName].filter(Boolean).join(' ').trim();
    return fullName || user.username || user.userName || 'Alphintra User';
  }, [user]);

  const maskedToken = useMemo(() => {
    if (!token) return null;
    if (token.length <= 12) return token;
    return `${token.slice(0, 6)}…${token.slice(-6)}`;
  }, [token]);

  const derivedKycStatus = useMemo(() => {
    if (!user) return 'NOT_AVAILABLE';
    return user.kycStatus ?? user.kyc_status ?? 'NOT_AVAILABLE';
  }, [user]);

  const derivedRoles = useMemo(() => {
    if (claims?.roles && claims.roles.length > 0) {
      return claims.roles;
    }
    if (user?.roles && user.roles.length > 0) {
      return user.roles;
    }
    if (user?.role) {
      return [user.role];
    }
    return ['USER'];
  }, [claims?.roles, user]);

  return (
    <div className="min-h-screen flex flex-col gap-6 px-4 py-6 md:px-8 lg:px-14">
      <ProfileCard
        avatarUrl="/images/profile/user-1.jpg"
        nickname={profileName}
        uid={user ? String(user.id) : 'N/A'}
        handle={user?.username ?? user?.userName ?? '—'}
      />

      <VerifyStepper />

      <div className="md:rounded-3xl rounded-2xl border border-border bg-card p-6 md:ml-4 md:mr-7 mx-6 space-y-6">
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Auth Summary</h2>
          <p className="text-sm text-muted-foreground">
            We persist your Alphintra JWT locally so profile details remain available after a refresh. Clear your browser storage if you wish to remove it.
          </p>

          <div className="rounded-xl border border-muted/40 bg-muted/10 p-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <span className="text-sm font-medium text-muted-foreground">Stored JWT</span>
              <span className="font-mono text-sm break-all text-foreground/80">
                {maskedToken ?? 'No token stored'}
              </span>
            </div>
            {claims && (
              <dl className="mt-3 grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                {claims.sub && (
                  <div>
                    <dt className="font-medium text-foreground">Subject</dt>
                    <dd className="font-mono">{claims.sub}</dd>
                  </div>
                )}
                {claims.roles && (
                  <div>
                    <dt className="font-medium text-foreground">Roles</dt>
                    <dd>{claims.roles.join(', ')}</dd>
                  </div>
                )}
                <div>
                  <dt className="font-medium text-foreground">Issued</dt>
                  <dd>{formatDateTime(claims.iat) ?? '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-foreground">Expires</dt>
                  <dd>{formatDateTime(claims.exp) ?? '—'}</dd>
                </div>
              </dl>
            )}
          </div>

          {user && (
            <div className="rounded-xl border border-muted/40 bg-muted/10 p-4">
              <h3 className="text-sm font-semibold text-muted-foreground mb-2">Stored User Details</h3>
              <dl className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <dt className="font-medium text-foreground">Email</dt>
                  <dd>{user.email}</dd>
                </div>
                <div>
                  <dt className="font-medium text-foreground">Username</dt>
                  <dd>{user.username ?? user.userName ?? '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-foreground">KYC Status</dt>
                  <dd>{derivedKycStatus}</dd>
                </div>
                <div>
                  <dt className="font-medium text-foreground">Roles</dt>
                  <dd>{derivedRoles.join(', ')}</dd>
                </div>
              </dl>
            </div>
          )}
        </section>

        <BalanceCard />
      </div>
    </div>
  );
}
