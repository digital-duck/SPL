"""Imperative Python baselines for comparison with SPL.

Each function implements the same task as an SPL example,
but using manual imperative Python code (as a data engineer would).
These are NOT executed---they exist to measure code complexity
(lines of code, manual token ops, etc.) against SPL equivalents.
"""

# ============================================================
# Task 1: Simple QA (hello_world.spl equivalent)
# ============================================================

SIMPLE_QA_PYTHON = '''\
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def simple_qa(user_input: str, max_budget: int = 2000) -> str:
    system = "You are a friendly assistant"
    system_tokens = len(enc.encode(system))
    input_tokens = len(enc.encode(user_input))
    output_budget = 1000
    input_limit = 500

    # Manual truncation
    if input_tokens > input_limit:
        chars = int(len(user_input) * input_limit / input_tokens)
        user_input = user_input[:chars]
        input_tokens = input_limit

    # Check budget
    total = system_tokens + input_tokens + output_budget
    if total > max_budget:
        raise ValueError(f"Over budget: {total} > {max_budget}")

    prompt = f"{system}\\n\\nInput: {user_input}\\n\\nRespond:"
    # result = call_llm(prompt, max_tokens=output_budget)
    return prompt
'''

# ============================================================
# Task 2: RAG-augmented QA (rag_query.spl equivalent)
# ============================================================

RAG_QA_PYTHON = '''\
import tiktoken
from some_vector_store import VectorStore

enc = tiktoken.get_encoding("cl100k_base")
vector_store = VectorStore("./vectors")

def rag_qa(question: str, max_budget: int = 8000) -> str:
    system = "You are a knowledgeable assistant. Answer based on the provided documents."
    system_tokens = len(enc.encode(system))
    output_budget = 2000

    # Count question tokens and truncate
    question_tokens = len(enc.encode(question))
    question_limit = 200
    if question_tokens > question_limit:
        chars = int(len(question) * question_limit / question_tokens)
        question = question[:chars]
        question_tokens = question_limit

    # Retrieve documents
    docs = vector_store.query(question, top_k=5)
    docs = [d for d in docs if d["score"] > 0.7]
    docs.sort(key=lambda d: d["score"], reverse=True)

    # Manually truncate docs to fit budget
    doc_limit = 3000
    doc_text = ""
    doc_tokens = 0
    for doc in docs:
        t = len(enc.encode(doc["text"]))
        if doc_tokens + t <= doc_limit:
            doc_text += doc["text"] + "\\n\\n"
            doc_tokens += t
        else:
            remaining = doc_limit - doc_tokens
            if remaining > 50:
                chars = int(len(doc["text"]) * remaining / t)
                doc_text += doc["text"][:chars]
                doc_tokens = doc_limit
            break

    # Load history from memory
    history = load_memory("conversation_history")
    history_tokens = len(enc.encode(history))
    history_limit = 500
    if history_tokens > history_limit:
        chars = int(len(history) * history_limit / history_tokens)
        history = history[:chars]

    # Check budget
    total = system_tokens + question_tokens + doc_tokens + history_limit + output_budget
    if total > max_budget:
        # Manual proportional compression
        excess = total - max_budget
        doc_tokens = max(100, doc_tokens - excess)

    prompt = f"{system}\\n\\nDocuments:\\n{doc_text}\\n\\nHistory:\\n{history}\\n\\nQuestion: {question}\\nAnswer:"
    # result = call_llm(prompt, max_tokens=output_budget, temperature=0.3)
    return prompt
'''

# ============================================================
# Task 3: Multi-step with CTEs (multi_step.spl equivalent)
# ============================================================

MULTI_STEP_PYTHON = '''\
import tiktoken
from some_vector_store import VectorStore

enc = tiktoken.get_encoding("cl100k_base")
vector_store = VectorStore("./vectors")

def multi_step_recommend(user_profile: str, max_budget: int = 12000) -> str:
    system = "You are a product recommendation expert"
    system_tokens = len(enc.encode(system))
    output_budget = 4000

    # CTE 1: Compress user profile
    profile_tokens = len(enc.encode(user_profile))
    profile_limit = 500
    if profile_tokens > profile_limit:
        chars = int(len(user_profile) * profile_limit / profile_tokens)
        user_profile = user_profile[:chars]
        # Try to end at sentence boundary
        last_period = user_profile.rfind(".")
        if last_period > len(user_profile) * 0.8:
            user_profile = user_profile[:last_period + 1]
        profile_tokens = profile_limit

    # CTE 2: Retrieve relevant docs
    docs = vector_store.query("product recommendations", top_k=3)
    doc_limit = 2000
    doc_text = ""
    doc_tokens = 0
    for doc in docs:
        t = len(enc.encode(doc["text"]))
        if doc_tokens + t <= doc_limit:
            doc_text += doc["text"] + "\\n\\n"
            doc_tokens += t
        else:
            remaining = doc_limit - doc_tokens
            if remaining > 50:
                chars = int(len(doc["text"]) * remaining / t)
                doc_text += doc["text"][:chars]
                doc_tokens = doc_limit
            break

    # Load purchase history from memory
    history = load_memory("purchase_history")
    history_tokens = len(enc.encode(history))
    history_limit = 1000
    if history_tokens > history_limit:
        chars = int(len(history) * history_limit / history_tokens)
        history = history[:chars]
        history_tokens = history_limit

    # Budget check
    total = system_tokens + profile_tokens + doc_tokens + history_tokens + output_budget
    if total > max_budget:
        excess = total - max_budget
        # Compress largest sources first
        if doc_tokens > profile_tokens:
            doc_tokens = max(200, doc_tokens - excess)
        else:
            profile_tokens = max(100, profile_tokens - excess)

    prompt = (
        f"{system}\\n\\n"
        f"User Profile:\\n{user_profile}\\n\\n"
        f"Relevant Products:\\n{doc_text}\\n\\n"
        f"Purchase History:\\n{history}\\n\\n"
        f"Based on this information, provide product recommendations in markdown format."
    )
    # result = call_llm(prompt, max_tokens=output_budget, temperature=0.5)
    # save_memory("last_recommendations", result)
    return prompt
'''

# ============================================================
# Task 4: Function reuse (custom_function.spl equivalent)
# ============================================================

FUNCTION_REUSE_PYTHON = '''\
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def compress_bio(bio: str, max_tokens: int) -> str:
    """Reusable compression function."""
    tokens = len(enc.encode(bio))
    if tokens <= max_tokens:
        return bio
    chars = int(len(bio) * max_tokens / tokens)
    truncated = bio[:chars]
    last_period = truncated.rfind(".")
    if last_period > len(truncated) * 0.8:
        truncated = truncated[:last_period + 1]
    return truncated

def team_overview(team_data: str, project_status: str, max_budget: int = 10000) -> str:
    system = "You are a team management assistant"
    system_tokens = len(enc.encode(system))
    output_budget = 3000

    # Manual token counting for each context source
    team_tokens = len(enc.encode(team_data))
    team_limit = 2000
    if team_tokens > team_limit:
        chars = int(len(team_data) * team_limit / team_tokens)
        team_data = team_data[:chars]
        team_tokens = team_limit

    project_tokens = len(enc.encode(project_status))
    project_limit = 1500
    if project_tokens > project_limit:
        chars = int(len(project_status) * project_limit / project_tokens)
        project_status = project_status[:chars]
        project_tokens = project_limit

    # Budget check
    total = system_tokens + team_tokens + project_tokens + output_budget
    if total > max_budget:
        excess = total - max_budget
        team_tokens = max(200, team_tokens - excess)

    prompt = (
        f"{system}\\n\\n"
        f"Team Data:\\n{team_data}\\n\\n"
        f"Project Status:\\n{project_status}\\n\\n"
        f"Provide a team summary."
    )
    # result = call_llm(prompt, max_tokens=output_budget, temperature=0.4)
    return prompt
'''

# ============================================================
# Task 5: Cached repeat query
# ============================================================

CACHED_REPEAT_PYTHON = '''\
import hashlib
import sqlite3
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

# Manual cache implementation
cache_db = sqlite3.connect("./cache.db")
cache_db.execute("""
    CREATE TABLE IF NOT EXISTS prompt_cache (
        hash TEXT PRIMARY KEY,
        result TEXT,
        model TEXT,
        tokens_used INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

def cached_qa(user_input: str, max_budget: int = 2000) -> str:
    system = "You are a friendly assistant"
    system_tokens = len(enc.encode(system))
    input_tokens = len(enc.encode(user_input))
    output_budget = 1000
    input_limit = 500

    if input_tokens > input_limit:
        chars = int(len(user_input) * input_limit / input_tokens)
        user_input = user_input[:chars]
        input_tokens = input_limit

    prompt = f"{system}\\n\\nInput: {user_input}\\n\\nRespond:"

    # Manual caching
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    row = cache_db.execute(
        "SELECT result FROM prompt_cache WHERE hash = ?",
        (prompt_hash,)
    ).fetchone()
    if row:
        return row[0]

    # result = call_llm(prompt, max_tokens=output_budget)
    result = "..."  # placeholder
    cache_db.execute(
        "INSERT OR REPLACE INTO prompt_cache (hash, result, model, tokens_used) VALUES (?, ?, ?, ?)",
        (prompt_hash, result, "claude-sonnet-4-5", input_tokens + len(enc.encode(result)))
    )
    cache_db.commit()
    return result
'''


# All baselines keyed by task name
BASELINES = {
    "simple_qa": SIMPLE_QA_PYTHON,
    "rag_qa": RAG_QA_PYTHON,
    "multi_step": MULTI_STEP_PYTHON,
    "function_reuse": FUNCTION_REUSE_PYTHON,
    "cached_repeat": CACHED_REPEAT_PYTHON,
}
