from bitcoinutils.constants import TAPROOT_SIGHASH_ALL
from bitcoinutils.keys import PrivateKey, PublicKey
from bitcoinutils.transactions import TxWitnessInput
from bitcoinutils.utils import ControlBlock

from bitvmx_execution.execution_trace_commitment_generation_service import (
    ExecutionTraceCommitmentGenerationService,
)
from mutinyet_api.services.broadcast_transaction_service import BroadcastTransactionService
from mutinyet_api.services.transaction_info_service import TransactionInfoService
from scripts.services.execution_challenge_script_list_generator_service import (
    ExecutionChallengeScriptListGeneratorService,
)


class ExecutionChallengeTransactionService:
    def __init__(self):
        self.transaction_info_service = TransactionInfoService()
        self.broadcast_transaction_service = BroadcastTransactionService()
        self.execution_challenge_script_generator_service = (
            ExecutionChallengeScriptListGeneratorService()
        )
        self.execution_trace_commitment_generation_service = (
            ExecutionTraceCommitmentGenerationService(
                "./execution_files/instruction_commitment.txt",
                "./execution_files/instruction_mapping.txt",
            )
        )

    def __call__(self, protocol_dict):
        trace_words_lengths = protocol_dict["trace_words_lengths"]
        trace_prover_public_keys = protocol_dict["trace_prover_public_keys"]
        trigger_execution_challenge_transaction = protocol_dict["trigger_execution_challenge_tx"]
        # execution_challenge_signatures = protocol_dict["execution_challenge_signatures"]
        execution_challenge_tx = protocol_dict["execution_challenge_tx"]
        destroyed_public_key = PublicKey(hex_str=protocol_dict["destroyed_public_key"])
        signature_public_keys = protocol_dict["public_keys"]
        trace_verifier_public_keys = protocol_dict["trace_verifier_public_keys"]
        amount_of_bits_per_digit_checksum = protocol_dict["amount_of_bits_per_digit_checksum"]
        step_fees_satoshis = protocol_dict["step_fees_satoshis"]

        trigger_execution_challenge_published_transaction = self.transaction_info_service(
            trigger_execution_challenge_transaction.get_txid()
        )
        trigger_execution_challenge_witness = (
            trigger_execution_challenge_published_transaction.inputs[0].witness[2:]
        )

        verifier_keys_witness_values = []
        processed_values = 0
        real_values = []
        for i in reversed(range(len(trace_words_lengths))):
            current_keys_length = len(trace_prover_public_keys[i])
            current_verifier_witness = trigger_execution_challenge_witness[
                processed_values
                + 2 * current_keys_length : processed_values
                + 4 * current_keys_length
            ]
            verifier_keys_witness_values.append(current_verifier_witness)
            processed_values += 4 * current_keys_length
            real_values.append(
                "".join(
                    map(
                        lambda elem: "0" if len(elem) == 0 else elem[1],
                        current_verifier_witness[1 : 2 * trace_words_lengths[i] : 2],
                    )
                )
            )

        trace_to_script_mapping = (
            self.execution_challenge_script_generator_service.trace_to_script_mapping()
        )
        verifier_keys_witness = []
        witness_real_values = []
        for i in trace_to_script_mapping:
            verifier_keys_witness.extend(verifier_keys_witness_values[i])
            witness_real_values.append(real_values[i])

        execution_challenge_script_list = self.execution_challenge_script_generator_service(
            signature_public_keys,
            trace_verifier_public_keys,
            trace_words_lengths,
            amount_of_bits_per_digit_checksum,
        )
        execution_challenge_script_tree = execution_challenge_script_list.to_scripts_tree()

        execution_challenge_script_address = destroyed_public_key.get_taproot_address(
            execution_challenge_script_tree
        )

        key_list, instruction_dict = self.execution_trace_commitment_generation_service()
        pc_read_addr = real_values[6]
        pc_read_micro = real_values[7]
        instruction_index = pc_read_addr + pc_read_micro
        print("Instruction index: " + str(instruction_index))
        current_script_index = key_list.index(instruction_index)

        execution_challenge_control_block = ControlBlock(
            destroyed_public_key,
            scripts=execution_challenge_script_tree,
            index=current_script_index,
            is_odd=execution_challenge_script_address.is_odd(),
        )

        private_key = PrivateKey(b=bytes.fromhex(protocol_dict["prover_secret_key"]))
        execution_challenge_signature = private_key.sign_taproot_input(
            execution_challenge_tx,
            0,
            [execution_challenge_script_address.to_script_pub_key()],
            [execution_challenge_tx.outputs[0].amount + step_fees_satoshis],
            script_path=True,
            tapleaf_script=execution_challenge_script_list[current_script_index],
            sighash=TAPROOT_SIGHASH_ALL,
            tweak=False,
        )

        execution_challenge_tx.witnesses.append(
            TxWitnessInput(
                [execution_challenge_signature]
                + verifier_keys_witness
                + [
                    execution_challenge_script_list[current_script_index].to_hex(),
                    execution_challenge_control_block.to_hex(),
                ]
            )
        )

        self.broadcast_transaction_service(transaction=execution_challenge_tx.serialize())
        print("Execution challenge transaction: " + execution_challenge_tx.get_txid())
        return execution_challenge_tx
