import gradio

from facefusion import state_manager
from facefusion.uis.components import about, terminal


def pre_check() -> bool:
	return True


def pre_render() -> bool:
	return True


def render() -> gradio.Blocks:
	with gradio.Blocks() as layout:
		with gradio.Row():
			with gradio.Column(scale = 4):
				with gradio.Blocks():
					terminal.render()

	return layout


def listen() -> None:

	terminal.listen()



def run(ui : gradio.Blocks) -> None:
	ui.launch(favicon_path = 'facefusion.ico', inbrowser = state_manager.get_item('open_browser'))
