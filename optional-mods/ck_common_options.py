from typing import List, Optional

import gradio

from facefusion import state_manager, wording
from facefusion.uis import choices as uis_choices

COMMON_OPTIONS_CHECKBOX_GROUP: Optional[gradio.Checkboxgroup] = None
LOG_LEVEL_DROPDOWN: Optional[gradio.Dropdown] = None

def render() -> None:
	global COMMON_OPTIONS_CHECKBOX_GROUP, LOG_LEVEL_DROPDOWN

	common_options = []

	if state_manager.get_item('skip_download'):
		common_options.append('skip-download')
	if state_manager.get_item('keep_temp'):
		common_options.append('keep-temp')
	if state_manager.get_item('skip_audio'):
		common_options.append('skip-audio')

	COMMON_OPTIONS_CHECKBOX_GROUP = gradio.Checkboxgroup(
		label=wording.get('uis.common_options_checkbox_group'),
		choices=uis_choices.common_options,
		value=common_options
	)

	log_level = state_manager.get_item('log_level') or 'info'  # Default to 'info' if not set
	LOG_LEVEL_DROPDOWN = gradio.Dropdown(
		label=('log_level'),
		choices=['error', 'warn', 'info', 'debug'],
		value=log_level
	)

def listen() -> None:
	COMMON_OPTIONS_CHECKBOX_GROUP.change(update, inputs=COMMON_OPTIONS_CHECKBOX_GROUP)
	LOG_LEVEL_DROPDOWN.change(update_log_level, inputs=LOG_LEVEL_DROPDOWN)

def update(common_options: List[str]) -> None:
	skip_temp = 'skip-download' in common_options
	keep_temp = 'keep-temp' in common_options
	skip_audio = 'skip-audio' in common_options
	state_manager.set_item('skip_download', skip_temp)
	state_manager.set_item('keep_temp', keep_temp)
	state_manager.set_item('skip_audio', skip_audio)

def update_log_level(log_level: str) -> None:
	state_manager.set_item('log_level', log_level)
