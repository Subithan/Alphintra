import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define route protection patterns
const protectedRoutes = {
  agent: [
    '/support/dashboard',
    '/support/tickets',
    '/support/analytics',
    '/support/team',
    '/support/knowledge-base/admin'
  ],
  manager: [
    '/support/analytics',
    '/support/team',
    '/support/reports'
  ],
  user: [
    '/support',
    '/dashboard',
    '/strategy',
    '/trading'
  ]
};

const publicRoutes = [
  '/login',
  '/register',
  '/support',
  '/support/dashboard',
  '/support/knowledge-base',
  '/api/health',
  '/_next',
  '/favicon.ico',
  '/logo.png',
  '/site.webmanifest',
  '/apple-touch-icon.png',
  '/icon',
  '/manifest'
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('auth_token')?.value || 
                request.headers.get('authorization')?.replace('Bearer ', '');

  // Allow public routes
  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  // Check if user is authenticated
  if (!token) {
    return redirectToLogin(request);
  }

  // For protected routes, verify user roles
  if (isProtectedRoute(pathname)) {
    // In a real implementation, you would verify the JWT token here
    // and extract user roles to check permissions
    const userRoles = getUserRolesFromToken(token);
    
    if (!hasRequiredPermissions(pathname, userRoles)) {
      return NextResponse.json(
        { error: 'Insufficient permissions' },
        { status: 403 }
      );
    }
  }

  return NextResponse.next();
}

function isPublicRoute(pathname: string): boolean {
  // Allow root path and exact public routes
  if (pathname === '/') return true;
  
  return publicRoutes.some(route => 
    pathname.startsWith(route)
  );
}

function isProtectedRoute(pathname: string): boolean {
  return Object.values(protectedRoutes).flat().some(route =>
    pathname.startsWith(route)
  );
}

function redirectToLogin(request: NextRequest): NextResponse {
  const loginUrl = new URL('/login', request.url);
  loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
  return NextResponse.redirect(loginUrl);
}

function getUserRolesFromToken(token: string): string[] {
  // In a real implementation, decode and verify the JWT token
  // For now, return mock roles based on token content
  try {
    // This is a simplified mock implementation
    // In production, use a proper JWT library to decode and verify
    if (token.includes('agent')) {
      return ['USER', 'SUPPORT_AGENT'];
    }
    if (token.includes('manager')) {
      return ['USER', 'SUPPORT_AGENT', 'SUPPORT_MANAGER'];
    }
    return ['USER'];
  } catch (error) {
    console.error('Error decoding token:', error);
    return [];
  }
}

function hasRequiredPermissions(pathname: string, userRoles: string[]): boolean {
  // Check agent routes
  if (protectedRoutes.agent.some(route => pathname.startsWith(route))) {
    return userRoles.includes('SUPPORT_AGENT');
  }

  // Check manager routes
  if (protectedRoutes.manager.some(route => pathname.startsWith(route))) {
    return userRoles.includes('SUPPORT_MANAGER');
  }

  // Check user routes
  if (protectedRoutes.user.some(route => pathname.startsWith(route))) {
    return userRoles.includes('USER');
  }

  return true;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, logo.png, etc. (static assets)
     * - site.webmanifest (PWA manifest)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|logo.png|site.webmanifest|apple-touch-icon.png|icon|manifest).*)',
  ],
};