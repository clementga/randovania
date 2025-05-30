from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.gui.generated.preset_generation_ui import Ui_PresetGeneration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.base.logical_pickup_placement_configuration import LogicalPickupPlacementConfiguration
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PySide6 import QtWidgets

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetGeneration(PresetTab, Ui_PresetGeneration):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        # Game-specific Settings
        for w in self.game_specific_widgets:
            self.game_specific_layout.addWidget(w)

        # Item Placement
        signal_handling.on_checked(self.check_major_minor, self._persist_major_minor)
        signal_handling.on_checked(self.local_first_progression_check, self._persist_local_first_progression)

        for i, logical_placement_mode in enumerate(LogicalPickupPlacementConfiguration):
            self.logical_pickup_placement_combo.setItemData(i, logical_placement_mode)
        signal_handling.on_combo(self.logical_pickup_placement_combo, self._on_logical_pickup_placement_mode_changed)

        # Logic Settings
        self.dangerous_combo.setItemData(0, LayoutLogicalResourceAction.RANDOMLY)
        self.dangerous_combo.setItemData(1, LayoutLogicalResourceAction.LAST_RESORT)
        signal_handling.on_combo(self.dangerous_combo, self._on_dangerous_changed)

        signal_handling.on_checked(self.trick_level_minimal_logic_check, self._on_trick_level_minimal_logic_check)

        # Minimal Logic
        for w in [self.trick_level_minimal_logic_check, self.trick_level_minimal_logic_label, self.minimal_logic_line]:
            w.setVisible(game_description.minimal_logic is not None)
        if game_description.minimal_logic is not None:
            self.trick_level_minimal_logic_label.setText(
                self.trick_level_minimal_logic_label.text().format(
                    game_specific_text=game_description.minimal_logic.description
                )
            )

        # Development
        signal_handling.on_checked(
            self.check_if_beatable_after_base_patches_check,
            self._persist_bool_layout_field("check_if_beatable_after_base_patches"),
        )
        signal_handling.on_checked(
            self.consider_unsafe_check,
            self._persist_bool_layout_field("consider_possible_unsafe_resources"),
        )

        # Damage strictness
        self.damage_strictness_combo.setItemData(0, LayoutDamageStrictness.STRICT)
        self.damage_strictness_combo.setItemData(1, LayoutDamageStrictness.MEDIUM)
        self.damage_strictness_combo.setItemData(2, LayoutDamageStrictness.LENIENT)
        self.damage_strictness_combo.currentIndexChanged.connect(self._on_update_damage_strictness)

    def update_experimental_visibility(self):
        super().update_experimental_visibility()
        any_visible = any(w.isVisibleTo(self.game_specific_group) for w in self.game_specific_widgets)
        self.game_specific_group.setVisible(any_visible)

    def on_preset_changed(self, preset: Preset):
        layout = preset.configuration

        self.local_first_progression_check.setChecked(layout.first_progression_must_be_local)
        self.check_major_minor.setChecked(
            layout.available_locations.randomization_mode == RandomizationMode.MAJOR_MINOR_SPLIT
        )

        signal_handling.set_combo_with_value(self.logical_pickup_placement_combo, layout.logical_pickup_placement)

        self.check_if_beatable_after_base_patches_check.setChecked(layout.check_if_beatable_after_base_patches)
        self.consider_unsafe_check.setChecked(layout.consider_possible_unsafe_resources)

        self.trick_level_minimal_logic_check.setChecked(layout.trick_level.minimal_logic)
        signal_handling.set_combo_with_value(self.dangerous_combo, layout.logical_resource_action)

        signal_handling.set_combo_with_value(self.damage_strictness_combo, preset.configuration.damage_strictness)

    @classmethod
    def tab_title(cls) -> str:
        return "Generation"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._editor._game

    @property
    def game_specific_widgets(self) -> Iterable[QtWidgets.QWidget]:
        yield from []

    @property
    def experimental_settings(self) -> Iterable[QtWidgets.QWidget]:
        # Always hidden right now
        yield self.check_if_beatable_after_base_patches_check
        yield self.local_first_progression_check
        yield self.local_first_progression_label
        yield self.line_2

        yield self.experimental_generator_line
        yield self.consider_unsafe_line
        yield self.minimal_logic_line
        yield self.logical_pickup_placement_line
        yield self.logical_pickup_placement_combo
        yield self.logical_pickup_placement_label
        yield self.logical_pickup_placement_description
        yield self.consider_unsafe_check
        yield self.consider_unsafe_description

    def _persist_major_minor(self, value: bool):
        mode = RandomizationMode.MAJOR_MINOR_SPLIT if value else RandomizationMode.FULL
        with self._editor as editor:
            editor.available_locations = dataclasses.replace(editor.available_locations, randomization_mode=mode)

    def _persist_local_first_progression(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("first_progression_must_be_local", value)

    def _persist_logical_pickup_placement(self, value: LogicalPickupPlacementConfiguration):
        with self._editor as editor:
            editor.set_configuration_field("logical_pickup_placement", value)

    def _on_dangerous_changed(self, value: LayoutLogicalResourceAction):
        with self._editor as editor:
            editor.set_configuration_field("logical_resource_action", value)

    def _on_check_base_patches_changed(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("check_if_beatable_after_base_patches", value)

    def _on_trick_level_minimal_logic_check(self, state: bool):
        with self._editor as options:
            options.set_configuration_field(
                "trick_level", dataclasses.replace(options.configuration.trick_level, minimal_logic=state)
            )

    def _on_update_damage_strictness(self, new_index: int):
        with self._editor as editor:
            editor.layout_configuration_damage_strictness = self.damage_strictness_combo.currentData()

    def _on_logical_pickup_placement_mode_changed(self, logical_placement_config: LogicalPickupPlacementConfiguration):
        self._persist_logical_pickup_placement(logical_placement_config)
        self.logical_pickup_placement_description.setText(logical_placement_config.description)
