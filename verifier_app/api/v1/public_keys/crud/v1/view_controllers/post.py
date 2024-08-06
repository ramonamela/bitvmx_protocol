from verifier_app.api.v1.public_keys.crud.v1.view_models.post import (
    PublicKeysPostV1Input,
    PublicKeysPostV1Output,
)


class PublicKeysPostViewControllerV1:

    def __init__(self, generate_public_keys_controller):
        self.generate_public_keys_controller = generate_public_keys_controller

    async def __call__(
        self, public_keys_post_view_input: PublicKeysPostV1Input
    ) -> PublicKeysPostV1Output:
        setup_uuid = public_keys_post_view_input.setup_uuid
        (
            bitvmx_verifier_winternitz_public_keys_dto,
            verifier_public_key_hex,
        ) = await self.generate_public_keys_controller(
            setup_uuid=setup_uuid,
            public_keys_post_view_input=public_keys_post_view_input,
            bitvmx_protocol_properties_dto=public_keys_post_view_input.bitvmx_protocol_properties_dto,
            bitvmx_protocol_setup_properties_dto=public_keys_post_view_input.bitvmx_protocol_setup_properties_dto,
            bitvmx_prover_winternitz_public_keys_dto=public_keys_post_view_input.bitvmx_prover_winternitz_public_keys_dto,
        )
        return PublicKeysPostV1Output(
            bitvmx_verifier_winternitz_public_keys_dto=bitvmx_verifier_winternitz_public_keys_dto,
            verifier_public_key=verifier_public_key_hex,
        )