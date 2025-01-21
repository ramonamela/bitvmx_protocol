from bitcoinutils.setup import setup
from fastapi import FastAPI

from bitvmx_protocol_library.config import common_protocol_properties
from bitvmx_protocol_library.enums import BitcoinNetwork
from verifier_app.api.router import router as verifier_router
from verifier_app.config import protocol_properties

if common_protocol_properties.network == BitcoinNetwork.MUTINYNET:
    setup("testnet")
else:
    setup(common_protocol_properties.network.value)

if protocol_properties.sentry_dsn is not None:
    import sentry_sdk

    sentry_sdk.init(
        dsn=protocol_properties.sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        _experiments={
            # Set continuous_profiling_auto_start to True
            # to automatically start the profiler on when
            # possible.
            "continuous_profiling_auto_start": True,
        },
    )

app = FastAPI(
    title="Verifier service",
    description="Microservice to perform all the operations related to the verifier",
)


@app.get("/healthcheck")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(verifier_router, prefix="/api")  # , tags=["Prover API"])
