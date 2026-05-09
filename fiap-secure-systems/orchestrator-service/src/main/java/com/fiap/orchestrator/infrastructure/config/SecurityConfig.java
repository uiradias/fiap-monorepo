package com.fiap.orchestrator.infrastructure.config;

import com.fiap.orchestrator.adapter.in.security.InternalHmacFilter;
import com.fiap.orchestrator.application.service.Clock;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class SecurityConfig {

    private final String hmacSecret;
    private final int replayWindowSeconds;
    private final Clock clock;

    public SecurityConfig(
            @Value("${orchestrator.internal-hmac-secret}") String hmacSecret,
            @Value("${orchestrator.internal-hmac-replay-window-seconds:300}") int replayWindowSeconds,
            Clock clock) {
        this.hmacSecret = hmacSecret;
        this.replayWindowSeconds = replayWindowSeconds;
        this.clock = clock;
    }

    @Bean
    public InternalHmacFilter internalHmacFilter() {
        return new InternalHmacFilter(hmacSecret, replayWindowSeconds, clock);
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http, InternalHmacFilter hmacFilter)
            throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                    .requestMatchers("/actuator/health", "/actuator/info").permitAll()
                    .anyRequest().permitAll()
            )
            .addFilterBefore(hmacFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }
}
