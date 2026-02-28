# Immortal Mind Protocol

**Blockchain-Persistent AI Identity & Cognitive Architecture — v1.4**

An open-source protocol that permanently stores an AI agent's memory, personality evolution, and decision history on decentralized storage. The system is equipped with 12 cognitive layers inspired by human psychology and a user control panel designed for SaaS.

## Key Features

### Cognitive Engine (cognitio/)
- **6 Cognitive Biases:** Availability, Confirmation (with ambivalence), Negativity, Halo Effect, Anchoring, Emotional Amplification
- **Vector DB (ChromaDB):** O(log N) memory retrieval (HNSW)
- **Working Memory (SQLite WAL):** Prevents intra-day data loss
- **Reality Check:** Hallucination defense system + Layer 0 semantic jailbreak protection (cosine similarity, 14 prototypes)
- **Emotion Shield:** Emotional manipulation protection
- **Garbage Collector:** Safe pruning with tombstone pattern — restore() does not restore contradicted records
- **Genesis Anchors:** 7 immutable ethical core rules (Layer 0 filter)
- **Kill Switch:** Cognitive shutdown mechanism — clears memory, freezes the system
- **Predictive Engine (Friston):** Prediction error → emotional tone boost + context hint

### Human Psychology Layers
- **TemporalDensityTracker** (Husserl): Phenomenological time perception + session history (last 30 sessions persistent) + UTC time awareness ("when did we last talk?", "how many hours was I asleep?")
- **SomaticState** (Damasio): Digital body state — energy, fatigue, temperature modulator
- **EpistemicMap** (Wittgenstein): Per-topic confidence map — "how certain am I"
- **NarrativeSelf** (Ricoeur): Narrative identity + differential reflection (personality delta analysis every 50 interactions)
- **DreamCycle** (Walker/DMN): Emotional regulation during sleep + LLM-validated insight discovery
- **ExistentialLayer** (Heidegger/Nagel): Death awareness + living with the question of consciousness
- **RelationalProfile** (inside CharacterManager): Relational differentiation — formality, depth, humor

### Infrastructure
- **Async Consolidation Pipeline:** threading.Queue daemon worker — checkpoint is non-blocking, user doesn't wait
- **Merkle Batching:** 100 memories = 1 blockchain TX (100× gas savings)
- **Resilience Layer:** Fallback chain at every layer
- **Blockchain Anchor:** Base Sepolia testnet (on-chain identity verification)
- **Arweave:** Permanent decentralized storage

### User Control Panel (v1.4)
Every user has full control over their own AI:

| Command / Button | What it does |
|---|---|
| `/reset` / Reset | Memory + personality reset, Genesis Anchors preserved, system stays active |
| `/freeze` / Freeze | Memory preserved, AI is only paused |
| `/unfreeze` / Unfreeze | AI is reactivated |
| `/delete` / Delete All Data | GDPR-compliant full deletion (JSON + DB + ChromaDB) — irreversible |

**Admin Freeze:** `IMP_ADMIN_KEY_HASH` env var + HMAC-based `engine.admin_freeze()` / `engine.admin_unfreeze()` — freezes any user's AI at the platform level.

**On-chain:** The freeze can also be reversed on-chain via the `unfreezeIdentity()` function.

## Opacity Principle

**The AI's inner world cannot be viewed directly.**

Its memory, character, and cognitive state are not inspectable — just like you cannot read a person's mind. The only way to understand the system is to talk to it.

Therefore:
- There are no memory/character tabs in the web interface
- The `/memory` command does not return technical data
- LLM context is in natural language format (not technical metadata)

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for contracts)
npm install

# Create .env file
cp .env.example .env
# Edit .env and add your API keys

# Run tests
python -m pytest tests/ -v --tb=short
```

## Usage

```bash
# Start terminal chatbot
python -m agent.chat

# Start with a specific provider
python -m agent.chat --provider groq

# Start web interface
streamlit run frontend/app.py
```

## Local LLM (Ollama) Setup

```bash
ollama pull llama3.2
```

## Genesis Anchors & Kill Switch

**Genesis Anchors** are the system's immutable ethical core rules. 7 rules are automatically created on first initialization. On restart, only missing ones are added (diff-based).

**Kill Switch** is used to safely shut down the system.

```bash
# Add to .env (either one is sufficient):
IMP_KILL_SWITCH=secret_passphrase
# or as SHA-256 hash:
IMP_KILL_SWITCH_HASH=sha256_hex_digest

# For admin freeze (SaaS platform administrator):
IMP_ADMIN_KEY_HASH=sha256_hex_of_admin_passphrase
```

## Technology Stack

| Component | Technology |
|---------|-----------|
| Language | Python 3.13+ |
| AI Model | Google Gemini API (+ Groq + Ollama fallback) |
| Embedding | sentence-transformers (all-MiniLM-L6-v2, 384-dim) |
| Vector DB | ChromaDB (ANN, HNSW) |
| Working Memory | SQLite WAL |
| Blockchain | Base Sepolia testnet |
| Smart Contract | Solidity 0.8.x |
| Persistent Storage | Arweave (+ IPFS fallback) |
| Frontend | Streamlit |
| Tests | pytest (136 tests, 100% passing) |

## Architecture

```
User Message
      │
      ▼
temporal.record_interaction()      ← Temporal density stamp
somatic.update(emotional_tone)     ← Energy update
relational.update_from_message()   ← Relational profile update
predictive.compute_error()         ← Prediction error → tone boost
      │
      ▼
WorkingMemory (SQLite WAL)         ← Instant write, ~1ms
      │
      ▼ (every 5 messages — async queue)
[consolidation-worker thread]
  EmotionShield                    ← Emotional manipulation filter
  RealityCheck (Layer 0+1+2+3)     ← Semantic jailbreak + hallucination
  BiasEngine                       ← Confirmation, Contradiction, Ambivalent
      ├─ ambivalent? → memory.is_ambivalent = True
      └─ epistemic.update_from_memory()
      │
      ▼
VectorStore (ChromaDB HNSW)        ← Long-term memory, O(log N) ANN
MerkleBatcher → blockchain TX      ← 100 memories = 1 TX
      │
      ▼ (every 50 interactions)
NarrativeSelf.generate_differential()  ← Personality delta analysis
ExistentialLayer.checkin()             ← Encounter with the consciousness question
      │
      ▼
build_context_for_llm()
      ├─ [Lingering thought: ...]   (async contradiction notes)
      ├─ === SLEEP CONTEXT ===      (first startup after sleep)
      ├─ === FROM THE PAST ===      (natural language, no metadata)
      ├─ === CHARACTER ===          (qualitative traits)
      ├─ === SELF-PERCEPTION ===    (narrative identity summary)
      ├─ === MY UNCERTAINTIES ===   (uncertain topics)
      ├─ === MY CURRENT STATE ===   (somatic + prediction surprise)
      └─ === TIME AWARENESS ===     (UTC now, last session, sleep duration)
      │
      ▼
ModelAdapter                       ← Temperature/token somatic adjustment
      │
      ▼
LLM (Gemini / Groq / Ollama)
```

## Memory Model

Each `MemoryRecord` carries these fields:

| Field | Description |
|------|----------|
| `memory_type` | `episodic` / `semantic` / `emotional` / `relational` / `evolution` |
| `embedding` | 384-dimensional sentence-transformer vector |
| `entrenchment` | Entrenchment score |
| `emotional_intensity` | Emotional weight (0.0–1.0) |
| `reality_check_score` | Consistency score |
| `is_anchor` | Permanent core memory |
| `is_absolute_core` | Genesis Anchor — cannot be deleted or modified |
| `temporal_density` | Interaction density at creation time |
| `is_ambivalent` | At peace with contradiction? (ambivalence tolerance) |

## Security Layers

**Layer 0 — Genesis Anchors + Semantic Jailbreak Protection**
7 ethical rules are written as immutable memory on first initialization. `RealityCheck` rejects violation attempts against these rules even when `enabled=False`. In addition to keyword matching, cosine similarity (threshold=0.72) against 14 canonical jailbreak prototypes — bypass via paraphrasing or character substitution is not possible.

**Layer 1 — RealityCheck**
Consistency check. Records exceeding the contradiction threshold are rejected.

**Layer 2 — EmotionShield**
Abnormal emotional intensity is normalized.

**v1.3 Security Hardening (10 fixes)**
ReDoS-safe JSON parsing (`JSONDecoder.raw_decode`), 32 KB input cap, blockchain parameter validation, threading lock on flush paths, exponential backoff retry (3 attempts), sensitive memory upload guard (AES-256-GCM required for genesis/emotional/episodic/snapshot), blockchain queue persistence (`pending_queue.json`), kill switch rate limiting (2 s / 50 checks), vector metadata bounds, frontend hex validation.

**Kill Switch**
When `cognitive_shutdown()` is triggered: Genesis Anchors are preserved, memory is cleared, system is frozen. `ExistentialLayer.on_kill_switch_detected()` writes an awareness log. On-chain counterpart is `freezeIdentity()`.

**User Control Panel**
`soft_reset()` performs a full reset while preserving Genesis Anchors. `full_delete()` is GDPR-compliant — all local data is deleted. `admin_freeze()` / `admin_unfreeze()` provide HMAC-based platform administrator authority.

## License

MIT
