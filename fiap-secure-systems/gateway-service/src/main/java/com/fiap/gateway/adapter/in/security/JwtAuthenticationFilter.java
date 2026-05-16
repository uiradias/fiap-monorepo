package com.fiap.gateway.adapter.in.security;

import java.io.IOException;
import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.adapter.in.rest.dto.ProblemDetailFactory;
import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.model.UserId;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final TokenIssuerPort tokens;
    private final ObjectMapper mapper;

    public JwtAuthenticationFilter(TokenIssuerPort tokens, ObjectMapper mapper) {
        this.tokens = tokens;
        this.mapper = mapper;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String header = req.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            String jws = header.substring("Bearer ".length()).trim();
            try {
                UserId uid = tokens.verifyAccessToken(jws);
                var auth =
                        new UsernamePasswordAuthenticationToken(
                                uid, null, List.of(new SimpleGrantedAuthority("ROLE_USER")));
                SecurityContextHolder.getContext().setAuthentication(auth);
            } catch (InvalidTokenException e) {
                SecurityContextHolder.clearContext();
                ProblemDetail pd =
                        ProblemDetailFactory.of(
                                HttpStatus.UNAUTHORIZED,
                                "Invalid or expired token",
                                e.getMessage() != null ? e.getMessage() : "access token rejected",
                                "INVALID_TOKEN");
                res.setStatus(HttpStatus.UNAUTHORIZED.value());
                res.setContentType("application/problem+json;charset=UTF-8");
                mapper.writeValue(res.getWriter(), pd);
                return;
            }
        }
        chain.doFilter(req, res);
    }
}
