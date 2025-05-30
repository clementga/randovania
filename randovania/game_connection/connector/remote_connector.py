from __future__ import annotations

import enum
import typing

from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.lib import enum_lib
from randovania.lib.signal import RdvSignal

if typing.TYPE_CHECKING:
    import uuid

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.region import Region
    from randovania.network_common.remote_pickup import RemotePickup


class PlayerLocationEvent(typing.NamedTuple):
    world: Region | None
    area: Area | None


class ImportantStatusMessage(enum.Enum):
    """Messages that Randovania can request the game displays."""

    DISCONNECTED_FROM_SERVER = "disconnected-from-server"

    long_name: str


enum_lib.add_long_name(
    ImportantStatusMessage,
    {
        ImportantStatusMessage.DISCONNECTED_FROM_SERVER: (
            "Connection to the server has been lost. Please check Randovania application for details."
        )
    },
)


class RemoteConnector:
    _layout_uuid: uuid.UUID
    PlayerLocationChanged = RdvSignal[[PlayerLocationEvent]]()
    PickupIndexCollected = RdvSignal[[PickupIndex]]()
    InventoryUpdated = RdvSignal[[Inventory]]()

    @property
    def game_enum(self) -> RandovaniaGame:
        raise NotImplementedError

    def description(self) -> str:
        raise NotImplementedError

    @property
    def layout_uuid(self) -> uuid.UUID:
        return self._layout_uuid

    async def display_important_message(self, message: ImportantStatusMessage) -> None:
        """Requests the game to display a message from a predetermined list.

        Overriding this method is only necessary if implementing display_arbitrary_message is impossible for this game.
        :param message: The enum of the message to send.
        """
        await self.display_arbitrary_message(message.long_name)

    @classmethod
    def can_display_arbitrary_messages(cls) -> bool:
        """Returns if arbitrary messages can be sent to this game."""
        return cls.display_arbitrary_message is not RemoteConnector.display_arbitrary_message

    async def display_arbitrary_message(self, message: str) -> None:
        """Requests the game to display an arbitrary message.

        Not necessary to be implemented by every game.
        :param message: The message to send.
        """
        raise NotImplementedError

    async def set_remote_pickups(self, remote_pickups: tuple[RemotePickup, ...]) -> None:
        """
        Sets the list of remote pickups that must be sent to the game.
        :param remote_pickups: Ordered list of pickups sent from other players, with the name of the player.
        """
        raise NotImplementedError

    async def force_finish(self) -> None:
        """Disconnect from the game, releasing any resources."""
        raise NotImplementedError

    def is_disconnected(self) -> bool:
        """When True, this connector has lost connection with the game and must be discarded."""
        raise NotImplementedError

    def inform_connected_tracker(self, tracker_details: dict | None) -> None:
        """Called when an AutoTracker is created using this connector."""
