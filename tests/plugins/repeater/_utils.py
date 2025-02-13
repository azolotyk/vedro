from argparse import ArgumentParser, Namespace
from pathlib import Path
from time import monotonic_ns
from unittest.mock import Mock

import pytest

from vedro import Scenario
from vedro.core import (
    Config,
    ConfigType,
    Dispatcher,
    Factory,
    MonotonicScenarioScheduler,
    ScenarioResult,
    ScenarioScheduler,
    VirtualScenario,
)
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    ConfigLoadedEvent,
    ScenarioFailedEvent,
    StartupEvent,
)
from vedro.plugins.repeater import Repeater, RepeaterPlugin
from vedro.plugins.repeater import RepeaterScenarioScheduler as Scheduler


@pytest.fixture()
def dispatcher() -> Dispatcher:
    return Dispatcher()


@pytest.fixture()
def repeater(dispatcher: Dispatcher) -> RepeaterPlugin:
    plugin = RepeaterPlugin(Repeater)
    plugin.subscribe(dispatcher)
    return plugin


@pytest.fixture()
def scheduler() -> Scheduler:
    return Scheduler([])


@pytest.fixture()
def scheduler_() -> Scheduler:
    return Mock(spec=Scheduler)


def make_vscenario() -> VirtualScenario:
    class _Scenario(Scenario):
        __file__ = Path(f"scenario_{monotonic_ns()}.py").absolute()

    return VirtualScenario(_Scenario, steps=[])


def make_scenario_result() -> ScenarioResult:
    return ScenarioResult(make_vscenario())


def make_config() -> ConfigType:
    class TestConfig(Config):
        class Registry(Config.Registry):
            ScenarioScheduler = Factory[ScenarioScheduler](MonotonicScenarioScheduler)

    return TestConfig


async def fire_arg_parsed_event(dispatcher: Dispatcher, repeats: int) -> None:
    config_loaded_event = ConfigLoadedEvent(Path(), make_config())
    await dispatcher.fire(config_loaded_event)

    arg_parse_event = ArgParseEvent(ArgumentParser())
    await dispatcher.fire(arg_parse_event)

    arg_parsed_event = ArgParsedEvent(Namespace(repeats=repeats))
    await dispatcher.fire(arg_parsed_event)


async def fire_startup_event(dispatcher: Dispatcher, scheduler: Scheduler) -> None:
    startup_event = StartupEvent(scheduler)
    await dispatcher.fire(startup_event)


async def fire_failed_event(dispatcher: Dispatcher) -> ScenarioFailedEvent:
    scenario_result = make_scenario_result().mark_failed()
    scenario_failed_event = ScenarioFailedEvent(scenario_result)
    await dispatcher.fire(scenario_failed_event)
    return scenario_failed_event
