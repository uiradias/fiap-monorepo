package com.fiap.gateway.adapter.in.rest;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.application.service.InMemoryFakes;
import com.fiap.gateway.application.service.LoginService;
import com.fiap.gateway.application.service.LogoutService;
import com.fiap.gateway.application.service.RefreshTokenService;
import com.fiap.gateway.application.service.RegisterUserService;
import com.fiap.gateway.application.service.Clock;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;

import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class AuthControllerTest {

    private final InMemoryFakes.FakeUsers users = new InMemoryFakes.FakeUsers();
    private final InMemoryFakes.FakeRefreshTokens tokens = new InMemoryFakes.FakeRefreshTokens();
    private final InMemoryFakes.FakeHasher hasher = new InMemoryFakes.FakeHasher();
    private final InMemoryFakes.FakeTokens issuer = new InMemoryFakes.FakeTokens();
    private final Clock clock = () -> Instant.parse("2026-05-09T12:00:00Z");

    private final RegisterUserService register = new RegisterUserService(users, hasher, clock);
    private final LoginService login = new LoginService(users, tokens, hasher, issuer, clock, Duration.ofDays(7));
    private final RefreshTokenService refresh = new RefreshTokenService(tokens, issuer, clock, Duration.ofDays(7));
    private final LogoutService logout = new LogoutService(tokens, issuer, clock);

    private final MockMvc mvc = MockMvcBuilders
            .standaloneSetup(new AuthController(register, login, refresh, logout))
            .setControllerAdvice(new GlobalExceptionHandler())
            .build();
    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    void register_then_login_round_trip() throws Exception {
        mvc.perform(post("/api/v1/auth/register")
                        .contentType(APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of(
                                "email", "a@b.com", "password", "hunter22", "displayName", "A"))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.userId").exists());

        mvc.perform(post("/api/v1/auth/login")
                        .contentType(APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of(
                                "email", "a@b.com", "password", "hunter22"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.refreshToken").exists());
    }

    @Test
    void duplicate_register_returns_409() throws Exception {
        String body = mapper.writeValueAsString(Map.of(
                "email", "dup@x.com", "password", "hunter22"));
        mvc.perform(post("/api/v1/auth/register").contentType(APPLICATION_JSON).content(body))
                .andExpect(status().isCreated());
        mvc.perform(post("/api/v1/auth/register").contentType(APPLICATION_JSON).content(body))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("EMAIL_TAKEN"));
    }
}
