package com.fiap.gateway.adapter.in.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;

import java.time.Instant;
import java.util.UUID;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.core.context.SecurityContextHolder;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.application.service.InMemoryFakes;
import com.fiap.gateway.domain.model.UserId;

import jakarta.servlet.FilterChain;

class JwtAuthenticationFilterTest {

    private final InMemoryFakes.FakeTokens tokens = new InMemoryFakes.FakeTokens();
    private final ObjectMapper mapper = new ObjectMapper().findAndRegisterModules();
    private final JwtAuthenticationFilter filter = new JwtAuthenticationFilter(tokens, mapper);

    @AfterEach
    void clear() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void valid_bearer_sets_principal() throws Exception {
        UserId uid = new UserId(UUID.randomUUID());
        String jws = tokens.issueAccessToken(uid, Instant.now());
        MockHttpServletRequest req = new MockHttpServletRequest("GET", "/api/v1/sessions/x");
        req.addHeader("Authorization", "Bearer " + jws);
        MockHttpServletResponse res = new MockHttpServletResponse();
        FilterChain chain = mock(FilterChain.class);

        filter.doFilter(req, res, chain);

        assertThat(SecurityContextHolder.getContext().getAuthentication().getPrincipal())
                .isEqualTo(uid);
        verify(chain).doFilter(req, res);
    }

    @Test
    void missing_header_leaves_context_empty_and_passes_through() throws Exception {
        MockHttpServletRequest req = new MockHttpServletRequest("GET", "/api/v1/sessions/x");
        MockHttpServletResponse res = new MockHttpServletResponse();
        FilterChain chain = mock(FilterChain.class);

        filter.doFilter(req, res, chain);

        assertThat(SecurityContextHolder.getContext().getAuthentication()).isNull();
        verify(chain).doFilter(req, res);
    }

    @Test
    void invalid_token_returns_401_and_does_not_continue_chain() throws Exception {
        MockHttpServletRequest req = new MockHttpServletRequest("GET", "/api/v1/sessions/x");
        req.addHeader("Authorization", "Bearer junk");
        MockHttpServletResponse res = new MockHttpServletResponse();
        FilterChain chain = mock(FilterChain.class);

        filter.doFilter(req, res, chain);

        assertThat(SecurityContextHolder.getContext().getAuthentication()).isNull();
        verifyNoInteractions(chain);
        assertThat(res.getStatus()).isEqualTo(HttpStatus.UNAUTHORIZED.value());
        assertThat(res.getContentAsString()).contains("INVALID_TOKEN");
    }
}
