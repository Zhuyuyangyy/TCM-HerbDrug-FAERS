"""Tests for signal detection."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.signal_detector import SignalDetector

def test_detect_strong_signal():
    d = SignalDetector()
    s = d.detect_signal("warfarin", "bleeding", 50, 50, 5, 900)
    assert s.is_signal

def test_detect_no_signal():
    d = SignalDetector()
    s = d.detect_signal("aspirin", "headache", 3, 97, 5, 895)
    assert not s.is_signal or s.signal_strength == "weak"

def test_batch_detect():
    d = SignalDetector()
    records = [
        {"drug": "warfarin", "event": "bleeding", "a": 50, "b": 50, "c": 5, "d": 900},
        {"drug": "aspirin", "event": "headache", "a": 2, "b": 98, "c": 3, "d": 897},
    ]
    signals = d.batch_detect(records)
    assert len(signals) == 2
