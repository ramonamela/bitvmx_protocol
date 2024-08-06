from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from bitvmx_protocol_library.transaction_generation.entities.dtos.bitvmx_verifier_signatures_dto import (
    BitVMXVerifierSignaturesDTO,
)
from bitvmx_protocol_library.transaction_generation.enums import TransactionProverStepType


class BitVMXProtocolProverDTO(BaseModel):
    prover_public_key: str
    verifier_public_keys: Dict[str, str]
    prover_signatures_dto: BitVMXVerifierSignaturesDTO
    verifier_signatures_dtos: Dict[str, BitVMXVerifierSignaturesDTO]
    last_confirmed_step: Optional[TransactionProverStepType] = None
    last_confirmed_step_tx_id: Optional[str] = None
    search_choices: List[int] = Field(default_factory=list)
    published_hashes_dict: Dict[int, str] = Field(default_factory=dict)

    @property
    def hash_result_signatures(self):
        hash_result_signatures_list = []
        for elem in reversed(sorted(self.verifier_public_keys.keys())):
            hash_result_signatures_list.append(
                self.verifier_signatures_dtos[elem].hash_result_signature
            )
        hash_result_signatures_list.append(self.prover_signatures_dto.hash_result_signature)
        return hash_result_signatures_list

    @property
    def search_hash_signatures(self):
        search_hash_signatures_list = []
        amount_of_iterations = len(
            list(self.verifier_signatures_dtos.values())[0].search_hash_signatures
        )
        for i in range(amount_of_iterations):
            current_signatures_list = []
            for elem in reversed(sorted(self.verifier_public_keys.keys())):
                current_signatures_list.append(
                    self.verifier_signatures_dtos[elem].search_hash_signatures[i]
                )
            current_signatures_list.append(self.prover_signatures_dto.search_hash_signatures[i])
            search_hash_signatures_list.append(current_signatures_list)
        return search_hash_signatures_list

    @property
    def trace_signatures(self):
        trace_signatures_list = []
        for elem in reversed(sorted(self.verifier_public_keys.keys())):
            trace_signatures_list.append(self.verifier_signatures_dtos[elem].trace_signature)
        trace_signatures_list.append(self.prover_signatures_dto.trace_signature)
        return trace_signatures_list
