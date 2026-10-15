import unittest

from heart.intent_engine import HeartIntentEngine


class HeartIntentEngineTests(unittest.TestCase):
    def test_rule_matcher_maps_status_questions(self) -> None:
        engine = HeartIntentEngine()
        intent = engine.interpret("Heart, como está a máquina?")
        self.assertEqual(intent["tool"], "system_status")

    def test_semantic_matcher_maps_natural_language(self) -> None:
        engine = HeartIntentEngine()
        intent = engine.interpret("tá tudo certo na máquina?")
        self.assertEqual(intent["tool"], "system_status")

    def test_llm_resolver_maps_monitor_requests(self) -> None:
        engine = HeartIntentEngine()
        intent = engine.interpret("verifica aquele monitor do sentinel")
        self.assertEqual(intent["tool"], "run_script")

    def test_execution_formats_system_status(self) -> None:
        engine = HeartIntentEngine()
        response = engine.execute({"type": "tool_call", "tool": "system_status", "arguments": {}})
        self.assertEqual(response["type"], "response")
        self.assertIn("CPU em", response["content"])
        self.assertIn("context_summary", response)
        self.assertEqual(response["tool_call"]["tool"], "system_status")

    def test_context_tracks_last_tool_and_intent(self) -> None:
        engine = HeartIntentEngine()
        engine.interpret("como está a máquina?")
        self.assertEqual(engine.context.last_tool, None)
        engine.execute({"type": "tool_call", "tool": "system_status", "arguments": {}})
        self.assertEqual(engine.context.last_tool, "system_status")
        self.assertIn("last_intent", engine.context.summary())

    def test_error_response_includes_context_summary(self) -> None:
        engine = HeartIntentEngine()
        response = engine.execute({"type": "tool_call", "tool": "missing_tool", "arguments": {}})
        self.assertEqual(response["type"], "error")
        self.assertIn("context_summary", response)
        self.assertIn("missing_tool", response["tool_call"]["tool"])


if __name__ == "__main__":
    unittest.main()
