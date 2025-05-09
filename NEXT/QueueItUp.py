import gradio
from facefusion import state_manager
from facefusion.uis.components import about, age_modifier_options, common_options, deep_swapper_options, download, execution, execution_queue_count, execution_thread_count, expression_restorer_options, face_debugger_options, face_detector, face_editor_options, face_enhancer_options, face_landmarker, face_masker, face_selector, face_swapper_options, frame_colorizer_options, frame_enhancer_options, instant_runner, job_manager, job_runner, lip_syncer_options, memory, output, output_options, preview, processors, source, target, temp_frame, terminal, trim_frame, ui_workflow

import os
import re
import sys
import uuid
import time
import math
import json
import glob
import shutil
import tkinter as tk
import threading
import configparser
import subprocess
from tkinter import filedialog, font, Toplevel, messagebox, PhotoImage, Scrollbar, Button
from facefusion.processors import choices as processors_choices
from facefusion import choices as ff_choices
from facefusion.core import process_step
from facefusion.jobs import job_runner as runqueuedjobs
from facefusion import metadata
from facefusion import logger, filesystem
facefusion_version = metadata.get('version')
queueitup_version = 'Next'
ytext = True
debugging_enabled = False  # Default value, will be updated from settings
try:
	from facefusion.uis.components import target_options
except Exception as e:
	print ("yt extention not installed")
	ytext = False
def pre_check() -> bool:
	return True


def render() -> gradio.Blocks:
	global ADD_JOB_BUTTON, RUN_JOBS_BUTTON, SETTINGS_BUTTON
	with gradio.Blocks() as layout:
		with gradio.Row():
			with gradio.Column(scale = 3):
				with gradio.Blocks():
					ADD_JOB_BUTTON.render()
					EDIT_JOB_BUTTON.render()
					RUN_JOBS_BUTTON.render()
				with gradio.Blocks():
					processors.render()
				with gradio.Blocks():
					age_modifier_options.render()
				with gradio.Blocks():
					deep_swapper_options.render()
				with gradio.Blocks():
					expression_restorer_options.render()
				with gradio.Blocks():
					face_debugger_options.render()
				with gradio.Blocks():
					face_editor_options.render()
				with gradio.Blocks():
					face_enhancer_options.render()
				with gradio.Blocks():
					face_swapper_options.render()
				with gradio.Blocks():
					frame_colorizer_options.render()
				with gradio.Blocks():
					frame_enhancer_options.render()
				with gradio.Blocks():
					lip_syncer_options.render()
				with gradio.Blocks():
					output_options.render()
			with gradio.Column(scale = 2):
				with gradio.Blocks():
					ui_workflow.render()
					instant_runner.render()
					job_runner.render()
					job_manager.render()
				with gradio.Blocks():
					source.render()
				with gradio.Blocks():
					target.render()
				if ytext:
					with gradio.Blocks():
						target_options.render()
				with gradio.Blocks():
					output.render()
			with gradio.Column(scale = 7):
				with gradio.Blocks():
					preview.render()
				with gradio.Blocks():
					trim_frame.render()
				with gradio.Blocks():
					face_selector.render()
			with gradio.Column(scale = 3):
				with gradio.Blocks():
					face_masker.render()
				with gradio.Blocks():
					face_detector.render()
				with gradio.Blocks():
					face_landmarker.render()

		with gradio.Row():
			with gradio.Column(scale = 9):
				with gradio.Blocks():
					terminal.render()
		with gradio.Row():
			with gradio.Column(scale = 4):
				with gradio.Blocks():
					execution.render()
					execution_thread_count.render()
					execution_queue_count.render()
					memory.render()
			with gradio.Column(scale = 2):
				with gradio.Blocks():
					ABOUT.render()
					download.render()
					temp_frame.render()
					common_options.render()



	return layout


def listen() -> None:
	global EDIT_JOB_BUTTON
	ADD_JOB_BUTTON.click(assemble_queue)
	RUN_JOBS_BUTTON.click(execute_jobs)
	EDIT_JOB_BUTTON.click(edit_queue)
	processors.listen()
	age_modifier_options.listen()
	deep_swapper_options.listen()
	expression_restorer_options.listen()
	face_debugger_options.listen()
	face_editor_options.listen()
	face_enhancer_options.listen()
	face_swapper_options.listen()
	frame_colorizer_options.listen()
	frame_enhancer_options.listen()
	lip_syncer_options.listen()
	execution.listen()
	execution_thread_count.listen()
	execution_queue_count.listen()
	download.listen()
	memory.listen()
	temp_frame.listen()
	output_options.listen()
	source.listen()
	target.listen()
	if ytext:
		target_options.listen()
	output.listen()
	instant_runner.listen()
	job_runner.listen()
	job_manager.listen()
	terminal.listen()
	preview.listen()
	trim_frame.listen()
	face_selector.listen()
	face_masker.listen()
	face_detector.listen()
	face_landmarker.listen()
	common_options.listen()


def run(ui : gradio.Blocks) -> None:
	ui.launch(favicon_path = 'facefusion.ico', inbrowser = state_manager.get_item('open_browser'))

########
def assemble_queue():
	#global RUN_JOBS_BUTTON, ADD_JOB_BUTTON, jobs_queue_file, jobs, default_values, current_values, edit_queue_running 
	global jobs_queue_file, jobs, default_values, current_value  
	missing_paths = []
	if not state_manager.get_item('target_path'):
		missing_paths.append("target path")
	if not state_manager.get_item('output_path'):
		missing_paths.append("output path")

	if missing_paths:
		whats_missing = ", ".join(missing_paths)
		custom_print(f"{RED}Whoops!!!, you are missing {whats_missing}. Make sure you add {whats_missing} before clicking add job{ENDC}")
		return
	current_values = get_values_from_FF('current_values')

	differences = {}
	keys_to_skip = ['command', 'jobs_path', 'open_browser', 'download_providers', 'job_id', 'job_status', 'step_index', 'source_paths', 'target_path', 'output_path', 'source_pattern', 'target_pattern', 'output_pattern', 'ui_layouts', 'ui_workflow', 'config_path', 'force_download', 'skip_download', 'execution_queue_count', 'video_memory_strategy', 'system_memory_limit', 'execution_thread_count', 'execution_device_id']

	for key, current_value in current_values.items():
		if key in keys_to_skip:
			continue  # Skip these keys
		default_value = default_values.get(key)
		if current_value != default_value:
			if current_value is None:
				continue
			formatted_value = current_value
			if isinstance(current_value, list):
				formatted_value = ' '.join(map(str, current_value))
			elif isinstance(current_value, tuple):
				formatted_value = ' '.join(map(str, current_value))
			differences[key] = formatted_value

	output_path = current_values.get("output_path", "")
	# Split the path into the directory and the file extension
	path_without_ext, ext = os.path.splitext(output_path)  # UNUSED: path_without_ext is never used

	# Check if there's an extension to determine if it's a file path
	if ext:
		debug_print(output_path)
		output_path = os.path.dirname(output_path)
		debug_print("just fixed output path")
		debug_print(output_path)

	source_paths = current_values.get("source_paths", [])
	target_path = current_values.get("target_path", "")

	if source_paths is not None:
		cache_source_paths = copy_to_media_cache(source_paths)
		if isinstance(cache_source_paths, list):
			source_basenames = [os.path.basename(path) for path in cache_source_paths]
			source_name, _ = os.path.splitext(source_basenames[0])	# Take the first path's basename without extension
		else:
			source_basenames = os.path.basename(cache_source_paths)
			source_name, _ = os.path.splitext(source_basenames)	 # Handle single path correctly
		debug_print(f"{GREEN}Source file{ENDC} copied to Media Cache folder: {GREEN}{source_basenames}{ENDC}")

	cache_target_path = copy_to_media_cache(target_path)

	output_hash = str(uuid.uuid4())[:8]
	target_name, target_extension = os.path.splitext(os.path.basename(cache_target_path))
	output_extension = target_extension

	if source_paths:
		outputname = source_name + '-' + target_name
	else:
		outputname = target_name
	queueitup_job_id = outputname + '-' + output_hash
	full_output_path = os.path.join(output_path, queueitup_job_id + output_extension)

	# Construct the arguments string
	arguments = " ".join(f"--{key.replace('_', '-')} {value}" for key, value in differences.items() if value)
	if debugging:
		with open(os.path.join(working_dir, "arguments_values.txt"), "w") as file:
			file.write(json.dumps(arguments) + "\n")
	job_args = f"{arguments}"  # REDUNDANT: Unnecessary formatting as f-string 

	if source_paths == None:
		cache_source_paths = None
		source_name = None
	if isinstance(cache_source_paths, str):
		cache_source_paths = [cache_source_paths]
	string_processors = " + ".join(current_values['processors'])

	new_job = {
		"job_args": job_args,
		"status": "pending",
		"headless": "--headless",
		"processors": string_processors,
		"sourcecache": (cache_source_paths),  # UNNECESSARY: Extra parentheses not needed
		"source_name": (source_name),  # UNNECESSARY: Extra parentheses not needed
		"targetcache": (cache_target_path),  # UNNECESSARY: Extra parentheses not needed
		"target_name": (target_name),  # UNNECESSARY: Extra parentheses not needed
		"outputname": (outputname),  # UNNECESSARY: Extra parentheses not needed
		"output_extension": (output_extension),  # UNNECESSARY: Extra parentheses not needed
		"full_output_path": (full_output_path),  # UNNECESSARY: Extra parentheses not needed
		"output_path": (output_path),  # UNNECESSARY: Extra parentheses not needed
		"hash": (output_hash),  # UNNECESSARY: Extra parentheses not needed
		"id": (queueitup_job_id)  # UNNECESSARY: Extra parentheses not needed
	}

	if debugging:
		with open(os.path.join(working_dir, "job_args_values.txt"), "w") as file:
			for key, val in current_values.items():
				file.write(f"{key}: {val}\n")

	jobs = load_jobs(jobs_queue_file)
	jobs.append(new_job)
	create_grid_thumbnail(new_job)
	save_jobs(jobs_queue_file, jobs)
	load_jobs(jobs_queue_file)


def create_grid_thumbnail(job):
	# Creating grid thumbnails separately for source and target without using `parent`
	job_id_hash = job["id"]
	outputname = job["outputname"]
	job_args = job["job_args"]
	if not os.path.exists(thumbnail_dir):
		os.makedirs(thumbnail_dir)

	# Generate grid thumbnails for source files
	if job["sourcecache"]:
		thumb_source_paths = job["sourcecache"]
		num_images = len(thumb_source_paths)
		grid_size = math.ceil(math.sqrt(num_images))
		thumb_size = 200 // grid_size

		source_thumbnail_files = []
		for idx, file_path in enumerate(thumb_source_paths):
			thumbnail_path = os.path.join(thumbnail_dir, f"source_grid_{job_id_hash}_{idx}.png")
			# debug_print(f"Processing source file for thumbnail creation: {file_path}")
			if not os.path.exists(file_path):
				debug_print(f"Source file not found for thumbnail creation: {file_path}")
				continue
			if file_path.lower().endswith(('.mp3', '.wav', '.aac', '.flac')):
				audio_icon_path = os.path.join(thumbnail_dir, 'audioicon.png')
				cmd = [
					'ffmpeg', '-i', audio_icon_path,
					'-vf', f'scale={thumb_size}:{thumb_size}',
					'-vframes', '1',
					'-y', thumbnail_path
				]
			elif file_path.lower().endswith(('.jpg', '.webp', '.jpeg', '.png', '.bmp', '.gif', '.tiff')):
				cmd = [
					'ffmpeg', '-i', file_path,
					'-vf', f"""thumbnail,scale='if(gt(a,1),{thumb_size},-1)':'if(gt(a,1),-1,{thumb_size})',pad={thumb_size}:{thumb_size}:(ow-iw)/2:(oh-ih)/2:black""",
					'-vframes', '1',
					'-y', thumbnail_path
				]
			else:
				# For video or other formats, use a specific frame to create the thumbnail
				probe_cmd = [
					'ffmpeg', '-i', file_path,
					'-show_entries', 'format=duration',
					'-v', 'quiet', '-of', 'csv=p=0'
				]
				# debug_print(f"Running ffmpeg probe command for source: {' '.join(probe_cmd)}")
				result = subprocess.run(probe_cmd, capture_output=True, text=True)
				if result.returncode != 0:
					debug_print(f"Error running ffmpeg probe command for source: {result.stderr}")
					continue
				try:
					duration = float(result.stdout.strip())
				except ValueError:
					duration = 100
				seek_time = duration * 0.10
				cmd = [
					'ffmpeg', '-ss', str(seek_time), '-i', file_path,
					'-vf', f"""thumbnail,scale='if(gt(a,1),{thumb_size},-1)':'if(gt(a,1),-1,{thumb_size})',pad={thumb_size}:{thumb_size}:(ow-iw)/2:(oh-ih)/2:black""",
					'-vframes', '1',
					'-y', thumbnail_path
				]

			# Run ffmpeg command to generate the thumbnail
			# debug_print(f"Running ffmpeg command for source: {' '.join(cmd)}")
			result = subprocess.run(cmd, capture_output=True)
			if result.returncode != 0:
				debug_print(f"Error creating source thumbnail: {result.stderr}")
			else:
				source_thumbnail_files.append(thumbnail_path)

		# Create a grid thumbnail for source files using the generated thumbnails
		if len(source_thumbnail_files) > 0:
			source_list_file_path = os.path.join(thumbnail_dir, f'{job_id_hash}_source_input_list.txt')
			with open(source_list_file_path, 'w') as list_file:
				for thumb in source_thumbnail_files:
					list_file.write(f"file '{thumb}'\n")

			source_grid_thumb_path = os.path.join(thumbnail_dir, f"source_grid_{job_id_hash}.png")
			source_grid_cmd = [
				'ffmpeg',
				'-loglevel', 'error',
				'-f', 'concat', '-safe', '0', '-i', source_list_file_path,
				'-filter_complex', f'tile={grid_size}x{grid_size}:padding=2',
				'-y', source_grid_thumb_path
			]
			# debug_print(f"Running ffmpeg command for source grid thumbnail: {' '.join(source_grid_cmd)}")
			source_grid_result = subprocess.run(source_grid_cmd, capture_output=True)
			if source_grid_result.returncode != 0:
				debug_print(f"Error creating source grid: {source_grid_result.stderr}")

			# Cleanup individual thumbnails and list file after creating the source grid
			for file in source_thumbnail_files:
				filesystem.remove_file(file)
			filesystem.remove_file(source_list_file_path)

	# Generate grid thumbnails for target files
	if job["targetcache"]:
		thumb_target_path = job["targetcache"]
		target_thumbnail_files = []
		thumbnail_path = os.path.join(thumbnail_dir, f"target_grid_{job_id_hash}.png")
		# debug_print(f"Processing target file for thumbnail creation: {thumb_target_path}")
		thumb_size = 200
		if not os.path.exists(thumb_target_path):
			debug_print(f"Target file not found for thumbnail creation: {thumb_target_path}")
		else:
			# For video or other formats, determine frame using frame_number if available
			if not thumb_target_path.lower().endswith(('.jpg', '.webp', '.jpeg', '.png', '.bmp', '.gif', '.tiff')):
				# Extract frame number based on job arguments
				frame_number = None
				if '--reference-frame-number' in job_args:
					args_list = job_args.split()
					if '--reference-frame-number' in args_list:
						idx = args_list.index('--reference-frame-number')
						if idx + 1 < len(args_list):
							try:
								frame_number = int(args_list[idx + 1])
							except ValueError:
								frame_number = None
				if frame_number is not None:
					seek_time = frame_number
					cmd = [
						'ffmpeg', '-i', thumb_target_path,
						'-vf', f'select=eq(n\\,{frame_number}),scale=\'if(gt(a,1),{thumb_size},-1)\':\'if(gt(a,1),-1,{thumb_size})\',pad={thumb_size}:{thumb_size}:(ow-iw)/2:(oh-ih)/2:black',
						'-vframes', '1',
						'-y', thumbnail_path
					]
					
				else:
					# For video or other formats, use a specific frame to create the thumbnail
					probe_cmd = [
						'ffmpeg', '-i', file_path,
						'-show_entries', 'format=duration',
						'-v', 'quiet', '-of', 'csv=p=0'
					]
					# debug_print(f"Running ffmpeg probe command for source: {' '.join(probe_cmd)}")
					result = subprocess.run(probe_cmd, capture_output=True, text=True)

					try:
						duration = float(result.stdout.strip())
					except ValueError:
						duration = 100
					seek_time = duration * 0.10
					cmd = [
						'ffmpeg', '-ss', str(seek_time), '-i', thumb_target_path,
						'-vf', f'thumbnail,scale=\'if(gt(a,1),{thumb_size},-1)\':\'if(gt(a,1),-1,{thumb_size})\',pad={thumb_size}:{thumb_size}:(ow-iw)/2:(oh-ih)/2:black',
						'-vframes', '1',
						'-y', thumbnail_path
					]

			else:
				# If it's an image file
				cmd = [
					'ffmpeg', '-i', thumb_target_path,
					'-vf', f"""thumbnail,scale='if(gt(a,1),{thumb_size},-1)':'if(gt(a,1),-1,{thumb_size})',pad={thumb_size}:{thumb_size}:(ow-iw)/2:(oh-ih)/2:black""",
					'-vframes', '1',
					'-y', thumbnail_path
				]

			result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			target_thumbnail_files.append(thumbnail_path)


def refresh_listbox_if_open():
	if edit_queue_running:
		try:
			refresh_frame_listbox()
			debug_print(f"{YELLOW}DEBUG: Listbox refreshed{ENDC}")

			
		except Exception as e:
			print ("window not open will refresh queue on open")

def execute_jobs():
	global JOB_IS_RUNNING, JOB_IS_EXECUTING, CURRENT_JOB_NUMBER, jobs_queue_file, jobs
	load_jobs(jobs_queue_file)
	count_existing_jobs()
	if not PENDING_JOBS_COUNT + JOB_IS_RUNNING > 0:
		custom_print(f"{RED}Whoops!!!, {YELLOW}There are {PENDING_JOBS_COUNT} Job(s) queued.{ENDC} Add a job to the queue before pressing Run Jobs.")
		return
	if PENDING_JOBS_COUNT + JOB_IS_RUNNING > 0 and JOB_IS_RUNNING:
		custom_print(f"{RED}Whoops {YELLOW}a Job is already executing, with {PENDING_JOBS_COUNT} more job(s) waiting to be processed. {RED}You don't want more than one job running at the same time your GPU can't handle that,{YELLOW}\n You just need to click add job if jobs are already running, and the job will be placed in line for execution. you can edit the job order with Edit Queue button{ENDC}")
		return
	jobs = load_jobs(jobs_queue_file)
	JOB_IS_RUNNING = 1
	CURRENT_JOB_NUMBER = 0
	first_pending_job = next((job for job in jobs if job['status'] == 'pending'), None)
	jobs = [job for job in jobs if job != first_pending_job]
	# Change status to 'executing' and add it back to the jobs
	first_pending_job['status'] = 'executing'
	jobs.append(first_pending_job)
	save_jobs(jobs_queue_file, jobs)

	while True:
		if not first_pending_job['status'] == 'executing':
			break
		current_run_job = first_pending_job
		current_run_job['headless'] = '--headless'
		count_existing_jobs()
		JOB_IS_EXECUTING = 1
		CURRENT_JOB_NUMBER += 1
		# custom_print(f"{BLUE}Starting Job #{GREEN} {CURRENT_JOB_NUMBER}{ENDC}")
		printjobtype = current_run_job['processors']
		custom_print(f"{BLUE}Executing Job # {CURRENT_JOB_NUMBER} of {CURRENT_JOB_NUMBER + PENDING_JOBS_COUNT}	{ENDC}")

		if not os.path.exists(current_run_job['output_path']):
			os.makedirs(current_run_job['output_path'])
		source_basenames = ""
		if isinstance(current_run_job['sourcecache'], list):
			source_basenames = f"with Source Media {', '.join(os.path.basename(path) for path in current_run_job['sourcecache'])}"
		elif current_run_job['sourcecache']:
			source_basenames = f"with Source Media {os.path.basename(current_run_job['sourcecache'])}"
		target_filetype, orig_video_length, output_video_length, output_dimensions, orig_dimensions = get_target_info(current_run_job['targetcache'], current_run_job)
		if target_filetype == 'Video':
			custom_print(f"{BLUE}Job #{CURRENT_JOB_NUMBER} will be doing {YELLOW}{printjobtype}{ENDC} - {GREEN}{source_basenames}\n{YELLOW} to -> the Target {orig_video_length} {orig_dimensions} {target_filetype} {GREEN}{os.path.basename(current_run_job['targetcache'])}{ENDC}, \n which will be saved in the folder {GREEN}{current_run_job['output_path']}{ENDC}")
		else:
			custom_print(f"{BLUE}Job #{CURRENT_JOB_NUMBER} will be doing {YELLOW}{printjobtype}{ENDC} - {GREEN}{source_basenames}\n{YELLOW} to -> the Target {orig_dimensions} {target_filetype} {GREEN}{os.path.basename(current_run_job['targetcache'])}{ENDC}, \n which will be saved in the folder {GREEN}{current_run_job['output_path']}{ENDC}")

		RUN_job_args(current_run_job)  # OPTIMIZATION: This function could be inlined since it's only called once
		if current_run_job['status'] == 'failed':
			custom_print(f"{BLUE}Job # {CURRENT_JOB_NUMBER} {RED} failed. Please check the validity of {source_basenames} and {RED}{os.path.basename(current_run_job['targetcache'])}.\n {BLUE}{PENDING_JOBS_COUNT} jobs remaining, pausing 1 second before starting next job{ENDC}")
		else:
			custom_print(f"{BLUE}Job # {CURRENT_JOB_NUMBER} {GREEN} completed successfully {BLUE}{PENDING_JOBS_COUNT} jobs remaining, pausing 1 second before starting next job{ENDC}")

		JOB_IS_EXECUTING = 0  # Reset the job execution flag
		time.sleep(1)
		jobs = load_jobs(jobs_queue_file)
		jobs = [job for job in jobs if job['status'] != 'executing']
		jobs.append(current_run_job)
		just_save_jobs(jobs_queue_file, jobs)

		# Reset current_run_job to None, indicating it's no longer holding a job
		current_run_job = None
		# Find the first pending job
		jobs = load_jobs(jobs_queue_file)

		first_pending_job = next((job for job in jobs if job['status'] == 'pending'), None)

		if first_pending_job:
			jobs = [job for job in jobs if job != first_pending_job]
			current_run_job = first_pending_job.copy()
			current_run_job['status'] = 'executing'
			jobs.append(current_run_job)
			first_pending_job = current_run_job

			save_jobs(jobs_queue_file, jobs)
		else:#no more pending jobs
			custom_print(f"{BLUE}a total of {CURRENT_JOB_NUMBER} Jobs have completed processing,{ENDC}...... {GREEN}the Queue is now empty, {BLUE}Feel Free to QueueItUp some more..{ENDC}")
			current_run_job = None
			first_pending_job = None
			break
	JOB_IS_RUNNING = 0
	check_for_unneeded_media_cache
	save_jobs(jobs_queue_file, jobs)



# Initialize the setini variable in the global scope
setini = None


def load_settings():
	config = configparser.ConfigParser()
	if not os.path.exists(settings_path):
		config['QueueItUp'] = {
			'keep_completed_jobs': 'True',
			'debugging': 'False'
		}

		with open(settings_path, 'w') as configfile:
			config.write(configfile)
	config.read(settings_path)
	if 'QueueItUp' not in config.sections():
		config['QueueItUp'] = {
			'keep_completed_jobs': 'True',
			'debugging': 'False'
		}
		with open(settings_path, 'w') as configfile:
			config.write(configfile)
	
	# Handle case where debugging option doesn't exist in config yet
	if not config.has_option('QueueItUp', 'debugging'):
		config.set('QueueItUp', 'debugging', 'False')
		with open(settings_path, 'w') as configfile:
			config.write(configfile)
	
	settings = {
		'keep_completed_jobs': config.getboolean('QueueItUp', 'keep_completed_jobs'),
		'debugging': config.getboolean('QueueItUp', 'debugging')
	}
	return settings

def save_settings(settings):
	config = configparser.ConfigParser()
	config.read(settings_path)
	if 'QueueItUp' not in config.sections():
		config.add_section('QueueItUp')
	if 'misc' not in config.sections():
		config.add_section('misc')
	config.set('QueueItUp', 'keep_completed_jobs', str(settings['keep_completed_jobs']))
	config.set('QueueItUp', 'debugging', str(settings['debugging']))
	with open(settings_path, 'w') as configfile:
		config.write(configfile)

def initialize_settings():
	settings = load_settings()
	global keep_completed_jobs, debugging_enabled
	keep_completed_jobs = settings['keep_completed_jobs']
	debugging_enabled = settings['debugging']

def queueitup_settings():
	def create_settings_window():
		global setini
		settings = load_settings()
		original_keep_completed_jobs_value = settings['keep_completed_jobs']

		def save_and_close():
			global setini
			settings['keep_completed_jobs'] = keep_completed_jobs_var.get()
			settings['debugging'] = debugging_var.get()
			save_settings(settings)
			initialize_settings()

			if original_keep_completed_jobs_value and not settings['keep_completed_jobs']:
				jobs_to_delete("completed")

			if setini is not None:
				setini.destroy()
				setini = None

		def on_closing():
			global setini
			if setini is not None:
				setini.destroy()
				setini = None

		if setini is not None and setini.winfo_exists():
			setini.lift()
			setini.focus_force()
			return

		if root and root.winfo_exists():
			setini = Toplevel(root)
		else:
			setini = tk.Tk()

		setini.title("QueueItUp Settings")
		setini.protocol("WM_DELETE_WINDOW", on_closing)

		window_width = 300
		window_height = 200  # Increased height to accommodate new option
		screen_width = setini.winfo_screenwidth()
		screen_height = setini.winfo_screenheight()
		position_top = int(screen_height / 2 - window_height / 2)
		position_right = int(screen_width / 2 - window_width / 2)

		setini.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
		setini.attributes('-topmost', True)

		keep_completed_jobs_var = tk.BooleanVar(value=settings['keep_completed_jobs'])
		debugging_var = tk.BooleanVar(value=settings['debugging'])

		tk.Label(setini, text="Keep Completed Jobs:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
		tk.Checkbutton(setini, variable=keep_completed_jobs_var).grid(row=1, column=1, padx=10, pady=5)
		
		tk.Label(setini, text="Enable Debugging:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
		tk.Checkbutton(setini, variable=debugging_var).grid(row=2, column=1, padx=10, pady=5)

		tk.Button(setini, text="Save", command=save_and_close).grid(row=3, column=0, columnspan=2, pady=10)

		setini.mainloop()

	if root and root.winfo_exists():
		root.after(0, create_settings_window)
	else:
		create_settings_window()


def edit_queue():
	global root, edit_queue_running, frame, canvas, jobs_queue_file, jobs, job, thumbnail_dir, working_dir, pending_jobs_var, PENDING_JOBS_COUNT  # UNNECESSARY: 'job' is declared as global but never used in this function
	# Prevent multiple instances of the edit queue window
	if edit_queue_running:
		debug_print(f"{RED}DEBUG: edit_queue_running is True, returning early{ENDC}")
		return	# Prevent multiple instances of the window
		
	edit_queue_running = True
	debug_print(f"{BLUE}DEBUG: Set edit_queue_running to True{ENDC}")
	
	try:
		# Create the main Tkinter window
		root = tk.Tk()
		debug_print(f"{BLUE}DEBUG: Created root Tk instance{ENDC}")
		
		def on_window_close_internal():
			global root, edit_queue_running, pending_jobs_var, frame, canvas
			debug_print(f"{BLUE}DEBUG: Window close event triggered{ENDC}")
			
			# Clean up resources to prevent memory leaks and threading issues
			pending_jobs_var = None
			frame = None
			canvas = None
			
			if root:
				try:
					root.quit()
					root.destroy()
				except:
					pass
				root = None
			
			debug_print(f"{BLUE}DEBUG: Window closed and resources cleaned up{ENDC}")
			edit_queue_running = False
			debug_print(f"{BLUE}DEBUG: edit_queue_running = False{ENDC}")

		root.protocol("WM_DELETE_WINDOW", on_window_close_internal)
		
		# Load jobs and set up the window properties
		jobs = load_jobs(jobs_queue_file)
		PENDING_JOBS_COUNT = count_existing_jobs()
		root.geometry('1200x800')
		root.title("Edit Queued Jobs")
		root.lift()
		root.attributes('-topmost', True)
		root.after_idle(root.attributes, '-topmost', False)
		scrollbar = Scrollbar(root, orient="vertical")
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

		canvas = tk.Canvas(root)
		canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		# EFFICIENCY NOTE: This two-way binding is essential for proper scrolling behavior
		canvas.configure(yscrollcommand=scrollbar.set)
		scrollbar.configure(command=canvas.yview)
		
		# Create a frame inside the canvas to hold all the job items
		frame = tk.Frame(canvas)
		canvas_window = canvas.create_window((0, 0), window=frame, anchor='nw')
		
		# Configure the canvas to adjust its scroll region when the frame size changes
		# This ensures that the scrollbar reflects the actual content size
		def on_frame_configure(event):
			canvas.configure(scrollregion=canvas.bbox("all"))
		frame.bind('<Configure>', on_frame_configure)
		
		# Make the canvas window width match the canvas width when resized
		# This ensures the content spans the full width of the canvas
		def on_canvas_configure(event):
			canvas.itemconfig(canvas_window, width=event.width)
		canvas.bind('<Configure>', on_canvas_configure)
		
		# Enable mousewheel scrolling for the canvas
		# EFFICIENCY NOTE: The calculation for scroll speed could be adjusted based on OS
		def _on_mousewheel(event):
			canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
		canvas.bind_all("<MouseWheel>", _on_mousewheel)

		# Create fonts for UI elements after the root window is initialized
		# EFFICIENCY NOTE: Creating fonts is resource-intensive; consider caching these
		try:
			custom_font = font.Font(root=root, family="Helvetica", size=12, weight="bold")
			bold_font = font.Font(root=root, family="Helvetica", size=12, weight="bold")
		except Exception as e:
			debug_print(f"{RED}DEBUG: Could not create fonts: {str(e)}{ENDC}")
			# Fallback to default fonts if custom fonts can't be created
			custom_font = None
			bold_font = None
		
		# Create a StringVar to hold the text for the pending jobs button
		debug_print(f"{BLUE}DEBUG: Creating pending_jobs_var{ENDC}")
		pending_jobs_var = tk.StringVar(master=root)
		pending_jobs_var.set(f"Delete {PENDING_JOBS_COUNT} Pending Jobs")
		close_button = tk.Button(root, text="Close Window", command=on_window_close_internal, font=custom_font)
		close_button.pack(pady=5)

		settings_button2 = tk.Button(root, text="queueitup_settings", command=queueitup_settings, font=custom_font)
		settings_button2.pack(pady=5)
		refresh_button = tk.Button(root, text="Refresh View", command=refresh_frame_listbox, font=custom_font)
		refresh_button.pack(pady=5)

		run_jobs_button = tk.Button(root, text="Run Pending Jobs", command=run_jobs_click, font=custom_font)
		run_jobs_button.pack(pady=5)
		pending_jobs_button = tk.Button(root, textvariable=pending_jobs_var, command=lambda: jobs_to_delete("pending"), font=custom_font)
		pending_jobs_button.pack(pady=5)

		missing_jobs_button = tk.Button(root, text="Delete Missing ", command=lambda: jobs_to_delete("missing"), font=custom_font)
		missing_jobs_button.pack(pady=5)

		archived_jobs_button = tk.Button(root, text="Delete archived ", command=lambda: jobs_to_delete("archived"), font=custom_font)
		archived_jobs_button.pack(pady=5)

		failed_jobs_button = tk.Button(root, text="Delete Failed", command=lambda: jobs_to_delete("failed"), font=custom_font)
		failed_jobs_button.pack(pady=5)

		completed_jobs_button = tk.Button(root, text="Delete Completed", command=lambda: jobs_to_delete("completed"), font=custom_font)
		completed_jobs_button.pack(pady=5)

		root.update_idletasks() #is this necessary 

		def delayed_refresh():
			debug_print(f"{BLUE}DEBUG: Calling refresh_frame_listbox{ENDC}")
			try:
				# Populate the job list
				refresh_frame_listbox()
				# Update the scroll region after populating the frame to ensure proper scrolling
				canvas.configure(scrollregion=canvas.bbox("all"))
			except Exception as e:
				debug_print(f"{RED}DEBUG: Error in delayed_refresh: {str(e)}{ENDC}")
		
		# Schedule the refresh to happen after a short delay
		# EFFICIENCY NOTE: The 100ms delay is somewhat arbitrary and could be tuned
		root.after(100, delayed_refresh)

		# Start the Tkinter event loop
		debug_print(f"{BLUE}DEBUG: Starting mainloop{ENDC}")
		root.mainloop()
		debug_print(f"{BLUE}DEBUG: Mainloop finished, cleaning up{ENDC}")
	except Exception as e:
		# Catch and log any exceptions that occur during window creation/operation
		debug_print(f"{RED}DEBUG: Exception in edit_queue: {str(e)}{ENDC}")
		import traceback
		traceback.print_exc()
	finally:
		# Ensure resources are cleaned up even if an exception occurs
		edit_queue_running = False
		pending_jobs_var = None
		frame = None
		canvas = None
		if root is not None:  # REDUNDANT: This cleanup code duplicates what's in on_window_close_internal
			try:
				if root.winfo_exists():
					root.quit()
					root.destroy()
			except:
				pass
			root = None

def run_jobs_click():
	global edit_queue_running, root  # UNUSED: edit_queue_running and root are declared but not used in this function
	debug_print(f"{BLUE}DEBUG: run_jobs_click called{ENDC}")
	
	save_jobs(jobs_queue_file, jobs)
	threading.Thread(target=execute_jobs).start()  # Run execute_jobs in a separate thread

def clone_job(job):
	clonebaseid = job['id']
	clonedjob = job.copy()	# Copy the existing job to preserve other attributes
	update_paths(clonedjob, "", "")
	create_grid_thumbnail(clonedjob)
	jobs = load_jobs(jobs_queue_file)
	original_index = jobs.index(job)  # Find the index of the original job
	jobs.insert(original_index + 1, clonedjob)	# Insert the cloned job right after the original job
	save_jobs(jobs_queue_file, jobs)
	custom_print(f"{YELLOW} The Job {clonebaseid} Was Cloned{ENDC}")	

def batch_job(job):
	target_filetype = None
	source_or_target = None
	if isinstance(job['sourcecache'], str):
		job['sourcecache'] = [job['sourcecache']]
	current_extension = job['targetcache'].lower().rsplit('.', 1)[-1]
	if current_extension in ['jpg', 'jpeg', 'png', 'webp']:
		target_filetype = 'Image'
	elif current_extension in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
		target_filetype = 'Video'

	def on_use_source():
		nonlocal source_or_target
		source_or_target = 'target'
		dialog.destroy()
		open_file_dialog()

	def on_use_target():
		nonlocal source_or_target
		if job['sourcecache']:
			source_or_target = 'source'
			if any(ext in src.lower() for ext in ['.mp3', '.wav', '.aac'] for src in job['sourcecache']):
				messagebox.showinfo("BatchItUp Error", "Sorry, BatchItUp cannot clone lipsync jobs yet.")
				dialog.destroy()
				return
			if len(job['sourcecache']) > 1:
				source_filenames = [os.path.basename(src) for src in job['sourcecache']]
				proceed = messagebox.askyesno(
					"BatchItUp Multiple Faces",
					f"Your current source contains multiple faces ({', '.join(source_filenames)}). BatchItUp cannot create multiple target {target_filetype} jobs while still maintaining multiple source faces. "
					f"If you click 'Yes' to proceed, you will get 1 target {target_filetype} for each source face you select in the next file dialog, but you can use the edit queue window "
					f"to add more source faces to each job created after BatchItUp has created them. Do you want to proceed?"
				)
				if not proceed:
					dialog.destroy()
					return
		else:
			source_or_target == 'target'
			file_types = [('Image files', '*.jpg *.jpeg *.webp *.png')] if target_filetype == 'Image' else [('Video files', '*.mp4 *.avi *.webm *.mov *.mkv')]
			selected_paths = filedialog.askopenfilenames(
				title="Select Multiple sources for BatchItUp to make multiple cloned jobs using each File",
				filetypes=file_types
			)
			if selected_paths:
				batchbasename = os.path.basename(job['targetcache'])
				batchbase = 'Target'
				jobs = load_jobs(jobs_queue_file)
				original_index = jobs.index(job)  # Find the index of the original job
				for path in selected_paths:
					add_new_job = job.copy()  # Copy the existing job to preserve other attributes
					path = copy_to_media_cache(path)
					add_new_job['targetcache'] = path
					update_paths(add_new_job, path, 'target')
					# update_paths(add_new_job, path, 'outputpath')
					debug_print(f"{YELLOW} target - {GREEN}{add_new_job['targetcache']}{YELLOW} copied to temp media cache dir{ENDC}")
					original_index += 1	 # Increment the index for each new job
					jobs.insert(original_index, add_new_job)  # Insert the new job right after the original job
					create_grid_thumbnail(add_new_job)
					save_jobs(jobs_queue_file, jobs)
				
				custom_print(f"{YELLOW} The {batchbase} {batchbasename} was used to create Batched Jobs{ENDC}")

		dialog.destroy()
		open_file_dialog()

	def open_file_dialog():
		selected_paths = []
		if source_or_target == 'source':
			batchbasename = os.path.basename(job['targetcache'])
			batchbase = 'Target'
			selected_paths = filedialog.askopenfilenames(
				title="Select Multiple targets for BatchItUp to make multiple cloned jobs using each File",
				filetypes=[('Image files', '*.jpg *.jpeg  *.webp *.png')]
			)
		elif source_or_target == 'target':
			batchbasename = 'media'
			batchbase = 'Source'
			file_types = [('Image files', '*.jpg *.jpeg *.webp *.png')] if target_filetype == 'Image' else [('Video files', '*.mp4 *.avi *.webm *.mov *.mkv')]
			selected_paths = filedialog.askopenfilenames(
				title="Select Multiple sources for BatchItUp to make multiple cloned jobs using each File",
				filetypes=file_types
			)
		if selected_paths:
			jobs = load_jobs(jobs_queue_file)
			original_index = jobs.index(job)  # Find the index of the original job
			for path in selected_paths:
				add_new_job = job.copy()  # Copy the existing job to preserve other attributes
				path = copy_to_media_cache(path)
				add_new_job[source_or_target + 'cache'] = path
				update_paths(add_new_job, path, source_or_target)
				debug_print(f"{YELLOW}{source_or_target} - {GREEN}{add_new_job[source_or_target + 'cache']}{YELLOW} copied to temp media cache dir{ENDC}")
				original_index += 1	 # Increment the index for each new job
				jobs.insert(original_index, add_new_job)  # Insert the new job right after the original job
				create_grid_thumbnail(add_new_job)
				save_jobs(jobs_queue_file, jobs)
			# save_jobs(jobs_queue_file, jobs)
			custom_print(f"{YELLOW} The {batchbase} {batchbasename} was used to create Batched Jobs{ENDC}")
			# print_existing_jobs()
	dialog = tk.Toplevel()
	dialog.withdraw()
	if job['sourcecache']:
		source_filenames = [os.path.basename(src) for src in job['sourcecache']]
		message = (
			f"Welcome to the BatchItUp feature. Here you can add multiple batch jobs with just a few clicks."
			f"Click the 'Use Source' button to select as many target {target_filetype}s as you like and BatchItUp will create a job for each {target_filetype} "
			f"using {', '.join(source_filenames)} as the source image(s), OR you can Click 'Use Target' to select as many Source Images as you like and BatchItUp will "
			f"create a job for each source image using {os.path.basename(job['targetcache'])} as the target {target_filetype}."
		)

	dialog.deiconify()
	dialog.geometry("500x300")
	dialog.title("BatchItUp")

	if job['sourcecache']:
		label = tk.Label(dialog, text=message, wraplength=450, justify="left")
		label.pack(pady=20)

	button_frame = tk.Frame(dialog)
	button_frame.pack(pady=10)
	if job['sourcecache']:
		use_source_button = tk.Button(button_frame, text="Use Source", command=on_use_source)
		use_source_button.pack(side="left", padx=10)

	use_target_button = tk.Button(button_frame, text="Use Target", command=on_use_target)
	use_target_button.pack(side="left", padx=10)

	dialog.mainloop()


def update_job_listbox():
	global frame, canvas, jobs, thumbnail_dir
	debug_print(f"{BLUE}DEBUG: update_job_listbox called{ENDC}")
	update_counters()
	
	try:
		custom_font = font.Font(family="Helvetica", size=12, weight="bold")  # OPTIMIZATION: These fonts could be created once and reused instead of recreating them each time
		bold_font = font.Font(family="Helvetica", size=12, weight="bold")
		debug_print(f"{BLUE}DEBUG: Created fonts successfully{ENDC}")

		if frame.winfo_exists():
			debug_print(f"{BLUE}DEBUG: Frame exists, updating job list{ENDC}")
			
			jobs = load_jobs(jobs_queue_file)  
			count_existing_jobs()
			for widget in frame.winfo_children():
				widget.destroy()
			
			debug_print(f"{BLUE}DEBUG: Processing {len(jobs)} jobs{ENDC}")
			for index, job in enumerate(jobs):
				if job['sourcecache']:
					source_cache_path = job['sourcecache'] if isinstance(job['sourcecache'], list) else [job['sourcecache']]
					source_mediacache_exists = all(os.path.exists(os.path.normpath(source)) for source in source_cache_path)
				target_cache_path = job['targetcache'] if isinstance(job['targetcache'], str) else job['targetcache'][0]
				target_mediacache_exists = os.path.exists(os.path.normpath(target_cache_path))
				bg_color = 'SystemButtonFace'
				
				# Rest of the function remains unchanged
				if job['status'] == 'failed':
					bg_color = 'red'
				if job['status'] == 'executing':
					bg_color = 'black'
				if job['status'] == 'completed':
					bg_color = 'goldenrod'
				if job['status'] == 'editing':
					bg_color = 'green'
				if job['status'] == 'pending':
					bg_color = 'SystemButtonFace'
				if not job['status'] == 'completed':
					job_id_hash = job['id']
					if job['sourcecache'] and not source_mediacache_exists:
						debug_print(f"source mediacache {source_cache_path} is missing ")
						job['status'] = 'missing'
						remove_old_grid(job_id_hash, 'source')
						bg_color = 'red'
					if not target_mediacache_exists:
						debug_print(f"target mediacache {target_cache_path} is missing ")
						job['status'] = 'missing'
						remove_old_grid(job_id_hash, 'target')
						bg_color = 'red'
				if job['status'] == 'missing':
					if job['sourcecache'] and source_mediacache_exists and target_mediacache_exists:
						job['status'] = 'pending'
						bg_color = 'SystemButtonFace'
					if not job['sourcecache'] and target_mediacache_exists:
						job['status'] = 'pending'
						bg_color = 'SystemButtonFace'
				if job['status'] == 'archived':
					bg_color = 'brown'
				job_frame = tk.Frame(frame, borderwidth=2, relief='groove', background=bg_color)
				job_frame.pack(fill='x', expand=True, padx=5, pady=5)
				move_job_frame = tk.Frame(job_frame)
				move_job_frame.pack(side='left', fill='x', padx=5)
				move_top_button = tk.Button(move_job_frame, text=" Move to Top ", command=lambda idx=index, j=job: move_job_to_top(idx))
				move_top_button.pack(side='top', fill='y')
				move_up_button = tk.Button(move_job_frame, text=" Move Up ", command=lambda idx=index, j=job: move_job_up(idx))
				move_up_button.pack(side='top', fill='y')
				move_down_button = tk.Button(move_job_frame, text=" Move Down ", command=lambda idx=index, j=job: move_job_down(idx))
				move_down_button.pack(side='top', fill='y')
				move_bottom_button = tk.Button(move_job_frame, text="Move to Bottom", command=lambda idx=index, j=job: move_job_to_bottom(idx))
				move_bottom_button.pack(side='top', fill='y')

				source_frame = tk.Frame(job_frame)
				source_frame.pack(side='left', fill='x', padx=5)
				job_id_hash = job['id']
				source_thumbnail_path = os.path.join(thumbnail_dir, f"source_grid_{job_id_hash}.png")

				if os.path.exists(source_thumbnail_path):
					source_photo_image = PhotoImage(file=source_thumbnail_path)
					source_button = Button(source_frame, image=source_photo_image, command=lambda ft='source', j=job: select_job_file(source_frame, j, ft))
					source_button.image = source_photo_image
					source_button.pack(side='left', padx=5)
				elif job['sourcecache']:
					source_button = create_job_thumbnail(source_frame, job, source_or_target='source')
					if source_button:
						source_button.pack(side='left', padx=5)
					else:
						debug_print("Failed to create source button.")

				action_frame = tk.Frame(job_frame)
				action_frame.pack(side='left', fill='x', padx=5)

				arrow_label = tk.Label(action_frame, text=f"{job['status']}\n\u27A1", font=bold_font)
				if job['status'] != 'pending':
					arrow_label.bind("<Button-1>", lambda event, j=job: make_job_pending(j))
				arrow_label.pack(side='top', padx=5)

				output_path_button = tk.Button(action_frame, text="Output Path", command=lambda j=job: output_path_job(j))
				output_path_button.pack(side='top', padx=2)

				delete_button = tk.Button(action_frame, text=" Delete ", command=lambda j=job: delete_job(j))
				delete_button.pack(side='top', padx=2)

				button_text = "Un-Archive" if job['status'] == "archived" else "Archive"
				archive_button = tk.Button(action_frame, text=button_text, command=lambda j=job: archive_job(j))
				archive_button.pack(side='top', padx=2)

				clone_job_button = tk.Button(action_frame, text="Clone Job", command=lambda j=job: clone_job(j))
				clone_job_button.pack(side='top', padx=2)

				batch_button = tk.Button(action_frame, text="BatchItUp", command=lambda j=job: batch_job(j))
				batch_button.pack(side='top', padx=2)

				target_frame = tk.Frame(job_frame)
				target_frame.pack(side='left', fill='x', padx=5)

				target_thumbnail_path = os.path.join(thumbnail_dir, f"target_grid_{job_id_hash}.png")
				if os.path.exists(target_thumbnail_path):
					target_photo_image = PhotoImage(file=target_thumbnail_path)
					target_button = Button(target_frame, image=target_photo_image, command=lambda ft='target', j=job: select_job_file(target_frame, j, ft))
					target_button.image = target_photo_image
					target_button.pack(side='left', padx=5)
				else:
					target_button = create_job_thumbnail(target_frame, job, source_or_target='target')
					if target_button:
						target_button.pack(side='left', padx=5)
					else:
						debug_print("Failed to create target button.")

				argument_frame = tk.Frame(job_frame)
				argument_frame.pack(side='left', fill='x', padx=5)

				argument_button = tk.Button(argument_frame, text="EDIT JOB ARGUMENTS", wraplength=325, justify='center')
				argument_button.pack(side='bottom', padx=5, fill='x', expand=False)
				argument_button.bind("<Button-1>", lambda event, j=job: edit_job_arguments_text(j))

			debug_print(f"{BLUE}DEBUG: update_job_listbox completed successfully{ENDC}")
	except Exception as e:
		debug_print(f"{RED}DEBUG: Exception in update_job_listbox: {str(e)}{ENDC}")
		import traceback
		traceback.print_exc()


def refresh_frame_listbox():
	global jobs
	debug_print(f"{BLUE}DEBUG: refresh_frame_listbox called{ENDC}")
	
	try:
		# Define a priority order for job statuses to determine sorting order
		# Lower numbers = higher priority in the list
		status_priority = {'editing': 0, 'executing': 1, 'pending': 2, 'failed': 3, 'missing': 4, 'completed': 5, 'archived': 6}
		
		jobs = load_jobs(jobs_queue_file)
		
		jobs.sort(key=lambda x: status_priority.get(x['status'], 6))
	
		update_job_listbox()
		debug_print(f"{BLUE}DEBUG: refresh_frame_listbox completed with UI update{ENDC}")
	except Exception as e:
		debug_print(f"{RED}DEBUG: Exception in refresh_frame_listbox: {str(e)}{ENDC}")
		import traceback
		traceback.print_exc()

def refresh_buttonclick():
	save_jobs(jobs_queue_file, jobs)
	
def make_job_pending(job):
	job['status'] = 'pending'
	custom_print(f"{YELLOW}A Job Status was changed to pending{ENDC}")
	save_jobs(jobs_queue_file, jobs)
	# print_existing_jobs()
	
	
def jobs_to_delete(jobstatus):
	global jobs
	jobs = load_jobs(jobs_queue_file)
	for job in jobs:
		if job['status'] == jobstatus:
			job_id_hash = job['id']
			remove_old_grid(job_id_hash, source_or_target = 'source')
			remove_old_grid(job_id_hash, source_or_target = 'target')
	jobs = [job for job in jobs if job['status'] != jobstatus]
	save_jobs(jobs_queue_file, jobs)
	custom_print(f"{YELLOW}All {jobstatus} Jobs have been Deleted{ENDC}")
	check_for_unneeded_media_cache
	# print_existing_jobs()

def remove_old_grid(job_id_hash, source_or_target):
	image_ref_key = f"{source_or_target}_grid_{job_id_hash}.png"
	grid_thumb_path = os.path.join(thumbnail_dir, image_ref_key)
	filesystem.remove_file(grid_thumb_path)
	check_for_unneeded_thumbnail_cache

def archive_job(job):
	if job['status'] == 'archived':
		job['status'] = 'pending'
		custom_print(f"{YELLOW} Job Un-Archived - {GREEN}{job['id']} {ENDC}")
	else:
		job['status'] = 'archived'
		custom_print(f"{YELLOW} Job Archived - {GREEN}{job['id']}{ENDC}")
	save_jobs(jobs_queue_file, jobs)
	# print_existing_jobs()

def output_path_job(job):
	selected_path = filedialog.askdirectory(title="Select A New Output Path for this Job")

	if selected_path:
		formatted_path = selected_path.replace('/', '\\')
		job['output_path'] = formatted_path
		update_paths(job, formatted_path, 'outputpath')
	save_jobs(jobs_queue_file, jobs)

def delete_job(job):
	job['status'] = ('deleting')
	job_id_hash = job['id']
	jobs.remove(job)
	remove_old_grid(job_id_hash, source_or_target = 'source')
	remove_old_grid(job_id_hash, source_or_target = 'target')
	check_for_unneeded_media_cache
	custom_print(f"{YELLOW} Job Deleted{ENDC}")
	save_jobs(jobs_queue_file, jobs)
	# print_existing_jobs()


def move_job_up(index):
	if index > 0:
		jobs.insert(index - 1, jobs.pop(index))
		save_jobs(jobs_queue_file, jobs)


def move_job_down(index):
	if index < len(jobs) - 1:
		jobs.insert(index + 1, jobs.pop(index))
		save_jobs(jobs_queue_file, jobs)


def move_job_to_top(index):
	if index > 0:
		jobs.insert(0, jobs.pop(index))
		save_jobs(jobs_queue_file, jobs)


def move_job_to_bottom(index):
	if index < len(jobs) - 1:
		jobs.append(jobs.pop(index))
		save_jobs(jobs_queue_file, jobs)


def edit_job_arguments_text(job):
	global default_values
	job_args = job.get('job_args', '')
	edit_arg_window = tk.Toplevel()
	edit_arg_window.title("Edit Job Arguments - tip greyed out values are defaults and will be used if needed, uncheck any argument to restore it to the default value")
	edit_arg_window.geometry("1050x590")
	canvas = tk.Canvas(edit_arg_window)
	scrollable_frame = tk.Frame(canvas)
	canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
	canvas.pack(side="left", fill="both", expand=True)
	entries = {}
	checkboxes = {}
	row = 0
	col = 0
	args_pattern = r'(--[\w-]+)\s+((?:.(?! --))+.)'
	iter_args = re.finditer(args_pattern, job_args)
	job_args_dict = {}
	for match in iter_args:
		arg, value = match.groups()
		value = ' '.join(value.split())	 # Normalize spaces
		job_args_dict[arg] = value
	skip_keys = ['--command', '--jobs-path', '--open-browser', '--job-id', '--job-status', '--step-index', '--source-paths', '--target-path', '--output-path', '--source_pattern', '--target_pattern', '--output_pattern', '--ui-layouts', '--ui-workflow', '--config-path', '--force-download', '--skip-download', '--download_providers', '--execution-queue-count', '--video-memory-strategy', '--system-memory-limit', '--execution-thread-count', '--execution-device-id']

	for arg, default_value in default_values.items():
		cli_arg = '--' + arg.replace('_', '-')
		if cli_arg in skip_keys:
			continue  # Skip the creation of GUI elements for these keys

		formatted_default_value = format_cli_value(default_value)
		current_value = job_args_dict.get(cli_arg, formatted_default_value)
		is_checked = cli_arg in job_args_dict

		var = tk.BooleanVar(value=is_checked)
		chk = tk.Checkbutton(scrollable_frame, text=cli_arg, variable=var)
		chk.grid(row=row, column=col*3, padx=5, pady=2, sticky="w")

		entry = tk.Entry(scrollable_frame)
		entry.insert(0, str(current_value if current_value else default_value))
		entry.grid(row=row, column=col*3+1, padx=5, pady=2, sticky="w")
		entry.config(state='normal' if is_checked else 'disabled')

		entries[cli_arg] = entry
		checkboxes[cli_arg] = var

		def update_entry(var=var, entry=entry, default_value=default_value, cli_arg=cli_arg):
			if var.get():
				entry.config(state=tk.NORMAL)
				debug_print(f"Checkbox checked: {cli_arg}, Current value: {entry.get()}")
			else:
				entry.config(state=tk.DISABLED)
				entry.delete(0, tk.END)
				entry.insert(0, str(default_value))
				debug_print(f"Checkbox unchecked: {cli_arg}, Default value: {default_value}")

		var.trace_add("write", lambda *args, var=var, entry=entry, default_value=default_value, cli_arg=cli_arg: update_entry(var, entry, default_value, cli_arg))
		row += 1
		if row >= 20:
			row = 0
			col += 1

	def save_changes():
		new_job_args = []
		for arg, var in checkboxes.items():
			if var.get():
				entry_text = entries[arg].get().strip()
				if entry_text:
					new_job_args.append(f"{arg} {entry_text}")
					debug_print(f"Saving argument: {arg}, Value: {entry_text}")

		job['job_args'] = ' '.join(new_job_args)
		debug_print("Updated Job Args:", job['job_args'])

		# Check for updated --processors to update job['processors']
		if '--processors' in job['job_args']:
			job_args_list = job['job_args'].split()
			try:
				fp_index = job_args_list.index('--processors')
				new_processors_args = []
				for arg in job_args_list[fp_index + 1:]:
					if arg.startswith('--'):
						break
					new_processors_args.append(arg)
				job['processors'] = ' '.join(new_processors_args)
			except ValueError:
				pass
		save_jobs(jobs_queue_file, jobs)
		edit_arg_window.destroy()

	ok_button = tk.Button(edit_arg_window, text="OK", command=save_changes)
	ok_button.pack(pady=5, padx=5, side=tk.RIGHT)

	cancel_button = tk.Button(edit_arg_window, text="Cancel", command=edit_arg_window.destroy)
	cancel_button.pack(pady=5, padx=5, side=tk.RIGHT)

	scrollable_frame.update_idletasks()
	canvas.configure(scrollregion=canvas.bbox("all"))
	edit_arg_window.mainloop()

def select_job_file(parent, job, source_or_target):
	job_id_hash = job['id']
	file_types = []
	if source_or_target == 'source':
		file_types = [('source files', '*.jpg *.jpeg *.png *.webp *.mp3 *.wav *.aac')]
	elif source_or_target == 'target':
		current_extension = job['targetcache'].lower().rsplit('.', 1)[-1]
		if current_extension in ['jpg', 'jpeg', 'png', 'webp']:
			file_types = [('Image files', '*.jpg *.jpeg *.webp *.png')]
		elif current_extension in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
			file_types = [('Video files', '*.mp4 *.avi *.mov *.webm *.mkv')]

	if source_or_target == 'source':
		selected_paths = filedialog.askopenfilenames(title=f"Select {source_or_target.capitalize()} File(s)", filetypes=file_types)
	else:
		selected_path = filedialog.askopenfilename(title=f"Select {source_or_target.capitalize()} File", filetypes=file_types)
		selected_paths = [selected_path] if selected_path else []

	if selected_paths:
		remove_old_grid(job_id_hash, source_or_target)
		update_paths(job, selected_paths, source_or_target)

		if isinstance(job['sourcecache'], list):
			source_cache_exists = all(os.path.exists(cache) for cache in job['sourcecache'])
		else:
			if job['sourcecache']:
				source_cache_exists = os.path.exists(job['sourcecache'])
				if source_cache_exists and os.path.exists(job['targetcache']):
					job['status'] = 'pending'
		if not job['sourcecache']:
			if os.path.exists(job['targetcache']):
				job['status'] = 'pending'
			else:
				job['status'] = 'missing'

		save_jobs(jobs_queue_file, jobs)
		check_for_unneeded_media_cache

def create_job_thumbnail(parent, job, source_or_target):
	job_id_hash = job['id']
	image_ref_key = f"{source_or_target}_grid_{job_id_hash}.png"
	grid_thumb_path = os.path.join(thumbnail_dir, image_ref_key)
	if not os.path.exists(thumbnail_dir):
		os.makedirs(thumbnail_dir)
		debug_print(f"Created thumbnail directory: {thumbnail_dir}")

	file_paths = job[source_or_target + 'cache']
	file_paths = file_paths if isinstance(file_paths, list) else [file_paths]

	for file_path in file_paths:
		if not os.path.exists(file_path):
			debug_print(f"File not found: {file_path}")
			button = Button(parent, text=f"File not found:\n\n {os.path.basename(file_path)}\nClick to update", bg='white', fg='black', command=lambda j=job: select_job_file(parent, j, source_or_target))
			button.pack(pady=2, fill='x', expand=False)
			return button

		if os.path.exists(grid_thumb_path):
			button = Button(parent, image=PhotoImage(file=grid_thumb_path), command=lambda ft=source_or_target, j=job: select_job_file(parent, j, ft))
			button.image = PhotoImage(file=grid_thumb_path)
			return button

	num_images = len(file_paths)
	grid_size = math.ceil(math.sqrt(num_images))
	thumb_size = 200 // grid_size

	thumbnail_files = []
	for idx, file_path in enumerate(file_paths):
		thumbnail_path = os.path.join(thumbnail_dir, f"{source_or_target}_thumb_{job_id_hash}_{idx}.png")
		if file_path.lower().endswith(('.mp3', '.wav', '.aac', '.flac')):
			audio_icon_path = os.path.join(thumbnail_dir, 'audioicon.png')
			cmd = [
				'ffmpeg', '-i', audio_icon_path,
				'-vf', f'scale={thumb_size}:{thumb_size}',
				'-vframes', '1',
				'-y', thumbnail_path
			]
		elif file_path.lower().endswith(('.jpg', '. webp', '.jpeg', '.png', '.bmp', '.gif', '.tiff')):
			cmd = [
				'ffmpeg', '-i', file_path,
				'-vf', f'thumbnail,scale=\'if(gt(a,1),{thumb_size},-1)\':\'if(gt(a,1),-1,{thumb_size})\',pad={thumb_size}:{thumb_size}:(ow-iw)/2:(oh-ih)/2:black',
				'-vframes', '1',
				'-y', thumbnail_path
			]
		else:
			probe_cmd = [
				'ffmpeg', '-i', file_path,
				'-show_entries', 'format=duration',
				'-v', 'quiet', '-of', 'csv=p=0'
			]

			result = subprocess.run(probe_cmd, capture_output=True, text=True)
			try:
				duration = float(result.stdout.strip())
			except ValueError:
				duration = 100
			seek_time = duration * 0.10
			job_args = job['job_args']
			frame_number = None

			if '--reference-frame-number' in job_args:
				args_list = job_args.split()
				if '--reference-frame-number' in args_list:
					idx = args_list.index('--reference-frame-number')
					if idx + 1 < len(args_list):
						try:
							frame_number = int(args_list[idx + 1])
						except ValueError:
							frame_number = None

			if frame_number is not None:
				cmd = [
					'ffmpeg', '-i', file_path,
					'-vf', f'select=eq(n\\,{frame_number}),scale=\'if(gt(a,1),{thumb_size},-1)\':\'if(gt(a,1),-1,{thumb_size})\',pad={thumb_size}:{thumb_size}:(ow-iw)/2:(oh-ih)/2:black',
					'-vframes', '1',
					'-y', thumbnail_path
				]
			else:
				cmd = [
					'ffmpeg', '-ss', str(seek_time), '-i', file_path,
					'-vf', f'thumbnail,scale=\'if(gt(a,1),{thumb_size},-1)\':\'if(gt(a,1),-1,{thumb_size})\',pad={thumb_size}:{thumb_size}:(ow-iw)/2:(oh-ih)/2:black',
					'-vframes', '1',
					'-y', thumbnail_path
				]
		result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		thumbnail_files.append(thumbnail_path)

	list_file_path = os.path.join(thumbnail_dir, f'{job_id_hash}_input_list.txt')
	with open(list_file_path, 'w') as file:
		for thumb in thumbnail_files:
			file.write(f"file '{thumb}'\n")

	grid_thumb_path = os.path.join(thumbnail_dir, f"{source_or_target}_grid_{job_id_hash}.png")
	grid_cmd = [
		'ffmpeg',
		'-loglevel', 'error',
		'-f', 'concat', '-safe', '0', '-i', list_file_path,
		'-filter_complex', f'tile={grid_size}x{grid_size}:padding=2',
		'-y', grid_thumb_path
	]
	grid_result = subprocess.run(grid_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if grid_result.returncode != 0:
		debug_print(f"Error creating grid: {grid_result.stderr.decode()}")
		return None
	try:
		grid_photo_image = PhotoImage(file=grid_thumb_path)
		button = Button(parent, image=grid_photo_image, command=lambda ft=source_or_target, j=job: select_job_file(parent, j, ft))
		button.image = grid_photo_image
		button.pack(side='left', padx=5)
	except Exception as e:
		debug_print(f"Failed to open grid image: {e}")

	for file in thumbnail_files:
		filesystem.remove_file(file)
	filesystem.remove_file(list_file_path)
	return button

def update_paths(job, path, source_or_target):
	output_hash = str(uuid.uuid4())[:8]
	if source_or_target == 'source':
		cache_path = copy_to_media_cache(path)
		if not isinstance(cache_path, list):
			cache_path = [cache_path]
		cache_key = 'sourcecache'
		job[cache_key] = cache_path
		source_name, _ = os.path.splitext(os.path.basename((job[cache_key])[0]))
		job['source_name'] = source_name


	if source_or_target == 'target':
		cache_path = copy_to_media_cache(path)
		cache_key = 'targetcache'
		job[cache_key] = cache_path
		target_name, _ = os.path.splitext(os.path.basename(job[cache_key]))
		job['target_name'] = target_name

	if source_or_target == 'outputpath':
		cache_key = 'output_path'
		job[cache_key] = path

	if job['source_name']:
		outputname = job['source_name'] + '-' + job['target_name']
	else:
		outputname = job['target_name']
	queueitup_job_id = outputname + '-' + output_hash
	job['id'] = queueitup_job_id
	job['hash'] = output_hash
	job['outputname'] = outputname
	job['full_output_path'] = os.path.join(job['output_path'], job['id'] + job['output_extension'])
	just_save_jobs(jobs_queue_file, jobs)



def RUN_job_args(current_run_job):
	global RUN_job_args

	failed_path = os.path.join(state_manager.get_item('jobs_path'), 'failed', f"{current_run_job['id']}.json")
	draft_path = os.path.join(state_manager.get_item('jobs_path'), 'draft', f"{current_run_job['id']}.json")
	queued_path = os.path.join(state_manager.get_item('jobs_path'), 'queued', f"{current_run_job['id']}.json")
	completed_path = os.path.join(state_manager.get_item('jobs_path'), 'completed', f"{current_run_job['id']}.json")

	#add code if any of these files failed_path or draft_path or queued_path exist then delete it

	for path in [failed_path, draft_path, queued_path]:
		if os.path.exists(path):
			os.remove(path)

	if isinstance(current_run_job['sourcecache'], list):
		arg_source_paths = ' '.join(f'-s "{p}"' for p in current_run_job['sourcecache'])
	else:
		if current_run_job['sourcecache']:
			arg_source_paths = f"-s \"{current_run_job['sourcecache']}\""
		else:
			arg_source_paths = ""
	debug_print(arg_source_paths)
	arg_target_path = f"-t \"{current_run_job['targetcache']}\""
	debug_print(arg_target_path)
	clioutputname = current_run_job['full_output_path']
	arg_output_path = f"-o \"{clioutputname}\""
	debug_print(arg_output_path)
	simulated_args = f"{arg_source_paths} {arg_target_path} {arg_output_path} {current_run_job['job_args']}"
	simulated_cmd = simulated_args.replace('\\\\', '\\')
	process = subprocess.Popen(f"python facefusion.py job-create {current_run_job['id']}")
	process.wait()	# Wait for process to complete
	process = subprocess.Popen(f"python facefusion.py job-add-step {current_run_job['id']} {simulated_cmd}")
	process.wait()	# Wait for process to complete
	process = subprocess.Popen(f"python facefusion.py job-submit {current_run_job['id']}")
	process.wait()	# Wait for process to complete
	import facefusion.jobs.job_runner
	# job_runner.run(job-run, (current_run_job['id']), process_step)
	facefusion.jobs.job_runner.run_job((current_run_job['id']), process_step)
	#process = subprocess.Popen(f"python facefusion.py job-run {current_run_job['id']}", stdout=subprocess.PIPE)
	#process.wait()

	if os.path.exists(completed_path):
		current_run_job['status'] = 'completed'
		print (f"{BLUE}Job completed{ENDC}")

		if not keep_completed_jobs:
			process = subprocess.Popen(f"python facefusion.py job-delete {current_run_job['id']}",stdout=subprocess.PIPE)

	else:
		print (f"{RED}Job FAILED{ENDC}")
		process = subprocess.Popen(f"python facefusion.py job-delete {current_run_job['id']}",stdout=subprocess.PIPE)
		current_run_job['status'] = 'failed'

	return current_run_job


def get_target_info(file_path, current_run_job):
	current_extension = file_path.lower().rsplit('.', 1)[-1]
	target_filetype = None
	orig_video_length = "unknown length"
	output_video_length = "unknown length"
	output_dimensions = "unknown dimensions"
	orig_dimensions = "unknown dimensions"
	target_filetype = "web media"
	if current_extension in ['jpg', 'jpeg', 'png']:
		target_filetype = 'Image'
	elif current_extension in ['mp4', 'mov', 'avi', 'mkv']:
		target_filetype = 'Video'
	job_args = current_run_job.get('job_args')

	if target_filetype == 'Video':
		# Use ffprobe to get video dimensions, fps, and total frames
		def get_video_info(file_path):
			command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
					   'stream=width,height,r_frame_rate,nb_frames', '-of', 'default=noprint_wrappers=1', file_path]
			process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
			stdout, stderr = process.communicate()
			video_info = dict(re.findall(r'(\w+)=([^\n]+)', stdout))
			return video_info

		video_info = get_video_info(file_path)
		orig_dimensions = f"{video_info['width']}x{video_info['height']}"
		orig_fps = eval(video_info['r_frame_rate'])	 # Converts 'num/den' to float
		orig_frames = int(video_info['nb_frames'])
		total_seconds = orig_frames / orig_fps

		# Fetch values from job_args if they exist
		trim_frame_start_match = re.search(r'--trim-frame-start\s+(\d+)', job_args)
		trim_frame_end_match = re.search(r'--trim-frame-end\s+(\d+)', job_args)
		output_fps_match = re.search(r'--output-video-fps\s+(\d+)', job_args)
		output_fps = int(output_fps_match.group(1)) if output_fps_match else orig_fps
		output_dimensions_match = re.search(r'--output-video-resolution\s+(\d+x\d+)', job_args)
		output_dimensions = output_dimensions_match.group(1) if output_dimensions_match else orig_dimensions


		# Calculate output frames
		output_frames = None
		if trim_frame_start_match and trim_frame_end_match:
			trim_frame_start = int(trim_frame_start_match.group(1))
			trim_frame_end = int(trim_frame_end_match.group(1))
			output_frames = trim_frame_end - trim_frame_start
		elif trim_frame_start_match:
			trim_frame_start = int(trim_frame_start_match.group(1))
			output_frames = orig_frames - trim_frame_start
		elif trim_frame_end_match:
			trim_frame_end = int(trim_frame_end_match.group(1))
			output_frames = trim_frame_end
		else:
			output_frames = orig_frames

		output_seconds = output_frames / output_fps
		orig_video_length = get_vid_length(total_seconds)
		output_video_length = get_vid_length(output_seconds)

	elif target_filetype == 'Image':
		process = subprocess.Popen(
			['ffmpeg', '-i', file_path],
			stderr=subprocess.PIPE,
			stdout=subprocess.PIPE,
			universal_newlines=True
		)
		stdout, stderr = process.communicate()
		dimensions_match = re.search(r'Stream.*Video.* (\d+)x(\d+)', stderr)
		if dimensions_match:
			orig_dimensions = f"{dimensions_match.group(1)}x{dimensions_match.group(2)}"
		else:
			orig_dimensions = "Unknown dimensions"
		output_dimensions_match = re.search(r'--output-image-resolution\s+(\d+x\d+)', job_args)
		output_dimensions = output_dimensions_match.group(1) if output_dimensions_match else orig_dimensions



	return target_filetype, orig_video_length, output_video_length, output_dimensions, orig_dimensions

def get_vid_length(total_seconds):
	if total_seconds is not None:
		hours = int(total_seconds // 3600)
		minutes = int((total_seconds % 3600) // 60)
		seconds = int(total_seconds % 60)  # Round to nearest whole number

		if hours > 0:
			video_length = f"{hours} hour{'s' if hours > 1 else ''} {minutes} min{'s' if minutes > 1 else ''} long"
		elif minutes > 0:
			if seconds > 0:
				video_length = f"{minutes} min{'s' if minutes > 1 else ''} {seconds} sec{'s' if seconds > 1 else ''} long"
			else:
				video_length = f"{minutes} min{'s' if minutes > 1 else ''} long"
		else:
			video_length = f"{seconds} second{'s' if seconds > 1 else ''} long"
	else:
		video_length = "Unknown duration"
	return video_length

def get_values_from_FF(state_name):
	global debugging
	state_dict = {}
	processors_choices_dict = {}
	ff_choices_dict = {}
	# Get the state context and state dictionary
	app_context = state_manager.detect_app_context()
	state = state_manager.STATE_SET.get(app_context)

	# Process state dictionary
	for key, value in state.items():
		try:
			json.dumps(value)  # Check if the value is JSON serializable
			state_dict[key] = value	 # Store or update the value in the dictionary
		except TypeError:
			continue  # Skip values that are not JSON serializable

	other_choices = [processors_choices, ff_choices]
	for other_choice in other_choices:
		other_choice_dict = {}
		for attr in dir(other_choice):
			if not attr.startswith("__"):
				value = getattr(other_choice, attr)
				try:
					json.dumps(value)	 # Check if the value is JSON serializable
					other_choice_dict[attr] = value	 # Store or update the value in the dictionary
				except TypeError:
					continue	# Skip values that are not JSON serializable

		if other_choice is processors_choices:
			processors_choices_dict = other_choice_dict
		elif other_choice is ff_choices:
			ff_choices_dict = other_choice_dict

	debugstate = state_dict.get("log_level", []) in ['debug', 'error', 'warn']

	print(f"state_dict debugging {debugstate}")

	if debugging:
		with open(os.path.join(working_dir, f"{state_name}.txt"), "w") as file:
			for key, val in state_dict.items():
				file.write(f"{key}: {val}\n")

	if debugging:
		choice_dicts = {
			"processors_choices_values.txt": processors_choices_dict,
			"ff_choices_values.txt": ff_choices_dict
		}

		for filename, choice_dict in choice_dicts.items():
			with open(os.path.join(working_dir, filename), "w") as file:
				for key, val in choice_dict.items():
					file.write(f"{key}: {val}\n")
	if not debugging:
		files_to_delete_pattern = os.path.join(working_dir, '*_values.txt')
		for file_path in glob.glob(files_to_delete_pattern):
			try:
				filesystem.remove_file(file_path)
			except PermissionError as e:
				messagebox.showerror("Permission Error", f"Failed to delete {file_path}: {e}")
			except Exception as e:
				messagebox.showerror("Error", f"An error occurred while deleting {file_path}: {e}")

	return state_dict


def custom_print(*msgs):
	global last_justtextmsg
	message = " ".join(str(msg) for msg in msgs)
	justtextmsg = re.sub(r'\033\[\d+m', '', message)
	last_justtextmsg = justtextmsg
	print(message)
	# Log the plain text message
	if last_justtextmsg != "":
		logger.info(' \n ', last_justtextmsg)
		logger.debug('QueueItUp Debug', last_justtextmsg)


def debug_print(*msgs):
	global debugging_enabled
	
	if debugging_enabled:
		message = " ".join(str(msg) for msg in msgs)
		
		justtextmsg = re.sub(r'\033\[\d+m', '', message)
		
		last_justtextmsg = justtextmsg  # POTENTIAL MEMORY LEAK: This global variable accumulates messages without cleanup
		print(message)
		if not last_justtextmsg == "":
			logger.debug('QueueItUp Debug', last_justtextmsg)

def print_existing_jobs():
	count_existing_jobs()
	if JOB_IS_RUNNING:
		message = f"{BLUE}There are {PENDING_JOBS_COUNT + JOB_IS_RUNNING} job(s) being Processed - Click Add Job to Queue more Jobs{ENDC}"
	else:
		if PENDING_JOBS_COUNT > 0:
			message = f"{GREEN}There are {PENDING_JOBS_COUNT + JOB_IS_RUNNING} job(s) in the queue - Click Run Jobs to Execute Them, or continue adding more jobs to the queue{ENDC}"
		else:
			message = f"{YELLOW}There are No jobs in the queue - Click Add Job instead of Start{ENDC}"
	custom_print(message)

def count_existing_jobs():
	global PENDING_JOBS_COUNT
	jobs = load_jobs(jobs_queue_file)
	PENDING_JOBS_COUNT = len([job for job in jobs if job['status'] in ['pending']])
	return PENDING_JOBS_COUNT


def update_counters():
	global root, pending_jobs_var
	if pending_jobs_var:
		root.after(0, lambda: pending_jobs_var.set(f"Delete {PENDING_JOBS_COUNT} Pending Jobs"))



def attempt_fix_json(content):
	try:
		return json.loads(content)
	except json.JSONDecodeError as e:
		# Attempt to fix common issues
		if "Expecting ',' delimiter" in str(e):
			fixed_content = content.replace('\n', '').replace(',]', ']').replace(',}', '}')
			try:
				return json.loads(fixed_content)
			except json.JSONDecodeError:
				pass
		if "Extra data" in str(e):
			fixed_content = content.split('}', 1)[0] + '}'
			try:
				return json.loads(fixed_content)
			except json.JSONDecodeError:
				pass
	return None

def create_and_verify_json(file_path):
	if os.path.exists(file_path):
		try:
			with open(file_path, "r") as json_file:
				json.load(json_file)
		except json.JSONDecodeError:
			backup_path = file_path + ".bak"
			shutil.copy(file_path, backup_path)
			debug_print(f"Backup of corrupt JSON file saved as '{backup_path}'. Please check it for salvageable data.")

			with open(file_path, "r") as json_file:
				content = json_file.read()
				fixed_data = attempt_fix_json(content)
				if fixed_data is not None:
					with open(file_path, "w") as json_file:
						json.dump(fixed_data, json_file)
					debug_print(f"JSON file '{file_path}' was corrupt and has been repaired.")
				else:
					with open(file_path, "w") as json_file:
						json.dump([], json_file)
					debug_print(f"Original JSON file '{file_path}' was corrupt and could not be repaired. It has been reset to an empty list.")
	else:
		with open(file_path, "w") as json_file:
			json.dump([], json_file)
		debug_print(f"JSON file '{file_path}' did not exist and has been created.")


def load_jobs(file_path):
	status_priority = {'editing': 0, 'executing': 1, 'pending': 2, 'failed': 3, 'missing': 4, 'completed': 5, 'archived': 6}
	with open(file_path, 'r') as file:
		jobs = json.load(file)

	jobs.sort(key=lambda x: status_priority.get(x['status'], 6))
	return jobs


def just_save_jobs(file_path, jobs):
	with open(file_path, 'w') as file:
		json.dump(jobs, file, indent=4)

def save_jobs(file_path, jobs):
	with open(file_path, 'w') as file:
		json.dump(jobs, file, indent=4)
	print_existing_jobs()
	refresh_listbox_if_open()


def format_cli_value(value):
	if isinstance(value, list) or isinstance(value, tuple):
		return ' '.join(map(str, value))  # Convert list or tuple to space-separated string
	if value is None:
		return 'None'
	return str(value)


def check_for_completed_failed_or_aborted_jobs():
	jobs = load_jobs(jobs_queue_file)
	for job in jobs:
		if job['status'] == 'executing':
			job['status'] = 'pending'
			
			print(f"{RED}A probable crash or aborted job execution was detected from your last use.... checking on status of unfinished jobs..{ENDC}")
			
			source_basenames = ""
			if isinstance(job['sourcecache'], list):
				source_basenames = [os.path.basename(path) for path in job['sourcecache']]
			elif job['sourcecache']:
				source_basenames = os.path.basename(job['sourcecache'])
			jobidname = job['id'] + ".json"  
			queued_directory = os.path.join(base_dir, '.jobs', 'queued')  
			halted_job = os.path.join(queued_directory, jobidname)  
			filesystem.remove_file(halted_job)
			save_jobs(jobs_queue_file, jobs)
			custom_print(f"{GREEN}A job {GREEN}{source_basenames}{ENDC} to -> {GREEN}{os.path.basename(job['targetcache'])} was found that terminated early it will be moved back to the pending jobs queue - you have a Total of {PENDING_JOBS_COUNT + JOB_IS_RUNNING} in the Queue")

	if not keep_completed_jobs:
		jobs_to_delete("completed")
		print(f"{BLUE}All completed jobs have been removed, if you would like to keep completed jobs change the setting to True{ENDC}")
	check_for_unneeded_media_cache()



def sanitize_filename(filename):
	max_length=25
	valid_chars = "-_.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	sanitized = ''.join(c if c in valid_chars else '_' for c in filename)
	sanitized = sanitized.strip()  # Remove leading and trailing spaces
	
	# Ensure the basename is limited to max_length
	if len(sanitized) > max_length:
		base_name, ext = os.path.splitext(sanitized)
		if len(ext) > max_length:
			sanitized = sanitized[:max_length]	# If the extension alone exceeds max_length, truncate
		else:
			sanitized = base_name[:max_length - len(ext)] + ext
	
	return sanitized

def copy_to_media_cache(file_paths):
	if not os.path.exists(working_dir):
		os.makedirs(working_dir)
	if not os.path.exists(media_cache_dir):
		os.makedirs(media_cache_dir)
	if isinstance(file_paths, str):
		file_paths = [file_paths]  # Convert single file path to list
	cached_paths = []
	for file_path in file_paths:
		file_name = os.path.basename(file_path)
		sanitized_name = sanitize_filename(file_name)  # Sanitize the filename
		file_size = os.path.getsize(file_path)
		base_name, ext = os.path.splitext(sanitized_name)
		counter = 0
		while True:
			new_name = f"{base_name}_{counter}{ext}" if counter > 0 else sanitized_name
			cache_path = os.path.join(media_cache_dir, new_name)
			if not os.path.exists(cache_path):
				shutil.copy(file_path, cache_path)
				cached_paths.append(cache_path)
				break
			else:
				cache_size = os.path.getsize(cache_path)
				if file_size == cache_size:
					cached_paths.append(cache_path)	 # If size matches, assume it's the same file
					break
			counter += 1

	# Ensure target_path is treated as a single path
	if isinstance(cached_paths, list) and len(cached_paths) == 1:
		return cached_paths[0]	# Return the single path
	else:
		return cached_paths	 # Return the list of paths
	
def check_for_unneeded_thumbnail_cache():
	if not os.path.exists(thumbnail_dir):
		os.makedirs(thumbnail_dir)
	thumb_files = os.listdir(thumbnail_dir)
	jobs = load_jobs(jobs_queue_file)
	# Create a set to store all needed thumbnail patterns from the jobs
	needed_thumbnail_patterns = set()
	for job in jobs:
		job_hash = job['hash']
		# Add the hash pattern to the set of needed thumbnails
		needed_thumbnail_patterns.add(f"{job_hash}.png")
	# Delete thumbnails that do not match any needed pattern
	for thumb_file in thumb_files:
		if not any(thumb_file.endswith(pattern) for pattern in needed_thumbnail_patterns):
			filesystem.remove_file(os.path.join(thumbnail_dir, thumb_file))
	
def check_for_unneeded_media_cache():
	if not os.path.exists(working_dir):
		os.makedirs(working_dir)
	if not os.path.exists(media_cache_dir):
		os.makedirs(media_cache_dir)
	
	# List all files in the media cache and thumbnail directories
	cache_files = os.listdir(media_cache_dir)
	jobs = load_jobs(jobs_queue_file)
	
	# Create a set to store all needed filenames from the jobs
	needed_files = set() 
	
	# Add 'completed' status to needed files if keep_completed_jobs is True
	valid_statuses = {'pending', 'failed', 'missing', 'editing', 'archived', 'executing'}
	if keep_completed_jobs:
		valid_statuses.add('completed')
	
	for job in jobs:
		if job['status'] in valid_statuses:
			# Ensure sourcecache is a list
			if job['sourcecache']:
				for source_cache_path in job['sourcecache']:
					source_basename = os.path.basename(source_cache_path)
					needed_files.add(source_basename)
			target_basename = os.path.basename(job['targetcache'])
			needed_files.add(target_basename)
	
	# Delete files in the media cache directory that are not needed
	for cache_file in cache_files:
		if cache_file not in needed_files:
			filesystem.remove_file(os.path.join(media_cache_dir, cache_file))
	check_for_unneeded_thumbnail_cache()



#startup_init_checks_and_cleanup, Globals and toggles
script_root = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_root)))
user_dir = "QueueItUp"
working_dir = os.path.normpath(os.path.join(base_dir, user_dir))
media_cache_dir = os.path.normpath(os.path.join(working_dir, "mediacache"))
keep_completed_jobs = True
default_values = {}
debugging = True
if not os.path.exists(working_dir):
	os.makedirs(working_dir)
if not os.path.exists(media_cache_dir):
	os.makedirs(media_cache_dir)
jobs_queue_file = os.path.normpath(os.path.join(working_dir, "jobs_queue.json"))
# ANSI Color Codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'

# HTML Color Mapping
COLOR_MAPPING = {
	RED: '<span style="color:red;">',
	GREEN: '<span style="color:green;">',
	YELLOW: '<span style="color:orange;">',
	BLUE: '<span style="color:blue;">',
	ENDC: '</span>',
}
print(f"{BLUE}FaceFusion version: {GREEN}{facefusion_version}{ENDC}")
print(f"{BLUE}QueueItUp! version: {GREEN}{queueitup_version}{ENDC}")

default_values = get_values_from_FF("default_values")
settings_path = default_values.get("config_path", "")

initialize_settings()
create_and_verify_json(jobs_queue_file)

thumbnail_dir = os.path.normpath(os.path.join(working_dir, "thumbnails"))
ABOUT = gradio.Button(value = 'About QUEUEITUP Next', link = 'https://github.com/chuckkay/QueueItUp-addon')
ADD_JOB_BUTTON = gradio.Button("Add Job to QueueItUp", variant="primary")
RUN_JOBS_BUTTON = gradio.Button("Run QueueItUp Jobs", variant="primary")
EDIT_JOB_BUTTON = gradio.Button("Edit QueueItUp Jobs")
SETTINGS_BUTTON = gradio.Button("Change Settings")  # UNUSED: This button is defined but never used in the code
JOB_IS_RUNNING = 0
JOB_IS_EXECUTING = 0
CURRENT_JOB_NUMBER = 0
edit_queue_running = False




PENDING_JOBS_COUNT = count_existing_jobs()

root = None
pending_jobs_var = None
last_justtextmsg = (f"there are {PENDING_JOBS_COUNT} jobs in the queue")
read_logs = (f"there are {PENDING_JOBS_COUNT} jobs in the queue")  # UNUSED: This variable is set but never used

debug_print("FaceFusion Base Directory:", base_dir)
debug_print("Working Directory:", working_dir)
debug_print("Media Cache Directory:", media_cache_dir)
debug_print("Jobs Queue File:", jobs_queue_file)
print(f"{BLUE}Welcome Back To QueueItUp The FaceFusion Queueing Addon{ENDC}\n\n")
print(f"QUEUEITUP{BLUE}	 COLOR OUTPUT KEY")
print(f"{BLUE}BLUE = normal color output key")
print(f"{GREEN}GREEN = file name, cache managment or processing progress")
print(f"{YELLOW}YELLOW = informational")
print(f"{RED}RED = detected a Problem")
print(f"{YELLOW}Checking Status{ENDC}\n\n")
print(" ")
check_for_completed_failed_or_aborted_jobs()
print(f"{GREEN}STATUS CHECK COMPLETED. {BLUE}You are now ready to QUEUE IT UP!{ENDC}")
print_existing_jobs()
