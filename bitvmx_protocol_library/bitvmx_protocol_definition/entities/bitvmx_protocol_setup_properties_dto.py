import hashlib
from typing import List

from bitcoinutils.keys import PublicKey
from pydantic import BaseModel


class BitVMXProtocolSetupPropertiesDTO(BaseModel):
    setup_uuid: str
    funding_amount_of_satoshis: int
    step_fees_satoshis: int
    funding_tx_id: str
    funding_index: int
    verifier_list: List[str]
    prover_destination_address: str
    prover_signature_public_key: str
    seed_unspendable_public_key: str
    # controlled_prover_address: str
    # controlled_verifier_address: str
    prover_destroyed_public_key: str
    verifier_destroyed_public_key: str

    @staticmethod
    def unspendable_public_key_from_seed(seed_unspendable_public_key: str):
        destroyed_public_key_hex = hashlib.sha256(
            bytes.fromhex(seed_unspendable_public_key)
        ).hexdigest()
        # This is done so everyone can verify that they participated on the seed construction
        # but at the same time the public key is unspendable
        return PublicKey(hex_str="02" + destroyed_public_key_hex)

    @property
    def unspendable_public_key(self):
        return self.unspendable_public_key_from_seed(self.seed_unspendable_public_key)

    @property
    def signature_public_keys(self):
        return [self.verifier_destroyed_public_key, self.prover_destroyed_public_key]
