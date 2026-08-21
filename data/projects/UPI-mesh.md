# UPI Offline Mesh

## One-line summary
A Spring Boot backend demonstrating offline UPI-style payments: a payment is encrypted on a sender's phone, hops device-to-device through a Bluetooth-style mesh with zero connectivity, and settles exactly once when any device in the mesh reaches the internet.

## Problem / context
UPI requires connectivity. This explores "mesh-routed deferred settlement" — can a payment be composed offline, physically carried through untrusted intermediary devices, and settle correctly and exactly once whenever any device in the chain reconnects — without any intermediary being able to read or tamper with it.

## Architecture
Sender phone builds a `PaymentInstruction` (sender, receiver, amount, pinHash, nonce, timestamp), encrypts it with the server's RSA public key, wraps it in a `MeshPacket` with a TTL, and hands it to the mesh. Devices gossip the packet to every device in range each round, decrementing TTL per hop. A "bridge" device (one with internet) POSTs held packets to `/api/bridge/ingest`. Backend pipeline: hash ciphertext (SHA-256) → atomically claim the hash (idempotency check) → decrypt (RSA unwraps AES key, AES-GCM decrypts + verifies) → freshness check (reject if signed >24h ago) → settle in a single `@Transactional` debit/credit/ledger-write, with `@Version` optimistic locking on Account as defense in depth. Ships with a software mesh simulator (dashboard UI) so the full flow demos on one laptop with no real Bluetooth hardware.

## Tech stack
Java 17, Spring Boot 3.3, RSA-OAEP, AES-256-GCM, SHA-256, H2 (in-memory for demo), JPA, JUnit.

## Key decisions & why
- **Hybrid encryption (RSA-OAEP + AES-256-GCM), same pattern TLS uses** — RSA alone can't encrypt payloads over ~245 bytes (2048-bit key), so a fresh AES-256 key encrypts the actual JSON payload (fast + authenticated via GCM), and only that small AES key gets RSA-encrypted. The packet is `[RSA-encrypted AES key][IV][AES ciphertext + GCM tag]`. GCM's authentication tag means any single bit flipped by a malicious intermediary makes decryption throw — tampered data can never reach settlement.
- **Idempotency via atomic `putIfAbsent` on the ciphertext hash, not the packetId** — packetId can be rewritten by a malicious intermediate, so it's an unsafe dedupe key. Deduping on ciphertext hash means dedup happens *before* spending CPU on RSA decryption, and because AES is deterministic for a given key+IV+plaintext, two legitimate deliveries of the same packet produce byte-identical ciphertexts — so the same hash reliably catches duplicates. In production this becomes `Redis SET key NX EX 86400` with identical semantics across replicas; a unique DB index on `packet_hash` is a second defense-in-depth layer if the cache layer ever fails.
- **Two-layer replay protection** — a `signedAt` freshness window (reject anything older than 24h, which can't be forged without breaking the GCM tag) plus a per-packet nonce so two legitimate identical-amount payments produce different ciphertexts/hashes and both settle correctly, while a true replay of one specific packet is byte-identical and gets caught by the idempotency cache.

## Challenges & fixes
- **The duplicate-storm problem** — if 3 bridge devices all hold the same packet and upload near-simultaneously, naive processing would settle it 3 times. Solved with `ConcurrentHashMap.putIfAbsent`, which is atomic even under concurrent access from many threads — exactly one caller gets `null` (first claimer) and proceeds; the rest are short-circuited as `DUPLICATE_DROPPED`. Verified with a dedicated concurrency test firing 3 threads at the ingestion service simultaneously and asserting exactly one settles.
- **Choosing what to hash for dedup** — initially tempting to key on `packetId`, but that's attacker-controllable; settled on ciphertext hash instead, which is both tamper-evident (via GCM) and computed before the expensive decrypt step.
- **Honest scope-setting on the concept itself** — explicitly documented what this demo does *not* solve (a receiver can't verify the sender has funds offline, so a malicious sender could double-spend across two separate offline baskets; real BLE mesh networking is genuinely hard on modern mobile OSes and is simulated here rather than implemented). Naming the concept accurately as "mesh-routed deferred settlement" rather than overclaiming "real-time offline UPI" was a deliberate framing decision.

## Results / metrics
Verified via automated test that exactly 1 of 3 simultaneous duplicate deliveries settles, with the sender's balance changing by exactly the transaction amount once — not three times. Tamper test confirms a single flipped ciphertext byte is rejected as `INVALID` rather than crashing or incorrectly settling.

## Links
GitHub: https://github.com/Anas2604-web/upi-offline-mesh