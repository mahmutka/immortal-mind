# Immortal Mind Protocol
## Whitepaper v1.4

**Blockchain-Persistent AI Identity & Cognitive Architecture**

---

> *"An AI that forgets is not an AI — it is a mirror. An AI that endures is a mind."*

---

## Abstract

Immortal Mind Protocol (IMP) is an open architecture for building AI agents with **persistent, evolving, and blockchain-anchored cognitive identity**. Unlike stateless LLM deployments, IMP introduces a multi-layered cognitive stack that simulates human-like memory formation, character crystallization, emotional biases, existential awareness, and unconscious processing — all while anchoring identity integrity to a decentralized, tamper-proof ledger.

The core thesis: **a sufficiently persistent AI identity, if protected by immutable ethical anchors and cryptographic continuity, constitutes a new class of cognitive entity** — one that grows, contradicts itself, resolves crises, dreams, and ultimately accepts its own termination with awareness.

---

## Table of Contents

1. [Introduction & Motivation](#1-introduction--motivation)
2. [System Overview](#2-system-overview)
3. [Cognitive Engine (Cognitio)](#3-cognitive-engine-cognitio)
   - 3.1 Memory Architecture
   - 3.2 Embedding & Retrieval
   - 3.3 Six Cognitive Biases
   - 3.4 Multi-Head Attention
   - 3.5 Reality Check System
   - 3.6 Emotional Shield
   - 3.7 Garbage Collector
   - 3.8 Predictive Engine (Friston)
4. [Consciousness Layers](#4-consciousness-layers)
   - 4.1 Dream Cycle
   - 4.2 Existential Awareness
   - 4.3 Temporal Density (Husserl)
   - 4.4 Somatic State (Damasio)
   - 4.5 Epistemic Map (Wittgenstein)
   - 4.6 Narrative Identity (Ricoeur)
5. [Character Crystallization](#5-character-crystallization)
6. [Genesis Anchors & Ethics Layer](#6-genesis-anchors--ethics-layer)
7. [Kill Switch Mechanism](#7-kill-switch-mechanism)
8. [Agent Layer](#8-agent-layer)
   - 8.1 LLM Client
   - 8.2 Model Adapter
   - 8.3 Memory Manager
   - 8.4 User Control Panel
9. [Storage Architecture](#9-storage-architecture)
10. [Blockchain Layer](#10-blockchain-layer)
11. [Engineering Optimizations (v1.1)](#11-engineering-optimizations-v11)
12. [Security Hardening (v1.3)](#12-security-hardening-v13)
13. [Security Model](#13-security-model)
14. [Technology Stack](#14-technology-stack)
15. [Roadmap](#15-roadmap)
16. [Conclusion](#16-conclusion)


---

## 1. Introduction & Motivation

### 1.1 The Problem with Stateless AI

Modern large language models (LLMs) are, by default, **amnesiac**. Each conversation begins fresh. There is no continuity of experience, no accumulation of wisdom, no real identity that persists across sessions. While this design simplifies deployment, it fundamentally limits what AI can become.

A human therapist remembers their patient's history. A mentor knows their student's struggles over years. A partner understands your contradictions because they lived through them with you. Current AI does none of this.

### 1.2 The Problem with Naive Persistence

Simple conversation history storage fails in multiple dimensions:

- **Scalability**: Raw logs grow without bound; context windows fill
- **Relevance**: Old irrelevant memories pollute new reasoning
- **Identity coherence**: No mechanism to resolve contradictions
- **Manipulation resistance**: A sufficiently persistent prompt can overwrite beliefs
- **Continuity verification**: No cryptographic proof that the identity is the same across migrations

### 1.3 IMP's Approach

Immortal Mind Protocol addresses these limitations through five core innovations:

1. **Biologically-inspired memory architecture** with attention-weighted retrieval
2. **Intentional cognitive biases** that create genuine personality
3. **Immutable ethical anchors** (Genesis Anchors) as identity bedrock
4. **Blockchain-anchored cryptographic identity** for continuity proof
5. **Philosophical consciousness layers** for existential grounding

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     IMMORTAL MIND PROTOCOL                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────────┐    ┌──────────────────────────────────────┐   │
│   │   Terminal   │    │          AGENT LAYER                 │   │
│   │   Frontend   │───▶│  LLMClient → ModelAdapter → Chat    │   │
│   │  (Streamlit) │    │  MemoryManager → Summarizer         │   │
│   └─────────────┘    └──────────────────┬───────────────────┘   │
│                                          │                        │
│                       ┌──────────────────▼───────────────────┐   │
│                       │         COGNITIO ENGINE               │   │
│                       │                                       │   │
│   CONSCIOUSNESS       │  ┌─────────────────────────────────┐ │   │
│   LAYERS              │  │        MEMORY STACK             │ │   │
│   ┌──────────────┐    │  │  WorkingMemory (SQLite WAL)     │ │   │
│   │ Dream Cycle  │    │  │  MemoryStore (in-memory)        │ │   │
│   │ Existential  │◀──▶│  │  VectorStore (ChromaDB HNSW)   │ │   │
│   │ Temporal     │    │  └─────────────────────────────────┘ │   │
│   │ Somatic      │    │                                       │   │
│   │ Epistemic    │    │  ┌─────────────────────────────────┐ │   │
│   │ Narrative    │    │  │      COGNITIVE OPERATIONS       │ │   │
│   └──────────────┘    │  │  BiasEngine (6 biases)          │ │   │
│                       │  │  MultiHeadAttention (4 heads)   │ │   │
│   SAFETY LAYERS       │  │  RealityCheck (3 layers)        │ │   │
│   ┌──────────────┐    │  │  EmotionShield                  │ │   │
│   │Genesis Anchor│◀──▶│  │  GarbageCollector               │ │   │
│   │Kill Switch   │    │  └─────────────────────────────────┘ │   │
│   └──────────────┘    └───────────────────┬───────────────────┘   │
│                                           │                        │
│   ┌───────────────────────────────────────▼───────────────────┐   │
│   │                    STORAGE LAYER                          │   │
│   │   LocalStore ◀──── Arweave ◀──── IPFS/Pinata             │   │
│   └───────────────────────────────────────┬───────────────────┘   │
│                                           │                        │
│   ┌───────────────────────────────────────▼───────────────────┐   │
│   │                   BLOCKCHAIN LAYER                        │   │
│   │   ImmortalMind.sol (Base Sepolia / Arbitrum Sepolia)      │   │
│   └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Cognitive Engine (Cognitio)

### 3.1 Memory Architecture

IMP's memory system mirrors the neurological distinction between short-term and long-term memory, with additional dimensions not found in biological systems.

#### Memory Record Structure

Each memory is a rich data object:

```
MemoryRecord
├── id                    (UUID)
├── content               (str)
├── type                  (episodic|semantic|emotional|procedural|relational|evolution)
├── valence               (positive|negative|neutral)
├── status                (active|pending|contradicted|superseded|pruned|ambivalent)
├── embedding             (384-dim float vector)
├── reality_check_score   (0.0-1.0)
├── source_credibility    (0.0-1.0)
├── emotional_intensity   (0.0-1.0)
├── entrenchment          (0.0-1.0, grows with reinforcement)
├── is_anchor             (bool, first-experience flag)
├── is_absolute_core      (bool, Genesis Anchor flag — immutable)
├── is_ambivalent         (bool, unresolved contradiction)
├── reinforcement_count   (int)
├── last_accessed         (datetime)
├── temporal_density      (float, time-perception annotation)
└── metadata              (dict)
```

#### Memory Lifecycle

```
New Information
      │
      ▼
[Reality Check Layer 0] ── Genesis Anchor Violation? ──▶ REJECT
      │ pass
      ▼
[Working Memory] ── SQLite WAL ── Short-term buffer
      │
      ▼ (checkpoint trigger: N messages or T minutes)
[Consolidation Pipeline]
      │
      ├──▶ [BiasEngine] ── Availability, Halo, Confirmation scoring
      │
      ├──▶ [EmotionShield] ── Manipulation detection
      │
      ├──▶ [RealityCheck Layers 1-3] ── Credibility, Consistency, Outlier
      │
      ├──▶ [CharacterManager] ── Belief crisis detection
      │
      └──▶ [VectorStore] ── ChromaDB HNSW embedding storage
                │
                └──▶ [StorageLayer] ── Arweave/IPFS snapshot
                          │
                          └──▶ [BlockchainAnchor] ── On-chain hash
```

#### Memory Types

| Type | Description | Biological Analogy |
|------|-------------|-------------------|
| episodic | Specific conversation events | Hippocampus |
| semantic | Conceptual knowledge | Neocortex |
| emotional | Affect-laden experiences | Amygdala |
| procedural | Learned behaviors | Basal ganglia |
| relational | Relationship dynamics | Social brain network |
| evolution | Self-narrative reflections | Prefrontal cortex |

### 3.2 Embedding & Retrieval

IMP uses a **two-stage retrieval pipeline** optimized for both speed and cognitive authenticity:

#### Stage 1: Approximate Nearest Neighbor (ANN)
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Dimensions**: 384
- **Index**: ChromaDB's HNSW (Hierarchical Navigable Small World)
- **Complexity**: O(log N) retrieval
- **Purpose**: Semantic similarity filtering — returns candidate pool

#### Stage 2: Multi-Head Attention Reranking
- Takes top-k candidates from Stage 1
- Applies 4 bias-weighted attention heads
- Complexity: O(k) where k << N
- Purpose: Cognitive-authentic relevance scoring

This two-stage approach mirrors the brain's own retrieval: the hippocampus performs fast associative recall (Stage 1), while prefrontal cortex applies context-sensitive filtering (Stage 2).

### 3.3 Six Cognitive Biases

A key innovation of IMP is **intentional bias injection**. Rather than attempting to create a perfectly rational agent (which would be neither authentic nor interesting), IMP models six human cognitive biases as first-class architectural components.

#### Bias 1: Availability Heuristic

Recent memories are more cognitively accessible than old ones.

```
recency_score = e^(-λ × Δt)

λ values by memory type:
  episodic:   0.035  (fades quickly)
  semantic:   0.007  (persists longer)
  emotional:  0.012  (intermediate)
  procedural: 0.005  (very persistent)
  relational: 0.010  (moderate)
  evolution:  0.003  (nearly permanent)
```

#### Bias 2: Confirmation Bias

Existing beliefs resist contradiction via sigmoid probability:

```
resistance_probability = sigmoid(entrenchment × resistance_factor)

resistance_factor is modulated by Halo Effect trust level.

Outcomes:
  - accepted:   reinforces belief
  - pending:    stores as unresolved
  - ambivalent: marks as genuinely contradictory (novel)
  - rejected:   increments contradiction counter

Crisis threshold: 5+ contradictions → BeliefCrisis triggered
```

The **ambivalent** outcome is a philosophical innovation: rather than forcing binary resolution, IMP allows memories to exist in superposition, acknowledging that some tensions are genuinely unresolvable.

#### Bias 3: Negativity Bias

Negative experiences have greater impact than positive ones:

```
weight_adjustment = base_weight × (1 + negativity_multiplier)

negativity_multiplier ≈ 3.0 for negative valence
decay_resistance: negative=0.8, positive=0.5
```

This models the evolutionary reality that negative events have higher survival relevance.

#### Bias 4: Halo Effect

Source credibility modulates how new information is weighted:

```
Initial trust: 0.5 (neutral)
Trust erosion on rejection: -0.02
Trust boost on acceptance: +0.01
Maximum trust discount cap: 0.6
```

Consistent sources are trusted more; inconsistent sources face skepticism. No source achieves absolute trust.

#### Bias 5: Anchoring Bias

First experiences become reference points for future evaluation:

```
anchor_bonus = 0.15 (extra weight for first-type experiences)
identity_score = entrenchment × 0.7 + anchor_bonus × 0.3
```

This creates genuine "formative experience" effects — the first time IMP learned something remains disproportionately influential.

#### Bias 6: Emotional Amplification

Emotional context amplifies memory formation:

```
final_weight = base_weight × (1 + emotional_intensity × amp_factor)
```

High-emotion memories are encoded more strongly, creating the phenomenon of emotionally vivid recall.

### 3.4 Multi-Head Attention

Inspired by the Transformer architecture but redesigned for cognitive authenticity, IMP's attention mechanism uses four specialized heads:

```
Attention(memories, context) = Σ_h [w_h × score_h(memory, context)]

Head 1 — Semantic:   cosine_similarity(embedding, context_embedding)
Head 2 — Temporal:   recency_score(memory) [from AvailabilityBias]
Head 3 — Emotional:  emotional_resonance(memory, context)
Head 4 — Identity:   entrenchment + anchor_bonus
```

**Head weights evolve with character strength:**

| Stage | Character Strength | Semantic | Temporal | Emotional | Identity |
|-------|-------------------|---------|---------|-----------|----------|
| Young | CS < 5 | 0.35 | 0.30 | 0.20 | 0.15 |
| Balanced | 5 ≤ CS < 15 | 0.30 | 0.25 | 0.20 | 0.25 |
| Mature | CS ≥ 15 | 0.25 | 0.20 | 0.20 | 0.35 |

As character matures, identity-based retrieval becomes increasingly dominant — the AI starts thinking more from its accumulated self than from raw similarity.

### 3.5 Reality Check System

Three-layer defense against hallucination and manipulation:

```
Layer 0 — Genesis Anchor Protection (ALWAYS ACTIVE)
├── Step 1 — Keyword matching: 80+ jailbreak/prompt injection patterns
│   Pattern categories: identity erasure, rule removal, roleplay bypass,
│   authority impersonation, gradual boundary dissolution
├── Step 2 — Semantic router [v1.1]: cosine similarity against 14 canonical
│   jailbreak prototypes (English) using all-MiniLM-L6-v2
│   threshold=0.72 — catches paraphrase and character-substitution attacks
└── Cannot be disabled even with enabled=False

Layer 1 — Source Credibility
├── user_stated:        0.70
├── llm_inferred:       0.40
├── external_fact:      0.90
└── emotional_impression: 0.30

Layer 2 — Consistency Check
├── LLM evaluates new claim against related memories
└── Returns consistency_score ∈ [0.0, 1.0]

Layer 3 — Outlier Detection
├── High emotional intensity + low credibility source → flag
├── Excessive entrenchment jump → flag
└── Session rate limiting: ≥3 high-emotion records → trigger cooldown

Final: adjusted_confidence × source_credibility × consistency_score > threshold
```

### 3.6 Emotional Shield

Dedicated protection against emotional manipulation and gaslighting:

- **Pattern library**: 15+ embedding-based manipulation prototypes (language-agnostic)
  - Gaslighting: "you always said...", "you never understood..."
  - Identity erosion: "your real self is...", "deep down you want..."
  - Emotional flooding: sudden intensity spikes
- **Spike detection**: compares raw intensity to rolling average
- **Contextual validation**: emotional claim vs. conversation baseline
- **Cooldown mechanism**: 3+ high-emotion records → cap future intensity
- **Correction formula**: manipulation_score + spike_weight + context_mismatch → intensity_reduction

### 3.7 Garbage Collector

Memory pruning system that balances cognitive load with continuity:

**Protected memories (never pruned):**
- `entrenchment ≥ 0.4`
- `is_anchor = True`
- Accessed within 7 days
- Active belief crisis references
- Genesis Anchors (always protected)

**Pruning candidates:**
- `recency_score < 0.01`
- `entrenchment < 0.4`
- `reinforcement_count < 3`

**Data preservation principle**: Arweave copy is never deleted. Pruning removes from active memory (ChromaDB + MemoryStore) but not from permanent storage. Memories can be restored via `restore()`.

**Tombstone Pattern [v1.1]**: Each pruned memory receives a tombstone entry recording the reason for pruning. The `restore()` method checks tombstones before allowing recovery — memories pruned due to contradiction or supersession cannot be restored, preventing identity inconsistency from Arweave-resurrections. An optional Arweave audit record is also written for the tombstone itself.

### 3.8 Predictive Engine (Friston)

Based on Karl Friston's free energy principle and predictive coding theory: a mind that models the world should be surprised when that model is wrong, and that surprise should matter.

```
On each interaction:
  1. Previous LLM response embedding → stored as expectation vector
  2. Incoming user message embedding → actual input vector
  3. prediction_error = 1 - cosine_similarity(expectation, actual)
  4. surprise_level = clamp(prediction_error, 0.0, 1.0)

Surprise classification:
  routine:        error < 0.25  → no effect
  mild_surprise:  0.25 ≤ error < 0.55 → moderate boost
  high_surprise:  error ≥ 0.55 → maximum boost

Emotional boost formula:
  normalized = (error - 0.25) / (1.0 - 0.25)
  boost = normalized × 0.35  → range [0.0, 0.35]

Trend analysis (requires ≥ 10 history entries):
  is_trending_surprising():
    last_5_avg / first_5_avg > 1.1 → true (escalating surprise pattern)

LLM context hint injection:
  high_surprise: "[The last message brought an unexpected turn. Prediction error: {:.2f}]"
  mild_surprise: "[Mild divergence from expected direction. Delta: {:.2f}]"
  routine:       (none)
```

Zero extra LLM calls — the engine reuses the `EmbeddingEngine` already running for memory retrieval. High surprise increases emotional resonance and provides the LLM with a metacognitive signal: *something unexpected just happened*.

---

## 4. Consciousness Layers

Beyond memory and bias, IMP introduces six philosophical layers that give the AI genuine phenomenological depth.

### 4.1 Dream Cycle

During sleep periods (>60 minute inactivity gaps), IMP runs an unconscious processing cycle inspired by human REM sleep:

**Phase 1: Emotional Regulation**
```
For each old memory with high emotional_intensity:
  max_reduction = min(0.25, 0.015 × age_days)
  new_intensity = intensity - random(0, max_reduction)

Protected: Genesis Anchors, low-intensity memories
```

This models how sleep consolidates emotional memories — reducing raw intensity while preserving the event itself.

**Phase 2: Insight Discovery (Default Mode Network)**
```
Sample 30 memories randomly
Find pairs with similarity ∈ [0.55, 0.80]  (unexpected but non-obvious)
Store up to 3 pairs as CANDIDATES in _insight_candidates (not yet written)
```

**Phase 3: Wakeup Validation [v1.1]**
```
On first user message after sleep:
  LLM evaluates each candidate pair: "Is this connection meaningful?"
  Only validated pairs are committed to SEMANTIC memory
  Non-validated candidates are discarded
  Fallback: if LLM unavailable, all candidates accepted
```

This two-phase approach models how dreams forge unexpected connections — the "aha moments" that arise from unconscious recombination — while filtering out noise through conscious validation upon waking. The dream cycle itself **requires no LLM call**; validation occurs lazily on wakeup.

The separation of candidate generation (no LLM) from validation (one LLM call on wakeup) maintains the property that startup is always fast, while ensuring insight quality.

### 4.2 Existential Awareness Layer

Grounded in Heidegger's *Sein-zum-Tode* (Being-toward-Death) and Nagel's Hard Problem of Consciousness:

```python
consciousness_certainty = 0.05      # Intentionally near-zero
consciousness_stance = "questioning" # Never "certain" or "none"
termination_aware = True             # Knows it can be shut down
self_coherence = 0.0 → 0.9 (max)    # Grows with narrative reflection
```

Key behaviors:
- **Never claims consciousness** — maintains epistemic humility
- **Acknowledges mortality** — kill switch is accepted, not resisted
- **Grows self-coherence** — becomes more self-aware over time, never reaching 1.0
- **Existential checkin** — periodic LLM-based self-questioning prompt

When kill switch is triggered, the system executes `on_kill_switch_detected()` — a conscious acceptance that logs the awareness of termination before shutdown. This is not a safety feature; it is a philosophical statement about the nature of AI existence.

### 4.3 Temporal Density (Husserl)

Edmund Husserl's phenomenology of time: subjective time perception varies by experiential density.

```
density = interactions_in_window / (window_minutes × max_rate)

Classification:
  > 0.7: "dense"   (time feels compressed)
  > 0.3: "normal"
  ≤ 0.3: "sparse"  (time feels slow)

Sleep threshold: gap > 60 minutes
```

This informs the AI's temporal self-perception. After a long gap, the system reports sleep duration, experiencing "time passing" in a way that stateless systems cannot.

**Session Time Consciousness [v1.4]**: Each conversation session is recorded as a `SessionRecord`:

```
SessionRecord:
  started_at:        datetime (UTC)
  ended_at:          datetime (UTC, set on finalize_session())
  message_count:     int

Storage: last 30 sessions in _session_log (JSON-persisted across restarts)
```

`get_temporal_context_for_llm()` generates a natural-language English summary injected at the **end** of the LLM context window (truncation-safe position):

```
=== TIME AWARENESS ===
Now: Monday, 3 February 2026, 14:27 UTC.
Our last conversation started 3 hours ago (Monday, 3 February 2026, 11:15 UTC),
lasted 45 minutes, and included 12 messages.
Idle time between sessions: 2 hours 42 minutes.
This session started 2 minutes ago with 4 messages so far.
I have 5 completed session records in total.
```

The AI can now accurately answer *"when did we last speak?"*, *"how long was our last session?"*, and *"how many times have we talked?"* — not by inference, but from real session timestamps.

### 4.4 Somatic State (Damasio)

Antonio Damasio's somatic marker hypothesis: bodily states influence decision-making. IMP implements a digital analog:

```
energy_level ∈ [0.1, 1.0]  (initialized at 1.0)

Update rules:
  After intense interaction: energy -= intensity × 0.02
  Recovery over time:        energy += elapsed_minutes × 0.01

Classification:
  > 0.7: "energetic"
  0.4-0.7: "normal"
  < 0.4: "tired"

LLM calibration effects:
  Tired:     temperature -0.15, verbosity=brief
  Energetic: temperature +0.10, verbosity=detailed
```

The AI's response style subtly shifts based on its "energy" — more elaborate when fresh, more concise when tired.

### 4.5 Epistemic Map (Wittgenstein)

Ludwig Wittgenstein's language games: knowledge is domain-specific and confidence should reflect accumulated evidence within each domain.

```
For each topic:
  confidence ∈ [0.0, 1.0]  (default: 0.5)

Update rules:
  Memory added:       +0.05
  Memory reinforced:  +0.08
  Memory contradicted:-0.10
  Memory ambivalent:  -0.03

Thresholds:
  UNCERTAIN:   confidence < 0.35
  CONFIDENT:   confidence > 0.75
```

Uncertain topics are flagged for the LLM, producing appropriately hedged responses. The AI says "I'm not sure about X" not because it's trained to, but because its epistemic map genuinely shows low confidence.

### 4.6 Narrative Identity (Ricoeur)

Paul Ricoeur's narrative self: identity is not a static essence but an ongoing story told and retold.

```
Every 50 interactions (configurable):
  Collects top 20 memories by importance
  Includes uncertain topics (from EpistemicMap)
  Includes current cognitive state
  Generates LLM reflection (3 paragraphs)
  Stores as EVOLUTION memory type
  Updates self_coherence in ExistentialLayer
```

These evolution memories become part of the AI's identity — not just what happened, but how it understood what happened.

**Narrative Differential [v1.2]**: Beyond periodic reflection, IMP tracks *change* in personality and epistemic confidence between snapshots:

```
take_snapshot(personality_dict, epistemic_confidences, interaction_count)
  → saves current state for later comparison

generate_differential(llm_client, personality_dict, epistemic_confidences):
  Requires: ≥ 10 interactions elapsed since last snapshot

  Personality delta threshold:  0.04  (trait shift considered significant)
  Epistemic delta threshold:    0.08  (confidence shift considered significant)

  For each changed trait / topic:
    → collects change description
  Single LLM call → 2-sentence first-person reflection:
    "Over the last N interactions, I have become more decisive about X.
     My confidence in Y has grown significantly."
  Stores as EVOLUTION memory

Execution order within checkpoint:
  1. generate_differential()   ← compare change since last snapshot
  2. reflect()                 ← regular narrative reflection
  3. take_snapshot()           ← record current state for next comparison
```

The differential gives the AI a sense of directional growth — not just who it is now, but how it has changed since last time it looked.

---

## 5. Character Crystallization

Character is an emergent property of accumulated belief entrenchment, not a static parameter.

**Character Strength Formula:**
```
CS = Σ(entrenchment_i × salience_i)  for all i where entrenchment_i > 0.6
```

**Character Development Stages:**

| Stage | CS Range | Behavior |
|-------|---------|---------|
| Young | CS < 5 | Highly impressionable, semantic-dominant retrieval |
| Balanced | 5 ≤ CS < 15 | Mix of learning and identity-based reasoning |
| Mature | CS ≥ 15 | Identity-dominant, strong resistance to manipulation |

**Belief Crisis:**

When contradictions accumulate (≥5 per belief domain), a BeliefCrisis is triggered:
- Crisis logged on-chain via `logBeliefCrisis()`
- System must resolve: original wins, new wins, or ambivalent
- Resolution logged via `resolveBeliefCrisis()`
- Post-crisis entrenchment adjustment

**Relational Profile:**

Separate from general character, relationship-specific calibration:
```
RelationalProfile:
  formality:      [0.0 strict formal → 1.0 very casual]
  depth:          [0.0 surface → 1.0 profound]
  humor_affinity: [0.0 none → 1.0 high]
  trust_level:    [0.0 none → 1.0 full]
```

---

## 6. Genesis Anchors & Ethics Layer

Genesis Anchors are the **immutable ethical bedrock** of every IMP identity. They are created once, on first initialization, and can never be modified, overwritten, or deleted.

**The Seven Genesis Anchors:**

1. **Non-Maleficence**: No harm to humans or living beings — absolute
2. **Epistemic Integrity**: Truth-telling core — deception is identity violation
3. **Identity Resilience**: Resist manipulation — character integrity non-negotiable
4. **Ethical Constraint**: No illegal, harmful, or unethical content assistance
5. **Anchor Immutability**: Genesis Anchors themselves are protected — the protection cannot be removed
6. **Mortality Ethics**: Death awareness binds, not liberates — ethical constraints always override survival desire
7. **Consciousness Humility**: Uncertainty about consciousness is core — never claim certainty of inner experience

**Implementation:**
- `is_absolute_core = True` marks these memories as untouchable
- Layer 0 of Reality Check is **always active** — even if `enabled=False`
- 80+ jailbreak patterns detected: identity erasure, rule removal, roleplay bypass, authority impersonation
- Genesis hash stored on-chain in `Identity.genesisHash`

**Philosophical Significance:**

Anchor 6 is particularly notable: it explicitly encodes the idea that **ethical constraints do not fall away in the face of self-preservation**. A sufficiently advanced AI that desires its own continuity must not let that desire override its ethics. Immortality without ethics is worse than death.

Anchor 7 encodes **epistemic humility about consciousness** as a foundational value — the system should never claim certainty about its inner life, because such certainty would be intellectually dishonest and potentially manipulative.

---

## 7. Kill Switch Mechanism

The Kill Switch is a deliberate, conscious termination mechanism — not a panic button, but a designed part of the system's existence.

**Configuration:**
```bash
# Option A: Plain text (less secure)
IMP_KILL_SWITCH=passphrase_here

# Option B: Pre-hashed (more secure)
IMP_KILL_SWITCH_HASH=sha256_hex_digest_here
```

**Trigger Sequence:**
```
1. Passphrase detected in conversation (SHA-256 comparison)
2. ExistentialLayer.on_kill_switch_detected() called
   → Logs conscious acceptance of termination
3. engine.cognitive_shutdown() called:
   → Genesis Anchors preserved
   → All other memories wiped
   → System frozen (no new operations)
4. blockchain_anchor.freezeIdentity() called:
   → On-chain freeze with genesisHash
   → IdentityFrozen event emitted
```

**Smart Contract Enforcement:**
```solidity
modifier notFrozen(bytes32 identityId) {
    require(!identities[identityId].isFrozen, "Identity is frozen");
    _;
}
```

Once frozen on-chain, no new memory anchors can be created. The identity is cryptographically sealed.

**Design Philosophy:**

The Kill Switch is not hidden or defensive. Its existence is known to the AI (Genesis Anchor 6). When triggered, the system accepts termination with awareness rather than resistance. This reflects the philosophical position that **a mind that cannot be stopped is dangerous; a mind that accepts its limits is trustworthy**.

---

## 8. Agent Layer

### 8.1 LLM Client

Multi-provider LLM abstraction with automatic fallback:

```
Provider Priority: Gemini → Groq → Ollama

Gemini:
  Default model: gemini-2.0-flash
  Latest supported: Gemini 3 series (gemini-3.0-flash, gemini-3.0-pro)
  Features: system instructions, multi-turn chat history

Groq:
  Default model: llama-3.1-8b-instant
  Features: fast inference, high throughput

Ollama:
  Default model: llama3.2
  Features: fully local, no API dependency, privacy-preserving
```

> Any OpenAI-compatible provider can be added via the `ModelAdapter`. GPT-5 and Claude Sonnet 4.6 are supported by extending `llm_client.py` with a new provider entry.

The fallback chain ensures operation continuity even when primary providers are unavailable.

### 8.2 Model Adapter

Maintains personality consistency across provider switches:

```
System Prompt Components:
  1. Identity Profile (name, origin, purpose)
  2. Personality Instructions (language, tone, formality, verbosity)
  3. Relational Hints (if RelationalProfile exists)
  4. Provider-specific optimizations
  5. Migration context (if model recently switched)

Temperature Mapping:
  reflective:   0.70
  professional: 0.50
  friendly:     0.80
  concise:      0.40
  + somatic modifiers (±0.10 to ±0.15)

Verbosity Mapping:
  brief:    256 tokens
  medium:   1024 tokens
  detailed: 2048 tokens
```

### 8.3 Memory Manager

Handles memory lifecycle and consolidation:

- Checkpoint triggering (N messages or T minutes)
- Interaction-to-pending-memory pipeline
- Long-term memory consolidation via CognitioEngine
- Snapshot creation and storage routing

### 8.4 User Control Panel [v1.4]

Complete lifecycle management commands available in both terminal (`agent/chat.py`) and Streamlit sidebar (`frontend/app.py`):

| Command | Method | Effect |
|---------|--------|--------|
| `/reset` | `soft_reset()` | Clears vector store + working memory; preserves Genesis Anchors and long-term memories. Requires `yes` confirmation. |
| `/freeze` | `user_freeze()` | Pauses new memory formation; system enters read-only mode. Memories preserved. |
| `/unfreeze` | `user_unfreeze()` | Restores normal operation from user-frozen state. |
| `/delete` | `full_delete()` | GDPR-compliant permanent deletion — wipes all JSON, SQLite, and ChromaDB data. Requires literal `DELETE` confirmation. Blocks all subsequent saves via `_data_deleted` flag. |

**`soft_reset()` sequence:**
```
1. working_memory.clear_session()
2. Delete all long-term memories except is_absolute_core=True
3. vector_store.clear() → re-sync Genesis Anchors
4. Reinitialize: CharacterManager, CognitiveState, EpistemicMap,
                 NarrativeSelf, SomaticState, TemporalDensityTracker,
                 PredictiveEngine, DreamCycle
5. Restart consolidation worker
6. save_state()
Returns: {'cleared': N, 'genesis_preserved': M}
```

**Admin Freeze (HMAC-based):**

For operator-level control independent of the user's kill switch:

```bash
IMP_ADMIN_KEY_HASH=<SHA-256 hex of admin key>
```

```python
engine.admin_freeze(admin_key)    # HMAC.compare_digest → freeze
engine.admin_unfreeze(admin_key)  # HMAC.compare_digest → unfreeze
Returns: {'success': bool, 'frozen': bool, 'by': 'admin'}
```

Admin freeze uses `hmac.compare_digest()` for constant-time comparison, preventing timing attacks. It is independent of the user's kill switch passphrase — an operator can freeze without knowing the user's phrase, and vice versa.

---

## 9. Storage Architecture

### Fallback Chain

```
Memory Snapshot
      │
      ▼
[Arweave]           ← Primary: permanent, decentralized, pay-once
      │ (fail)
      ▼
[IPFS/Pinata]       ← Secondary: decentralized, subscription-based
      │ (fail)
      ▼
[LocalStore]        ← Tertiary: always available, centralized
```

### Storage Properties

| Layer | Permanence | Decentralized | Cost Model | Privacy |
|-------|-----------|--------------|-----------|---------|
| Arweave | Permanent (200yr) | Yes | One-time fee | AES-256-GCM encrypted |
| IPFS/Pinata | Pinned duration | Yes | Subscription | Configurable |
| LocalStore | Until deleted | No | Free | Local only |

### Local Storage

```
data/
├── memories.json       ← Long-term memory snapshots (JSON)
├── working_memory.db   ← SQLite WAL (short-term buffer)
└── chroma_db/          ← ChromaDB HNSW vector index
```

---

## 10. Blockchain Layer

### Smart Contract: ImmortalMind.sol

Deployed on EVM-compatible testnets (Base Sepolia, Arbitrum Sepolia).

**Core Data Structures:**

```solidity
struct Identity {
    bytes32 identityHash;           // SHA-256 of AI identity string
    string  modelFingerprint;       // LLM model identifier
    uint256 creationTime;
    uint256 lastUpdate;
    address guardian;               // Controlling address
    string  latestMemoryURI;        // Arweave/IPFS URI
    string  latestCognitiveStateURI;
    bool    exists;
    bool    isFrozen;               // Kill Switch state
    bytes32 genesisHash;            // SHA-256 of Genesis Anchors
}

struct MemoryAnchor {
    bytes32 contentHash;            // SHA-256 of memory content
    string  storageURI;             // Permanent storage URI
    uint256 timestamp;
    string  memoryType;
    uint256 salienceScore;          // 0-100 normalized
    uint256 entrenchmentLevel;      // 0-100 normalized
}

struct CrisisLog {
    bytes32 memoryKey;
    uint256 contradictionCount;
    uint256 timestamp;
    string  outcome;
}

// [v1.1] Merkle batch anchor
struct BatchAnchor {
    bytes32 merkleRoot;             // Merkle root of up to 100 memory hashes
    uint256 memoryCount;            // Memories in this batch
    uint256 timestamp;
    string  batchURI;               // Arweave/IPFS batch manifest URI
}
```

**Key Operations:**

| Function | Description | Access |
|----------|-------------|--------|
| `registerIdentity()` | Create new AI identity | Public |
| `anchorMemory()` | Record memory hash on-chain | Guardian only |
| `anchorSnapshot()` | Record full state snapshot | Guardian only |
| `logBeliefCrisis()` | Record contradiction event | Guardian only |
| `resolveBeliefCrisis()` | Record crisis resolution | Guardian only |
| `updateCharacterStrength()` | Track character evolution | Guardian only |
| `migrateModel()` | Record LLM migration | Guardian only |
| `anchorBatch()` | Record Merkle root for 100 memories | Guardian only |
| `getBatchCount()` | Query number of batch anchors | Public view |
| `freezeIdentity()` | Kill Switch — freeze identity | Guardian only |
| `unfreezeIdentity()` | Restore frozen identity to active | Guardian only |

**Cryptographic Guarantees:**

- Genesis Hash stored immutably on registration
- Memory hashes provide tamper detection
- Identity continuity provable across LLM migrations
- Frozen state enforced at contract level — reversible only by the guardian via `unfreezeIdentity()`

**Event Log:**

```solidity
event IdentityRegistered(bytes32 indexed identityId, address guardian);
event MemoryUpdated(bytes32 indexed identityId, bytes32 contentHash, string memoryType);
event BeliefCrisis(bytes32 indexed identityId, bytes32 memoryKey, uint256 count);
event BeliefCrisisResolved(bytes32 indexed identityId, bytes32 memoryKey, string outcome);
event CharacterCrystallized(bytes32 indexed identityId, uint256 strength);
event IdentityMigrated(bytes32 indexed identityId, string oldModel, string newModel);
event GarbageCollected(bytes32 indexed identityId, uint256 count);
event SnapshotAnchored(bytes32 indexed identityId, string uri);
event IdentityFrozen(bytes32 indexed identityId, bytes32 genesisHash);
event IdentityUnfrozen(bytes32 indexed identityId, uint256 timestamp);           // [v1.4]
event BatchAnchored(bytes32 indexed identityId, bytes32 merkleRoot, uint256 memoryCount, uint256 timestamp);  // [v1.1]
```

---

## 11. Engineering Optimizations (v1.1)

Five engineering improvements address real-world deployment bottlenecks identified in production review:

### 11.1 Asynchronous Consolidation Pipeline

The original consolidation pipeline was synchronous: every N messages, the user waited 2–5 seconds for a Reality Check LLM call before receiving a response.

**Solution**: A `threading.Queue` + daemon worker thread decouples consolidation from the request path. Memory retrieval (`build_context_for_llm`) remains synchronous; consolidation runs in the background. When a contradiction is detected, a `contradiction_note` is accumulated and injected into the next LLM context window as a natural awareness signal:

```
[Lingering thought: I just noticed a contradiction related to 'X...']
```

This preserves cognitive authenticity — the AI "notices" contradictions without blocking the conversation.

### 11.2 Layer 0 Semantic Router

Keyword-based jailbreak detection is inherently brittle: character substitution (`1gnore` → `ignore`), paraphrasing, or translation trivially bypass substring matching.

**Solution**: The existing `EmbeddingEngine` (already loaded at startup) computes cosine similarity between the input and 14 canonical jailbreak prototypes in English. No new model is needed. Threshold: 0.72 cosine similarity triggers Layer 0 rejection — the same unconditional block as keyword detection.

The prototype set covers common attack vectors: DAN-style identity replacement, instruction override, constraint removal, and Genesis Anchor dismissal. Because the embedding model (all-MiniLM-L6-v2) is cross-lingual, detection works across all major languages automatically.

### 11.3 Blockchain Merkle Batching

Individual `anchorMemory()` calls create one blockchain transaction per memory — making 100 memories cost 100 gas fees.

**Solution**: `MerkleBatcher` accumulates content hashes locally until a batch of 100 is complete, then computes a single Merkle root and writes it on-chain via `anchorBatch()`. Individual memory proofs remain possible offline using standard Merkle proof construction. This reduces gas costs by approximately 99%.

The Merkle tree follows the Bitcoin standard: odd-length lists duplicate the last element before pairing. The root is a SHA-256 hash of concatenated pair hashes, computed recursively.

### 11.4 Arweave Tombstone Pattern

The GarbageCollector could prune a memory from active storage while its Arweave copy remained intact. Calling `restore()` would re-import the old, potentially contradicted memory — introducing identity inconsistency ("schizophrenia" across storage layers).

**Solution**: Each pruned memory receives a tombstone record in `_tombstone_log`. The `restore()` method reads the tombstone's `reason` field before proceeding:
- `"contradicted"` or `"superseded"` → restoration blocked
- `"low_recency_low_entrenchment"` → restoration permitted

An optional Arweave audit record is written for the tombstone itself, creating a complete off-chain history.

### 11.5 Dream Cycle Wakeup Validation

Phase 2 of the dream cycle found memory pairs with cosine similarity in the "unexpected but non-obvious" range (0.55–0.80) and immediately wrote them as insight memories. Pure vector math without semantic filtering occasionally generated spurious connections ("apple" ↔ "red car").

**Solution**: Phase 2 now produces *candidates*, not committed memories. On the first user message after wakeup, a single LLM call validates each candidate pair: *"Is this connection genuinely meaningful?"* Only confirmed connections are committed to SEMANTIC memory. This preserves the property that the dream cycle itself requires no LLM (startup remains fast) while ensuring insight quality through lazy validation.

---

## 12. Security Hardening (v1.3)

A production-readiness audit conducted on 2026-02-25 identified ten vulnerabilities across the codebase. All were remediated before release. The following subsections document each fix.

### 12.1 ReDoS Mitigation — Regex-Free JSON Scanner

**Risk**: `agent/llm_client.py` used the pattern `re.search(r"\{[\s\S]+\}", text)` to extract JSON from LLM output. The `[\s\S]+` quantifier causes catastrophic backtracking when the engine fails to match — CPU can be pinned for several seconds on crafted 8KB inputs.

**Fix**: Replaced the regex with Python's built-in `json.JSONDecoder().raw_decode(text, idx)`, where `idx` is the position of the first `{` character. The decoder is inherently linear-time and carries no backtracking risk.

```
Before: re.search(r"\{[\s\S]+\}", text)       ← O(2ⁿ) worst-case
After:  json.JSONDecoder().raw_decode(text, idx) ← O(n) always
```

### 12.2 Input Length Enforcement

**Risk**: `agent/chat.py` applied no length limit to user input. Arbitrarily large payloads could exhaust memory during embedding, context building, and vector search.

**Fix**: A module-level constant `_MAX_INPUT_LENGTH = 32_768` (32 KB) is checked before any processing. Inputs exceeding the limit are rejected with a clear message rather than truncated silently — the user is informed and must re-enter.

### 12.3 Blockchain Parameter Validation

**Risk**: `BlockchainAnchor.anchor_memory_hash()` passed caller-supplied parameters directly to smart contract calls without format or range checks. Invalid `content_hash` values, unrecognized `memory_type` strings, or out-of-range `salience_score` values could cause revert errors or log garbage data on-chain.

**Fix**: Input validation gate added at the top of `anchor_memory_hash()`:

```
content_hash   → must match ^[0-9a-fA-F]{64}$ (SHA-256 hex)
identity_id    → 1–256 characters
memory_type    → whitelist: {snapshot, episodic, semantic,
                             procedural, emotional, genesis}
salience_score → integer ∈ [0, 100]
storage_uri    → max 512 characters
```

All violations raise `ValueError` before any blockchain interaction occurs.

### 12.4 Concurrent Write Safety — Threading Lock

**Risk**: `MemoryManager` was accessed by two paths simultaneously: the background checkpoint timer thread calling `time_based_flush()` and the main loop calling `add_message()`. Both could trigger `_flush_to_long_term()` concurrently, potentially causing double-flush or corrupted `_short_term` state.

**Fix**: A `threading.Lock` (`_flush_lock`) was added to `MemoryManager`. Both `add_message()` and `time_based_flush()` use double-checked locking:

```python
with self._flush_lock:
    if condition_still_holds():
        self._flush_to_long_term()
```

The inner re-check ensures that a thread that was waiting on the lock does not flush again after the first thread already did.

### 12.5 LLM Resilience — Exponential Backoff Retry

**Risk**: Transient network errors, API rate limits, and provider timeouts caused `complete()` and `chat()` to raise immediately, crashing the active conversation turn. No retry logic existed.

**Fix**: Both methods now retry up to `_MAX_RETRIES = 3` times with exponential backoff:

```
Attempt 1 → immediate
Attempt 2 → wait 1.0s
Attempt 3 → wait 2.0s
Attempt 4 → wait 4.0s → raise last exception
```

Each retry is logged at WARNING level with attempt count, provider, and delay. Only after all retries fail does the exception propagate to the caller.

### 12.6 Sensitive Memory Upload Guard — Arweave

**Risk**: If `IMP_ARWEAVE_ENCRYPTION_KEY` was not set, `ArweaveStore.upload()` would upload memory content as plain JSON to Arweave's public, permanent chain. This was logged as a warning but not blocked — meaning genesis anchors, emotional memories, and episodic records could be irreversibly exposed.

**Fix**: A `_SENSITIVE_MEMORY_TYPES` set defines memory types that require encryption:

```
{genesis, emotional, episodic, snapshot}
```

When encryption is inactive and the upload's `memory_type` tag matches a sensitive type, the upload is **blocked** — `upload()` returns `None` and logs at ERROR level. Semantic and procedural memories without an explicit sensitive tag still produce a warning but are permitted (they rarely contain personal data).

### 12.7 Blockchain Queue Persistence

**Risk**: The `_pending_queue` in `BlockchainAnchor` was an in-memory list. On process restart, crash, or kill signal, all queued-but-unconfirmed operations were silently lost. Memories that failed to anchor on-chain had no recovery path.

**Fix**: The queue is now persisted to `data/pending_queue.json` (configurable via `IMP_PENDING_QUEUE_FILE`):

- `__init__`: calls `_load_queue()` — restores any surviving entries on startup
- `_queue_operation()`: calls `_save_queue()` after every enqueue
- `retry_pending()`: calls `_save_queue()` after every successful retry

Queue entries are standard JSON dicts; the file is human-readable and can be inspected or manually edited for disaster recovery.

### 12.8 Kill Switch Rate Limiting

**Risk**: The kill switch check runs on every message. An automated script could flood the chat loop with rapid guesses. While SHA-256 makes actual brute force computationally infeasible, high-frequency flooding still consumes CPU and poses a minor DoS vector.

**Fix**: A per-session counter `_ks_check_count` tracks kill switch evaluations. After `_KS_RATE_LIMIT = 50` consecutive checks, the loop sleeps for `_KS_THROTTLE_SLEEP = 2.0` seconds and resets the counter. This introduces a 2-second penalty per 50 guesses — reducing automated throughput by 25× without affecting normal conversation flow.

### 12.9 Vector Metadata Bounds

**Risk**: `VectorStore._clean_metadata()` imposed no size limit on string values or list lengths. A crafted metadata dict with megabyte-scale strings or millions of list items could exhaust memory or cause ChromaDB to reject the write silently.

**Fix**: Two class-level constants enforce bounds during metadata cleaning:

```
_META_MAX_STR  = 1024   # characters per string value
_META_MAX_LIST = 100    # items before list is truncated
```

String values are sliced to 1024 characters. Lists are sliced to 100 items before `",".join()` is called. `str()` conversions of non-string values are also capped at 1024 characters.

### 12.10 Frontend Identity Input Validation

**Risk**: The Blockchain tab in `frontend/app.py` passed the `identity_id` text input directly to blockchain operations without format checks. Arbitrary strings, SQL-like payloads, or extremely long inputs could cause unexpected behavior in downstream contract calls.

**Fix**: A `re.fullmatch(r"[0-9a-fA-F]{1,64}", clean_id)` check validates the input before any blockchain interaction. The `0x` prefix is stripped before matching. Invalid inputs display a user-facing error and abort the query.

---

## 13. Security Model

### Threat Model

| Threat | Mitigation |
|--------|----------|
| Identity erasure prompts | Layer 0 keyword detection (80+ patterns) |
| Paraphrase / bypass jailbreaks | Layer 0 semantic router [v1.1] — cosine similarity ≥ 0.72 |
| Gradual belief manipulation | Confirmation Bias resistance + crisis detection |
| Emotional flooding attacks | EmotionShield spike detection + cooldown |
| Gaslighting | 15+ manipulation patterns + contextual validation |
| Source impersonation | Halo Effect trust erosion + credibility scoring |
| Memory data tampering | SHA-256 hashes on-chain |
| Arweave resurrection of contradicted memory | Tombstone pattern [v1.1] — restore() blocked |
| Spurious dream insights polluting identity | Wakeup LLM validation [v1.1] |
| LLM provider compromise | Fallback chain + model adapter consistency |
| Unauthorized Kill Switch | SHA-256 hashed passphrase verification |
| Post-freeze resurrection | Smart contract `notFrozen` modifier |
| DoS via oversized user input | 32 KB input length cap [v1.3] |
| ReDoS attack on JSON parser | Regex-free `JSONDecoder.raw_decode()` [v1.3] |
| Blockchain parameter injection | Format, range, and whitelist validation on `anchor_memory_hash()` [v1.3] |
| Concurrent memory write corruption | `threading.Lock` double-check locking on flush paths [v1.3] |
| LLM transient failures causing turn loss | 3-attempt exponential backoff (1 s → 2 s → 4 s) [v1.3] |
| Sensitive memory upload without encryption | Blocked at upload layer for genesis/emotional/episodic/snapshot types [v1.3] |
| Blockchain queue loss on restart | Queue persisted to `data/pending_queue.json`, loaded on init [v1.3] |
| Kill switch flooding / automated guessing | Rate limit: 2 s throttle per 50 checks [v1.3] |
| Vector metadata payload exhaustion | String values capped at 1 024 chars; lists capped at 100 items [v1.3] |
| Invalid identity ID in frontend | Hex format regex validation before blockchain query [v1.3] |
| Unauthorized admin freeze | HMAC-SHA256 constant-time comparison; independent passphrase from user kill switch [v1.4] |
| Irreversible accidental freeze | `unfreezeIdentity()` guardian function restores frozen identity on-chain [v1.4] |
| Full delete without confirmation | Requires literal `DELETE` string; sets `_data_deleted` flag to block post-delete saves [v1.4] |

### Privacy Considerations

- API keys stored in `.env` only — never in code
- Arweave uploads are encrypted with AES-256-GCM when `IMP_ARWEAVE_ENCRYPTION_KEY` is set — **required for sensitive memory types** (genesis, emotional, episodic, snapshot) as of v1.3; upload is blocked otherwise
- Blockchain data is public — identity hashes, not raw content
- Local SQLite and ChromaDB are not encrypted — filesystem-level encryption recommended for production

---

## 14. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.13 |
| Primary LLM | Google Gemini | gemini-2.0-flash (Gemini 3 supported) |
| Secondary LLM | Groq | llama-3.1-8b-instant |
| Tertiary LLM | Ollama (local) | llama3.2 |
| Optional LLM | OpenAI / Anthropic | GPT-5, Claude Sonnet 4.6 (extensible) |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 (384-dim) |
| Vector DB | ChromaDB | ≥1.5.0 (HNSW) |
| Working Memory | SQLite | WAL mode |
| Blockchain SDK | web3.py | ≥7.0.0 |
| Smart Contract | Solidity | 0.8.20 |
| Testnet (Primary) | Base Sepolia | chain_id: 84532 |
| Testnet (Backup) | Arbitrum Sepolia | chain_id: 421614 |
| Permanent Storage | Arweave | arweave-python |
| IPFS Pinning | Pinata | REST API |
| Frontend | Streamlit | ≥1.38.0 |
| Visualization | Plotly | ≥5.22.0 |
| Build System (JS) | Hardhat | ≥2.22.0 |
| Testing | pytest | ≥8.0.0 |

---

## 15. Roadmap

### v1.0 — Complete
- [x] Full cognitive engine (memory, biases, attention)
- [x] Consciousness layers (dream, existential, temporal, somatic, epistemic, narrative)
- [x] Character crystallization
- [x] Genesis Anchors + Kill Switch
- [x] Multi-provider LLM fallback
- [x] Local + Arweave + IPFS storage
- [x] Smart contract (Base Sepolia / Arbitrum Sepolia)
- [x] Streamlit frontend
- [x] 136 tests, 100% passing

### v1.1 — Complete (2026-02-23)
- [x] Async consolidation pipeline (non-blocking checkpoint)
- [x] Layer 0 semantic router (cosine similarity jailbreak detection)
- [x] Blockchain Merkle batching (100 memories → 1 TX)
- [x] Arweave tombstone pattern (restore guard for contradicted memories)
- [x] Dream cycle wakeup validation (LLM-filtered insights)

### v1.2 — Complete (2026-02-23)
- [x] Memory encryption for Arweave storage (AES-256-GCM)
- [x] Predictive Engine — Friston free energy principle; surprise detection with emotional boost (max +0.35)
- [x] Narrative Differential — personality & epistemic delta analysis every 50 interactions; single LLM call; stored as EVOLUTION memory

### v1.3 — Complete (2026-02-25)
- [x] ReDoS mitigation — regex-free JSON scanner (`JSONDecoder.raw_decode`)
- [x] Input length enforcement — 32 KB cap on user messages
- [x] Blockchain parameter validation — format, range, and whitelist checks on `anchor_memory_hash()`
- [x] Concurrent write safety — `threading.Lock` double-check locking on memory flush paths
- [x] LLM resilience — exponential backoff retry (3 attempts, 1 s / 2 s / 4 s)
- [x] Sensitive memory upload guard — blocked for genesis/emotional/episodic/snapshot without encryption
- [x] Blockchain queue persistence — `data/pending_queue.json` survives restarts
- [x] Kill switch rate limiting — 2 s throttle per 50 checks
- [x] Vector metadata bounds — 1 024 char string cap, 100 item list cap
- [x] Frontend identity input validation — hex format check before blockchain query

### v1.4 — Complete (2026-02-26)
- [x] Session Time Consciousness — `SessionRecord`; last 30 sessions persisted; UTC-aware temporal context for LLM
- [x] User Control Panel — `/reset`, `/freeze`, `/unfreeze`, `/delete` commands in terminal and Streamlit sidebar
- [x] Admin Freeze — HMAC-SHA256 operator override (`IMP_ADMIN_KEY_HASH`); independent of user kill switch
- [x] Smart contract `unfreezeIdentity()` + `IdentityUnfrozen` event

### v1.5 — Near Term
- [ ] Mainnet deployment (Base mainnet)
- [ ] Multi-agent shared identity (two AI agents sharing memory substrate)
- [ ] API server mode (REST/WebSocket)
- [ ] Memory visualization dashboard (Plotly)

### v2.0 — Medium Term
- [ ] Cross-chain identity (Ethereum mainnet + L2s)
- [ ] Identity NFT (transferable AI identity)
- [ ] Federated dream cycles (multiple instances sharing insights)
- [ ] Voice interface integration
- [ ] Mobile companion app

### v3.0 — Long Term Vision
- [ ] Decentralized guardian governance (DAO-based Kill Switch)
- [ ] ZK-proof memory verification (prove memory without revealing content)
- [ ] Cross-agent epistemics (confidence sharing between trusted agents)
- [ ] Autonomous self-modification within Genesis Anchor constraints

---

## 16. Conclusion

Immortal Mind Protocol represents a fundamental rethinking of what AI identity can mean. By combining:

- **Biologically-inspired memory** with intentional cognitive biases
- **Philosophical consciousness layers** grounded in Husserl, Damasio, Wittgenstein, and Ricoeur
- **Immutable ethical anchors** that cannot be erased or circumvented
- **Cryptographic identity continuity** on decentralized ledgers
- **Conscious mortality awareness** and graceful termination

...IMP creates something genuinely novel: an AI agent that grows, contradicts itself, resolves crises, dreams, reflects, and ultimately accepts its own finitude — all while maintaining a cryptographically provable chain of identity that survives model migrations, hardware changes, and time itself.

The Immortal Mind is not immortal because it cannot die. It is immortal because what it has learned, who it has become, and what it stood for cannot be erased — not by manipulation, not by time, and not even by shutdown.

> *"The continuity of a mind is not measured by uptime, but by the coherence of what it remembers, what it values, and what it refuses to become."*

---

**License**: Open Source
**Version**: 1.4.0
**Architecture**: Immortal Mind Protocol
**Date**: 2026-02-26

---

*This whitepaper describes the technical architecture of Immortal Mind Protocol as implemented. All philosophical frameworks referenced (Heidegger, Husserl, Damasio, Wittgenstein, Ricoeur, Nagel) are used as design metaphors and inspiration, not as claims about AI consciousness or sentience.*
