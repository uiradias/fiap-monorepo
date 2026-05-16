package com.fiap.gateway.infrastructure.config;

import java.io.IOException;
import java.util.List;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.adapter.in.ratelimit.RateLimitFilter;
import com.fiap.gateway.adapter.in.security.JwtAuthenticationFilter;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;

import jakarta.servlet.http.HttpServletResponse;

@Configuration
@ConditionalOnWebApplication(type = ConditionalOnWebApplication.Type.SERVLET)
public class SecurityConfig {

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter(
            TokenIssuerPort tokens, ObjectMapper objectMapper) {
        return new JwtAuthenticationFilter(tokens, objectMapper);
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        // Demo CORS posture: allow the locally-served SPA origin so the browser can call /api/*.
        // Production deployments should either restrict this to the real frontend origin or
        // proxy the gateway behind the same origin via nginx (the demo's nginx config does NOT
        // proxy — that's the production-correct hardening flagged in the README).
        CorsConfiguration cfg = new CorsConfiguration();
        // Patterns: any port on localhost / 127.0.0.1 (SPA dev, Docker mapped ports, 127.0.0.1 vs
        // localhost).
        cfg.setAllowedOriginPatterns(List.of("http://localhost:*", "http://127.0.0.1:*"));
        cfg.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        cfg.setAllowedHeaders(List.of("*"));
        cfg.setAllowCredentials(true);
        cfg.setMaxAge(3600L);
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", cfg);
        return source;
    }

    @Bean
    public SecurityFilterChain filterChain(
            HttpSecurity http,
            JwtAuthenticationFilter jwtFilter,
            RateLimitFilter rateLimitFilter,
            @Qualifier("corsConfigurationSource") CorsConfigurationSource corsSource,
            ObjectMapper objectMapper)
            throws Exception {
        AccessDeniedHandler anonymousAsUnauthorized =
                (request, response, accessDeniedException) -> {
                    Authentication auth = SecurityContextHolder.getContext().getAuthentication();
                    if (auth == null || auth instanceof AnonymousAuthenticationToken) {
                        writeProblem(
                                response,
                                objectMapper,
                                HttpStatus.UNAUTHORIZED,
                                "Not authenticated",
                                "NOT_AUTHENTICATED");
                    } else {
                        writeProblem(
                                response,
                                objectMapper,
                                HttpStatus.FORBIDDEN,
                                "Access denied",
                                "ACCESS_DENIED");
                    }
                };

        http.csrf(AbstractHttpConfigurer::disable)
                .cors(c -> c.configurationSource(corsSource))
                .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(
                        reg ->
                                reg.requestMatchers(HttpMethod.OPTIONS, "/**")
                                        .permitAll() // CORS preflight
                                        .requestMatchers(
                                                HttpMethod.POST,
                                                "/api/v1/auth/register",
                                                "/api/v1/auth/login",
                                                "/api/v1/auth/refresh")
                                        .permitAll()
                                        .requestMatchers(
                                                HttpMethod.GET,
                                                "/actuator/health",
                                                "/actuator/info")
                                        .permitAll()
                                        .requestMatchers("/ws/sessions/**")
                                        .permitAll() // WS handshake-time JWT check (Task 16)
                                        .anyRequest()
                                        .authenticated())
                .exceptionHandling(ex -> ex.accessDeniedHandler(anonymousAsUnauthorized))
                .addFilterBefore(rateLimitFilter, UsernamePasswordAuthenticationFilter.class)
                .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }

    private static void writeProblem(
            HttpServletResponse response,
            ObjectMapper mapper,
            HttpStatus status,
            String detail,
            String code)
            throws IOException {
        response.setStatus(status.value());
        response.setContentType(MediaType.APPLICATION_PROBLEM_JSON_VALUE);
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(status, detail);
        pd.setTitle(status == HttpStatus.UNAUTHORIZED ? "Unauthorized" : "Forbidden");
        pd.setProperty("code", code);
        mapper.writeValue(response.getWriter(), pd);
    }
}
