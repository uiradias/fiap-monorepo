package com.fiap.gateway.adapter.in.rest;

import com.fiap.gateway.application.service.*;
import com.fiap.gateway.domain.model.*;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.method.annotation.AuthenticationPrincipalArgumentResolver;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class AssetBundlesControllerTest {

    private final Clock clock = () -> Instant.parse("2026-05-09T12:00:00Z");

    private final InMemoryFakes.FakeBundles bundles = new InMemoryFakes.FakeBundles();
    private final InMemoryFakes.FakeAssets assets = new InMemoryFakes.FakeAssets();
    private final InMemoryFakes.FakeS3 s3 = new InMemoryFakes.FakeS3();
    private final InMemoryFakes.FakeProjections projections = new InMemoryFakes.FakeProjections();
    private final InMemoryFakes.FakeOrchestrator orchestrator = new InMemoryFakes.FakeOrchestrator();

    private final CreateBundleService createBundle = new CreateBundleService(bundles, clock);
    private final UploadAssetService uploadAsset = new UploadAssetService(bundles, assets, s3, clock);
    private final FinalizeBundleService finalizeBundle = new FinalizeBundleService(
            bundles, assets, orchestrator, projections, clock);
    private final GetBundleService getBundle = new GetBundleService(bundles, assets);

    private final UserId userId = new UserId(UUID.randomUUID());

    private final MockMvc mvc = MockMvcBuilders
            .standaloneSetup(new AssetBundlesController(createBundle, uploadAsset, finalizeBundle, getBundle))
            .setControllerAdvice(new GlobalExceptionHandler())
            .setCustomArgumentResolvers(new AuthenticationPrincipalArgumentResolver())
            .build();

    @BeforeEach
    void setAuth() {
        var token = new UsernamePasswordAuthenticationToken(
                userId, null, List.of(new SimpleGrantedAuthority("ROLE_USER")));
        SecurityContextHolder.getContext().setAuthentication(token);
    }

    @AfterEach
    void clearAuth() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void create_bundle_returns_201() throws Exception {
        mvc.perform(post("/api/v1/asset-bundles"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.bundleId").exists())
                .andExpect(jsonPath("$.status").value("INITIATED"));
    }

    @Test
    void get_bundle_not_found_returns_404() throws Exception {
        UUID unknownId = UUID.randomUUID();
        mvc.perform(get("/api/v1/asset-bundles/" + unknownId))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("BUNDLE_NOT_FOUND"));
    }
}
