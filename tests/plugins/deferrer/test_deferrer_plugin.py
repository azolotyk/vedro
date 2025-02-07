import sys

from vedro import defer
from vedro.plugins.deferrer import Deferrer, DeferrerPlugin

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock
else:
    from asynctest.mock import CoroutineMock as AsyncMock

from collections import deque
from unittest.mock import Mock, call

import pytest
from baby_steps import given, then, when

from vedro.core import Dispatcher, ScenarioResult
from vedro.events import ScenarioFailedEvent, ScenarioPassedEvent, ScenarioRunEvent

from ._utils import deferrer, dispatcher, make_vscenario, queue

__all__ = ("dispatcher", "deferrer", "queue")  # fixtures


@pytest.mark.asyncio
@pytest.mark.usefixtures(deferrer.__name__)
async def test_scenario_run_event(*, dispatcher: Dispatcher, queue: deque):
    with given:
        queue.append((Mock(), (), {}))

        scenario_result = ScenarioResult(make_vscenario())
        event = ScenarioRunEvent(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert len(queue) == 0


@pytest.mark.asyncio
@pytest.mark.usefixtures(deferrer.__name__)
@pytest.mark.parametrize("event_class", [ScenarioPassedEvent, ScenarioFailedEvent])
async def test_scenario_end_event(event_class, *, dispatcher: Dispatcher, queue: deque):
    with given:
        manager = Mock()
        deferred1 = Mock()
        manager.attach_mock(deferred1, "deferred1")
        deferred2 = Mock()
        manager.attach_mock(deferred2, "deferred2")

        args1, kwargs1 = ("arg1", "arg2"), {"key1": "val1"}
        queue.append((deferred1, args1, kwargs1))
        args2, kwargs2 = ("arg3", "arg4"), {"key2": "val2"}
        queue.append((deferred2, args2, kwargs2))

        scenario_result = ScenarioResult(make_vscenario())
        event = event_class(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert manager.mock_calls == [
            call.deferred2(*args2, **kwargs2),
            call.deferred1(*args1, **kwargs1),
        ]
        assert len(queue) == 0


@pytest.mark.asyncio
@pytest.mark.usefixtures(deferrer.__name__)
@pytest.mark.parametrize("event_class", [ScenarioPassedEvent, ScenarioFailedEvent])
async def test_scenario_end_event_async(event_class, *, dispatcher: Dispatcher, queue: deque):
    with given:
        manager = Mock()
        deferred1 = AsyncMock()
        manager.attach_mock(deferred1, "deferred1")
        deferred2 = AsyncMock()
        manager.attach_mock(deferred2, "deferred2")

        args1, kwargs1 = ("arg1", "arg2"), {"key1": "val1"}
        queue.append((deferred1, args1, kwargs1))
        args2, kwargs2 = ("arg3", "arg4"), {"key2": "val2"}
        queue.append((deferred2, args2, kwargs2))

        scenario_result = ScenarioResult(make_vscenario())
        event = event_class(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert manager.mock_calls == [
            call.deferred2(*args2, **kwargs2),
            call.deferred1(*args1, **kwargs1),
        ]
        deferred1.assert_awaited_once()
        deferred2.assert_awaited_once()
        assert len(queue) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("event_class", [ScenarioPassedEvent, ScenarioFailedEvent])
async def test_(event_class, *, dispatcher: Dispatcher):
    with given:
        deferrer = DeferrerPlugin(Deferrer)
        deferrer.subscribe(dispatcher)

        manager = Mock()
        deferred1 = AsyncMock()
        manager.attach_mock(deferred1, "deferred1")
        deferred2 = Mock()
        manager.attach_mock(deferred2, "deferred2")

        args1, kwargs1 = ("arg1", "arg2"), {"key1": "val1"}
        defer(deferred1, *args1, **kwargs1)
        args2, kwargs2 = ("arg3", "arg4"), {"key2": "val2"}
        defer(deferred2, *args2, **kwargs2)

        scenario_result = ScenarioResult(make_vscenario())
        event = event_class(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert manager.mock_calls == [
            call.deferred2(*args2, **kwargs2),
            call.deferred1(*args1, **kwargs1),
        ]
        deferred1.assert_awaited_once()
