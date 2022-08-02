import sys

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock
else:
    from asynctest.mock import CoroutineMock as AsyncMock

from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest
from baby_steps import given, then, when

from vedro.core import (
    Config,
    ConfigFileLoader,
    ConfigLoader,
    Dispatcher,
    Lifecycle,
    MonotonicRunner,
    Report,
    ScenarioDiscoverer,
)


@pytest.fixture()
def dispatcher_():
    return AsyncMock(Dispatcher)


@pytest.fixture()
def discoverer_():
    return Mock(ScenarioDiscoverer)


@pytest.fixture()
def config_loader():
    return ConfigFileLoader(Config)


@pytest.fixture()
def runner_(dispatcher_: Dispatcher):
    report = Report()
    return Mock(MonotonicRunner(dispatcher_), run=AsyncMock(return_value=report))


@pytest.mark.asyncio
async def test_lifecycle_register_start(*, dispatcher_: Dispatcher,
                                        discoverer_: ScenarioDiscoverer,
                                        runner_: MonotonicRunner,
                                        config_loader: ConfigLoader):
    with given:
        scenarios = []
        discoverer_.discover = AsyncMock(return_value=scenarios)

        lifecycle = Lifecycle(dispatcher_, discoverer_, runner_, config_loader)

    with when, patch("argparse.ArgumentParser.parse_args", return_value=Namespace()):
        report = await lifecycle.start()

    with then:
        assert isinstance(report, Report)
        assert discoverer_.mock_calls == [
            call.discover(Path("scenarios"))
        ]
        assert len(runner_.mock_calls) == 1
        assert len(dispatcher_.mock_calls) > 0


def test_lifecycle_repr(*, dispatcher_: Dispatcher,
                        discoverer_: ScenarioDiscoverer,
                        runner_: MonotonicRunner,
                        config_loader: ConfigLoader):
    with when:
        lifecycle = Lifecycle(dispatcher_, discoverer_, runner_, config_loader)

    with then:
        assert repr(lifecycle) == (
            f"Lifecycle({dispatcher_!r}, {discoverer_!r}, {runner_!r}, {config_loader!r})"
        )
