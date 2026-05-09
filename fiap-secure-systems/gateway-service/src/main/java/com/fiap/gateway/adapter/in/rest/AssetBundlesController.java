package com.fiap.gateway.adapter.in.rest;

import com.fiap.gateway.adapter.in.rest.dto.*;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/asset-bundles")
public class AssetBundlesController {

    private final CreateBundleUseCase createBundle;
    private final UploadAssetUseCase uploadAsset;
    private final FinalizeBundleUseCase finalizeBundle;
    private final GetBundleUseCase getBundle;

    public AssetBundlesController(CreateBundleUseCase c, UploadAssetUseCase u,
                                  FinalizeBundleUseCase f, GetBundleUseCase g) {
        this.createBundle = c;
        this.uploadAsset = u;
        this.finalizeBundle = f;
        this.getBundle = g;
    }

    @PostMapping
    public ResponseEntity<BundleResponse> create(@AuthenticationPrincipal UserId requester) {
        AssetBundle b = createBundle.create(requester);
        return ResponseEntity.status(HttpStatus.CREATED).body(BundleResponse.of(b, java.util.List.of()));
    }

    @PostMapping(value = "/{id}/assets", consumes = "multipart/form-data")
    @ResponseStatus(HttpStatus.CREATED)
    public AssetResponse uploadAsset(
            @AuthenticationPrincipal UserId requester,
            @PathVariable("id") UUID id,
            @RequestPart("file") MultipartFile file) throws IOException {
        BundleId bundleId = new BundleId(id);
        ContentType ct = ContentType.ofLenient(file.getContentType());
        Asset a = uploadAsset.upload(bundleId, requester,
                file.getOriginalFilename(), ct, file.getSize(), file.getInputStream());
        return AssetResponse.of(a);
    }

    @PostMapping("/{id}/finalize")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public FinalizeResponse finalizeBundle(
            @AuthenticationPrincipal UserId requester,
            @PathVariable("id") UUID id) {
        var r = finalizeBundle.finalize(new BundleId(id), requester);
        return new FinalizeResponse(r.sessionId().value(), r.state().name());
    }

    @GetMapping("/{id}")
    public BundleResponse getBundle(
            @AuthenticationPrincipal UserId requester,
            @PathVariable("id") UUID id) {
        var view = getBundle.get(new BundleId(id), requester);
        return BundleResponse.of(view.bundle(),
                view.assets().stream().map(AssetResponse::of).toList());
    }
}
