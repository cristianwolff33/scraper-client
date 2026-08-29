from __future__ import annotations


LOCAL_ADAPTER_REGISTRY: dict[str, str] = {
    "polskieflagi": "adapters.polskieflagi.adapter.PolskieFlagiAdapter",
}

LOCAL_TRANSFORMER_REGISTRY: dict[str, str] = {
    "polskieflagi": "adapters.polskieflagi.transformer.PolskieFlagiTransformer",
}

# Some framework builds read the non-prefixed names directly.
ADAPTER_REGISTRY = LOCAL_ADAPTER_REGISTRY
TRANSFORMER_REGISTRY = LOCAL_TRANSFORMER_REGISTRY
