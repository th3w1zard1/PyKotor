from __future__ import annotations

import inspect
import sys
import types
import weakref

from typing import TYPE_CHECKING, Any

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    from types import TracebackType


def _forward_exception_to_excepthook() -> None:
    etype: type[BaseException] | None = None
    exc: BaseException | None = None
    tback: TracebackType | None = None
    etype, exc, tback = sys.exc_info()
    if etype is None or exc is None:
        return
    try:
        sys.excepthook(etype, exc, tback)
    except Exception:  # noqa: BLE001
        # Never allow exception-handling to crash the app.
        RobustLogger().exception("sys.excepthook raised unexpectedly")


def install_sys_unraisablehook() -> None:
    """Route unraisable exceptions (e.g. __del__) to sys.excepthook."""
    if not hasattr(sys, "unraisablehook"):
        return

    def _hook(hook_args: types.SimpleNamespace):  # matches sys.UnraisableHookArgs shape
        try:
            etype = hook_args.exc_type
            exc = hook_args.exc_value
            tback = hook_args.exc_traceback
            if etype is not None and exc is not None:
                sys.excepthook(etype, exc, tback)
        except Exception:  # noqa: BLE001
            RobustLogger().exception("sys.unraisablehook handler failed")

    sys.unraisablehook = _hook  # type: ignore[assignment]


def install_asyncio_exception_handler() -> None:
    """Route asyncio loop exceptions to sys.excepthook (best-effort)."""
    try:
        import asyncio
    except Exception:  # noqa: BLE001
        return

    try:
        loop = asyncio.get_event_loop()
    except Exception:  # noqa: BLE001
        return

    def _handler(_loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:  # noqa: ANN001
        exc: Any | None = context.get("exception")
        if isinstance(exc, BaseException):
            etype = type(exc)
            tback = exc.__traceback__
            try:
                sys.excepthook(etype, exc, tback)
            except Exception:  # noqa: BLE001
                RobustLogger().exception("asyncio exception handler failed")
        else:
            RobustLogger().error("asyncio error: %s", context.get("message", "unknown"))

    try:
        loop.set_exception_handler(_handler)
    except Exception:  # noqa: BLE001
        RobustLogger().exception("Failed to set asyncio exception handler")


def install_qt_signal_slot_safety_net() -> None:  # noqa: C901
    """Monkeypatch Qt signal connect/disconnect so Python slot exceptions never crash the app.

    Why this exists:
    - Qt callback exceptions frequently do not reach Python's "uncaught exception" machinery.
    - Some bindings will print+swallow, others can terminate the process depending on context.
    - Wrapping at connect-time is the closest thing to a "global" fix for a large codebase.
    """

    # (signal_instance) -> { id(original_slot) -> wrapped_slot }
    try:
        _slot_map: weakref.WeakKeyDictionary[object, dict[int, object]] = weakref.WeakKeyDictionary()
    except TypeError:
        _slot_map = weakref.WeakKeyDictionary()  # type: ignore[assignment]

    def _get_wrapped(signal_obj: object, slot: object) -> Any | None:
        try:
            return _slot_map.get(signal_obj, {}).get(id(slot))
        except Exception:  # noqa: BLE001
            return None

    def _remember(
        signal_obj: object,
        slot: object,
        wrapped: object,
    ) -> None:
        try:
            d = _slot_map.get(signal_obj)
            if d is None:
                d = {}
                _slot_map[signal_obj] = d
            d[id(slot)] = wrapped
        except Exception:  # noqa: BLE001
            # Never allow mapping issues to break normal connect() behavior.
            pass

    def _wrap_slot(slot: object):  # noqa: ANN001
        if not callable(slot):
            return slot
        if getattr(slot, "__toolset_qt_safe_slot__", False):
            return slot

        max_positional_args: int | None
        try:
            sig = inspect.signature(slot)
            if any(p.kind is inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values()):
                max_positional_args = None
            else:
                max_positional_args = sum(
                    1
                    for p in sig.parameters.values()
                    if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                )
        except Exception:  # noqa: BLE001
            # If we can't introspect the callable, fall back to passing the original args through.
            max_positional_args = None

        def wrapped(*args, **kwargs):  # noqa: ANN001
            try:
                call_args = args if max_positional_args is None else args[:max_positional_args]
                return slot(*call_args, **kwargs)
            except Exception:  # noqa: BLE001
                # Route to global handler and swallow so Qt can continue running.
                _forward_exception_to_excepthook()
                return None

        setattr(wrapped, "__toolset_qt_safe_slot__", True)
        setattr(wrapped, "__toolset_qt_original_slot__", slot)
        return wrapped

    # --- PyQt ---
    if qtpy.PYQT5 or qtpy.PYQT6:
        try:
            if qtpy.PYQT5:
                from PyQt5.QtCore import pyqtBoundSignal  # type: ignore
            else:
                from PyQt6.QtCore import pyqtBoundSignal  # type: ignore
        except Exception:  # noqa: BLE001
            RobustLogger().warning("Qt signal safety net: could not import pyqtBoundSignal")
            return

        if getattr(pyqtBoundSignal.connect, "__toolset_patched__", False):
            return

        _orig_connect = pyqtBoundSignal.connect
        _orig_disconnect = pyqtBoundSignal.disconnect

        def connect(
            self,
            slot: object,
            *args,
            **kwargs,
        ) -> Any:  # noqa: ANN001
            wrapped = _wrap_slot(slot)
            if wrapped is not slot:
                _remember(self, slot, wrapped)
            return _orig_connect(self, wrapped, *args, **kwargs)  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]

        def disconnect(
            self,
            slot: Any | None = None,
        ):  # noqa: ANN001
            if slot is None:
                return _orig_disconnect(self)
            wrapped: Any | None = _get_wrapped(self, slot)
            if wrapped is not None:
                try:
                    return _orig_disconnect(self, wrapped)
                except Exception:  # noqa: BLE001
                    # Fall through to original slot.
                    pass
            return _orig_disconnect(self, slot)

        connect.__toolset_patched__ = True  # type: ignore[attr-defined]
        pyqtBoundSignal.connect = connect  # pyright: ignore[reportAssignmentType]  # type: ignore[assignment]
        pyqtBoundSignal.disconnect = disconnect  # pyright: ignore[reportAssignmentType]  # type: ignore[assignment]
        RobustLogger().debug("Installed Qt signal safety net for PyQt (pyqtBoundSignal.connect/disconnect)")
        return

    # --- PySide ---
    if qtpy.PYSIDE2 or qtpy.PYSIDE6:
        try:
            if qtpy.PYSIDE2:
                from PySide2.QtCore import SignalInstance  # type: ignore
            else:
                from PySide6.QtCore import SignalInstance  # type: ignore
        except Exception:  # noqa: BLE001
            RobustLogger().warning("Qt signal safety net: could not import SignalInstance")
            return

        if getattr(SignalInstance.connect, "__toolset_patched__", False):
            return

        _orig_connect = SignalInstance.connect
        _orig_disconnect = SignalInstance.disconnect

        def connect(self, slot, *args, **kwargs):  # noqa: ANN001
            wrapped = _wrap_slot(slot)
            if wrapped is not slot:
                _remember(self, slot, wrapped)
            return _orig_connect(self, wrapped, *args, **kwargs)

        def disconnect(self, slot=None):  # noqa: ANN001
            if slot is None:
                return _orig_disconnect(self)
            wrapped = _get_wrapped(self, slot)
            if wrapped is not None:
                try:
                    return _orig_disconnect(self, wrapped)
                except Exception:  # noqa: BLE001
                    pass
            return _orig_disconnect(self, slot)

        connect.__toolset_patched__ = True  # type: ignore[attr-defined]
        SignalInstance.connect = connect  # type: ignore[assignment]
        SignalInstance.disconnect = disconnect  # type: ignore[assignment]
        RobustLogger().debug("Installed Qt signal safety net for PySide (SignalInstance.connect/disconnect)")
        return

    RobustLogger().warning("Qt signal safety net: unknown Qt binding; no patch applied")
