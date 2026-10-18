"""
frontend/app.py

Immortal Mind Protocol — Streamlit Web Interface

One shared mind talks with every visitor. Visitors log in with a
username + password; what each person tells the mind is private to them
unless they turn on "Share publicly".

Tabs:
    1. Chat          — Conversation with the AI (single window)
    2. Blockchain    — On-chain log viewer (admins only)
    3. Resilience    — Provider status and fallback chain (admins only)

NOTE: Memory and character tabs have been removed.
The AI's inner world cannot be viewed directly.
Its character, memory, and consciousness can only be discovered through conversation.
"""

import hmac
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
# SHARED MIND
# ─────────────────────────────────────────────
#
# One mind talks with everyone. The engine is created once per server
# process (st.cache_resource) and shared by every browser session —
# separate engines would overwrite each other's files in data/.

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@st.cache_resource(show_spinner="Waking up the mind...")
def get_mind():
    """Create the shared engine, LLM client and account store (once per process)."""
    from dotenv import load_dotenv
    load_dotenv()

    from agent.accounts import AccountStore
    from agent.llm_client import LLMClient
    from agent.model_adapter import ModelAdapter
    from cognitio.engine import CognitioEngine

    provider = os.getenv("LLM_PROVIDER", "gemini")
    data_dir = os.getenv("IMP_DATA_DIR", "data")
    llm = LLMClient(provider=provider)
    engine = CognitioEngine(
        llm_client=llm,
        config={
            "reality_check_enabled": True,
            "max_active_memories": _env_int("MAX_ACTIVE_MEMORIES", 10000),
        },
        data_dir=data_dir,
    )
    return {
        "engine": engine,
        "llm": llm,
        "adapter": ModelAdapter(provider=provider),
        "accounts": AccountStore(os.path.join(data_dir, "accounts.db")),
    }


def is_admin(username: str | None) -> bool:
    admins = {
        a.strip().lower() for a in os.getenv("IMP_ADMIN_USERS", "").split(",") if a.strip()
    }
    return bool(username) and username in admins


def init_session_state():
    defaults = {
        "user": None,           # logged-in username (= memory owner_id)
        "last_seen": None,      # when this person last talked with the mind
        "messages": [],
        "share_public": False,  # messages sent while on become public memories
        "confirm_reset": False,
        "confirm_delete": False,
        "confirm_forget_me": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ─────────────────────────────────────────────
# LOGIN / REGISTER
# ─────────────────────────────────────────────

def render_login(accounts) -> None:
    from agent.accounts import AccountError

    st.title("🧠 Immortal Mind")
    st.caption(
        "One mind that talks with everyone and remembers everyone. "
        "What you tell it stays between the two of you."
    )

    login_tab, register_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            try:
                user = accounts.authenticate(username, password)
            except AccountError as e:
                st.error(str(e))
            else:
                if user:
                    _start_session(accounts, user)
                    st.rerun()
                else:
                    st.error("Wrong username or password.")

    with register_tab:
        if os.getenv("IMP_REGISTRATION_OPEN", "true").lower() != "true":
            st.info("New registrations are currently closed.")
            return
        max_accounts = _env_int("IMP_MAX_ACCOUNTS", 0)
        if max_accounts and accounts.count_accounts() >= max_accounts:
            st.info("The mind is not meeting new people right now. Please try again later.")
            return
        with st.form("register_form"):
            username = st.text_input(
                "Username", help="3-24 characters: lowercase letters, digits or _"
            )
            password = st.text_input("Password", type="password", help="At least 8 characters")
            password2 = st.text_input("Password (again)", type="password")
            submitted = st.form_submit_button("Create account", use_container_width=True)
        if submitted:
            if password != password2:
                st.error("Passwords do not match.")
            else:
                try:
                    user = accounts.register(username, password)
                except AccountError as e:
                    st.error(str(e))
                else:
                    _start_session(accounts, user)
                    st.rerun()


def _start_session(accounts, user: str) -> None:
    st.session_state.user = user
    st.session_state.last_seen = accounts.get_last_seen(user)
    st.session_state.messages = []
    st.session_state.share_public = False


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

def render_sidebar(mind) -> None:
    engine = mind["engine"]
    accounts = mind["accounts"]
    user = st.session_state.user

    with st.sidebar:
        st.title("🧠 Immortal Mind")
        st.caption(f"Logged in as **{user}**")

        daily_limit = _env_int("IMP_DAILY_MESSAGE_LIMIT", 50)
        if daily_limit:
            used = accounts.messages_today(user)
            st.caption(f"Messages today: {used} / {daily_limit}")

        st.toggle(
            "🌍 Share publicly",
            key="share_public",
            help=(
                "Off (default): what you say is private — the mind only recalls it "
                "when talking with you. On: what you say while this is on may be "
                "shared with anyone the mind talks with."
            ),
        )
        if st.session_state.share_public:
            st.warning("Your next messages may be shared with everyone.")

        if st.button("Log out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # Right to erasure — only this person's data
        with st.expander("🗑️ Delete my data"):
            st.caption(
                "The mind forgets everything you told it and your account is deleted. "
                "This cannot be undone."
            )
            if st.button("Delete my data and account"):
                st.session_state.confirm_forget_me = True
            if st.session_state.confirm_forget_me:
                st.error("Are you sure?")
                c1, c2 = st.columns(2)
                if c1.button("✅ Yes, delete", key="forget_me_yes"):
                    engine.delete_owner_data(user)
                    accounts.delete_account(user)
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
                if c2.button("❌ Cancel", key="forget_me_no"):
                    st.session_state.confirm_forget_me = False
                    st.rerun()

        if is_admin(user):
            render_admin_controls(engine)

        st.divider()
        st.caption("Immortal Mind Protocol v1.5")
        st.caption("The inner world can only be discovered through conversation.")


def render_admin_controls(engine) -> None:
    """Controls that affect the mind for everyone — admins only."""
    st.divider()
    st.markdown("**⚙️ Admin: System Control**")

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
        st.warning("⚠️ Everyone's memories and the personality will be deleted!")
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
            st.error("This action **cannot be undone!** Restart the server afterwards.")
            if st.button("💀 Delete Permanently", type="primary"):
                engine.full_delete()
                get_mind.clear()
                st.session_state.clear()
                st.rerun()
            if st.button("Cancel"):
                st.session_state.confirm_delete = False
                st.rerun()


# ─────────────────────────────────────────────
# CHAT TAB
# ─────────────────────────────────────────────

def render_chat(mind) -> None:
    st.header("💬 Chat")

    engine = mind["engine"]
    llm = mind["llm"]
    adapter = mind["adapter"]
    accounts = mind["accounts"]
    user = st.session_state.user

    # Frozen warning
    if engine.state.is_frozen:
        st.warning("⏸️ The mind is resting right now. Please come back later.")
        return

    # Message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User input
    if prompt := st.chat_input("Type your message..."):
        from cognitio.input_sanitizer import sanitize_input
        prompt = sanitize_input(prompt)
        if not prompt:
            return

        allowed, reason = accounts.consume_message(
            user,
            daily_limit=_env_int("IMP_DAILY_MESSAGE_LIMIT", 50),
            global_daily_limit=_env_int("IMP_GLOBAL_DAILY_LIMIT", 2000),
        )
        if not allowed:
            if reason == "user":
                st.warning("You have reached today's message limit. See you tomorrow!")
            else:
                st.warning("The mind has talked a lot today and needs rest. Please come back tomorrow.")
            return

        visibility = "public" if st.session_state.share_public else "private"

        with st.chat_message("user"):
            st.write(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        engine.process_interaction("user", prompt, owner_id=user, visibility=visibility)

        context = engine.build_context_for_llm(
            prompt, viewer_id=user, viewer_last_seen=st.session_state.last_seen,
        )

        # Somatic and relational hints
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

                    engine.process_interaction(
                        "assistant", response, owner_id=user, visibility=visibility,
                    )
                    accounts.touch(user)
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
                    logger.error("LLM error: %s", e)
                    st.error("The mind could not answer right now. Please try again.")


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
# AUTHENTICATION
# ─────────────────────────────────────────────

def check_auth() -> bool:
    """Check web UI authentication via IMP_WEB_PASSWORD env var.

    If IMP_WEB_PASSWORD is not set, authentication is disabled (backward compatible).
    Uses hmac.compare_digest for constant-time comparison.

    Returns:
        bool: True if authenticated or auth is disabled
    """
    expected_password = os.getenv("IMP_WEB_PASSWORD")
    if not expected_password:
        return True  # Auth disabled — backward compatible

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("🔒 Immortal Mind Protocol")
    st.caption("Authentication required")
    password = st.text_input("Password", type="password", key="auth_password")
    if st.button("Login", use_container_width=True):
        if hmac.compare_digest(password, expected_password):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid password.")
    return False


# ─────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────

def main():
    if not check_auth():
        return

    init_session_state()

    try:
        mind = get_mind()
    except Exception as e:
        logger.error("Initialization error: %s", e)
        st.error("The mind could not be started. Check the server logs.")
        return

    if not st.session_state.user:
        render_login(mind["accounts"])
        return

    render_sidebar(mind)

    if not is_admin(st.session_state.user):
        render_chat(mind)
        return

    tab1, tab2, tab3 = st.tabs([
        "💬 Chat",
        "⛓️ Blockchain",
        "🛡️ Resilience",
    ])

    with tab1:
        render_chat(mind)
    with tab2:
        render_blockchain()
    with tab3:
        render_resilience()


if __name__ == "__main__":
    main()
