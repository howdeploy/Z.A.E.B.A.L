#!/usr/bin/env python3
"""Z.A.E.B.A.L. core.

Zaebal? Audit. Errors. Break. Analize. Leave no assumption.

Modes:
  default            UserPromptSubmit hook. Detects profanity (ru/en/zh) in the
                     user's prompt, tracks the streak per session and prints the
                     escalation protocol. On L3 it first runs an EXTERNAL
                     auditor agent (headless CLI) against the transcript and
                     injects its verdict. An explicit acknowledgment from the
                     user ("продолжай", "согласен", ...) resets the streak.

Contract with host hooks (Claude Code / Codex CLI / Kimi CLI):
  - exit 0, non-empty stdout -> stdout is appended to the agent's context
  - exit 0, empty stdout     -> nothing happens
  - exit 2, stderr           -> blocked, stderr is the reason shown
Fail-open: any internal error results in silent exit 0.
"""

import argparse
import contextlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

try:
    import fcntl  # POSIX only; state locking degrades gracefully without it
except ImportError:  # pragma: no cover - Windows
    fcntl = None

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get("ZAEBAL_STATE_DIR", str(Path.home() / ".zaebal")))
STATE_FILE = STATE_DIR / "state.json"
STATE_LOCK = STATE_DIR / "state.lock"
CONFIG_USER = STATE_DIR / "config.json"
CONFIG_DEFAULT = BASE_DIR / "config.json"

# set in the auditor subprocess env so a globally installed zaebal hook
# never fires on the auditor's own prompt (anti-recursion guard)
CHILD_ENV_FLAG = "ZAEBAL_INTERNAL"

WINDOW_SECONDS = 30 * 60  # sliding window for the escalation streak
MAX_SESSIONS = 50         # cap on sessions kept in the state file

DEFAULT_CONFIG = {
    "auditor": "same",        # "same" = same vendor as the host, or kimi/claude/codex/opencode/none
    "audit_levels": [3],      # levels that trigger the external auditor (sync wait!)
    "auditor_timeout_sec": 90,
    "auditor_command": "",    # custom auditor command; prompt is appended as last arg
    "transcript_tail_chars": 12000,
}

# headless one-shot invocations per agent CLI.
# Where the CLI supports it, the auditor is restricted to read-only operation
# (kimi -p has no such flag — audit prompt instructs read-only, and the
# static deny rules of the host config still apply).
AUDITOR_CMDS = {
    "kimi": lambda prompt: ["kimi", "-p", prompt],
    "claude": lambda prompt: ["claude", "-p", prompt, "--allowedTools", "Read,Grep,Glob"],
    "codex": lambda prompt: ["codex", "exec", "--skip-git-repo-check",
                             "--sandbox", "read-only", prompt],
    "opencode": lambda prompt: ["opencode", "run", prompt],
}

# leet-deobfuscation tables, per language. Digits map to different letters in
# English and Russian ("за3бал" needs 3->е, "3ntered" needs 3->e), so each
# language's wordlist is matched against its own normalized variant.
LEET_EN = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    "@": "a", "$": "s", "ё": "e", "Ё": "e",
})
LEET_RU = str.maketrans({
    "0": "о", "3": "е", "6": "б", "ё": "е", "Ё": "е",
    "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х", "y": "у",
    "@": "а", "$": "з",
})

# valence / addressee heuristics, applied to normalized text BEFORE any streak
# is counted. Order matters: addressee is checked first, praise is cancelled
# by complaint markers, everything left is "ambiguous" (half-weight streak).
_PRAISE = re.compile(
    r"\b(спасиб|благодар|получилос|отличн|крут|здорово|молодц|красав"
    r"|thank|great|awesome|amazing|perfect|nice|love|excellent)"
    r"|(?<!не )\bработает\b"
    r"|谢谢|感谢|太好"
)
_SECOND_PERSON = re.compile(
    r"\b(?:ты|теб|тво|тобо|ваш)"                    # prefixes: тебя, твой, вашего
    r"|\b(?:вы|вас|вам|you|your|u|claude|codex|kimi|opencode|клод|гпт)\b"
    r"|你"
)
# complaint markers: cancel praise ("сначала было отлично, но теперь сломал")
_COMPLAINT = re.compile(
    r"\b(?:опять|снова|сломал|сломано?|поломал|глючит|падает"
    r"|still|again|broken|wrong)\b"
    r"|сколько можно|не работает|doesn'?t work|not working|\bне то\b|\bне так\b"
)
# explicit acknowledgment: closes the incident (streak reset)
_ACK = re.compile(
    r"\b(?:ладно|хорошо|давай|продолжай|продолжаем|согласен|принято|принимаю"
    r"|ок|окей|go ahead|continue|lgtm)\b"
    r"|по плану"
)

ACK_NOTICE = (
    '<zaebal level="0">\n'
    "Стрик обнулён: пользователь подтвердил продолжение.\n"
    "Продолжай по плану, согласованному с человеком.\n"
    "</zaebal>\n"
)

_NONWORD = re.compile(r"[^\w\u4e00-\u9fff]+", re.UNICODE)
_SPACES = re.compile(r"\s+")
_REPEATS = re.compile(r"(.)\1{2,}")


# ---------------------------------------------------------------- detection

def normalize(text, leet=None, punct_to_space=True):
    """Lowercase, NFKC, leet-deobfuscation, collapse repeats.

    punct_to_space=True  -> punctuation becomes spaces (for word-level
                            valence/addressee regexes).
    punct_to_space=False -> punctuation is kept (for junk-tolerant root
                            matching: "f.u.c.k" must match, but "о хуках"
                            must not — a space is a word boundary, junk is not).
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(leet or LEET_EN).lower()
    text = _NONWORD.sub(" ", text) if punct_to_space else _SPACES.sub(" ", text)
    text = _REPEATS.sub(r"\1", text)
    return text.strip()


def make_variants(text):
    """Per-language normalized texts (leet tables differ).

    "<lang>"      punctuation -> spaces; used by valence/addressee regexes.
    "<lang>_raw"  punctuation kept; used for junk-tolerant root matching.
    """
    out = {}
    for lang, table in (("ru", LEET_RU), ("en", LEET_EN), ("zh", LEET_EN)):
        out[lang] = normalize(text, table)
        out[lang + "_raw"] = normalize(text, table, punct_to_space=False)
    return out


def _tolerant(root):
    """Letters of root joined by optional non-space junk, so "з*а*е*б" /
    "f.u.c.k" match — but separate words ("о хуках") don't."""
    return r"[^\w\s]?".join(re.escape(ch) for ch in root)


def load_patterns(base_dir=None):
    """Compile wordlists into [(regex, lang)] pairs.

    root    -> prefix match at a word boundary
    root$   -> whole word match
    ~regex  -> raw regex, used verbatim (for lookaheads etc.)
    zh entries are matched as plain substrings.
    """
    base_dir = base_dir or BASE_DIR
    patterns = []
    for lang in ("ru", "en", "zh"):
        path = base_dir / "wordlists" / f"{lang}.txt"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("~"):
                patterns.append((re.compile(line[1:]), lang))
            elif lang == "zh":
                patterns.append((re.compile(re.escape(line.replace(" ", ""))), lang))
            elif line.endswith("$"):
                root = normalize(line[:-1], LEET_RU if lang == "ru" else LEET_EN).strip()
                patterns.append((re.compile(r"\b" + _tolerant(root) + r"\b"), lang))
            else:
                root = normalize(line, LEET_RU if lang == "ru" else LEET_EN).strip()
                patterns.append((re.compile(r"\b" + _tolerant(root)), lang))
    return patterns


def contains_profanity(variants, patterns):
    return any(p.search(variants[lang + "_raw"]) for p, lang in patterns)


def classify(variants, patterns):
    """Two-stage trigger: wordlist is only a recall filter.

    clean     -> no profanity
    praise    -> profanity with praise markers and NO complaint markers
                 ("заебись, работает!") — ignored entirely
    directed  -> profanity + second-person markers ("ты меня заебал") — full weight
    ambiguous -> profanity without an addressee ("опять npm заебал") — half
                 weight: impersonal rage still escalates, but slowly

    Addressee is checked FIRST: "ничего не работает, ты меня заебал" is
    directed even though it contains the word "работает".
    """
    if not contains_profanity(variants, patterns):
        return "clean"
    if _SECOND_PERSON.search(variants["ru"]) or _SECOND_PERSON.search(variants["en"]):
        return "directed"
    praised = _PRAISE.search(variants["ru"]) or _PRAISE.search(variants["en"])
    complained = _COMPLAINT.search(variants["ru"]) or _COMPLAINT.search(variants["en"])
    if praised and not complained:
        return "praise"
    return "ambiguous"


def weight_for(kind):
    return {"directed": 1.0, "ambiguous": 0.5}.get(kind, 0.0)


def extract_text(payload):
    """Pull the user's prompt text out of a hook payload."""
    if not isinstance(payload, dict):
        return ""
    for key in ("prompt", "user_prompt", "message", "text"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return "\n".join(v for v in payload.values() if isinstance(v, str))


def level_for(weight):
    """Level from the accumulated streak weight (directed=1.0, ambiguous=0.5)."""
    if weight >= 4:
        return 3
    if weight >= 2:
        return 2
    return 1


# ------------------------------------------------------------------ config

def load_config():
    cfg = dict(DEFAULT_CONFIG)
    for path in (CONFIG_DEFAULT, CONFIG_USER):
        try:
            user = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(user, dict):
                cfg.update(user)
        except Exception:
            pass
    return cfg


# ------------------------------------------------------------------ state

def _load_state():
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(state, dict):
            return state
    except Exception:
        pass
    return {}


def _save_state(state):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        os.replace(tmp, STATE_FILE)  # atomic on POSIX
    except Exception:
        pass  # fail-open


@contextlib.contextmanager
def _locked():
    """Exclusive lock around read-modify-write of the state file.

    Parallel hooks (several CLI instances, or parallel hook rules) otherwise
    lose triggers: each reads, appends, and overwrites the other's write.
    """
    if fcntl is None:
        yield
        return
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        fh = open(STATE_LOCK, "w")
    except Exception:
        yield  # fail-open: no lock is better than no protocol
        return
    with fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _session_entry(state, session_id):
    """Normalize a session entry to {'stamps': [...]}."""
    entry = state.get(session_id)
    if isinstance(entry, list):  # legacy format: plain list of timestamps
        entry = {"stamps": entry}
    if not isinstance(entry, dict):
        entry = {"stamps": []}
    entry.setdefault("stamps", [])
    state[session_id] = entry
    return entry


def _norm_stamps(stamps, now):
    """Normalize stamp entries to [timestamp, weight] pairs within the window.

    Legacy entries are bare timestamps (weight 1.0).
    """
    out = []
    for s in stamps:
        if isinstance(s, (int, float)):
            if now - s < WINDOW_SECONDS:
                out.append([s, 1.0])
        elif (isinstance(s, (list, tuple)) and len(s) == 2
              and all(isinstance(x, (int, float)) for x in s)):
            if now - s[0] < WINDOW_SECONDS:
                out.append([s[0], s[1]])
    return out


def _prune(state, now):
    pruned = {}
    for sid, raw in state.items():
        entry = _session_entry({sid: raw}, sid)
        entry["stamps"] = _norm_stamps(entry["stamps"], now)
        if entry["stamps"]:
            pruned[sid] = entry
    if len(pruned) > MAX_SESSIONS:
        key = lambda kv: max(s[0] for s in kv[1]["stamps"])
        pruned = dict(sorted(pruned.items(), key=key)[-MAX_SESSIONS:])
    return pruned


def record_trigger(session_id, now=None, weight=1.0):
    """Register a profanity trigger. Returns (streak_weight, level)."""
    now = now if now is not None else time.time()
    with _locked():
        state = _prune(_load_state(), now)
        entry = _session_entry(state, session_id)
        entry["stamps"].append([now, weight])
        total = sum(w for _, w in entry["stamps"])
        level = level_for(total)
        _save_state(state)
    return total, level


def acknowledge(session_id):
    """User acknowledged the plan: reset the streak. Returns True if it was."""
    with _locked():
        state = _load_state()
        entry = state.get(session_id)
        if not isinstance(entry, (dict, list)):
            return False
        entry = _session_entry(state, session_id)
        if not entry["stamps"]:
            return False
        entry["stamps"] = []
        _save_state(state)
    return True


# ---------------------------------------------------------------- auditor

def resolve_auditor(host, cfg):
    """Which auditor CLI to use. Returns a key of AUDITOR_CMDS or None."""
    choice = str(cfg.get("auditor", "same")).lower()
    if choice in ("none", "off", ""):
        return None
    if choice == "same":
        return host if host in AUDITOR_CMDS else None
    return choice if choice in AUDITOR_CMDS else None


def transcript_tail(path, max_chars):
    """Best-effort extraction of recent dialog from a session transcript file."""
    try:
        raw = Path(path).read_bytes()[-max_chars * 2:].decode("utf-8", "replace")
    except Exception:
        return ""
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            lines.append(line)
            continue
        if not isinstance(obj, dict):
            lines.append(line)  # unknown record shape — keep raw, never crash
            continue
        role = obj.get("role") or obj.get("type") or ""
        content = obj.get("message", obj).get("content") if isinstance(obj.get("message", obj), dict) else None
        if isinstance(content, list):
            text = " ".join(
                c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") in (None, "text")
            )
        elif isinstance(content, str):
            text = content
        else:
            text = obj.get("text") if isinstance(obj.get("text"), str) else ""
        if text:
            lines.append(f"[{role}] {text}")
    return "\n".join(lines)[-max_chars:]


def git_summary(cwd):
    if not cwd or not Path(cwd).is_dir():
        return "(рабочая директория недоступна)"
    def run(*args):
        try:
            r = subprocess.run(
                ["git", "-C", cwd, *args],
                capture_output=True, text=True, timeout=10,
            )
            return r.stdout.strip()
        except Exception:
            return ""
    status = run("status", "--short")
    diffstat = run("diff", "--stat")
    diff = run("diff")[:4000]  # bounded: the auditor needs evidence, not noise
    log = run("log", "--oneline", "-5")
    if not (status or diffstat or diff or log):
        return "(не git-репозиторий или git недоступен)"
    parts = []
    if status:
        parts.append("git status --short:\n" + status[:2000])
    if diffstat:
        parts.append("git diff --stat:\n" + diffstat[:2000])
    if diff:
        parts.append("git diff (первые 4000 символов):\n" + diff)
    if log:
        parts.append("git log --oneline -5:\n" + log[:1000])
    return "\n\n".join(parts)


def build_audit_prompt(payload, level, cfg):
    cwd = payload.get("cwd", "")
    trigger = extract_text(payload)
    tail = ""
    tp = payload.get("transcript_path")
    if tp:
        tail = transcript_tail(tp, int(cfg.get("transcript_tail_chars", 12000)))
    return f"""Ты — независимый аудитор, вызванный системой Z.A.E.B.A.L.: пользователь ругается на кодинг-агента (уровень эскалации {level} из 3).

Ключевое: агент ходит по кругу не от невнимательности — он искренне перестал понимать, в чём проблема. Почти всегда это значит одно: какое-то его убеждение о задаче или коде неверно, а все действия строятся на нём. Это убеждение для него невидимо — он считает его фактом, а не предположением. Твоя задача — найти именно его.

Признак, по которому искать: агент повторяет по сути одно действие с косметическими вариациями.

Рабочая директория проекта: {cwd or "(неизвестна)"}. При необходимости можешь читать файлы проекта — но не меняй ничего.

## Промпт пользователя, на котором сработал триггер (дословно)
{trigger}

## Хвост транскрипта сессии
{tail or "(транскрипт недоступен)"}

## Состояние репозитория
{git_summary(cwd)}

Ответь коротко и конкретно (до 250 слов, без пересказа транскрипта):
1. Что пользователь просил (его словами) и чем он недоволен.
2. НЕВЕРНОЕ УБЕЖДЕНИЕ агента: что он считает фактом, а это не так или не проверено. Если таких несколько — главное.
3. Какое действие это убеждение заставляет его повторять по кругу.
4. Как одним шагом проверить это убеждение: конкретная команда, файл или вопрос пользователю.

Отдельно проверь частый класс «записал ≠ подействовало»: агент создал конфиг, хук, файл инструкций или env-переменную и считает, что они работают, — но система потребляет их из ДРУГОГО пути (например, глобальный AGENTS.md читается из домашней директории harness'а, а не из папки проекта). Сверь реальные пути загрузки, а не предполагаемые."""


def run_auditor(auditor, prompt, cfg):
    """Run the external auditor CLI. Returns (verdict, error). Exactly one is set."""
    custom = str(cfg.get("auditor_command", "")).strip()
    if custom:
        cmd = shlex.split(custom) + [prompt]
    else:
        builder = AUDITOR_CMDS.get(auditor)
        if builder is None:
            return None, f"неизвестный аудитор: {auditor}"
        cmd = builder(prompt)
    try:
        r = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=int(cfg.get("auditor_timeout_sec", 90)),
            # the auditor's own prompt contains the user's verbatim profanity;
            # this flag keeps a globally installed zaebal hook from firing on it
            env={**os.environ, CHILD_ENV_FLAG: "1"},
        )
    except FileNotFoundError:
        return None, f"CLI аудитора «{auditor}» не найден в PATH"
    except subprocess.TimeoutExpired:
        return None, f"аудитор «{auditor}» не ответил за {cfg.get('auditor_timeout_sec', 90)}с"
    except Exception as e:
        return None, f"ошибка запуска аудитора: {e}"
    verdict = (r.stdout or "").strip()
    if r.returncode != 0 and not verdict:
        return None, f"аудитор «{auditor}» завершился с кодом {r.returncode}: {(r.stderr or '').strip()[:300]}"
    if not verdict:
        return None, f"аудитор «{auditor}» вернул пустой ответ"
    return verdict, None


# ------------------------------------------------------------------ modes

def mode_prompt(host, payload):
    """UserPromptSubmit handler."""
    cfg = load_config()
    # fall back to transcript path / cwd so hosts without a session id don't
    # dump every project's streak into one shared "unknown" bucket
    session_id = str(
        payload.get("session_id") or payload.get("sessionID")
        or payload.get("transcript_path") or payload.get("cwd") or "unknown"
    )
    text = extract_text(payload)
    patterns = load_patterns()
    variants = (make_variants(text) if text
                else {k: "" for k in ("ru", "en", "zh", "ru_raw", "en_raw", "zh_raw")})
    kind = classify(variants, patterns) if text else "clean"

    if kind in ("clean", "praise"):
        # incident closes only on explicit acknowledgment (or genuine praise),
        # not on any calm message: "что?" / "покажи ошибку" change nothing
        acked = (kind == "praise"
                 or _ACK.search(variants["ru"]) or _ACK.search(variants["en"]))
        if acked and acknowledge(session_id):
            sys.stdout.write(ACK_NOTICE)
        return 0

    _, level = record_trigger(session_id, weight=weight_for(kind))

    verdict_block = ""
    if level in cfg.get("audit_levels", []):
        auditor = resolve_auditor(host, cfg)
        if auditor:
            verdict, error = run_auditor(
                auditor, build_audit_prompt(payload, level, cfg), cfg
            )
            if verdict:
                verdict_block = (
                    f'\n<zaebal-verdict auditor="{auditor}">\n'
                    f"ЗАКЛЮЧЕНИЕ ВНЕШНЕГО АУДИТОРА. Это ПРИОРИТЕТНАЯ ГИПОТЕЗА, "
                    f"а не истина: проверь её первой тем шагом, который предложил "
                    f"аудитор. Опровержение — только артефактом (файл, прогон "
                    f"теста), не памятью и не мнением.\n\n"
                    f"{verdict}\n</zaebal-verdict>\n"
                )
            else:
                verdict_block = (
                    f'\n<zaebal-verdict auditor="{auditor}">\n'
                    f"Внешний аудитор недоступен ({error}). "
                    f"Выполняй протокол самостоятельно, с двойной самоцензурой.\n"
                    f"</zaebal-verdict>\n"
                )

    protocol = (BASE_DIR / "protocol" / f"L{level}.md").read_text(encoding="utf-8").strip()
    sys.stdout.write(f'<zaebal level="{level}">\n{protocol}\n</zaebal>\n{verdict_block}')
    return 0


def main():
    # anti-recursion: never fire inside the auditor's own subprocess
    if os.environ.get(CHILD_ENV_FLAG):
        return 0

    parser = argparse.ArgumentParser(description="Z.A.E.B.A.L. core")
    parser.add_argument("--host", default="unknown",
                        help="host agent: claude / codex / kimi / opencode")
    args = parser.parse_args()

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        return 0  # fail-open on malformed input

    try:
        return mode_prompt(args.host, payload)
    except Exception:
        return 0  # fail-open


if __name__ == "__main__":
    sys.exit(main())
