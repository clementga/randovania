from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def dread_preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.dread.gui.preset_settings.dread_energy_tab import PresetDreadEnergy
    from randovania.games.dread.gui.preset_settings.dread_generation_tab import PresetDreadGeneration
    from randovania.games.dread.gui.preset_settings.dread_goal_tab import PresetDreadGoal
    from randovania.games.dread.gui.preset_settings.dread_item_pool_tab import DreadPresetItemPool
    from randovania.games.dread.gui.preset_settings.dread_lights_tab import PresetDreadLights
    from randovania.games.dread.gui.preset_settings.dread_patches_chaos import PresetDreadChaos
    from randovania.games.dread.gui.preset_settings.dread_patches_tab import PresetDreadPatches
    from randovania.games.dread.gui.preset_settings.dread_teleporters_tab import PresetTeleportersDread
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    from randovania.gui.preset_settings.hints_tab import PresetHints
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetDreadGeneration,
        PresetHints,
        PresetLocationPool,
        PresetDreadGoal,
        DreadPresetItemPool,
        PresetTeleportersDread,
        PresetMetroidStartingArea,
        PresetDockRando,
        PresetDreadEnergy,
        PresetDreadPatches,
        PresetDreadLights,
        PresetDreadChaos,
    ]
