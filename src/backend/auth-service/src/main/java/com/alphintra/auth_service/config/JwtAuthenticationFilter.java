package com.alphintra.auth_service.config;

import com.alphintra.auth_service.entity.User;
import com.alphintra.auth_service.service.AuthService;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final AuthService authService;

    public JwtAuthenticationFilter(AuthService authService) {
        this.authService = authService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            String token = header.substring(7);
            if (authService.validateToken(token)) {
                try {
                    Claims claims = Jwts.parser()
                            .setSigningKey(authService.getJwtSecret()) // Assume added getter in AuthService
                            .parseClaimsJws(token)
                            .getBody();
                    String username = claims.getSubject();
                    if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                        User user = (User) loadUserByUsername(username); // Cast for principal
                        UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                                user, null, user.getRoles().stream().map(role -> new org.springframework.security.core.authority.SimpleGrantedAuthority("ROLE_" + role.getName())).toList());
                        authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                        SecurityContextHolder.getContext().setAuthentication(authToken);
                    }
                } catch (Exception e) {
                    // Invalid token, continue without auth
                }
            }
        }
        filterChain.doFilter(request, response);
    }

    // Temp loadUserByUsername; use UserDetailsService
    private UserDetails loadUserByUsername(String username) {
        // Add method if needed nject UserRepository and return new UserDetails impl wrapping User
        return org.springframework.security.core.userdetails.User.builder()
                .username(username)
                .password("") // No pass needed post-auth
                .authorities("ROLE_USER") // Default; expand with roles
                .build();
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path.startsWith("/api/auth") || path.startsWith("/api/auth/");
    }
}