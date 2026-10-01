import asyncio
from dataclasses import dataclass
from typing import Dict, Tuple


def record_template(config, database_name, *, async_):
    key = (config.host, config.port, database_name)
    created_templates[key] = CreatedTemplate(config, database_name, async_)


def drop_templates(config):
    server = (config.host, config.port)
    keys = [key for key in created_templates if key[:2] == server]
    templates = [created_templates.pop(key) for key in keys]
    if not templates:
        return

    # NOTE: Imported here because `container.base` calls this and `fixture.postgresql` imports
    #       `container.base`.
    from pytest_mock_resources.fixture.postgresql import _drop_database, _drop_database_async

    for template in templates:
        if not template.async_:
            _drop_database(template.config, template.database_name)

    async_templates = [template for template in templates if template.async_]
    if async_templates:
        # NOTE: A private loop is used because `asyncio.run` resets the current event loop, which
        #       breaks later tests under older pytest-asyncio versions.
        loop = asyncio.new_event_loop()
        try:
            for template in async_templates:
                loop.run_until_complete(
                    _drop_database_async(template.config, template.database_name)
                )

        finally:
            loop.close()


@dataclass(frozen=True)
class CreatedTemplate:
    config: object
    database_name: str
    async_: bool


created_templates: Dict[Tuple[object, object, str], CreatedTemplate] = {}
