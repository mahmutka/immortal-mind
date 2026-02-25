"""
frontend/app.py

Immortal Mind Protocol — Streamlit Web Interface

Tabs:
    1. Chat          — Conversation with the AI (single window)
    2. Blockchain    — On-chain log viewer
    3. Resilience    — Provider status and fallback chain

NOTE: Memory and character tabs have been removed.
The AI's inner world cannot be viewed directly.
Its character, memory, and consciousness can only be discovered through conversation.
"""

import logging
import os
import re
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# PAGE LAYOUT
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Immortal Mind Protocol",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

def init_session_state():
    if "engine" not in st.session_state:
        st.session_state.engine = None
    if "llm_client" not in st.session_state:
        st.session_state.llm_client = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "confirm_reset" not in st.session_state:
        st.session_state.confirm_reset = False
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
    if "model_adapter" not in st.session_state:
        st.session_state.model_adapter = None


def initialize_engine(provider: str = "gemini"):
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)

        from agent.llm_client import LLMClient
        from cognitio.engine import CognitioEngine

        llm = LLMClient(provider=provider)
        engine = CognitioEngine(
            llm_client=llm,
            config={
                "reality_check_enabled": True,
                "max_active_memories": int(os.getenv("MAX_ACTIVE_MEMORIES", "10000")),
            },
        )

        from agent.model_adapter import ModelAdapter
        st.session_state.llm_client = llm
        st.session_state.engine = engine
        st.session_state.model_adapter = ModelAdapter(provider=provider)
        st.session_state.initialized = True
        return True

    except Exception as e:
        st.error(f"Initialization error: {e}")
        return False


# ─────────────────────────────────────────────
# SIDEBAR — connection status only
# ─────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.title("🧠 Immortal Mind")
        st.caption("Blockchain-Persistent AI Identity")

        st.divider()

        provider = st.selectbox(
            "LLM Provider",
            ["groq", "gemini", "ollama"],
            index=0,
            help="Groq → Gemini → Ollama fallback chain",
        )

        if st.button("🚀 Start / Reconnect", use_container_width=True):
            with st.spinner("Initializing..."):
                if initialize_engine(provider):
                    st.success("Connection established.")
                    st.rerun()

        st.divider()

        if st.session_state.initialized:
            st.success("🟢 System active")
        else:
            st.info("Select a provider and click 'Start'.")

        st.divider()

        # ─── System Control (show only if initialized) ───
        if st.session_state.get("initialized"):
            engine = st.session_state.engine
            st.markdown("**⚙️ System Control**")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset", help="Reset memory and personality (Genesis preserved)"):
                    st.session_state.confirm_reset = True
            with col2:
                if engine.state.is_frozen:
                    if st.button("▶️ Activate", help="Activate the AI"):
                        engine.user_unfreeze()
                        st.rerun()
                else:
                    if st.button("⏸️ Freeze", help="Freeze the AI (memory preserved)"):
                        engine.user_freeze()
                        st.rerun()

            # Soft reset confirmation
            if st.session_state.get("confirm_reset"):
                st.warning("⚠️ All memory and personality will be deleted!")
                c1, c2 = st.columns(2)
                if c1.button("✅ Confirm", key="confirm_reset_yes"):
                    engine.soft_reset()
                    st.session_state.messages = []
                    st.session_state.confirm_reset = False
                    st.rerun()
                if c2.button("❌ Cancel", key="confirm_reset_no"):
                    st.session_state.confirm_reset = False
                    st.rerun()

            # Full delete — danger zone
            with st.expander("⚠️ Danger Zone"):
                if st.button("🗑️ Delete All Data (GDPR)", type="secondary"):
                    st.session_state.confirm_delete = True
                if st.session_state.get("confirm_delete"):
                    st.error("This action **cannot be undone!**")
                    if st.button("💀 Delete Permanently", type="primary"):
                        engine.full_delete()
                        st.session_state.clear()
                        st.rerun()
                    if st.button("Cancel"):
                        st.session_state.confirm_delete = False
                        st.rerun()

            st.divider()

        st.caption("Immortal Mind Protocol v0.5")
        st.caption("The inner world can only be discovered through conversation.")


# ─────────────────────────────────────────────
# CHAT TAB
# ─────────────────────────────────────────────

def render_chat():
    st.header("💬 Chat")

    if not st.session_state.initialized:
        st.warning("Initialize the system from the left panel.")
        return

    engine = st.session_state.engine
    llm = st.session_state.llm_client

    # Sleep / dream notification (only until the first message of this session)
    if "sleep_shown" not in st.session_state:
        st.session_state.sleep_shown = False

    if not st.session_state.sleep_shown and engine is not None:
        sleep_msg = engine.temporal.get_sleep_summary()
        dream_msg = engine.dream.get_dream_summary()
        if sleep_msg or dream_msg:
            parts = []
            if sleep_msg:
                parts.append(sleep_msg)
            if dream_msg:
                parts.append(dream_msg)
            st.info("🌙 " + " ".join(parts))
        st.session_state.sleep_shown = True

    # Frozen warning
    if engine is not None and engine.state.is_frozen:
        st.warning(
            "⏸️ The AI is currently frozen. "
            "Click the '▶️ Activate' button in the sidebar."
        )
        st.stop()

    # Message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User input
    if prompt := st.chat_input("Type your message..."):
        with st.chat_message("user"):
            st.write(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        engine.process_interaction("user", prompt)

        context = engine.build_context_for_llm(prompt)

        # Somatic and relational hints
        adapter = st.session_state.model_adapter
        somatic_mods = engine.somatic.get_modifiers()
        relational_hints = engine.character.relational.get_style_hints()

        system_prompt = adapter.build_system_prompt(
            base_prompt=context or None,
            relational_hints=relational_hints,
        )

        with st.chat_message("assistant"):
            with st.spinner("..."):
                try:
                    history = st.session_state.messages[-10:]
                    response = llm.chat(
                        history,
                        system_prompt=system_prompt,
                        max_tokens=adapter.get_max_tokens(somatic_mods),
                        temperature=adapter.get_temperature(somatic_mods),
                    )
                    st.write(response)

                    engine.process_interaction("assistant", response)
                    # Save session data to disk — no loss if tab closes
                    try:
                        engine.save_state()
                    except Exception as exc:
                        logger.debug("save_state failed: %s", exc)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                    })

                except Exception as e:
                    st.error(f"LLM error: {e}")


# ─────────────────────────────────────────────
# BLOCKCHAIN TAB
# ─────────────────────────────────────────────

def render_blockchain():
    st.header("⛓️ Blockchain Log")

    st.info(
        "This tab shows on-chain anchor logs and identity information. "
        "Simulated data is displayed before the contract is deployed."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Identity Verification")
        identity_id = st.text_input("Identity ID (bytes32)", placeholder="0x...")
        if st.button("Query") and identity_id:
            clean_id = identity_id.removeprefix("0x").strip()
            if not re.fullmatch(r"[0-9a-fA-F]{1,64}", clean_id):
                st.error("Invalid Identity ID: must be 1-64 hex characters (0x prefix optional).")
            else:
                try:
                    from storage.blockchain_anchor import BlockchainAnchor
                    BlockchainAnchor()
                    st.json({"identity_id": identity_id, "status": "simulated"})
                except Exception as e:
                    st.error(f"Blockchain connection error: {e}")

    with col2:
        st.subheader("Chain Status")
        chains = [
            {"name": "Base Sepolia", "rpc": os.getenv("BASE_RPC_URL", "https://sepolia.base.org")},
            {"name": "Arbitrum Sepolia", "rpc": os.getenv("ARBITRUM_RPC_URL", "https://sepolia-rollup.arbitrum.io/rpc")},
        ]

        for chain in chains:
            st.write(f"**{chain['name']}**")
            st.caption(f"RPC: {chain['rpc']}")
            if st.button(f"Test {chain['name']}", key=f"btn_{chain['name']}"):
                try:
                    from web3 import Web3
                    w3 = Web3(Web3.HTTPProvider(chain["rpc"]))
                    if w3.is_connected():
                        block = w3.eth.block_number
                        st.success(f"✅ Connected - Block: {block}")
                    else:
                        st.error("❌ Could not connect")
                except Exception as e:
                    st.error(f"❌ Error: {e}")


# ─────────────────────────────────────────────
# RESILIENCE TAB
# ─────────────────────────────────────────────

def render_resilience():
    st.header("🛡️ Resilience Dashboard")

    st.subheader("Provider Status")

    providers = [
        {"name": "Gemini API", "type": "LLM", "env": "GOOGLE_API_KEY"},
        {"name": "Groq API", "type": "LLM", "env": "GROQ_API_KEY"},
        {"name": "Ollama (Local)", "type": "LLM", "env": None},
        {"name": "Arweave", "type": "Storage", "env": "ARWEAVE_WALLET_PATH"},
        {"name": "IPFS/Pinata", "type": "Storage", "env": "PINATA_API_KEY"},
        {"name": "Base Sepolia", "type": "Blockchain", "env": "BASE_CONTRACT_ADDRESS"},
        {"name": "Arbitrum Sepolia", "type": "Blockchain", "env": "ARBITRUM_CONTRACT_ADDRESS"},
    ]

    for provider in providers:
        configured = bool(provider["env"] is None or os.getenv(provider["env"]))
        status = "✅ Configured" if configured else "⚠️ API Key Missing"
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{provider['name']}**")
        with col2:
            st.caption(provider["type"])
        with col3:
            st.caption(status)

    st.divider()
    st.subheader("Survival Levels")

    levels = [
        {"level": 1, "name": "Fully Operational", "desc": "LLM ✓ Blockchain ✓ Arweave ✓"},
        {"level": 2, "name": "Degraded Performance", "desc": "LLM API ✗ → Local Ollama"},
        {"level": 3, "name": "Offline Anchor", "desc": "Blockchain ✗ → Queue"},
        {"level": 4, "name": "Local Mode", "desc": "Computer only: Ollama + SQLite"},
        {"level": 5, "name": "Frozen", "desc": "Compute ✗ → 'Deep sleep'"},
    ]

    for lev in levels:
        st.write(f"**Level {lev['level']}: {lev['name']}** — {lev['desc']}")


# ─────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────

def main():
    init_session_state()
    render_sidebar()

    tab1, tab2, tab3 = st.tabs([
        "💬 Chat",
        "⛓️ Blockchain",
        "🛡️ Resilience",
    ])

    with tab1:
        render_chat()
    with tab2:
        render_blockchain()
    with tab3:
        render_resilience()


if __name__ == "__main__":
    main()
