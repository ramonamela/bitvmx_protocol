from bitcoinutils.transactions import TxWitnessInput
from bitcoinutils.utils import ControlBlock

from bitvmx_protocol_library.bitvmx_execution.services.execution_trace_query_service import (
    ExecutionTraceQueryService,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_setup_properties_dto import (
    BitVMXProtocolSetupPropertiesDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_verifier_dto import (
    BitVMXProtocolVerifierDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_verifier_private_dto import (
    BitVMXProtocolVerifierPrivateDTO,
)
from bitvmx_protocol_library.script_generation.services.bitvmx_bitcoin_scripts_generator_service import (
    BitVMXBitcoinScriptsGeneratorService,
)
from bitvmx_protocol_library.script_generation.services.script_generation.verifier.commit_search_choice_script_generator_service import (
    CommitSearchChoiceScriptGeneratorService,
)
from bitvmx_protocol_library.winternitz_keys_handling.services.generate_witness_from_input_single_word_service import (
    GenerateWitnessFromInputSingleWordService,
)
from blockchain_query_services.services.blockchain_query_services_dependency_injection import (
    broadcast_transaction_service,
    transaction_info_service,
)


class PublishChoiceReadSearchTransactionService:

    def __init__(self, verifier_private_key):
        self.commit_search_choice_script_generator_service = (
            CommitSearchChoiceScriptGeneratorService()
        )
        self.generate_verifier_witness_from_input_single_word_service = (
            GenerateWitnessFromInputSingleWordService(verifier_private_key)
        )
        self.execution_trace_query_service = ExecutionTraceQueryService("verifier_files/")
        self.bitvmx_bitcoin_scripts_generator_service = BitVMXBitcoinScriptsGeneratorService()

    def __call__(
        self,
        bitvmx_protocol_setup_properties_dto: BitVMXProtocolSetupPropertiesDTO,
        bitvmx_protocol_verifier_private_dto: BitVMXProtocolVerifierPrivateDTO,
        bitvmx_protocol_verifier_dto: BitVMXProtocolVerifierDTO,
    ):
        if len(bitvmx_protocol_verifier_dto.read_search_choices) == 0:
            amount_of_trace_steps = (
                bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_trace_steps
            )
            first_iteration_increment = int(
                amount_of_trace_steps
                / (
                    bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_wrong_step_search_hashes_per_iteration
                    + 1
                )
            )
            for i in range(
                1,
                bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_wrong_step_search_hashes_per_iteration
                + 2,
            ):
                current_step = first_iteration_increment * i - 1
                bitvmx_protocol_verifier_dto.published_read_hashes_dict[current_step] = (
                    bitvmx_protocol_verifier_dto.published_hashes_dict[current_step]
                )

        iteration = len(bitvmx_protocol_verifier_dto.read_search_choices)

        target_step, new_published_hashes_dict = self._get_target_step(
            iteration=iteration,
            bitvmx_protocol_setup_properties_dto=bitvmx_protocol_setup_properties_dto,
            bitvmx_protocol_verifier_dto=bitvmx_protocol_verifier_dto,
        )
        total_amount_of_choice_bits = (
            bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
            * bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_wrong_step_search_iterations
        )
        target_step_bin = bin(target_step)[2:].zfill(total_amount_of_choice_bits)
        split_target_step_bin = [
            target_step_bin[
                (
                    bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                )
                * i : (
                    bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                )
                * (i + 1)
            ]
            for i in range(
                bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_wrong_step_search_iterations
            )
        ]

        for i in range(iteration):
            assert bitvmx_protocol_verifier_dto.read_search_choices[i] == int(
                split_target_step_bin[i], 2
            )

        read_search_choice_signatures = bitvmx_protocol_verifier_dto.read_search_choice_signatures

        choice_read_search_witness = []

        current_choice = int(split_target_step_bin[iteration], 2)

        choice_read_search_witness += self.generate_verifier_witness_from_input_single_word_service(
            step=(
                3
                + 2
                * bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_wrong_step_search_iterations
                + 2
                + iteration * 2
                + 1
            ),
            case=0,
            input_number=current_choice,
            amount_of_bits=bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search,
        )

        bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto = (
            self.bitvmx_bitcoin_scripts_generator_service(
                bitvmx_protocol_setup_properties_dto=bitvmx_protocol_setup_properties_dto,
            )
        )

        if iteration == 0:
            current_read_choice_search_scripts_address = bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_challenge_address(
                bitvmx_protocol_setup_properties_dto.unspendable_public_key
            )
            current_read_choice_script_index = (
                bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_read_search_challenge_index()
            )
            trigger_challenge_taptree = (
                bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_challenge_taptree()
            )
            current_read_choice_search_control_block = ControlBlock(
                bitvmx_protocol_setup_properties_dto.unspendable_public_key,
                scripts=trigger_challenge_taptree,
                index=current_read_choice_script_index,
                is_odd=current_read_choice_search_scripts_address.is_odd(),
            )

            current_choice_read_search_script = bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_challenge_scripts_list[
                current_read_choice_script_index
            ]

            bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_choice_tx_list[
                iteration
            ].witnesses.append(
                TxWitnessInput(
                    read_search_choice_signatures[iteration]
                    + choice_read_search_witness
                    + [
                        current_choice_read_search_script.to_hex(),
                        current_read_choice_search_control_block.to_hex(),
                    ]
                )
            )

            broadcast_transaction_service(
                transaction=bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_choice_tx_list[
                    iteration
                ].serialize()
            )

            bitvmx_protocol_verifier_dto.read_search_choices.append(current_choice)
            bitvmx_protocol_verifier_dto.published_read_hashes_dict = new_published_hashes_dict
            print(
                "Search read choice iteration transaction "
                + str(iteration)
                + ": "
                + bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_choice_tx_list[
                    iteration
                ].get_txid()
            )

            return bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_choice_tx_list[
                iteration
            ]
        else:
            current_choice_read_search_scripts_address = bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.choice_read_search_scripts_address(
                destroyed_public_key=bitvmx_protocol_setup_properties_dto.unspendable_public_key,
                iteration=iteration,
            )
            current_choice_read_search_script_index = (
                bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.choice_read_search_script_index()
            )
            current_choice_read_search_taptree = bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.choice_read_search_script_list(
                iteration=iteration
            ).to_scripts_tree()
            current_choice_read_search_control_block = ControlBlock(
                bitvmx_protocol_setup_properties_dto.unspendable_public_key,
                scripts=current_choice_read_search_taptree,
                index=current_choice_read_search_script_index,
                is_odd=current_choice_read_search_scripts_address.is_odd(),
            )
            current_choice_read_search_script = bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.choice_read_search_script_list(
                iteration=iteration
            )[
                0
            ]

            bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_choice_tx_list[
                iteration
            ].witnesses.append(
                TxWitnessInput(
                    read_search_choice_signatures[iteration]
                    + choice_read_search_witness
                    + [
                        current_choice_read_search_script.to_hex(),
                        current_choice_read_search_control_block.to_hex(),
                    ]
                )
            )

            broadcast_transaction_service(
                transaction=bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_choice_tx_list[
                    iteration
                ].serialize()
            )

            bitvmx_protocol_verifier_dto.read_search_choices.append(current_choice)
            bitvmx_protocol_verifier_dto.published_read_hashes_dict = new_published_hashes_dict
            print(
                "Search read choice iteration transaction "
                + str(iteration)
                + ": "
                + bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_choice_tx_list[
                    iteration
                ].get_txid()
            )

            return bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_choice_tx_list[
                iteration
            ]

    def _get_target_step(
        self,
        iteration,
        bitvmx_protocol_setup_properties_dto: BitVMXProtocolSetupPropertiesDTO,
        bitvmx_protocol_verifier_dto: BitVMXProtocolVerifierDTO,
    ):
        previous_published_read_hashes_dict = (
            bitvmx_protocol_verifier_dto.published_read_hashes_dict.copy()
        )

        if iteration > 0:
            previous_hash_read_search_txid = bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.read_search_hash_tx_list[
                iteration - 1
            ].get_txid()
            previous_hash_read_search_tx = transaction_info_service(previous_hash_read_search_txid)
            previous_hash_read_search_witness = previous_hash_read_search_tx.inputs[0].witness

            published_read_hashes = []
            # This offset is due to the cross signed choices
            choice_offset = 8
            for j in range(
                2
                ** bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                - 1
            ):
                hash_witness_portion = previous_hash_read_search_witness[
                    len(bitvmx_protocol_setup_properties_dto.signature_public_keys)
                    + (
                        bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_nibbles_hash_with_checksum
                        * j
                        * 2
                    )
                    + choice_offset : len(
                        bitvmx_protocol_setup_properties_dto.signature_public_keys
                    )
                    + 2
                    * bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_nibbles_hash
                    + bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_nibbles_hash_with_checksum
                    * j
                    * 2
                    + choice_offset
                ]
                published_read_hashes.append(
                    "".join(
                        [
                            (hex_repr[1] if len(hex_repr) == 2 else "0")
                            for hex_repr in reversed(hash_witness_portion[1::2])
                        ]
                    )
                )
            published_read_hashes.reverse()
            prefix = ""
            for read_search_choice in bitvmx_protocol_verifier_dto.read_search_choices:
                prefix += bin(read_search_choice)[2:].zfill(
                    bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                )
            suffix = (
                "1"
                * bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                * (
                    bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_wrong_step_search_iterations
                    - iteration
                    - 1
                )
            )
            index_list = []
            for j in range(
                2
                ** bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                - 1
            ):
                index_list.append(
                    int(
                        prefix
                        + bin(j)[2:].zfill(
                            bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                        )
                        + suffix,
                        2,
                    )
                )

            for j in range(len(index_list)):
                previous_published_read_hashes_dict[index_list[j]] = published_read_hashes[j]

            index_list.append(
                int(
                    prefix
                    + bin(
                        2
                        ** bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                        - 1
                    )[2:].zfill(
                        bitvmx_protocol_setup_properties_dto.bitvmx_protocol_properties_dto.amount_of_bits_wrong_step_search
                    )
                    + suffix,
                    2,
                )
            )

        return 240, previous_published_read_hashes_dict
