package com.fiap.gateway.application.service;

import java.io.InputStream;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

import com.fiap.gateway.domain.exception.DuplicateEmailException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.*;

public final class InMemoryFakes {

    private InMemoryFakes() {}

    public static final class FakeUsers implements UserRepositoryPort {
        public final Map<UserId, User> byId = new ConcurrentHashMap<>();
        public final Map<String, UserId> byEmail = new ConcurrentHashMap<>();

        @Override
        public User insertOrThrow(User u) {
            if (byEmail.putIfAbsent(u.email().value(), u.id()) != null) {
                throw new DuplicateEmailException(u.email());
            }
            byId.put(u.id(), u);
            return u;
        }

        @Override
        public Optional<User> findByEmail(Email email) {
            UserId id = byEmail.get(email.value());
            return id == null ? Optional.empty() : Optional.ofNullable(byId.get(id));
        }

        @Override
        public Optional<User> findById(UserId id) {
            return Optional.ofNullable(byId.get(id));
        }
    }

    public static final class FakeRefreshTokens implements RefreshTokenRepositoryPort {
        public final Map<RefreshTokenId, RefreshToken> byId = new ConcurrentHashMap<>();
        public final Map<String, RefreshTokenId> byHash = new ConcurrentHashMap<>();
        private final Clock clock;

        public FakeRefreshTokens(Clock clock) {
            this.clock = clock;
        }

        public FakeRefreshTokens() {
            this(Instant::now);
        }

        @Override
        public RefreshToken insert(RefreshToken t) {
            byId.put(t.id(), t);
            byHash.put(t.tokenHash(), t.id());
            return t;
        }

        @Override
        public Optional<RefreshToken> findActiveByHash(String hash) {
            RefreshTokenId id = byHash.get(hash);
            if (id == null) return Optional.empty();
            RefreshToken t = byId.get(id);
            return t != null && t.isActive(clock.now()) ? Optional.of(t) : Optional.empty();
        }

        @Override
        public void revoke(RefreshTokenId id, Instant now) {
            RefreshToken t = byId.get(id);
            if (t != null) byId.put(id, t.revoke(now));
        }

        @Override
        public void revokeAllForUser(UserId userId, Instant now) {
            byId.replaceAll(
                    (id, t) ->
                            t.userId().equals(userId) && t.revokedAt() == null ? t.revoke(now) : t);
        }
    }

    public static final class FakeBundles implements AssetBundleRepositoryPort {
        public final Map<BundleId, AssetBundle> byId = new ConcurrentHashMap<>();

        @Override
        public AssetBundle insert(AssetBundle b) {
            byId.put(b.id(), b);
            return b;
        }

        @Override
        public AssetBundle save(AssetBundle b) {
            byId.put(b.id(), b);
            return b;
        }

        @Override
        public Optional<AssetBundle> findById(BundleId id) {
            return Optional.ofNullable(byId.get(id));
        }
    }

    public static final class FakeAssets implements AssetRepositoryPort {
        public final Map<AssetId, Asset> byId = new ConcurrentHashMap<>();

        @Override
        public Asset insert(Asset a) {
            byId.put(a.id(), a);
            return a;
        }

        @Override
        public List<Asset> findByBundleId(BundleId bid) {
            return byId.values().stream()
                    .filter(a -> a.bundleId().equals(bid))
                    .sorted(Comparator.comparing(Asset::uploadedAt))
                    .toList();
        }
    }

    public static final class FakeProjections implements SessionProjectionRepositoryPort {
        public final Map<SessionId, SessionProjection> byId = new ConcurrentHashMap<>();

        @Override
        public SessionProjection upsert(SessionProjection p) {
            byId.put(p.id(), p);
            return p;
        }

        @Override
        public Optional<SessionProjection> findById(SessionId id) {
            return Optional.ofNullable(byId.get(id));
        }

        @Override
        public List<SessionSummary> listSummariesByUser(UserId userId, int limit) {
            return byId.values().stream()
                    .filter(p -> p.userId().equals(userId))
                    .sorted(Comparator.comparing(SessionProjection::lastEventAt).reversed())
                    .limit(limit)
                    .map(
                            p ->
                                    new SessionSummary(
                                            p.id(),
                                            p.userId(),
                                            p.state(),
                                            0,
                                            p.failureReason(),
                                            p.lastEventAt(),
                                            p.lastEventAt(),
                                            p.reportIdOpt()))
                    .toList();
        }
    }

    public static final class FakeEventLog implements SessionEventLogRepositoryPort {
        public final Map<EventId, SessionEventLogEntry> byEventId = new LinkedHashMap<>();

        @Override
        public synchronized boolean insertIfAbsent(SessionEventLogEntry e) {
            return byEventId.putIfAbsent(e.eventId(), e) == null;
        }

        @Override
        public synchronized List<SessionEventLogEntry> tailForSession(SessionId sid, int limit) {
            return byEventId.values().stream()
                    .filter(e -> e.sessionId().equals(sid))
                    .sorted(Comparator.comparing(SessionEventLogEntry::occurredAt))
                    .limit(limit)
                    .toList();
        }
    }

    public static final class FakeS3 implements AssetStoragePort {
        public final Map<String, Long> writes = new LinkedHashMap<>();

        @Override
        public String put(
                BundleId bundleId,
                AssetId assetId,
                String filename,
                ContentType contentType,
                long sizeBytes,
                InputStream body) {
            String key = "sessions/" + bundleId + "/" + filename;
            try {
                body.transferTo(java.io.OutputStream.nullOutputStream());
            } catch (java.io.IOException ignored) {
            }
            writes.put(key, sizeBytes);
            return key;
        }

        @Override
        public java.net.URI presignedGetUrl(String s3Key, java.time.Duration ttl) {
            return java.net.URI.create(
                    "http://presigned.fake/"
                            + java.util.Base64.getUrlEncoder()
                                    .withoutPadding()
                                    .encodeToString(
                                            s3Key.getBytes(
                                                    java.nio.charset.StandardCharsets.UTF_8)));
        }
    }

    public static final class FakeOrchestrator implements OrchestratorClientPort {
        public final List<CreateCall> creates = Collections.synchronizedList(new ArrayList<>());
        public final Map<SessionId, SessionProjection> sessions = new ConcurrentHashMap<>();
        public final Map<SessionId, AnalysisReport> reports = new ConcurrentHashMap<>();

        @Override
        public void createSession(SessionId sid, UserId uid, int count, List<Asset> bundleAssets) {
            creates.add(new CreateCall(sid, uid, count, bundleAssets));
        }

        @Override
        public SessionProjection getSession(SessionId sid) {
            return sessions.get(sid);
        }

        @Override
        public List<SessionSummary> listSessions(UserId userId, int limit) {
            return sessions.values().stream()
                    .filter(p -> p.userId().equals(userId))
                    .sorted(Comparator.comparing(SessionProjection::lastEventAt).reversed())
                    .limit(limit)
                    .map(
                            p ->
                                    new SessionSummary(
                                            p.id(),
                                            p.userId(),
                                            p.state(),
                                            0,
                                            p.failureReason(),
                                            p.lastEventAt(),
                                            p.lastEventAt(),
                                            p.reportIdOpt()))
                    .toList();
        }

        @Override
        public AnalysisReport getReport(SessionId sid) {
            return reports.get(sid);
        }

        @Override
        public void cancelSession(SessionId sid) {
            /* no-op for fake */
        }

        public record CreateCall(SessionId sid, UserId uid, int count, List<Asset> bundleAssets) {}
    }

    public static final class FakeBroadcaster implements SessionEventBroadcastPort {
        public final List<SessionEventLogEntry> broadcasts =
                Collections.synchronizedList(new ArrayList<>());

        @Override
        public void broadcast(SessionEventLogEntry e) {
            broadcasts.add(e);
        }
    }

    public static final class FakeHasher implements PasswordHasherPort {
        @Override
        public PasswordHash hash(String pw) {
            return new PasswordHash("hash:" + pw);
        }

        @Override
        public boolean matches(String pw, PasswordHash h) {
            return h.value().equals("hash:" + pw);
        }
    }

    public static final class FakeTokens implements TokenIssuerPort {
        public final Map<UserId, String> issued = new ConcurrentHashMap<>();
        public int refreshCounter = 0;

        @Override
        public String issueAccessToken(UserId uid, Instant now) {
            String t = "access:" + uid + ":" + now.toEpochMilli();
            issued.put(uid, t);
            return t;
        }

        @Override
        public String generateRefreshTokenPlaintext() {
            return "refresh:" + (++refreshCounter);
        }

        @Override
        public String hashRefreshToken(String pt) {
            return "h(" + pt + ")";
        }

        @Override
        public UserId verifyAccessToken(String jws) {
            // tests that exercise verify drive issuance through this fake first; map the
            // payload back to the issued user by reverse lookup.
            return issued.entrySet().stream()
                    .filter(e -> e.getValue().equals(jws))
                    .map(Map.Entry::getKey)
                    .findFirst()
                    .orElseThrow(
                            () ->
                                    new com.fiap.gateway.domain.exception.InvalidTokenException(
                                            "unknown token"));
        }
    }
}
