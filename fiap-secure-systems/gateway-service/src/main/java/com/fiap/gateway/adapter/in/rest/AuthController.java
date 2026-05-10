package com.fiap.gateway.adapter.in.rest;

import java.util.Map;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import com.fiap.gateway.adapter.in.rest.dto.*;
import com.fiap.gateway.domain.model.Email;
import com.fiap.gateway.domain.port.in.*;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final RegisterUserUseCase registerUseCase;
    private final LoginUseCase loginUseCase;
    private final RefreshTokenUseCase refreshUseCase;
    private final LogoutUseCase logoutUseCase;

    public AuthController(
            RegisterUserUseCase r, LoginUseCase l, RefreshTokenUseCase rt, LogoutUseCase lo) {
        this.registerUseCase = r;
        this.loginUseCase = l;
        this.refreshUseCase = rt;
        this.logoutUseCase = lo;
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, UUID>> register(@Valid @RequestBody RegisterRequest body) {
        var u =
                registerUseCase.register(
                        Email.of(body.email()), body.password(), body.displayName());
        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of("userId", u.id().value()));
    }

    @PostMapping("/login")
    public TokenPairResponse login(@Valid @RequestBody LoginRequest body) {
        var pair = loginUseCase.login(Email.of(body.email()), body.password());
        return new TokenPairResponse(
                pair.accessToken(), pair.refreshToken(), pair.expiresInSeconds());
    }

    @PostMapping("/refresh")
    public TokenPairResponse refresh(@Valid @RequestBody RefreshRequest body) {
        var pair = refreshUseCase.refresh(body.refreshToken());
        return new TokenPairResponse(
                pair.accessToken(), pair.refreshToken(), pair.expiresInSeconds());
    }

    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(@Valid @RequestBody RefreshRequest body) {
        logoutUseCase.logout(body.refreshToken());
    }
}
