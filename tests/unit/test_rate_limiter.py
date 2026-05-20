"""Tests for RateLimiter — send_keys must be >= 2.5s apart (D18)."""

from __future__ import annotations

import asyncio
import time

from bonsai.runners.tmux_rpc import RateLimiter


class TestRateLimiter:
    async def test_first_call_is_immediate(self):
        rl = RateLimiter(min_interval=0.05)
        start = time.monotonic()
        await rl.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    async def test_second_call_waits(self):
        rl = RateLimiter(min_interval=0.1)
        await rl.acquire()
        start = time.monotonic()
        await rl.acquire()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.08

    async def test_calls_after_gap_are_immediate(self):
        rl = RateLimiter(min_interval=0.05)
        await rl.acquire()
        await asyncio.sleep(0.1)
        start = time.monotonic()
        await rl.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05

    async def test_default_interval_is_2_5_seconds(self):
        rl = RateLimiter()
        assert rl.min_interval == 2.5

    async def test_multiple_sequential_calls_all_spaced(self):
        rl = RateLimiter(min_interval=0.05)
        timestamps = []
        for _ in range(3):
            await rl.acquire()
            timestamps.append(time.monotonic())
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        for gap in gaps:
            assert gap >= 0.04
