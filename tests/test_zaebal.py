import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

CORE_DIR = Path(__file__).resolve().parent.parent / "core"
sys.path.insert(0, str(CORE_DIR))

import zaebal  # noqa: E402


class TempState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self._old = (zaebal.STATE_DIR, zaebal.STATE_FILE, zaebal.STATE_LOCK, zaebal.CONFIG_USER)
        zaebal.STATE_DIR = Path(self.tmp.name)
        zaebal.STATE_FILE = Path(self.tmp.name) / "state.json"
        zaebal.STATE_LOCK = Path(self.tmp.name) / "state.lock"
        zaebal.CONFIG_USER = Path(self.tmp.name) / "config.json"

    def tearDown(self):
        (zaebal.STATE_DIR, zaebal.STATE_FILE,
         zaebal.STATE_LOCK, zaebal.CONFIG_USER) = self._old


class TestNormalize(unittest.TestCase):
    def test_repeat_collapse(self):
        self.assertIn("бля", zaebal.normalize("бляяяя"))
        self.assertIn("fuck", zaebal.normalize("FUUUUCK"))

    def test_natural_doubles_survive(self):
        self.assertIn("ass", zaebal.normalize("ass"))
        self.assertIn("as", zaebal.normalize("as"))

    def test_punctuation_to_space(self):
        self.assertEqual(zaebal.normalize("привет, мир!"), "привет мир")

    def test_leet_cyrillic(self):
        self.assertIn("заебал", zaebal.normalize("за3бал", zaebal.LEET_RU))
        self.assertIn("fuck", zaebal.normalize("fuck", zaebal.LEET_EN))


class TestDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patterns = zaebal.load_patterns()

    def hit(self, text):
        return zaebal.contains_profanity(zaebal.make_variants(text), self.patterns)

    def test_ru(self):
        self.assertTrue(self.hit("ты меня заебал"))
        self.assertTrue(self.hit("сука долбаеб"))
        self.assertTrue(self.hit("бляяяять"))
        self.assertTrue(self.hit("з*а*е*б*а*л"))
        self.assertTrue(self.hit("охуеть"))
        self.assertTrue(self.hit("за3бал"))
        self.assertTrue(self.hit("заёб"))

    def test_en(self):
        self.assertTrue(self.hit("this is fucking broken"))
        self.assertTrue(self.hit("f.u.c.k"))
        self.assertTrue(self.hit("you piece of shit"))
        self.assertTrue(self.hit("wtf"))

    def test_zh(self):
        self.assertTrue(self.hit("我操 又坏了"))
        self.assertTrue(self.hit("这是什么傻逼代码"))

    def test_false_positives(self):
        self.assertFalse(self.hit("scunthorpe is a town"))
        self.assertFalse(self.hit("скипидар и растворители"))
        self.assertFalse(self.hit("use the assistant to help"))
        self.assertFalse(self.hit("as you can see"))
        self.assertFalse(self.hit("Fukushima data parser"))
        self.assertFalse(self.hit("ебраил прислал патч"))
        self.assertFalse(self.hit("操作数据库"))
        self.assertFalse(self.hit("我操作系统有问题"))
        self.assertFalse(self.hit("我草图还没画完"))
        self.assertFalse(self.hit("垃圾回收机制"))
        self.assertFalse(self.hit("滚动到顶部"))
        # junk-tolerant roots must not glue SEPARATE words across a space
        # (normalization turns punctuation into spaces; a space is a word
        # boundary, junk is not)
        self.assertFalse(self.hit("поговорим о хуках"))
        self.assertFalse(self.hit("статья о художнике"))
        self.assertFalse(self.hit("отчет о худших кейсах"))
        self.assertFalse(self.hit("вопрос о хуках"))

    def test_junk_inside_one_word_still_matches(self):
        self.assertTrue(self.hit("з*а*е*б*а*л"))
        self.assertTrue(self.hit("за-е-бал"))
        self.assertTrue(self.hit("f.u.c.k"))

    def test_clean_text(self):
        self.assertFalse(self.hit("спасибо, всё работает"))
        self.assertFalse(self.hit("please add tests for this function"))


class TestClassify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patterns = zaebal.load_patterns()

    def kind(self, text):
        return zaebal.classify(zaebal.make_variants(text), self.patterns)

    def test_praise_is_not_a_trigger(self):
        self.assertEqual(self.kind("заебись, работает!"), "praise")
        self.assertEqual(self.kind("охуенно получилось, спасибо"), "praise")
        self.assertEqual(self.kind("this is fucking great"), "praise")
        self.assertEqual(self.kind("пиздато вышло, красавчик"), "praise")

    def test_directed_beats_praise_words(self):
        # regression: complaints containing praise-like words must NOT be
        # silenced (SOL/Opus blocker)
        self.assertEqual(self.kind("ничего не работает, ты меня заебал"), "directed")
        self.assertEqual(self.kind("спасибо, но ты опять всё сломал, заебал"), "directed")
        self.assertEqual(self.kind("сначала было отлично, но теперь ты всё сломал, сука"), "directed")
        self.assertEqual(self.kind("nothing works, fuck you"), "directed")
        self.assertEqual(self.kind("nice try, but you fucked it up again"), "directed")
        self.assertEqual(self.kind("ты заебал, ничего не работает"), "directed")
        self.assertEqual(self.kind("ты долбоеб, спасибо что сломал прод"), "directed")

    def test_directed_addressee_forms(self):
        self.assertEqual(self.kind("ты меня заебал"), "directed")
        self.assertEqual(self.kind("тебя вообще не просили, заебал"), "directed")
        self.assertEqual(self.kind("вы опять всё сломали, сука"), "directed")
        self.assertEqual(self.kind("Codex, какого хуя это опять сломано"), "directed")
        self.assertEqual(self.kind("you broke it again, fuck"), "directed")

    def test_ambiguous(self):
        self.assertEqual(self.kind("опять npm заебал"), "ambiguous")
        self.assertEqual(self.kind("блядь, опять не то"), "ambiguous")
        self.assertEqual(self.kind("это полное говно, переделывай"), "ambiguous")
        self.assertEqual(self.kind("fucking broken, still doesn't work"), "ambiguous")

    def test_clean(self):
        self.assertEqual(self.kind("добавь тесты"), "clean")


class TestEscalation(TempState):
    def test_levels(self):
        now = time.time()
        self.assertEqual(zaebal.record_trigger("s", now), (1.0, 1))
        self.assertEqual(zaebal.record_trigger("s", now + 1), (2.0, 2))
        self.assertEqual(zaebal.record_trigger("s", now + 2), (3.0, 2))
        self.assertEqual(zaebal.record_trigger("s", now + 3), (4.0, 3))

    def test_ambiguous_half_weight(self):
        now = time.time()
        self.assertEqual(zaebal.record_trigger("s", now, weight=0.5), (0.5, 1))
        self.assertEqual(zaebal.record_trigger("s", now + 1, weight=0.5), (1.0, 1))
        self.assertEqual(zaebal.record_trigger("s", now + 2, weight=0.5), (1.5, 1))
        self.assertEqual(zaebal.record_trigger("s", now + 3, weight=0.5), (2.0, 2))

    def test_decay(self):
        old = time.time() - zaebal.WINDOW_SECONDS - 10
        zaebal.record_trigger("s", old)
        self.assertEqual(zaebal.record_trigger("s"), (1.0, 1))

    def test_sessions_isolated(self):
        zaebal.record_trigger("a")
        self.assertEqual(zaebal.record_trigger("b"), (1.0, 1))

    def test_legacy_state_migration(self):
        zaebal.STATE_FILE.write_text(json.dumps({"s": [time.time() - 5]}))
        total, level = zaebal.record_trigger("s")
        self.assertEqual((total, level), (2.0, 2))

    def test_concurrent_writes_keep_all_triggers(self):
        from concurrent.futures import ThreadPoolExecutor
        now = time.time()
        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(lambda i: zaebal.record_trigger("s", now + i * 0.001), range(50)))
        state = json.loads(zaebal.STATE_FILE.read_text())
        self.assertEqual(len(state["s"]["stamps"]), 50)


class TestAcknowledge(TempState):
    def test_ack_resets_streak(self):
        for _ in range(4):
            zaebal.record_trigger("s")
        self.assertTrue(zaebal.acknowledge("s"))
        self.assertEqual(zaebal.record_trigger("s"), (1.0, 1))  # not instant L3

    def test_ack_resets_streak_at_low_levels(self):
        zaebal.record_trigger("s")
        zaebal.record_trigger("s")
        self.assertTrue(zaebal.acknowledge("s"))
        self.assertEqual(zaebal.record_trigger("s"), (1.0, 1))

    def test_ack_noop(self):
        self.assertFalse(zaebal.acknowledge("s"))


class TestTranscriptTail(unittest.TestCase):
    def test_non_dict_jsonl_lines_do_not_crash(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write("[]\n")
            f.write(json.dumps({"role": "user", "content": "сделай фичу"}) + "\n")
            f.write('"just a string"\n')
            tp = f.name
        tail = zaebal.transcript_tail(tp, 12000)
        self.assertIn("сделай фичу", tail)
        os.unlink(tp)


class TestAuditor(TempState):
    def test_resolve_same_vendor(self):
        cfg = zaebal.load_config()
        self.assertEqual(zaebal.resolve_auditor("kimi", cfg), "kimi")
        self.assertEqual(zaebal.resolve_auditor("claude", cfg), "claude")

    def test_resolve_explicit_and_none(self):
        zaebal.CONFIG_USER.write_text(json.dumps({"auditor": "claude"}))
        cfg = zaebal.load_config()
        self.assertEqual(zaebal.resolve_auditor("kimi", cfg), "claude")
        zaebal.CONFIG_USER.write_text(json.dumps({"auditor": "none"}))
        self.assertIsNone(zaebal.resolve_auditor("kimi", zaebal.load_config()))

    def test_build_prompt_includes_trigger_and_transcript(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"role": "user", "content": "сделай фичу"}) + "\n")
            tp = f.name
        payload = {"cwd": "/nonexistent", "prompt": "ты заебал", "transcript_path": tp}
        prompt = zaebal.build_audit_prompt(payload, 3, zaebal.load_config())
        self.assertIn("ты заебал", prompt)
        self.assertIn("сделай фичу", prompt)
        os.unlink(tp)

    def test_run_auditor_missing_cli(self):
        with mock.patch.dict(zaebal.AUDITOR_CMDS, {"kimi": lambda p: ["definitely-not-a-real-cli-xyz", p]}):
            verdict, error = zaebal.run_auditor("kimi", "prompt", zaebal.load_config())
        self.assertIsNone(verdict)
        self.assertIn("не найден", error)

    def test_run_auditor_success(self):
        fake = lambda p: [sys.executable, "-c", "print('диагноз: всё сломано')"]
        with mock.patch.dict(zaebal.AUDITOR_CMDS, {"kimi": fake}):
            verdict, error = zaebal.run_auditor("kimi", "prompt", zaebal.load_config())
        self.assertEqual(verdict, "диагноз: всё сломано")
        self.assertIsNone(error)

    def test_auditor_subprocess_gets_antirecursion_flag(self):
        captured = []

        def fake_run(cmd, **kwargs):
            captured.append(kwargs.get("env", {}))
            class R:
                returncode = 0
                stdout = "ok"
                stderr = ""
            return R()

        with mock.patch.object(zaebal.subprocess, "run", fake_run):
            zaebal.run_auditor("kimi", "prompt", zaebal.load_config())
        self.assertEqual(captured[0].get(zaebal.CHILD_ENV_FLAG), "1")

    def test_auditor_cmds_are_sandboxed_where_possible(self):
        self.assertIn("read-only", zaebal.AUDITOR_CMDS["codex"]("p"))
        self.assertIn("--allowedTools", zaebal.AUDITOR_CMDS["claude"]("p"))


class TestEndToEnd(TempState):
    def run_core(self, payload, *argv, extra_env=None):
        env = dict(os.environ, ZAEBAL_STATE_DIR=zaebal.STATE_DIR)
        env.update(extra_env or {})
        return subprocess.run(
            [sys.executable, str(CORE_DIR / "zaebal.py"), *argv],
            input=json.dumps(payload),
            capture_output=True, text=True, env=env, timeout=20,
        )

    def set_config(self, **cfg):
        Path(zaebal.STATE_DIR, "config.json").write_text(json.dumps(cfg))

    def _prompt(self, sid, text):
        r = self.run_core({"session_id": sid, "prompt": text}, "--host", "kimi")
        assert r.returncode == 0, r.stderr
        return r.stdout

    def test_l1_protocol_injected(self):
        out = self._prompt("t1", "ты меня заебал")
        self.assertIn('<zaebal level="1">', out)
        self.assertIn("СТОП", out)

    def test_directed_complaint_with_praise_words_fires(self):
        out = self._prompt("t1b", "ничего не работает, ты меня заебал")
        self.assertIn('<zaebal level="1">', out)

    def test_antirecursion_env_flag_silences_core(self):
        r = self.run_core(
            {"session_id": "t", "prompt": "ты меня заебал"}, "--host", "kimi",
            extra_env={zaebal.CHILD_ENV_FLAG: "1"},
        )
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_praise_silences_core(self):
        self.assertEqual(self._prompt("tp", "заебись, работает!"), "")
        self.assertEqual(self._prompt("tp", "this is fucking great"), "")

    def test_ambiguous_builds_half_weight_streak(self):
        self.assertIn('<zaebal level="1">', self._prompt("ta", "опять npm заебал"))
        self.assertIn('<zaebal level="1">', self._prompt("ta", "опять docker заебал"))
        self.assertIn('<zaebal level="1">', self._prompt("ta", "блядь, опять не то"))
        out = self._prompt("ta", "да блять сколько можно")  # weight 2.0 -> L2
        self.assertIn('<zaebal level="2">', out)

    def test_l2_no_auditor_by_default(self):
        self.set_config(auditor_command="no-such-cli-xyz")
        self._prompt("t2", "ты заебал")
        out = self._prompt("t2", "ты опять заебал")
        self.assertIn('<zaebal level="2">', out)
        self.assertNotIn("<zaebal-verdict auditor=", out)

    def test_l3_auditor_verdict_injected(self):
        self.set_config(auditor_command=f'{sys.executable} -c "print(\'вердикт аудитора\')"')
        for i in range(3):
            self._prompt("t3", f"ты заебал {i}")
        out = self._prompt("t3", "ты заебал совсем")
        self.assertIn('<zaebal level="3">', out)
        self.assertIn('<zaebal-verdict auditor="kimi">', out)
        self.assertIn("вердикт аудитора", out)
        self.assertIn("ПРИОРИТЕТНАЯ ГИПОТЕЗА", out)

    def test_l3_auditor_failure_is_failopen(self):
        self.set_config(auditor_command="no-such-cli-xyz")
        for i in range(4):
            out = self._prompt("t4", f"ты заебал {i}")
        self.assertIn('<zaebal level="3">', out)
        self.assertIn("аудитор недоступен", out.lower())

    def test_l3_ack_lifecycle(self):
        self.set_config(auditor_command="no-such-cli-xyz")
        for i in range(4):
            out = self._prompt("t5", f"ты заебал {i}")
        self.assertIn('<zaebal level="3">', out)
        # calm message WITHOUT acknowledgment: streak persists
        self._prompt("t5", "покажи ошибку")
        out = self._prompt("t5", "ты заебал опять")
        self.assertIn('<zaebal level="3">', out)
        # explicit acknowledgment resets the streak and notifies
        out = self._prompt("t5", "хорошо, давай по плану")
        self.assertIn("Стрик обнулён", out)
        # next profanity is L1, not instant L3
        out = self._prompt("t5", "ты опять заебал")
        self.assertIn('<zaebal level="1">', out)

    def test_calm_message_does_not_reset_streak(self):
        self._prompt("t6", "ты заебал")
        self._prompt("t6", "покажи что сломано")   # no ack -> streak persists
        out = self._prompt("t6", "ты опять заебал")
        self.assertIn('<zaebal level="2">', out)

    def test_ack_resets_streak(self):
        self._prompt("t7", "ты заебал")
        self._prompt("t7", "ладно, продолжай")     # ack -> reset
        out = self._prompt("t7", "ты опять заебал")
        self.assertIn('<zaebal level="1">', out)

    def test_session_fallback_separates_projects(self):
        # no session_id: streaks must not share one "unknown" bucket
        out = self.run_core({"prompt": "ты заебал", "cwd": "/proj/a"},
                            "--host", "kimi").stdout
        self.assertIn('<zaebal level="1">', out)
        out = self.run_core({"prompt": "ты заебал", "cwd": "/proj/b"},
                            "--host", "kimi").stdout
        self.assertIn('<zaebal level="1">', out)  # not L2 from /proj/a's streak
        out = self.run_core({"prompt": "ты заебал", "cwd": "/proj/a"},
                            "--host", "kimi").stdout
        self.assertIn('<zaebal level="2">', out)

    def test_silence_and_failopen(self):
        self.assertEqual(self._prompt("t8", "сегодня хорошая погода"), "")
        env = dict(os.environ, ZAEBAL_STATE_DIR=zaebal.STATE_DIR)
        r = subprocess.run(
            [sys.executable, str(CORE_DIR / "zaebal.py")],
            input="{not json", capture_output=True, text=True, env=env, timeout=15,
        )
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
