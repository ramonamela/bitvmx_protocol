from bitcoinutils.constants import TAPROOT_SIGHASH_ALL
from bitcoinutils.keys import PrivateKey
from bitcoinutils.transactions import TxWitnessInput
from bitcoinutils.utils import ControlBlock

from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_setup_properties_dto import (
    BitVMXProtocolSetupPropertiesDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_verifier_dto import (
    BitVMXProtocolVerifierDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_verifier_private_dto import (
    BitVMXProtocolVerifierPrivateDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.services.get_choice_witness_service import (
    GetChoiceWitnessService,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.services.get_correct_hash_witness_service import (
    GetCorrectHashWitnessService,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.services.get_trace_witness_service import (
    GetTraceWitnessService,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.services.get_wrong_hash_witness_service import (
    GetWrongHashWitnessService,
)
from blockchain_query_services.services.blockchain_query_services_dependency_injection import (
    broadcast_transaction_service,
)


class TriggerWrongProgramCounterChallengeTransactionService:
    def __init__(self, verifier_private_key):
        self.get_correct_hash_witness_service = GetCorrectHashWitnessService()
        self.get_wrong_hash_witness_service = GetWrongHashWitnessService()
        self.get_trace_witness_service = GetTraceWitnessService()
        self.get_choice_witness_service = GetChoiceWitnessService()

    def __call__(
        self,
        bitvmx_protocol_setup_properties_dto: BitVMXProtocolSetupPropertiesDTO,
        bitvmx_protocol_verifier_private_dto: BitVMXProtocolVerifierPrivateDTO,
        bitvmx_protocol_verifier_dto: BitVMXProtocolVerifierDTO,
    ):
        trigger_challenge_taptree = (
            bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_challenge_taptree()
        )
        trigger_challenge_scripts_address = bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_challenge_address(
            bitvmx_protocol_setup_properties_dto.unspendable_public_key
        )

        wrong_program_counter_control_block = ControlBlock(
            bitvmx_protocol_setup_properties_dto.unspendable_public_key,
            scripts=trigger_challenge_taptree,
            index=bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_wrong_program_counter_challenge_index(
                choice=bitvmx_protocol_verifier_dto.first_wrong_step
            ),
            is_odd=trigger_challenge_scripts_address.is_odd(),
        )

        choices_witness = self.get_choice_witness_service(
            bitvmx_protocol_setup_properties_dto=bitvmx_protocol_setup_properties_dto,
            bitvmx_protocol_verifier_dto=bitvmx_protocol_verifier_dto,
        )

        private_key = PrivateKey(
            b=bytes.fromhex(bitvmx_protocol_verifier_private_dto.verifier_signature_private_key)
        )

        current_script = bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_challenge_scripts_list[
            bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_wrong_program_counter_challenge_index(
                choice=bitvmx_protocol_verifier_dto.first_wrong_step
            )
        ]

        wrong_program_counter_challenge_signature = private_key.sign_taproot_input(
            bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trigger_wrong_program_counter_challenge_tx,
            0,
            [trigger_challenge_scripts_address.to_script_pub_key()],
            [
                bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trigger_wrong_program_counter_challenge_tx.outputs[
                    0
                ].amount
                + bitvmx_protocol_setup_properties_dto.step_fees_satoshis * 4
            ],
            script_path=True,
            tapleaf_script=current_script,
            sighash=TAPROOT_SIGHASH_ALL,
            tweak=False,
        )

        trigger_wrong_program_counter_challenge_signature = [
            wrong_program_counter_challenge_signature
        ]
        trigger_challenge_witness = choices_witness

        bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trigger_wrong_program_counter_challenge_tx.witnesses.append(
            TxWitnessInput(
                trigger_challenge_witness
                + trigger_wrong_program_counter_challenge_signature
                + [
                    current_script.to_hex(),
                    wrong_program_counter_control_block.to_hex(),
                ]
            )
        )

        broadcast_transaction_service(
            transaction=bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trigger_wrong_program_counter_challenge_tx.serialize()
        )

        print(
            "Trigger wrong program counter challenge transaction: "
            + bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trigger_wrong_program_counter_challenge_tx.get_txid()
        )
        return (
            bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trigger_wrong_program_counter_challenge_tx
        )
