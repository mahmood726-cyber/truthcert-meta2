"""Deterministic seeding using hash-based approach + PCG64."""

import hashlib

import numpy as np
from numpy.random import Generator, PCG64


def hash32(a: int, b) -> int:
    """Produce a deterministic 32-bit seed from two values."""
    data = f"{a}:{b}".encode("utf-8")
    h = hashlib.sha256(data).digest()
    return int.from_bytes(h[:4], "big")


def make_rng(seed_master: int, topic_id: str, rep_index: int) -> Generator:
    """Create a deterministic RNG for a specific topic and replication."""
    seed_topic = hash32(seed_master, topic_id)
    seed_rep = hash32(seed_topic, rep_index)
    return Generator(PCG64(seed_rep))
