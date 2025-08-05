from trading_bot.coordinator import Coordinator
from trading_bot.pipeline import Pipeline


class DummyAgent:
    def __init__(self, name, message, question=None):
        self.name = name
        self.message = message
        self.question = question
        self.received_history = None

    def respond(self, symbol, history):
        # store history to assert later
        self.received_history = list(history)
        response = {"message": f"{self.message} {symbol}"}
        if self.question:
            response["question"] = self.question
        return response


def test_agents_exchange_messages_and_final_decision_composed():
    analyst = DummyAgent("Analyst", "analysis for", question="need more data?")
    trader = DummyAgent("Trader", "decision for")

    coordinator = Coordinator([analyst, trader])
    pipeline = Pipeline(coordinator)
    result = pipeline.run("TSLA")

    # first agent receives empty history
    assert analyst.received_history == []
    # second agent sees first agent's message
    assert trader.received_history == [
        {"agent": "Analyst", "message": "analysis for TSLA"}
    ]

    assert result["conversation"] == [
        {"agent": "Analyst", "message": "analysis for TSLA"},
        {"agent": "Trader", "message": "decision for TSLA"},
    ]
    assert result["follow_ups"] == [
        {"agent": "Analyst", "question": "need more data?"}
    ]
    assert result["final_decision"] == "decision for TSLA"
