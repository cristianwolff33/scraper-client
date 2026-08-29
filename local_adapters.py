from __future__ import annotations


LOCAL_ADAPTER_REGISTRY: dict[str, str] = {}
LOCAL_TRANSFORMER_REGISTRY: dict[str, str] = {}

# Some framework builds read the non-prefixed names directly.
ADAPTER_REGISTRY = LOCAL_ADAPTER_REGISTRY
TRANSFORMER_REGISTRY = LOCAL_TRANSFORMER_REGISTRY
