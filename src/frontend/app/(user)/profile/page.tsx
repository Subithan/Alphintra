'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import BalanceCard from '@/components/ui/user/dashboard/BalanceCard';
import ProfileCard from '@/components/ui/user/profile/profileCard';
import { VerifyStepper } from '@/components/ui/user/profile/verifyStepper';
import { authServiceApiClient } from '@/lib/api/auth-service-api';

const TOKEN_STORAGE_KEY = 'alphintra_jwt_token';
const USER_STORAGE_KEY = 'alphintra_jwt_user';
const WALLET_CREDENTIALS_KEY = 'alphintra_wallet_credentials';

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
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [claims, setClaims] = useState<TokenClaims | null>(null);
  const [user, setUser] = useState<StoredUser | null>(null);
  const [isConnectedToBinance, setIsConnectedToBinance] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
    const storedUser = localStorage.getItem(USER_STORAGE_KEY);
    const walletCredentials = localStorage.getItem(WALLET_CREDENTIALS_KEY);

    // Check if Binance is connected
    if (walletCredentials) {
      try {
        const credentials = JSON.parse(walletCredentials);
        if (credentials.apiKey && credentials.secretKey) {
          setIsConnectedToBinance(true);
        }
      } catch (error) {
        console.warn('Failed to parse wallet credentials', error);
      }
    }

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
        setFirstName(parsedUser.firstName || '');
        setLastName(parsedUser.lastName || '');
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

  const handleBinanceConnect = () => {
    router.push('/wallet');
  };

  const handleUpdateProfile = async () => {
    if (!user) return;

    try {
      // Call backend API to update profile
      const updatedUser = await authServiceApiClient.updateProfile({
        firstName,
        lastName,
      });

      // Update localStorage with new data
      const storedUser = {
        ...user,
        firstName: updatedUser.firstName,
        lastName: updatedUser.lastName,
      };

      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(storedUser));
      setUser(storedUser);
      setIsEditingProfile(false);
      
      console.log('✅ Profile updated successfully:', updatedUser);
    } catch (error) {
      console.error('❌ Failed to update profile:', error);
      alert('Failed to update profile. Please try again.');
    }
  };

  const handleCancelEdit = () => {
    setFirstName(user?.firstName || '');
    setLastName(user?.lastName || '');
    setIsEditingProfile(false);
  };

  const handleForgotPassword = () => {
    // TODO: Implement password reset flow
    router.push('/forgot-password');
  };

  const handleDeleteAccount = () => {
    setShowDeleteConfirm(true);
  };

  const confirmDeleteAccount = async () => {
    if (!user) return;

    try {
      // Call backend API to delete account
      await authServiceApiClient.deleteAccount();
      
      console.log('✅ Account deleted successfully');
      
      // Clear all localStorage and redirect to alphintra.com
      localStorage.clear();
      window.location.href = 'https://alphintra.com';
    } catch (error: any) {
      console.error('❌ Failed to delete account:', error);
      alert('Failed to delete account. Please try again.');
      setShowDeleteConfirm(false);
    }
  };

  const cancelDeleteAccount = () => {
    setShowDeleteConfirm(false);
  };

  return (
    <div className="min-h-screen flex flex-col gap-6 px-4 py-6 md:px-8 lg:px-14">
      <ProfileCard
        avatarUrl={null}
        nickname={profileName}
      />

      <div className="md:rounded-3xl rounded-2xl border border-border bg-card p-6 md:ml-4 md:mr-7 mx-6 space-y-6">
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Profile Details</h2>
            {!isEditingProfile && (
              <button
                onClick={() => setIsEditingProfile(true)}
                className="px-4 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors"
              >
                Edit Profile
              </button>
            )}
          </div>

          {user && (
            <div className="rounded-xl border border-muted/40 bg-muted/10 p-4">
              {isEditingProfile ? (
                <div className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        First Name
                      </label>
                      <input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-400"
                        placeholder="Enter first name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Last Name
                      </label>
                      <input
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-400"
                        placeholder="Enter last name"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={handleCancelEdit}
                      className="px-4 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleUpdateProfile}
                      className="px-4 py-2 text-sm font-medium bg-yellow-400 hover:bg-yellow-500 text-black rounded-lg transition-colors"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              ) : (
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
                    <dt className="font-medium text-foreground">First Name</dt>
                    <dd>{user.firstName || '—'}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-foreground">Last Name</dt>
                    <dd>{user.lastName || '—'}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-foreground">Role</dt>
                    <dd>{derivedRoles.join(', ')}</dd>
                  </div>
                </dl>
              )}
            </div>
          )}
        </section>

        {/* Binance Connection Section */}
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Exchange Connection</h2>
          <div className="rounded-xl border border-muted/40 bg-muted/10 p-4 flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold text-foreground">Binance API</h3>
              <p className="text-sm text-muted-foreground">
                {isConnectedToBinance 
                  ? 'Your Binance account is connected' 
                  : 'Connect your Binance account to start trading'}
              </p>
            </div>
            <button
              onClick={handleBinanceConnect}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                isConnectedToBinance
                  ? 'bg-green-500 hover:bg-green-600 text-white'
                  : 'bg-yellow-400 hover:bg-yellow-500 text-black'
              }`}
            >
              {isConnectedToBinance ? 'Connected' : 'Connect Binance'}
            </button>
          </div>
        </section>

        <BalanceCard />

        {/* Security Section */}
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Security</h2>
          <div className="rounded-xl border border-muted/40 bg-muted/10 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h3 className="font-semibold text-foreground">Password</h3>
                <p className="text-sm text-muted-foreground">
                  Reset your password to secure your account
                </p>
              </div>
              <button
                onClick={handleForgotPassword}
                className="px-4 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors"
              >
                Change Password
              </button>
            </div>
          </div>
        </section>

        {/* Danger Zone */}
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-red-500">Danger Zone</h2>
          <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h3 className="font-semibold text-foreground">Delete Account</h3>
                <p className="text-sm text-muted-foreground">
                  Permanently delete your account and all associated data
                </p>
              </div>
              <button
                onClick={handleDeleteAccount}
                className="px-4 py-2 text-sm font-medium bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
              >
                Delete Account
              </button>
            </div>
          </div>
        </section>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-xl p-6 max-w-md w-full space-y-4">
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-foreground">Delete Account?</h3>
              <p className="text-sm text-muted-foreground">
                Are you sure you want to delete your account? This action cannot be undone. 
                All your data, including trading history, bots, and wallet connections will be permanently deleted.
              </p>
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={cancelDeleteAccount}
                className="px-4 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteAccount}
                className="px-4 py-2 text-sm font-medium bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
              >
                Yes, Delete My Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
