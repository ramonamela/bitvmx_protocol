from dependency_injector import containers, providers

from bitvmx_protocol_library.config import common_protocol_properties
from bitvmx_protocol_library.script_generation.services.bitvmx_bitcoin_scripts_generator_service import (
    BitVMXBitcoinScriptsGeneratorService,
)
from bitvmx_protocol_library.transaction_generation.services.generate_signatures_service import (
    GenerateSignaturesService,
)
from bitvmx_protocol_library.transaction_generation.services.signature_verification.verify_prover_signatures_service import (
    VerifyProverSignaturesService,
)
from bitvmx_protocol_library.transaction_generation.services.transaction_generator_from_public_keys_service import (
    TransactionGeneratorFromPublicKeysService,
)
from verifier_app.domain.v1.signatures.controllers.generate_signatures_controller import (
    GenerateSignaturesController,
)


class GenerateSignaturesControllers(containers.DeclarativeContainer):
    bitvmx_protocol = providers.Singleton(
        GenerateSignaturesController,
        bitvmx_bitcoin_scripts_generator_service=BitVMXBitcoinScriptsGeneratorService(),
        transaction_generator_from_public_keys_service=TransactionGeneratorFromPublicKeysService(),
        generate_signatures_service_class=GenerateSignaturesService,
        verify_prover_signatures_service_class=VerifyProverSignaturesService,
        common_protocol_properties=common_protocol_properties,
    )