package com.alphintra.customersupport.config;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

/**
 * Filter to handle root-level /agents requests and forward them properly.
 */
public class AgentEndpointFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) 
            throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;
        
        String requestURI = httpRequest.getRequestURI();
        
        // Handle /agents request directly without context path
        if ("/agents".equals(requestURI) && "GET".equals(httpRequest.getMethod())) {
            // Set response headers
            httpResponse.setContentType("application/json");
            httpResponse.setCharacterEncoding("UTF-8");
            httpResponse.setStatus(200);
            
            // Add CORS headers
            httpResponse.setHeader("Access-Control-Allow-Origin", "*");
            httpResponse.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
            httpResponse.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
            
            // Write JSON response
            String jsonResponse = "{\"data\":[],\"message\":\"Agents endpoint is working\"}";
            httpResponse.getWriter().write(jsonResponse);
            httpResponse.getWriter().flush();
            return;
        }
        
        // Continue with normal filter chain for other requests
        chain.doFilter(request, response);
    }
}