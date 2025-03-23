from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, HuntersConfiguration)

    # Add Alimbic Artifacts to the item pool
    results.extend_with(add_alimbic_artifacts(game.resource_database))

    # Add Octoliths to the item pool
    results.extend_with(add_octoliths(game.resource_database))


def add_alimbic_artifacts(
    resource_database: ResourceDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: list[PickupEntry] = []

    for region in ("Celestial", "Alinos", "Arcterra", "VDO"):
        for artifact_type in ("Attameter", "Cartograph", "Binary Subscripture"):
            for i in range(2):
                artifact = f"{region} {artifact_type} Artifact"
                item_pool.append(create_generated_pickup(artifact, resource_database, i=i + 1))

    return PoolResults(item_pool, {}, [])


def add_octoliths(
    resource_database: ResourceDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: list[PickupEntry] = []
    octoliths_to_place: int = 8

    for key_number in range(octoliths_to_place):
        item_pool.append(create_generated_pickup("Octolith", resource_database, i=key_number + 1))
    first_automatic_key = octoliths_to_place

    starting = [
        create_generated_pickup("Octolith", resource_database, i=automatic_key_number + 1)
        for automatic_key_number in range(first_automatic_key, 8)
    ]

    return PoolResults(item_pool, {}, starting)
