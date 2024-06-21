import gradio as gr
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
import facefusion.globals
from facefusion.uis.components import about, frame_processors, frame_processors_options, execution, execution_thread_count, execution_queue_count, memory, temp_frame, output_options, common_options, source, target, output, preview, trim_frame, face_analyser, face_selector, face_masker
try:
    from facefusion.uis.components import target_options
    yt_addon = True
except ImportError:
    yt_addon = False

import pkg_resources


def pre_check() -> bool:
    return True


def pre_render() -> bool:
    return True


def render() -> gr.Blocks:
    global ADD_JOB_BUTTON, RUN_JOBS_BUTTON, STATUS_WINDOW, SETTINGS_BUTTON
    with gr.Blocks() as layout:
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Blocks():
                    about.render()
                with gr.Blocks():
                    frame_processors.render()
                with gr.Blocks():
                    frame_processors_options.render()
                with gr.Blocks():
                    execution.render()
                    execution_thread_count.render()
                    execution_queue_count.render()
                with gr.Blocks():
                    memory.render()
                with gr.Blocks():
                    temp_frame.render()
                with gr.Blocks():
                    output_options.render()
            with gr.Column(scale=2):
                with gr.Blocks():
                    source.render()
                with gr.Blocks():
                    target.render()
                if yt_addon:
                    with gr.Blocks():
                        target_options.render()
                with gr.Blocks():
                    output.render()
                with gr.Blocks():
                    STATUS_WINDOW.render()
                with gr.Blocks():
                    ADD_JOB_BUTTON.render()
                with gr.Blocks():
                    RUN_JOBS_BUTTON.render()
                with gr.Blocks():
                    EDIT_JOB_BUTTON.render()
                # with gr.Blocks():
                    # SETTINGS_BUTTON.render()
            with gr.Column(scale=3):
                with gr.Blocks():
                    preview.render()
                with gr.Blocks():
                    trim_frame.render()
                with gr.Blocks():
                    face_selector.render()
                with gr.Blocks():
                    face_masker.render()
                with gr.Blocks():
                    face_analyser.render()
                with gr.Blocks():
                    common_options.render()
    return layout


def listen() -> None:
    global EDIT_JOB_BUTTON, STATUS_WINDOW
    ADD_JOB_BUTTON.click(assemble_queue, outputs=STATUS_WINDOW)
    RUN_JOBS_BUTTON.click(execute_jobs)
    EDIT_JOB_BUTTON.click(edit_queue_window, outputs=STATUS_WINDOW)
    # SETTINGS_BUTTON.click(queueitup_settings)
    frame_processors.listen()
    frame_processors_options.listen()
    execution.listen()
    execution_thread_count.listen()
    execution_queue_count.listen()
    memory.listen()
    temp_frame.listen()
    output_options.listen()
    source.listen()
    target.listen()
    if yt_addon:
        target_options.listen()
    output.listen()
    preview.listen()
    trim_frame.listen()
    face_selector.listen()
    face_masker.listen()
    face_analyser.listen()
    common_options.listen()



def run(ui : gr.Blocks) -> None:
    if automatic1111:
        import multiprocessing

        concurrency_count = min(8, multiprocessing.cpu_count())
        ui.queue(concurrency_count = concurrency_count).launch(show_api = False, quiet = True)           
            
    else:
        ui.launch(show_api = False, inbrowser = facefusion.globals.open_browser)
            #ui.queue(concurrency_count = concurrency_count).launch(show_api = False, quiet = False, inbrowser = facefusion.globals.open_browser, favicon_path="test.ico")
        
    
def assemble_queue():
    global RUN_JOBS_BUTTON, ADD_JOB_BUTTON, jobs_queue_file, jobs, STATUS_WINDOW, default_values, current_values
    missing_paths = []

    if not facefusion.globals.source_paths:
        missing_paths.append("source paths")
    if not facefusion.globals.target_path:
        missing_paths.append("target path")
    if not facefusion.globals.output_path:
        missing_paths.append("output path")

    if missing_paths:
        whats_missing = ", ".join(missing_paths)
        custom_print(f"{RED}Whoops!!!, you are missing {whats_missing}. Make sure you add {whats_missing} before clicking add job{ENDC}\n\n")
        return STATUS_WINDOW.value

    current_values = get_values_from_globals('current_values')

    differences = {}
    keys_to_skip = ["source_paths", "output_hash", "target_path", "output_path", "ui_layouts", "face_recognizer_model", "headless"]
    ### is this still needed?
    if "frame_processors" in current_values:
        frame_processors = current_values["frame_processors"]
        if "face_enhancer" not in frame_processors:
            keys_to_skip.append("face_enhancer_model")
        if "frame_enhancer" not in frame_processors:
            keys_to_skip.append("frame_enhancer_blend")
        if "face_swapper" not in frame_processors:
            keys_to_skip.append("face_swapper_model")
        if "face_debugger" not in frame_processors:
            keys_to_skip.append("face_debugger_items")
        if "frame_colorizer" not in frame_processors:
            keys_to_skip.append("frame_colorizer_model")
        if "frame_colorizer" not in frame_processors:
            keys_to_skip.append("frame_colorizer_size")
        if "frame_colorizer" not in frame_processors:
            keys_to_skip.append("frame_colorizer_blend")
        if "lip_syncer" not in frame_processors:
            keys_to_skip.append("lip_syncer_model")
            
    # Compare current_values against default_values and record only changed current values
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

    source_paths = current_values.get("source_paths", [])
    target_path = current_values.get("target_path", "")
    output_path = current_values.get("output_path", "")
    output_hash = current_values.get("output_hash", "")
    # if output_path
    # if not output_path:
        # output_path = default_values.get("output_path", "")
        # if not output_path:
            # output_path = "outputs"
    if not next_beta:
        output_hash = str(uuid.uuid4())[:8]
    while True:
        if JOB_IS_RUNNING:
            if JOB_IS_EXECUTING:
                debug_print("Job is executing.")
                break
            else:
                debug_print("Job is running but not executing. Stuck in loop.\n")
                time.sleep(1)
        else:
            debug_print("Job is not running.")
            break
    oldeditjob = None
    found_editing = False
    jobs = load_jobs(jobs_queue_file)

    for job in jobs:
        if job['status'] == 'editing':
            oldeditjob = job.copy()  
            found_editing = True
            break

    cache_source_paths = copy_to_media_cache(source_paths)
    source_basenames = [os.path.basename(path) for path in cache_source_paths] if isinstance(cache_source_paths, list) else os.path.basename(cache_source_paths)
    debug_print(f"{GREEN}Source file{ENDC} copied to Media Cache folder: {GREEN}{source_basenames}{ENDC}\n\n")
    cache_target_path = copy_to_media_cache(target_path)
    debug_print(f"{GREEN}Target file{ENDC} copied to Media Cache folder: {GREEN}{os.path.basename(cache_target_path)}{ENDC}\n\n")

    # Construct the arguments string
    arguments = " ".join(f"--{key.replace('_', '-')} {value}" for key, value in differences.items() if value)
    if debugging:
        with open(os.path.join(working_dir, "arguments_values.txt"), "w") as file:
            file.write(json.dumps(arguments) + "\n")
    job_args = f"{arguments}"

    if isinstance(cache_source_paths, str):
        cache_source_paths = [cache_source_paths]
    string_frame_processors = " ".join(current_values['frame_processors'])
    new_job = {
        "job_args": job_args,
        "status": "pending",
        "headless": "--headless",
        "frame_processors": string_frame_processors,
        "sourcecache": (cache_source_paths),
        "targetcache": (cache_target_path),
        "output_path": (output_path),
        "id": (output_hash)
    }

    if debugging:
        with open(os.path.join(working_dir, "job_args_values.txt"), "w") as file:
            for key, val in current_values.items():
                file.write(f"{key}: {val}\n")

    if found_editing:
        if not (oldeditjob['sourcecache'] == new_job['sourcecache'] or oldeditjob['sourcecache'] == new_job['targetcache']):
            check_if_needed(oldeditjob, 'source')
        if not (oldeditjob['targetcache'] == new_job['sourcecache'] or oldeditjob['targetcache'] == new_job['targetcache']):
            check_if_needed(oldeditjob, 'target')
        job.update(new_job)
        save_jobs(jobs_queue_file, jobs)
        custom_print(f"{GREEN}You have successfully returned the Edited job back to the job Queue, it is now a Pending Job {ENDC}")

    if not found_editing:
        jobs.append(new_job)
        save_jobs(jobs_queue_file, jobs)
    if root and root.winfo_exists():
        debug_print("edit queue windows is open")
        save_jobs(jobs_queue_file, jobs)
        refresh_frame_listbox()
    load_jobs(jobs_queue_file)
    count_existing_jobs()    
    if JOB_IS_RUNNING:
        custom_print(f"{BLUE}job # {CURRENT_JOB_NUMBER + PENDING_JOBS_COUNT + 1} was added {ENDC}\n\n")
    else:
        custom_print(f"{BLUE}Your Job was Added to the queue, there are a total of #{PENDING_JOBS_COUNT} Job(s) in the queue, {YELLOW}  Add More Jobs, Edit the Queue, or Click Run Jobs to Execute all the queued jobs\n\n{ENDC}")
    return STATUS_WINDOW.value

        
def execute_jobs():
    global JOB_IS_RUNNING, JOB_IS_EXECUTING, CURRENT_JOB_NUMBER, jobs_queue_file, jobs
    load_jobs(jobs_queue_file)
    count_existing_jobs()    
    if not PENDING_JOBS_COUNT + JOB_IS_RUNNING > 0:
        custom_print(f"{RED}Whoops!!!, {YELLOW}There are {PENDING_JOBS_COUNT} Job(s) queued.{ENDC} Add a job to the queue before pressing Run Jobs.\n\n")
        return STATUS_WINDOW.value

    if PENDING_JOBS_COUNT + JOB_IS_RUNNING > 0 and JOB_IS_RUNNING:
        custom_print(f"{RED}Whoops {YELLOW}a Job is already executing, with {PENDING_JOBS_COUNT} more job(s) waiting to be processed.\n\n {RED}You don't want more than one job running at the same time your GPU can't handle that,{YELLOW}\n\nYou just need to click add job if jobs are already running, and the job will be placed in line for execution. you can edit the job order with Edit Queue button{ENDC}\n\n")
        return STATUS_WINDOW.value
        
    jobs = load_jobs(jobs_queue_file)
    JOB_IS_RUNNING = 1
    CURRENT_JOB_NUMBER = 0
    # current_run_job = {}
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
        custom_print(f"{BLUE}Starting Job #{GREEN} {CURRENT_JOB_NUMBER}{ENDC}\n\n")
        printjobtype = current_run_job['frame_processors']
        custom_print(f"{BLUE}Executing Job # {CURRENT_JOB_NUMBER} of {CURRENT_JOB_NUMBER + PENDING_JOBS_COUNT}  {ENDC}\n\n")

        if not os.path.exists(current_run_job['output_path']):
            os.makedirs(current_run_job['output_path'])
        if isinstance(current_run_job['sourcecache'], list):
            source_basenames = f"Source Files {', '.join(os.path.basename(path) for path in current_run_job['sourcecache'])}"
        else:
            source_basenames = f"Source File {os.path.basename(current_run_job['sourcecache'])}"

        target_filetype, orig_video_length, output_video_length, output_dimensions, orig_dimensions = get_target_info(current_run_job['targetcache'], current_run_job)

        custom_print(f"{BLUE}Job #{CURRENT_JOB_NUMBER} will be doing {YELLOW}{printjobtype}{ENDC} - with {GREEN}{source_basenames}{YELLOW} to -> the Target {orig_video_length} {orig_dimensions} {target_filetype} {GREEN}{os.path.basename(current_run_job['targetcache'])}{ENDC} , which will be saved as a {YELLOW}{output_video_length} {output_dimensions} sized {target_filetype}{ENDC} in the folder {GREEN}{current_run_job['output_path']}{ENDC}\n\n")
##
        run_job_args(current_run_job)
##
        if current_run_job['status'] == 'failed':
            source_basenames = [os.path.basename(path) for path in current_run_job['sourcecache']] if isinstance(current_run_job['sourcecache'], list) else [os.path.basename(current_run_job['sourcecache'])]
            custom_print(f"{BLUE}Job # {CURRENT_JOB_NUMBER} {RED} failed. Please check the validity of {source_basenames} and {RED}{os.path.basename(current_run_job['targetcache'])}.{BLUE}{PENDING_JOBS_COUNT} jobs remaining, pausing 1 second before starting next job{ENDC}\n")
        else:
            custom_print(f"{BLUE}Job # {CURRENT_JOB_NUMBER} {GREEN} completed successfully {BLUE}{PENDING_JOBS_COUNT} jobs remaining, pausing 1 second before starting next job{ENDC}\n")

        JOB_IS_EXECUTING = 0  # Reset the job execution flag
        time.sleep(1)
        jobs = load_jobs(jobs_queue_file)
        jobs = [job for job in jobs if job['status'] != 'executing']
        jobs.append(current_run_job)
        save_jobs(jobs_queue_file, jobs)
 
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
    save_jobs(jobs_queue_file, jobs)
    check_for_unneeded_media_cache()



# Initialize the setini variable in the global scope
setini = None


def load_settings():
    config = configparser.ConfigParser()
    if not os.path.exists(settings_path):
        config['QueueItUp'] = {
            'debugging': 'True',
            'keep_completed_jobs': 'True'
        }
        config['misc'] = {
            'log_level': 'debug'
        }
        with open(settings_path, 'w') as configfile:
            config.write(configfile)
    config.read(settings_path)
    if 'QueueItUp' not in config.sections():
        config['QueueItUp'] = {
            'debugging': 'True',
            'keep_completed_jobs': 'True'
        }
        with open(settings_path, 'w') as configfile:
            config.write(configfile)
    if 'misc' not in config.sections():
        config['misc'] = {
            'log_level': 'debug'
        }
        with open(settings_path, 'w') as configfile:
            config.write(configfile)
    settings = {
        'debugging': config.getboolean('QueueItUp', 'debugging'),
        'keep_completed_jobs': config.getboolean('QueueItUp', 'keep_completed_jobs'),
        'log_level': config.get('misc', 'log_level')
    }
    return settings

def save_settings(settings):
    config = configparser.ConfigParser()
    config.read(settings_path)
    if 'QueueItUp' not in config.sections():
        config.add_section('QueueItUp')
    if 'misc' not in config.sections():
        config.add_section('misc')
    config.set('QueueItUp', 'debugging', str(settings['debugging']))
    config.set('QueueItUp', 'keep_completed_jobs', str(settings['keep_completed_jobs']))
    config.set('misc', 'log_level', settings['log_level'])
    with open(settings_path, 'w') as configfile:
        config.write(configfile)

def initialize_settings():
    settings = load_settings()
    global debugging, keep_completed_jobs
    debugging = settings['debugging']
    keep_completed_jobs = settings['keep_completed_jobs']

def queueitup_settings():
    def create_settings_window():
        global setini
        settings = load_settings()
        original_debugging_value = settings['debugging']
        original_keep_completed_jobs_value = settings['keep_completed_jobs']

        def save_and_close():
            global setini
            settings['debugging'] = debugging_var.get()
            settings['log_level'] = 'debug' if settings['debugging'] else 'info'
            settings['keep_completed_jobs'] = keep_completed_jobs_var.get()
            save_settings(settings)
            initialize_settings()

            if original_debugging_value and not settings['debugging']:
                files_to_delete_pattern = os.path.join(working_dir, '*_values.txt')
                for file_path in glob.glob(files_to_delete_pattern):
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except PermissionError as e:
                        messagebox.showerror("Permission Error", f"Failed to delete {file_path}: {e}")
                    except Exception as e:
                        messagebox.showerror("Error", f"An error occurred while deleting {file_path}: {e}")

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
        window_height = 150
        screen_width = setini.winfo_screenwidth()
        screen_height = setini.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)

        setini.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
        setini.attributes('-topmost', True)

        debugging_var = tk.BooleanVar(value=settings['debugging'])
        keep_completed_jobs_var = tk.BooleanVar(value=settings['keep_completed_jobs'])

        tk.Label(setini, text="Debugging:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Checkbutton(setini, variable=debugging_var).grid(row=0, column=1, padx=10, pady=5)

        tk.Label(setini, text="Keep Completed Jobs:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Checkbutton(setini, variable=keep_completed_jobs_var).grid(row=1, column=1, padx=10, pady=5)

        tk.Button(setini, text="Save", command=save_and_close).grid(row=2, column=0, columnspan=2, pady=10)

        setini.mainloop()

    if root and root.winfo_exists():
        root.after(0, create_settings_window)
    else:
        create_settings_window()



def edit_queue_window():
    global root, edit_queue_running
    try:
        if root and root.winfo_exists() and edit_queue_running:
            root.deiconify()  # Ensure the window is not minimized
            root.lift()  # Lift the window to the top
            root.focus_force()  # Force focus on the window
            
            # Additional measures to ensure the window stays on top
            root.attributes('-topmost', True)
            root.after(10, lambda: root.attributes('-topmost', False))
            root.after(20, lambda: root.attributes('-topmost', True))
            root.after(30, lambda: root.attributes('-topmost', False))

            print_existing_jobs()
            return STATUS_WINDOW.value
        else:
            edit_queue()
            print_existing_jobs()
            return STATUS_WINDOW.value
    except tk.TclError as e:
        root = None
        edit_queue()
        print_existing_jobs()
        return STATUS_WINDOW.value

def edit_queue():
    global root, edit_queue_running, frame, canvas, STATUS_WINDOW, jobs_queue_file, jobs, job, thumbnail_dir, working_dir, pending_jobs_var, PENDING_JOBS_COUNT

    if edit_queue_running:
        return  # Prevent multiple instances of the window

    edit_queue_running = True

    root = tk.Tk()
    jobs = load_jobs(jobs_queue_file)
    PENDING_JOBS_COUNT = count_existing_jobs()

    root.geometry('1200x800')
    root.title("Edit Queued Jobs")
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)

    scrollbar = Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas = tk.Canvas(root)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=canvas.yview)

    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor='nw')
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

    custom_font = font.Font(family="Helvetica", size=12, weight="bold")
    bold_font = font.Font(family="Helvetica", size=12, weight="bold")

    pending_jobs_var = tk.StringVar()
    pending_jobs_var.set(f"Delete {PENDING_JOBS_COUNT} Pending Jobs")

    close_button = tk.Button(root, text="Close Window", command=close_window, font=custom_font)
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

    refresh_frame_listbox()
    root.protocol("WM_DELETE_WINDOW", close_window)
    root.mainloop()
    root = None  # Ensure root is set to None when the window is closed
    edit_queue_running = False  # Reset the running state
    return STATUS_WINDOW.value

def run_jobs_click():
    save_jobs(jobs_queue_file, jobs)
    threading.Thread(target=execute_jobs).start()  # Run execute_jobs in a separate thread

def clone_job(job):
    clonedjob = job.copy()  # Copy the existing job to preserve other attributes
    clonedjob['id'] = str(uuid.uuid4())  # Assign a new unique ID to the cloned job
    ###if next_beta update output path to include hash
    jobs = load_jobs(jobs_queue_file)
    
    original_index = jobs.index(job)  # Find the index of the original job
    jobs.insert(original_index + 1, clonedjob)  # Insert the cloned job right after the original job
    
    save_jobs(jobs_queue_file, jobs)
    refresh_frame_listbox()
    
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
        dialog.destroy()
        open_file_dialog()

    def open_file_dialog():
        selected_paths = []
        if source_or_target == 'source':
            selected_paths = filedialog.askopenfilenames(
                title="Select Multiple targets for BatchItUp to make multiple cloned jobs using each File",
                filetypes=[('Image files', '*.jpg *.jpeg  *.webp *.png')]
            )
        elif source_or_target == 'target':
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
                add_new_job['id'] = str(uuid.uuid4())
                    
                ###if next_beta update output path to include hash

                path = copy_to_media_cache(path)
                add_new_job[source_or_target + 'cache'] = path
                debug_print(f"{YELLOW}{source_or_target} - {GREEN}{add_new_job[source_or_target + 'cache']}{YELLOW} copied to temp media cache dir{ENDC}")
                original_index += 1  # Increment the index for each new job
                jobs.insert(original_index, add_new_job)  # Insert the new job right after the original job
            save_jobs(jobs_queue_file, jobs)
            refresh_frame_listbox()
    dialog = tk.Toplevel()
    dialog.withdraw()

    source_filenames = [os.path.basename(src) for src in job['sourcecache']]
    message = (
        f"Welcome to the BatchItUp feature. Here you can add multiple batch jobs with just a few clicks.\n\n"
        f"Click the 'Use Source' button to select as many target {target_filetype}s as you like and BatchItUp will create a job for each {target_filetype} "
        f"using {', '.join(source_filenames)} as the source image(s), OR you can Click 'Use Target' to select as many Source Images as you like and BatchItUp will "
        f"create a job for each source image using {os.path.basename(job['targetcache'])} as the target {target_filetype}."
    )

    dialog.deiconify()
    dialog.geometry("500x300")
    dialog.title("BatchItUp")

    label = tk.Label(dialog, text=message, wraplength=450, justify="left")
    label.pack(pady=20)

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=10)

    use_source_button = tk.Button(button_frame, text="Use Source", command=on_use_source)
    use_source_button.pack(side="left", padx=10)

    use_target_button = tk.Button(button_frame, text="Use Target", command=on_use_target)
    use_target_button.pack(side="left", padx=10)

    dialog.mainloop()
 

def update_job_listbox():
    global frame, canvas, jobs, thumbnail_dir
    update_counters()
    custom_font = font.Font(family="Helvetica", size=12, weight="bold")
    bold_font = font.Font(family="Helvetica", size=12, weight="bold")

    try:
        if frame.winfo_exists():
            jobs = load_jobs(jobs_queue_file)
            count_existing_jobs()            
            for widget in frame.winfo_children():
                widget.destroy()
            for index, job in enumerate(jobs):
                source_cache_path = job['sourcecache'] if isinstance(job['sourcecache'], list) else [job['sourcecache']]
                source_mediacache_exists = all(os.path.exists(os.path.normpath(source)) for source in source_cache_path)
                target_cache_path = job['targetcache'] if isinstance(job['targetcache'], str) else job['targetcache'][0]
                target_mediacache_exists = os.path.exists(os.path.normpath(target_cache_path))
                bg_color = 'SystemButtonFace'
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
                    if not source_mediacache_exists:
                        debug_print(f"source mediacache {source_cache_path} is missing ")
                        job['status'] = 'missing'
                        remove_old_grid(job_id_hash, 'source')
                        bg_color = 'red'
                    if not target_mediacache_exists:
                        debug_print(f"target mediacache {target_cache_path} is missing ")
                        job['status'] = 'missing'
                        remove_old_grid(job_id_hash, 'target')
                        bg_color = 'red'
                if job['status'] == 'archived':
                    bg_color = 'brown'
                job_frame = tk.Frame(frame, borderwidth=2, relief='groove', background=bg_color)
                job_frame.pack(fill='x', expand=True, padx=5, pady=5)
                move_job_frame = tk.Frame(job_frame)
                move_job_frame.pack(side='left', fill='x', padx=5)
                move_top_button = tk.Button(move_job_frame, text="   Top   ", command=lambda idx=index, j=job: move_job_to_top(idx))
                move_top_button.pack(side='top', fill='y')
                move_up_button = tk.Button(move_job_frame, text="   Up   ", command=lambda idx=index, j=job: move_job_up(idx))
                move_up_button.pack(side='top', fill='y')
                move_down_button = tk.Button(move_job_frame, text=" Down ", command=lambda idx=index, j=job: move_job_down(idx))
                move_down_button.pack(side='top', fill='y')
                move_bottom_button = tk.Button(move_job_frame, text="Bottom", command=lambda idx=index, j=job: move_job_to_bottom(idx))
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
                else:
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

        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    except tk.TclError as e:
        debug_print(e)

def refresh_buttonclick():
    count_existing_jobs()    
    save_jobs(jobs_queue_file, jobs)
    refresh_frame_listbox()

def refresh_frame_listbox():
    global jobs
    status_priority = {'editing': 0, 'executing': 1, 'pending': 2, 'failed': 3, 'missing': 4, 'completed': 5, 'archived': 6}
    jobs = load_jobs(jobs_queue_file)
    jobs.sort(key=lambda x: status_priority.get(x['status'], 6))
    save_jobs(jobs_queue_file, jobs)
    update_job_listbox()

def close_window():
    global root
    save_jobs(jobs_queue_file, jobs)
    edit_queue_running = False
    if root:
        root.destroy()
    return STATUS_WINDOW.value

def make_job_pending(job):
    job['status'] = 'pending'
    save_jobs(jobs_queue_file, jobs) 
    refresh_frame_listbox()
    
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
    if edit_queue_running:
        refresh_frame_listbox()
    
def remove_old_grid(job_id_hash, source_or_target):
    image_ref_key = f"{source_or_target}_grid_{job_id_hash}.png"
    grid_thumb_path = os.path.join(thumbnail_dir, image_ref_key)
    if os.path.exists(grid_thumb_path):
        os.remove(grid_thumb_path)
        debug_print(f"Deleted temporary Thumbnail: {GREEN}{os.path.basename(grid_thumb_path)}{ENDC}\n\n")  
    
def archive_job(job):
    if job['status'] == 'archived':
        job['status'] = 'pending'
    else:
        job['status'] = 'archived'
    save_jobs(jobs_queue_file, jobs) 
    refresh_frame_listbox()

def reload_job_in_facefusion_edit(job):
    sourcecache_path = job.get('sourcecache')
    targetcache_path = job.get('targetcache')

    if isinstance(sourcecache_path, list):
        missing_files = [path for path in sourcecache_path if not os.path.exists(path)]
        if missing_files:
            messagebox.showerror("Error", f"Cannot edit job. The following source files do not exist: {', '.join(os.path.basename(path) for path in missing_files)}")
            return
    else:
        if not os.path.exists(sourcecache_path):
            messagebox.showerror("Error", f"Cannot edit job. The source file '{os.path.basename(sourcecache_path)}' does not exist.")
            return

    if not os.path.exists(targetcache_path):
        messagebox.showerror("Error", f"Cannot edit job. The target file '{os.path.basename(targetcache_path)}' does not exist.")
        return

    response = messagebox.askyesno("Confirm Edit", "THIS WILL REMOVE THIS PENDING JOB FROM THE QUEUE, AND LOAD IT INTO FACEFUSION WEBUI FOR EDITING, WHEN DONE EDITING CLICK START TO RUN IT OR ADD JOB TO REQUEUE IT. ARE YOU SURE YOU WANT TO EDIT THIS JOB", icon='warning')
    if not response:
        return
    job['headless'] = ''
    job['status'] = 'editing'
    save_jobs(jobs_queue_file, jobs)
    top = Toplevel()
    top.title("Please Wait")
    message_label = tk.Label(top, text="Please wait while the job loads back into FaceFusion...", padx=20, pady=20)
    message_label.pack()
    top.after(1000, close_window)
    top.after(2000, top.destroy)
    custom_print(f"{GREEN} PLEASE WAIT WHILE THE Jobs IS RELOADED IN FACEFUSION{ENDC}...... {YELLOW}THIS WILL CREATE AN ADDITIONAL PYTHON PROCESS AND YOU SHOULD CONSIDER RESTARTING FACEFUSION AFTER DOING THIS MOR THEN 3 TIMES{ENDC}")
    root.destroy()
    #edit_job_args(job)       
    run_job_args(job)

def output_path_job(job):
    selected_path = filedialog.askdirectory(title="Select A New Output Path for this Job")

    if selected_path:
        formatted_path = selected_path.replace('/', '\\')  
        job['output_path'] = formatted_path
        update_paths(job, formatted_path, 'output')
    save_jobs(jobs_queue_file, jobs)  

def delete_job(job):
    job['status'] = ('deleting')
    job_id_hash = job['id']
    check_if_needed(job, 'both')
    jobs.remove(job)
    save_jobs(jobs_queue_file, jobs)
    remove_old_grid(job_id_hash, source_or_target = 'source')
    remove_old_grid(job_id_hash, source_or_target = 'target')
    refresh_frame_listbox()


def move_job_up(index):
    if index > 0:
        jobs.insert(index - 1, jobs.pop(index))
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()

def move_job_down(index):
    if index < len(jobs) - 1:
        jobs.insert(index + 1, jobs.pop(index))
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()

def move_job_to_top(index):
    if index > 0:
        jobs.insert(0, jobs.pop(index))
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()

def move_job_to_bottom(index):
    if index < len(jobs) - 1:
        jobs.append(jobs.pop(index))
        save_jobs(jobs_queue_file, jobs)
        update_job_listbox()


def edit_job_arguments_text(job):
    global default_values
    job_args = job.get('job_args', '')
    edit_arg_window = tk.Toplevel()
    edit_arg_window.title("Edit Job Arguments - tip greyed out values are defaults and will be used if needed, uncheck any argument to restore it to the default value")
    edit_arg_window.geometry("1050x500")
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
        value = ' '.join(value.split())  # Normalize spaces
        job_args_dict[arg] = value
    skip_keys = ['--source-paths', '--target-path', '--output-path', '--face-recognizer-model', '--ui-layouts', '--config-path', '--force-download', '--skip-download']
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
        if row >= 17:
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

        # Check for updated --frame-processors to update job['frame_processors']
        if '--frame-processors' in job['job_args']:
            job_args_list = job['job_args'].split()
            try:
                fp_index = job_args_list.index('--frame-processors')
                new_frame_processors_args = []
                for arg in job_args_list[fp_index + 1:]:
                    if arg.startswith('--'):
                        break
                    new_frame_processors_args.append(arg)
                job['frame_processors'] = ' '.join(new_frame_processors_args)
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
        check_if_needed(job, source_or_target)
        update_paths(job, selected_paths, source_or_target)
        
        if isinstance(job['sourcecache'], list):
            source_cache_exists = all(os.path.exists(cache) for cache in job['sourcecache'])
        else:
            source_cache_exists = os.path.exists(job['sourcecache'])
        
        if source_cache_exists and os.path.exists(job['targetcache']):
            job['status'] = 'pending'
        else:
            job['status'] = 'missing'

        save_jobs(jobs_queue_file, jobs)
        refresh_frame_listbox()

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
            audio_icon_path = os.path.join(working_dir, 'audioicon.png')
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
        debug_print(f"Created Thumbnail: {GREEN}{os.path.basename(grid_thumb_path)}{ENDC}\n\n")
    except Exception as e:
        debug_print(f"Failed to open grid image: {e}")

    for file in thumbnail_files:
        if os.path.exists(file):
            os.remove(file)
    if os.path.exists(list_file_path):
        os.remove(list_file_path)
    return button

def update_paths(job, path, source_or_target):
    
    if source_or_target == 'source':
        cache_path = copy_to_media_cache(path)
        if not isinstance(cache_path, list):
            cache_path = [cache_path]
        cache_key = 'sourcecache'
        job[cache_key] = cache_path

    if source_or_target == 'target':
        cache_path = copy_to_media_cache(path)
        cache_key = 'targetcache'
        job[cache_key] = cache_path
        copy_to_media_cache(path)
       
    if source_or_target == 'output':
        cache_key = 'output_path'
        cache_path = job['output_path']
    job[cache_key] = cache_path
    save_jobs(jobs_queue_file, jobs)

def run_job_args(current_run_job):
    global run_job_args
    if isinstance(current_run_job['sourcecache'], list):
        arg_source_paths = ' '.join(f'-s "{p}"' for p in current_run_job['sourcecache'])
    else:
        arg_source_paths = f"-s \"{current_run_job['sourcecache']}\""
        
    arg_target_path = f"-t \"{current_run_job['targetcache']}\""
    arg_output_path = f"-o \"{current_run_job['output_path']}\""

    simulated_args = f"{arg_source_paths} {arg_target_path} {arg_output_path} {current_run_job['headless']} {current_run_job['job_args']}"
    simulated_cmd = simulated_args.replace('\\\\', '\\')
    # ui_layouts = 'ui_layouts'
    # setattr(facefusion.globals, ui_layouts, ['QueueItUp'])

    if automatic1111:
        print (f"{venv_python} {base_dir}\\run2.py {simulated_cmd}")
        process = subprocess.Popen(
            f"{venv_python} {base_dir}\\run2.py {simulated_cmd}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line-buffered
        )
    else:
        #debug_print(f"python run.py {simulated_cmd}")
        process = subprocess.Popen(
            f"python run.py {simulated_cmd}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line-buffered
        )

    stdout_lines = []
    stderr_lines = []

    def handle_output(stream, lines, is_stdout):
        previous_line_was_progress = False
        while True:
            line = stream.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                lines.append(line)
                label = f"{BLUE}Job# {CURRENT_JOB_NUMBER}{ENDC}"
                if line.startswith("Processing:") or line.startswith("Analysing:"):
                    print(f"\r{label}: {GREEN}{line.strip()[:100]}{ENDC}", end='', flush=True)
                    previous_line_was_progress = True
                else:
                    if previous_line_was_progress:
                        print()  # Move to the next line before printing a new non-progress message
                        previous_line_was_progress = False
                    if "error" in line.lower() or "failed" in line.lower():
                        print(f"{label}: {RED}{line.strip()}{ENDC}")
                    else:
                        print(f"{label}: {YELLOW}{line.strip()}{ENDC}")
    stdout_thread = threading.Thread(target=handle_output, args=(process.stdout, stdout_lines, True))
    stderr_thread = threading.Thread(target=handle_output, args=(process.stderr, stderr_lines, False))

    stdout_thread.start()
    stderr_thread.start()

    stdout_thread.join()
    stderr_thread.join()

    return_code = process.poll()

    stdout = ''.join(stdout_lines)
    stderr = ''.join(stderr_lines)

    # Check for errors in the output
    if "error" in stdout.lower() or "error" in stderr.lower() or "failed" in stdout.lower() or "failed" in stderr.lower():
        current_run_job['status'] = 'failed'
        return_code = 1
    elif return_code == 0:
        current_run_job['status'] = 'completed'
    else:
        current_run_job['status'] = 'failed'
        with open(os.path.join(working_dir, f"stderr-{current_run_job['id']}.txt"), 'w') as f:
            f.write(stderr)
    
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
        orig_fps = eval(video_info['r_frame_rate'])  # Converts 'num/den' to float
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

    
def get_values_from_globals(state_name):
    state_dict = {}
    frame_processors_choices_dict = {}
    ff_choices_dict = {}
    import facefusion.choices
    from facefusion.processors.frame import globals as frame_processors_globals, choices as frame_processors_choices
    from facefusion import choices as ff_choices

    imp_current_values = [facefusion.globals, frame_processors_globals]
    other_choices = [frame_processors_choices, ff_choices]

    for imp_current_value in imp_current_values:
        for attr in dir(imp_current_value):
            if not attr.startswith("__"):
                value = getattr(imp_current_value, attr)
                try:
                    json.dumps(value)  # Check if the value is JSON serializable
                    state_dict[attr] = value  # Store or update the value in the dictionary
                except TypeError:
                    continue  # Skip values that are not JSON serializable

    for other_choice in other_choices:
        other_choice_dict = {}
        for attr in dir(other_choice):
            if not attr.startswith("__"):
                value = getattr(other_choice, attr)
                try:
                    json.dumps(value)  # Check if the value is JSON serializable
                    other_choice_dict[attr] = value  # Store or update the value in the dictionary
                except TypeError:
                    continue  # Skip values that are not JSON serializable
        
        if other_choice is frame_processors_choices:
            frame_processors_choices_dict = other_choice_dict
        elif other_choice is ff_choices:
            ff_choices_dict = other_choice_dict

    state_dict = preprocess_execution_providers(state_dict)
    
    if debugging:
        with open(os.path.join(working_dir, f"{state_name}.txt"), "w") as file:
            for key, val in state_dict.items():
                file.write(f"{key}: {val}\n")
        debug_print(f"{state_name}.txt created")
        
    if debugging:
        choice_dicts = {
            "frame_processors_choices_values.txt": frame_processors_choices_dict,
            "ff_choices_values.txt": ff_choices_dict
        }
        
        for filename, choice_dict in choice_dicts.items():
            with open(os.path.join(working_dir, filename), "w") as file:
                for key, val in choice_dict.items():
                    file.write(f"{key}: {val}\n")
            debug_print(f"{filename} created")

    return state_dict
    
def debug_print(*msgs):
    if debugging:
        custom_print(*msgs)


def custom_print(*msgs):
    global last_justtextmsg
    message = " ".join(str(msg) for msg in msgs)
    justtextmsg = re.sub(r'\033\[\d+m', '', message)
    last_justtextmsg = justtextmsg

    print(message)
    STATUS_WINDOW.value = last_justtextmsg
    
    return STATUS_WINDOW.value


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
        # Strip ANSI codes for STATUS_WINDOW
    message = re.sub(r'\033\[\d+m', '', message)
    STATUS_WINDOW.value = message
    return STATUS_WINDOW.value

def count_existing_jobs():
    global PENDING_JOBS_COUNT
    jobs = load_jobs(jobs_queue_file)
    PENDING_JOBS_COUNT = len([job for job in jobs if job['status'] in ['pending']])
    return PENDING_JOBS_COUNT 


def update_counters():
    global root, pending_jobs_var
    if pending_jobs_var:
        root.after(0, lambda: pending_jobs_var.set(f"Delete {PENDING_JOBS_COUNT} Pending Jobs"))


def create_and_verify_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as json_file:  
                json.load(json_file)
        except json.JSONDecodeError:
            backup_path = file_path + ".bak"
            shutil.copy(file_path, backup_path)
            debug_print(f"Backup of corrupt JSON file saved as '{backup_path}'. Please check it for salvageable data.\n\n")
            with open(file_path, "w") as json_file:
                json.dump([], json_file)
            debug_print(f"Original JSON file '{file_path}' was corrupt and has been reset to an empty list.\n\n")
    else:
        with open(file_path, "w") as json_file:
            json.dump([], json_file)
        debug_print(f"JSON file '{file_path}' did not exist and has been created.")


def load_jobs(file_path):
    status_priority = {'editing': 0, 'executing': 1, 'pending': 2, 'failed': 3, 'missing': 4, 'completed': 5, 'archived': 6}
    with open(file_path, 'r') as file:
        jobs = json.load(file)
    for job in jobs:
        if 'id' not in job or not job['id']:
            job['id'] = str(uuid.uuid4())
    jobs.sort(key=lambda x: status_priority.get(x['status'], 6))
    return jobs




def save_jobs(file_path, jobs):
    with open(file_path, 'w') as file:
        json.dump(jobs, file, indent=4)
      

def format_cli_value(value):
    if isinstance(value, list) or isinstance(value, tuple):
        return ' '.join(map(str, value))  # Convert list or tuple to space-separated string
    if value is None:
        return 'None'
    return str(value)


def check_for_completed_failed_or_aborted_jobs():
    jobs = load_jobs(jobs_queue_file)
    print_existing_jobs()  
    for job in jobs:
        if job['status'] == 'executing':
            job['status'] = 'pending'
            custom_print(f"{RED}A probable crash or aborted job execution was detected from your last use.... checking on status of unfinished jobs..{ENDC}\n\n")
            if isinstance(job['sourcecache'], list):
                source_basenames = [os.path.basename(path) for path in job['sourcecache']]
            else:
                source_basenames = os.path.basename(job['sourcecache'])

                custom_print(f"{GREEN}A job {GREEN}{source_basenames}{ENDC} to -> {GREEN}{os.path.basename(job['targetcache'])} was found that terminated early it will be moved back to the pending jobs queue - you have a Total of {PENDING_JOBS_COUNT + JOB_IS_RUNNING} in the Queue\n\n")
            save_jobs(jobs_queue_file, jobs)
    if not keep_completed_jobs:
        jobs_to_delete("completed")
        custom_print(f"{BLUE}All completed jobs have been removed, if you would like to keep completed jobs change the setting to True{ENDC}\n\n")


def sanitize_filename(filename):
    valid_chars = "-_.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    sanitized = ''.join(c if c in valid_chars else '_' for c in filename)
    sanitized = sanitized.strip()  # Remove leading and trailing spaces
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
                    cached_paths.append(cache_path)  # If size matches, assume it's the same file
                    break
            counter += 1

    # Ensure target_path is treated as a single path
    if isinstance(cached_paths, list) and len(cached_paths) == 1:
        return cached_paths[0]  # Return the single path
    else:
        return cached_paths  # Return the list of paths
        
        
def check_for_unneeded_media_cache():
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    if not os.path.exists(media_cache_dir):
        os.makedirs(media_cache_dir)

    # List all files in the media cache directory
    cache_files = os.listdir(media_cache_dir)
    jobs = load_jobs(jobs_queue_file)
    # Create a set to store all needed filenames from the jobs
    needed_files = set()
    for job in jobs:
        if job['status'] in {'pending', 'failed', 'missing', 'editing', 'archived', 'executing'}:
            # Now handle sourcecache as a list
            for source_cache_path in job['sourcecache']:
                source_basename = os.path.basename(source_cache_path)
                needed_files.add(source_basename)
            target_basename = os.path.basename(job['targetcache'])
            needed_files.add(target_basename)
    # Delete files that are not needed
    for cache_file in cache_files:
        if cache_file not in needed_files:
            os.remove(os.path.join(media_cache_dir, cache_file))
            debug_print(f"{GREEN}Deleted unneeded temp mediacache file: {cache_file}{ENDC}")


def check_if_needed(job, source_or_target):
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    if not os.path.exists(media_cache_dir):
        os.makedirs(media_cache_dir)

    with open(jobs_queue_file, 'r') as file:
        jobs = json.load(file)

    relevant_statuses = {'pending', 'executing', 'failed', 'missing', 'editing', 'archived'}
    file_usage_counts = {}

    # Create an index list for all jobs with relevant statuses and count file paths
    for other_job in jobs:
        if other_job['status'] in relevant_statuses:
            for key in ['sourcecache', 'targetcache']:
                paths = other_job[key] if isinstance(other_job[key], list) else [other_job[key]]
                for path in paths:
                    normalized_path = os.path.normpath(path)
                    file_usage_counts[normalized_path] = file_usage_counts.get(normalized_path, 0) + 1

    # Check and handle sourcecache paths
    if source_or_target in ['both', 'source']:
        source_cache_paths = job['sourcecache'] if isinstance(job['sourcecache'], list) else [job['sourcecache']]
        for source_cache_path in source_cache_paths:
            normalized_source_path = os.path.normpath(source_cache_path)
            file_use_count = file_usage_counts.get(normalized_source_path, 0)
            if file_use_count < 2:
                if os.path.exists(normalized_source_path):
                    try:
                        os.remove(normalized_source_path)
                        action_message = f"Successfully deleted the file: {GREEN}{os.path.basename(normalized_source_path)} {YELLOW}from the Temporary Mediacache Directory{ENDC} as it is no longer needed by any other jobs"
                    except Exception as e:
                        action_message = f"{RED}Failed to delete {YELLOW}{os.path.basename(normalized_source_path)} {YELLOW}from the Temporary Mediacache Directory{ENDC}: {e}"
                else:
                    action_message = f"{BLUE}No need to delete the file: {GREEN}{os.path.basename(normalized_source_path)} {YELLOW}from the Temporary Mediacache Directory{ENDC} as it does not exist."
            else:
                action_message = f"{BLUE}Did not delete the file: {GREEN}{os.path.basename(normalized_source_path)} {YELLOW}from the Temporary Mediacache Directory{ENDC} as it's needed by another job."
            debug_print(f"{action_message}\n\n")
            print_existing_jobs()
    # Check and handle targetcache path
    if source_or_target in ['both', 'target']:
        target_cache_path = job['targetcache']
        if isinstance(target_cache_path, list):
            target_cache_path = target_cache_path[0]  # Assuming the first element if it's erroneously a list
        normalized_target_path = os.path.normpath(target_cache_path)
        if file_usage_counts.get(normalized_target_path, 0) < 2:
            if os.path.exists(normalized_target_path):
                try:
                    os.remove(normalized_target_path)
                    action_message = (f"Successfully deleted the file: {GREEN}{os.path.basename(normalized_target_path)} {YELLOW}from the Temporary Mediacache Directory{ENDC} as it is no longer needed by any other jobs\n\n")
                except Exception as e:
                    action_message = (f"{RED}Failed to delete {YELLOW}{os.path.basename(normalized_target_path)} {YELLOW}from the Temporary Mediacache Directory{ENDC}: {e}\n\n")
            else:
                action_message = (f"{BLUE}No need to delete the file: {GREEN}{os.path.basename(normalized_target_path)} {YELLOW}from the Temporary Mediacache Directory{ENDC} as it does not exist.\n\n")
        else:
            action_message = (f"{BLUE}Did not delete the file: {GREEN}{os.path.basename(normalized_target_path)} {YELLOW}from the Temporary Mediacache Directory{ENDC} as it's needed by another job.\n\n")
        debug_print(f"{action_message}\n\n")
        print_existing_jobs()


def preprocess_execution_providers(data):
    new_data = data.copy()
    for key, value in new_data.items():
        if key == "execution_providers":
            new_providers = []
            for provider in value:
                if provider == "cuda" or provider == "CUDAExecutionProvider":
                    new_providers.append('cuda')
                elif provider == "cpu" or provider == "CPUExecutionProvider":
                    new_providers.append('cpu')
                elif provider == "coreml" or provider == "CoreMLExecutionProvider":
                    new_providers.append('coreml')
                # Assuming you don't want to keep original values that don't match, skip the else clause
            new_data[key] = new_providers  # Replace the old list with the new one
    return new_data
##

##
#startup_init_checks_and_cleanup, Globals and toggles
script_root = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_root)))
user_dir = "QueueItUp"
working_dir = os.path.normpath(os.path.join(base_dir, user_dir))
media_cache_dir = os.path.normpath(os.path.join(working_dir, "mediacache"))
debugging = True
keep_completed_jobs = True
default_values = {}
if not os.path.exists(working_dir):
    os.makedirs(working_dir)
if not os.path.exists(media_cache_dir):
    os.makedirs(media_cache_dir)
STATUS_WINDOW = gr.Textbox(label="Job Status", interactive=True)
jobs_queue_file = os.path.normpath(os.path.join(working_dir, "jobs_queue.json"))
    # ANSI Color Codes     
RED = '\033[91m'     #use this  
GREEN = '\033[92m'     #use this  
YELLOW = '\033[93m'     #use this  
BLUE = '\033[94m'     #use this  
ENDC = '\033[0m'       #use this    Resets color to default
version = facefusion.metadata.get('version')
queueitup_version = '2.6.9.1'
print(f"{BLUE}FaceFusion version: {GREEN}{version}{ENDC}")
print(f"{BLUE}QueueItUp! version: {GREEN}{queueitup_version}{ENDC}")
automatic1111 = "AUTOMATIC1111" in version
next_beta = "NEXT" in version
if not automatic1111:
    default_values = get_values_from_globals("default_values")  
    settings_path = default_values.get("config_path", "")
    
if automatic1111:
    import facefusion.core2 as core2
    venv_python = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(base_dir)), 'venv', 'scripts', 'python.exe'))
    settings_path = os.path.join(base_dir, "facefusion.ini")




initialize_settings()
create_and_verify_json(jobs_queue_file)

thumbnail_dir = os.path.normpath(os.path.join(working_dir, "thumbnails"))

ADD_JOB_BUTTON = gr.Button("Add Job ", variant="primary")
RUN_JOBS_BUTTON = gr.Button("Run Jobs", variant="primary")
EDIT_JOB_BUTTON = gr.Button("Edit Jobs")
SETTINGS_BUTTON = gr.Button("Change Settings")
JOB_IS_RUNNING = 0
JOB_IS_EXECUTING = 0
CURRENT_JOB_NUMBER = 0
edit_queue_running = False

                
                                                          
                     
PENDING_JOBS_COUNT = count_existing_jobs()

last_justtextmsg = ""
root = None
pending_jobs_var = None

        

gradio_version = pkg_resources.get_distribution("gradio").version
debug_print(f"gradio version: {gradio_version}")
debug_print("FaceFusion Base Directory:", base_dir)
debug_print("QueueItUp Working Directory:", working_dir)
debug_print("QueueItUp Media Cache Directory:", media_cache_dir)
debug_print("Jobs Queue File:", jobs_queue_file)
if automatic1111:
    debug_print("the Venv Python Path is:", venv_python)
debug_print(f"{BLUE}Welcome Back To QueueItUp The FaceFusion Queueing Addon{ENDC}\n\n")
debug_print(f"QUEUEITUP{BLUE} COLOR OUTPUT KEY")
debug_print(f"{BLUE}BLUE = normal QueueItUp color output key")
debug_print(f"{GREEN}GREEN = file name, cache managment or processing progress")
debug_print(f"{YELLOW}YELLOW = informational")
debug_print(f"{RED}RED =QueueItUp detected a Problem{ENDC}\n\n")
debug_print(f"{YELLOW}QueueItUp is Checking Status{ENDC}\n")

check_for_completed_failed_or_aborted_jobs()
debug_print(f"{GREEN}STATUS CHECK COMPLETED. {BLUE}You are now ready to QUEUE IT UP!{ENDC}")
