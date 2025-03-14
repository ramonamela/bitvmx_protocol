from bitcoinutils.constants import TAPROOT_SIGHASH_ALL
from bitcoinutils.keys import PrivateKey
from bitcoinutils.transactions import TxWitnessInput
from bitcoinutils.utils import ControlBlock

from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_prover_private_dto import (
    BitVMXProtocolProverPrivateDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.entities.bitvmx_protocol_setup_properties_dto import (
    BitVMXProtocolSetupPropertiesDTO,
)
from bitvmx_protocol_library.bitvmx_protocol_definition.services.witness_extraction.get_full_verifier_choice_witness_service import (
    GetFullVerifierChoiceWitnessService,
)
from blockchain_query_services.services.blockchain_query_services_dependency_injection import (
    broadcast_transaction_service,
    transaction_info_service,
)


class TriggerWrongTraceStepTransactionService:
    def __init__(self):
        self.get_full_verifier_choice_witness_service = GetFullVerifierChoiceWitnessService()

    def __call__(
        self,
        setup_uuid: str,
        bitvmx_protocol_setup_properties_dto: BitVMXProtocolSetupPropertiesDTO,
        bitvmx_protocol_prover_private_dto: BitVMXProtocolProverPrivateDTO,
    ):
        trigger_wrong_trace_step_taptree = (
            bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trace_script_list.to_scripts_tree()
        )
        trigger_wrong_trace_step_scripts_address = bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trace_script_list.get_taproot_address(
            public_key=bitvmx_protocol_setup_properties_dto.unspendable_public_key
        )
        current_script_index = (
            bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trigger_wrong_trace_step_index()
        )
        current_script = (
            bitvmx_protocol_setup_properties_dto.bitvmx_bitcoin_scripts_dto.trace_script_list[
                current_script_index
            ]
        )
        trigger_wrong_trace_step_control_block = ControlBlock(
            bitvmx_protocol_setup_properties_dto.unspendable_public_key,
            scripts=trigger_wrong_trace_step_taptree,
            index=current_script_index,
            is_odd=trigger_wrong_trace_step_scripts_address.is_odd(),
        )
        private_key = PrivateKey(
            b=bytes.fromhex(bitvmx_protocol_prover_private_dto.prover_signature_private_key)
        )

        trigger_wrong_trace_step_signature = private_key.sign_taproot_input(
            bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trace_tx,
            0,
            [trigger_wrong_trace_step_scripts_address.to_script_pub_key()],
            [
                bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trace_tx.outputs[
                    0
                ].amount
                + bitvmx_protocol_setup_properties_dto.step_fees_satoshis
            ],
            script_path=True,
            tapleaf_script=current_script,
            sighash=TAPROOT_SIGHASH_ALL,
            tweak=False,
        )

        trigger_protocol_tx = transaction_info_service(
            tx_id=bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trigger_protocol_tx.get_txid()
        )

        trigger_protocol_witness = trigger_protocol_tx.inputs[0].witness
        halt_step_witness_length = 2 * len(
            bitvmx_protocol_setup_properties_dto.bitvmx_prover_winternitz_public_keys_dto.halt_step_public_keys
        )
        verifier_halt_step_witness = trigger_protocol_witness[
            halt_step_witness_length : 2 * halt_step_witness_length
        ]

        full_choice_witness = self.get_full_verifier_choice_witness_service(
            bitvmx_protocol_setup_properties_dto=bitvmx_protocol_setup_properties_dto
        )

        trigger_wrong_trace_step_witness = verifier_halt_step_witness + full_choice_witness

        trigger_wrong_trace_step_signatures = [trigger_wrong_trace_step_signature]

        bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trace_tx.witnesses.append(
            TxWitnessInput(
                trigger_wrong_trace_step_witness
                + trigger_wrong_trace_step_signatures
                + [
                    current_script.to_hex(),
                    trigger_wrong_trace_step_control_block.to_hex(),
                ]
            )
        )

        broadcast_transaction_service(
            transaction=bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trace_tx
        )

        print(
            "Trigger wrong trace step transaction: "
            + bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trace_tx.get_txid()
        )
        return bitvmx_protocol_setup_properties_dto.bitvmx_transactions_dto.trace_tx
