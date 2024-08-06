from bitvmx_protocol_library.bitvmx_execution.entities.execution_trace_dto import ExecutionTraceDTO
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_properties_dto import (
    BitVMXProtocolPropertiesDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_setup_properties_dto import (
    BitVMXProtocolSetupPropertiesDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_verifier_dto import (
    BitVMXProtocolVerifierDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_prover_winternitz_public_keys_dto import (
    BitVMXProverWinternitzPublicKeysDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_verifier_winternitz_public_keys_dto import (
    BitVMXVerifierWinternitzPublicKeysDTO,
)
from bitvmx_protocol_library.transaction_generation.entities.dtos.bitvmx_transactions_dto import (
    BitVMXTransactionsDTO,
)
from bitvmx_protocol_library.transaction_generation.services.verifier_challenge_detection.verifier_execution_challenge_detection_service import (
    VerifierExecutionChallengeDetectionService,
)
from bitvmx_protocol_library.transaction_generation.services.verifier_challenge_detection.verifier_wrong_hash_challenge_detection_service import (
    VerifierWrongHashChallengeDetectionService,
)
from blockchain_query_services.services.blockchain_query_services_dependency_injection import (
    transaction_info_service,
)


class VerifierChallengeDetectionService:
    def __init__(self):
        self.verifier_challenge_detection_services = [
            VerifierWrongHashChallengeDetectionService(),
            VerifierExecutionChallengeDetectionService(),
        ]

    def __call__(
        self,
        protocol_dict,
        bitvmx_transactions_dto: BitVMXTransactionsDTO,
        bitvmx_protocol_properties_dto: BitVMXProtocolPropertiesDTO,
        bitvmx_protocol_setup_properties_dto: BitVMXProtocolSetupPropertiesDTO,
        bitvmx_prover_winternitz_public_keys_dto: BitVMXProverWinternitzPublicKeysDTO,
        bitvmx_verifier_winternitz_public_keys_dto: BitVMXVerifierWinternitzPublicKeysDTO,
        bitvmx_protocol_verifier_dto: BitVMXProtocolVerifierDTO,
    ):
        trace_tx_id = bitvmx_transactions_dto.trace_tx.get_txid()
        trace_transaction_info = transaction_info_service(trace_tx_id)
        previous_trace_witness = trace_transaction_info.inputs[0].witness

        # Ugly hardcoding here that should be computed somehow but it depends a lot on the structure of the
        # previous script
        # -> Make static call that gets checked when the script gets generated
        prover_trace_witness = previous_trace_witness[10:246]
        protocol_dict["prover_trace_witness"] = prover_trace_witness

        trace_words_lengths = bitvmx_protocol_properties_dto.trace_words_lengths[::-1]

        consumed_items = 0
        trace_values = []
        for i in range(len(bitvmx_verifier_winternitz_public_keys_dto.trace_verifier_public_keys)):
            current_public_keys = (
                bitvmx_verifier_winternitz_public_keys_dto.trace_verifier_public_keys[i]
            )
            current_length = trace_words_lengths[i]
            current_witness = prover_trace_witness[
                len(prover_trace_witness)
                - (len(current_public_keys) * 2 + consumed_items) : len(prover_trace_witness)
                - consumed_items
            ]
            consumed_items += len(current_public_keys) * 2
            current_witness_values = current_witness[1 : 2 * current_length : 2]
            current_digits = list(
                map(lambda elem: elem[1] if len(elem) > 0 else "0", current_witness_values)
            )
            current_value = "".join(reversed(current_digits))
            trace_values.append(current_value)

        execution_trace = ExecutionTraceDTO.from_trace_values_list(trace_values)
        protocol_dict["published_execution_trace"] = execution_trace

        first_wrong_step = int(
            "".join(
                map(
                    lambda digit: bin(digit)[2:].zfill(
                        bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                    ),
                    protocol_dict["search_choices"],
                )
            ),
            2,
        )
        protocol_dict["first_wrong_step"] = first_wrong_step

        for verifier_challenge_detection_service in self.verifier_challenge_detection_services:
            trigger_challenge_transaction_service, transaction_step_type = (
                verifier_challenge_detection_service(
                    protocol_dict,
                    setup_uuid=bitvmx_protocol_setup_properties_dto.setup_uuid,
                )
            )
            if (
                trigger_challenge_transaction_service is not None
                and transaction_step_type is not None
            ):
                return trigger_challenge_transaction_service, transaction_step_type

        raise Exception("No challenge detected")