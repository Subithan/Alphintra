// package com.alphintra.trading_engine.service;

// import io.jsonwebtoken.Claims;
// import io.jsonwebtoken.Jwts;
// import jakarta.servlet.FilterChain;
// import jakarta.servlet.ServletException;
// import jakarta.servlet.http.HttpServletRequest;
// import jakarta.servlet.http.HttpServletResponse;
// import org.springframework.beans.factory.annotation.Value;
// import org.springframework.security.core.context.SecurityContextHolder;
// import org.springframework.stereotype.Component;
// import org.springframework.web.filter.OncePerRequestFilter;

// import java.io.IOException;
// import java.util.Date;

// @Component
// public class JwtValidationFilter extends OncePerRequestFilter {

//     @Value("${jwt.secret:OTc0MjZhMWMtM2NmOS00OGZlLTk1MjEtNzYwNWRlZTg=}") // Same secret as auth-service
//     private String jwtSecret;

//     @Override
//     protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
//             throws ServletException, IOException {
//         // ====================================================================
//         // DEVELOPMENT MODE: JWT VALIDATION DISABLED
//         // For production, uncomment the validation logic below
//         // ====================================================================
//         System.err.println("⚠️  DEV MODE (Trading Engine): JWT validation is DISABLED - allowing all requests");
//         filterChain.doFilter(request, response);
        
//         // ====================================================================
//         // COMMENTED OUT FOR DEVELOPMENT - PRODUCTION JWT VALIDATION
//         // ====================================================================
//         /*
//         String header = request.getHeader("Authorization");
//         if (header != null && header.startsWith("Bearer ")) {
//             String token = header.substring(7);
//             try {
//                 Claims claims = Jwts.parser()
//                         .setSigningKey(jwtSecret)
//                         .parseClaimsJws(token)
//                         .getBody();
//                 if (claims.getExpiration().before(new Date())) {
//                     throw new RuntimeException("Token expired");
//                 }
//                 // String username = claims.getSubject();
//                 // Load user/roles using username
//                 // Set to SecurityContext if using Spring Security (similar to auth-service)
//                 SecurityContextHolder.getContext().setAuthentication(
//                     new org.springframework.security.authentication.UsernamePasswordAuthenticationToken(
//                         claims.getSubject(), null, null // Add authorities from claims.get("roles")
//                     )
//                 );
//             } catch (Exception e) {
//                 response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
//                 response.getWriter().write("Invalid token");
//                 return;
//             }
//         }
//         filterChain.doFilter(request, response);
//         */
//     }

//     @Override
//     protected boolean shouldNotFilter(HttpServletRequest request) {
//         // Skip public endpoints, e.g., /api/public/**
//         return request.getRequestURI().startsWith("/api/public");
//     }
// }