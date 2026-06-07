"""Observabilidad con OpenTelemetry.

La instrumentación es activable por entorno y no requiere un backend
OTLP configurado para que la aplicación arranque.
"""

import os

from fastapi import FastAPI


def init_observability(app: FastAPI) -> None:
    """Inicializa OpenTelemetry para FastAPI si está activado.

    La variable OTEL_ENABLED controla la activación.
    Si no hay exporter OTLP configurado, la app arranca igual.
    """
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        provider = TracerProvider()
        trace.set_tracer_provider(provider)

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))

        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        # No bloquear el arranque si OTel falla
        import logging
        logging.getLogger(__name__).warning("OpenTelemetry initialization failed, continuing without telemetry")
