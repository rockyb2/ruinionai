"""Privacy-safe helpers for Langfuse observations."""

from contextlib import contextmanager


@contextmanager
def sanitized_observation(observation_context, error_message):
    """Prevent raw provider exceptions from being attached to an observation.

    Langfuse/OpenTelemetry normally records exceptions escaping a context
    manager. Provider errors can contain request or response excerpts, so the
    original exception is re-raised only after the observation has closed.
    """
    deferred_error = None
    deferred_traceback = None

    with observation_context as observation:
        try:
            yield observation
        except Exception as error:
            observation.update(
                level="ERROR",
                status_message=error_message,
                output={
                    "status": "failed",
                    "error_type": type(error).__name__,
                },
            )
            deferred_error = error
            deferred_traceback = error.__traceback__

    if deferred_error is not None:
        raise deferred_error.with_traceback(deferred_traceback)
