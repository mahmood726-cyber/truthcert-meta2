"""Question Contract: estimand lock for reproducibility.

Every topic carries a contract that specifies exactly what is being estimated.
The contract_hash is included in every node capsule and manifest.
"""

import hashlib
import json
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QuestionContract(BaseModel):
    """Immutable specification of the analytic question."""
    population: str
    intervention_classes: List[str]
    comparator: str
    endpoints: List[str]
    effect_measure: str = "logRR"
    missingness_policy: str = "denominator_delta"
    decision_utility: str = "conservative"
    mapping_confidence_rules: Dict[str, str] = Field(default_factory=dict)

    def contract_hash(self) -> str:
        """Deterministic SHA-256 of the contract for provenance."""
        payload = json.dumps(self.model_dump(), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
