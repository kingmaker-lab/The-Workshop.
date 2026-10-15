import unittest

from heart.intents import IntentEngine, ToolCallIntent, create_tool_call_intent, parse_intent


class IntentProtocolTests(unittest.TestCase):
    def test_tool_call_intent_round_trips(self) -> None:
        intent = ToolCallIntent(tool="system_status", arguments={})
        payload = intent.to_dict()
        restored = parse_intent(payload)
        self.assertEqual(restored.type, "tool_call")
        self.assertEqual(restored.tool, "system_status")
        self.assertEqual(restored.arguments, {})

    def test_user_question_maps_to_system_status(self) -> None:
        engine = IntentEngine()
        request = engine.from_text("Heart, como está a máquina?")
        self.assertEqual(request["type"], "tool_call")
        self.assertEqual(request["tool"], "system_status")

    def test_engine_processes_tool_request(self) -> None:
        engine = IntentEngine()
        response = engine.handle({"type": "tool_call", "tool": "system_status", "arguments": {}})
        self.assertEqual(response["type"], "response")
        self.assertIn("cpu_percent_estimate", response["content"])

    def test_invalid_payload_returns_error(self) -> None:
        engine = IntentEngine()
        response = engine.handle({"type": "tool_call", "arguments": {}})
        self.assertEqual(response["type"], "error")
        self.assertIn("tool", response["message"])


if __name__ == "__main__":
    unittest.main()
