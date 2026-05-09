package com.fiap.gateway.adapter.in.security;

import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.model.UserId;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final TokenIssuerPort tokens;

    public JwtAuthenticationFilter(TokenIssuerPort tokens) { this.tokens = tokens; }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String header = req.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            String jws = header.substring("Bearer ".length()).trim();
            try {
                UserId uid = tokens.verifyAccessToken(jws);
                var auth = new UsernamePasswordAuthenticationToken(
                        uid, null, List.of(new SimpleGrantedAuthority("ROLE_USER")));
                SecurityContextHolder.getContext().setAuthentication(auth);
            } catch (InvalidTokenException ignored) {
                // leave unauthenticated; controllers / SecurityConfig decide what to do
            }
        }
        chain.doFilter(req, res);
    }
}
