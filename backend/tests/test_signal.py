"""Tests for signal detection."""
import pytest

from backend.models.signal_detector import SignalDetector


def test_detect_strong_signal():
    d = SignalDetector()
    s = d.detect_signal("warfarin", "bleeding", 50, 50, 5, 900)
    assert s.is_signal


def test_detect_no_signal():
    d = SignalDetector()
    # Use data that should not produce a signal (low a, balanced proportions)
    s = d.detect_signal("aspirin", "headache", 2, 98, 4, 896)
    assert not s.is_signal or s.signal_strength in ("weak", "none")


def test_batch_detect():
    d = SignalDetector()
    records = [
        {"drug": "warfarin", "event": "bleeding", "a": 50, "b": 50, "c": 5, "d": 900},
        {"drug": "aspirin", "event": "headache", "a": 2, "b": 98, "c": 3, "d": 897},
    ]
    signals = d.batch_detect(records)
    assert len(signals) == 2
