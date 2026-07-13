import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.simulation_service import (  # noqa: E402
    cancel_pending_order,
    calculate_default_fee,
    get_account_snapshot,
    get_market_status,
    get_pending_orders,
    get_trades,
    init_db,
    place_order,
    reset_account,
)


class SimulationServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "simulation_test.db"
        init_db(self.db_path)
        reset_account(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_buy_reduces_cash_and_creates_position(self):
        snapshot = place_order("buy", "AAPL", 10, price=100, fee=1, db_path=self.db_path, refresh_prices=False)

        account = snapshot["account"]
        position = snapshot["positions"][0]
        self.assertEqual(account["cash"], 98999.0)
        self.assertEqual(position["symbol"], "AAPL")
        self.assertEqual(position["quantity"], 10.0)
        self.assertEqual(position["averageCost"], 100.1)

    def test_weighted_average_cost_on_multiple_buys(self):
        place_order("buy", "AAPL", 10, price=100, fee=0, db_path=self.db_path, refresh_prices=False)
        snapshot = place_order("buy", "AAPL", 10, price=120, fee=0, db_path=self.db_path, refresh_prices=False)

        position = snapshot["positions"][0]
        self.assertEqual(position["quantity"], 20.0)
        self.assertEqual(position["averageCost"], 110.0)

    def test_sell_increases_cash_and_realizes_pnl(self):
        place_order("buy", "AAPL", 10, price=100, fee=0, db_path=self.db_path, refresh_prices=False)
        snapshot = place_order("sell", "AAPL", 4, price=120, fee=1, db_path=self.db_path, refresh_prices=False)

        account = snapshot["account"]
        position = snapshot["positions"][0]
        self.assertEqual(account["cash"], 99479.0)
        self.assertEqual(account["realizedPnl"], 79.0)
        self.assertEqual(position["quantity"], 6.0)

    def test_buy_rejects_insufficient_cash(self):
        with self.assertRaises(ValueError):
            place_order("buy", "AAPL", 2000, price=100, fee=1, db_path=self.db_path, refresh_prices=False)

    def test_sell_rejects_insufficient_holdings(self):
        place_order("buy", "AAPL", 1, price=100, db_path=self.db_path, refresh_prices=False)
        with self.assertRaises(ValueError):
            place_order("sell", "AAPL", 2, price=100, db_path=self.db_path, refresh_prices=False)

    def test_trades_are_persisted(self):
        place_order("buy", "AAPL", 1, price=100, db_path=self.db_path, refresh_prices=False)
        trades = get_trades(db_path=self.db_path)

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["symbol"], "AAPL")
        self.assertEqual(trades[0]["side"], "buy")

    # ── New tests for upgraded simulation engine ──────────────────

    def test_limit_order_goes_pending(self):
        """Limit buy at $150 (above market) should go pending, not execute immediately."""
        place_order("buy", "AAPL", 10, price=100, limit_price=150, order_type="limit",
                    db_path=self.db_path, refresh_prices=False)
        pending = get_pending_orders(db_path=self.db_path)

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["symbol"], "AAPL")
        self.assertEqual(pending[0]["order_type"], "limit")
        self.assertEqual(pending[0]["status"], "pending")

        # Cash should NOT be deducted
        account = get_account_snapshot(db_path=self.db_path, refresh_prices=False)["account"]
        self.assertEqual(account["cash"], 100000.0)

    def test_limit_order_lifecycle(self):
        """Limit buy order: created as pending, then fills on snapshot with live prices."""
        place_order("buy", "AAPL", 10, price=100, limit_price=150, order_type="limit",
                    db_path=self.db_path, refresh_prices=False)
        # Should go to pending queue (not execute immediately)
        pending = get_pending_orders(db_path=self.db_path)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["symbol"], "AAPL")
        self.assertEqual(pending[0]["order_type"], "limit")
        self.assertEqual(pending[0]["status"], "pending")
        # Positions should be empty (order not yet executed)
        snapshot = get_account_snapshot(db_path=self.db_path, refresh_prices=False)
        self.assertEqual(len(snapshot["positions"]), 0)

    def test_cancel_pending_order(self):
        place_order("buy", "AAPL", 5, price=100, limit_price=150, order_type="limit",
                    db_path=self.db_path, refresh_prices=False)
        pending = get_pending_orders(db_path=self.db_path)
        self.assertEqual(len(pending), 1)

        result = cancel_pending_order(pending[0]["id"], db_path=self.db_path)
        self.assertEqual(result["status"], "cancelled")

        pending = get_pending_orders(db_path=self.db_path)
        self.assertEqual(len(pending), 0)

    def test_default_fee_calculation(self):
        fee = calculate_default_fee(10, 100)
        self.assertGreater(fee, 0)
        self.assertAlmostEqual(fee, 10 * 100 * 0.0000278, places=4)

    def test_auto_fee_applied_when_not_provided(self):
        """Market order without explicit fee should auto-calculate fee."""
        snapshot = place_order("buy", "AAPL", 1, price=100, db_path=self.db_path, refresh_prices=False)
        # Cash reduction should include auto fee: 100000 - 100 - ~0.03
        self.assertLess(snapshot["account"]["cash"], 99900.0)

    def test_market_status_returns_valid_dict(self):
        status = get_market_status()
        self.assertIn("isOpen", status)
        self.assertIn("status", status)
        self.assertIn("label", status)
        self.assertIn(status["status"], ("open", "pre_market", "after_hours", "closed"))

    def test_stop_order_goes_pending(self):
        """Stop buy at $80 (below market price of $100) should go pending."""
        place_order("buy", "AAPL", 10, price=100, stop_price=80, order_type="stop",
                    db_path=self.db_path, refresh_prices=False)
        pending = get_pending_orders(db_path=self.db_path)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["order_type"], "stop")

    def test_market_order_still_works_with_new_signature(self):
        """Existing callers using only (side, symbol, quantity, price, fee) should still work."""
        snapshot = place_order("buy", "AAPL", 10, price=100, fee=1, db_path=self.db_path, refresh_prices=False)
        self.assertEqual(snapshot["positions"][0]["symbol"], "AAPL")
        self.assertEqual(snapshot["positions"][0]["quantity"], 10.0)

    def test_reset_clears_pending_orders(self):
        place_order("buy", "AAPL", 5, price=100, limit_price=150, order_type="limit",
                    db_path=self.db_path, refresh_prices=False)
        self.assertEqual(len(get_pending_orders(db_path=self.db_path)), 1)
        reset_account(self.db_path)
        self.assertEqual(len(get_pending_orders(db_path=self.db_path)), 0)


if __name__ == "__main__":
    unittest.main()

