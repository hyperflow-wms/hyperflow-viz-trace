#!/usr/bin/env python3

import os
import argparse
import math
from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
import colorsys
from natsort import natsorted
import mplcursors


def load_jsonl(path):
    df = pd.read_json(path, lines=True)
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
    return df


def build_job_map(job_descriptions):
    return {job['jobId']: job for job in job_descriptions.to_dict('records')}


def assert_single_value(items, key):
    values = set(item[key] for item in items)
    if len(values) != 1:
        raise ValueError(f"Inconsistent values for '{key}': {values}")
    return values.pop()


def extract_event_metrics(metrics_df):
    return metrics_df[metrics_df['parameter'] == 'event'].copy()



def extract_nodes_jobs(event_metrics, job_map):
    first_event_time = event_metrics['time'].min()
    nodes_jobs = defaultdict(lambda: defaultdict(dict))

    for _, row in event_metrics.iterrows():
        job_id = row['jobId']
        node = job_map[job_id]['nodeName']
        event = row['value']
        timestamp = (row['time'] - first_event_time).total_seconds()

        job_events = nodes_jobs[node][job_id]

        if event in job_events:
            if event == 'handlerStart' and timestamp > job_events[event]:
                print(f'WARNING: inconsistent logs - second handlerStart for job {job_id}, keeping earlier')
                continue
            else:
                print(f'WARNING: duplicate event "{event}" for job {job_id}, ignoring second occurrence')
                continue

        job_events[event] = timestamp

    return nodes_jobs


def split_disjoint_groups(jobs):
    intervals = []
    for job_id, details in jobs.items():
        start = details.get('handlerStart')
        end = details.get('handlerEnd') or details.get('jobEnd')
        if start is None or end is None:
            print(f"WARNING: Skipping job {job_id} — missing handlerStart or end time")
            continue
        intervals.append((start, end, job_id))
    intervals.sort()

    groups = []
    group_end_times = []

    for start, end, job_id in intervals:
        placed = False
        for i, group_end in enumerate(group_end_times):
            if start > group_end:
                groups[i].append(job_id)
                group_end_times[i] = end
                placed = True
                break
        if not placed:
            groups.append([job_id])
            group_end_times.append(end)

    return groups


def extract_nodes_jobs_nonoverlap(nodes_jobs):
    output = {}
    for node, jobs in nodes_jobs.items():
        disjoint = split_disjoint_groups(jobs)
        for i, group in enumerate(disjoint):
            key = f"{node}_{i}"
            output[key] = group
    return output


def extract_ordered_task_types(event_metrics):
    latest_by_name = event_metrics.groupby('name')['time'].max()
    return list(latest_by_name.sort_values().index)


def extract_stages(event_metrics, event_start='jobStart', event_end='jobEnd'):
    first_event_time = event_metrics['time'].min()
    stage_events = defaultdict(list)

    for _, row in event_metrics.iterrows():
        event = row['value']
        if event not in (event_start, event_end):
            continue

        offset = (row['time'] - first_event_time).total_seconds()
        stage_events[offset].append(1 if event == event_start else -1)

    stages = [{'timeOffset': 0.0, 'activeItems': 0}]
    active = 0

    for time, changes in sorted(stage_events.items()):
        for change in changes:
            active += change
        stages.append({'timeOffset': time, 'activeItems': active})

    return stages


def lighten_color(color, amount=0.5):
    r, g, b = to_rgb(color)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return colorsys.hls_to_rgb(h, 1 - amount * (1 - l), s)


def visualize_dir(source_dir, display_only, show_active_jobs, plot_full_names, interactive):
    metrics_path = os.path.join(source_dir, 'metrics.jsonl')
    job_desc_path = os.path.join(source_dir, 'job_descriptions.jsonl')

    metrics_df = load_jsonl(metrics_path)
    job_descriptions = load_jsonl(job_desc_path)
    job_map = build_job_map(job_descriptions)

    workflow_name = assert_single_value(job_descriptions.to_dict('records'), 'workflowName')
    workflow_size = assert_single_value(job_descriptions.to_dict('records'), 'size')
    workflow_version = assert_single_value(job_descriptions.to_dict('records'), 'version')

    event_metrics = extract_event_metrics(metrics_df)
    nodes_jobs = extract_nodes_jobs(event_metrics, job_map)
    nodes_jobs_no = extract_nodes_jobs_nonoverlap(nodes_jobs)
    task_types = extract_ordered_task_types(event_metrics)

    row_half = 15
    row_full = row_half * 2
    sorted_nodes = natsorted(nodes_jobs_no.keys())
    y_labels = sorted_nodes if plot_full_names else [k.rsplit('-', 1)[-1] for k in sorted_nodes]
    y_ticks = [row_half + i * row_full for i in range(len(sorted_nodes))]

    max_time = 0.0
    for node_key in sorted_nodes:
        for job_id in nodes_jobs_no[node_key]:
            full_node = job_map[job_id]['nodeName']
            details = nodes_jobs[full_node][job_id]
            for evt in ['handlerStart', 'jobStart', 'jobEnd', 'handlerEnd']:
                if evt in details:
                    max_time = max(max_time, details[evt])
    max_time = math.ceil(max_time)

    if show_active_jobs:
        fig, (ax, ax2) = plt.subplots(2, 1, figsize=(25, 15), gridspec_kw={'height_ratios': [3, 1]})
        ax.set_title(f'Workflow: {workflow_name}')
    else:
        fig, ax = plt.subplots(figsize=(25, 15))
        ax.set_title(f'Workflow: {workflow_name}')

    cmap = plt.get_cmap("gist_rainbow", len(task_types))
    colors_for_types = dict(zip(task_types, [cmap(i) for i in range(len(task_types))]))

    ax.set_xlim(0, max_time)
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Node offset')
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.grid(True)

    # 🔁 Alternating background shading by physical node
    last_node = None
    shade = False
    for i, node_key in enumerate(sorted_nodes):
        job_id = nodes_jobs_no[node_key][0]
        full_node = job_map[job_id]['nodeName']
        if full_node != last_node:
            shade = not shade
            last_node = full_node
        if shade:
            y_start = row_full * i
            ax.axhspan(y_start, y_start + row_full, color='gray', alpha=0.2, zorder=0)

    patches_by_task = defaultdict(list)
    legend_labels = {}

    for i, node in enumerate(sorted_nodes):
        jobs = nodes_jobs_no[node]
        bar_y = row_half + row_full * i
        for job_id in jobs:
            job = job_map[job_id]
            node_name = job['nodeName']
            job_details = nodes_jobs[node_name][job_id]

            # Skip jobs missing jobStart or jobEnd
            if 'jobStart' not in job_details or 'jobEnd' not in job_details:
                print(f"WARNING: Skipping job {job_id} — missing jobStart or jobEnd")
                continue

            task = job['name']
            color = colors_for_types[task]

            x = job_details['jobStart']
            width = job_details['jobEnd'] - job_details['jobStart']
            rect = mpatches.Rectangle((x, bar_y - 8), width, 16)
            patches_by_task[task].append((rect, job_id, x, x + width))

            if task not in legend_labels:
                legend_labels[task] = color

    for task, rect_data in patches_by_task.items():
        rects = [r[0] for r in rect_data]
        pc = PatchCollection(rects, facecolor=colors_for_types[task], label=task)
        ax.add_collection(pc)

        if interactive:
            cursor = mplcursors.cursor(pc, hover=True)

            @cursor.connect("add")
            def on_add(sel, task=task, data=rect_data):
                idx = sel.index
                rect_info = data[idx[0] if isinstance(idx, tuple) else idx]
                job_id = rect_info[1]
                start = rect_info[2]
                end = rect_info[3]
                job = job_map[job_id]
                sel.annotation.set_text(
                    f"{job['name']}\nJob ID: {job_id}\nStart: {start:.2f}s\nEnd: {end:.2f}s"
                )

    ax.legend(
        [mpatches.Patch(color=legend_labels[task], label=task) for task in legend_labels],
        list(legend_labels.keys()),
        loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=3, fancybox=True, shadow=True
    )

    if show_active_jobs:
        ax2.set_xlim(0, max_time)
        ax2.set_xlabel('Time [s]')
        ax2.set_ylabel('Active jobs')
        ax2.grid(True)

        stages = extract_stages(event_metrics)
        stage_x = [s['timeOffset'] for s in stages]
        stage_y = [s['activeItems'] for s in stages]

        ax2.step(stage_x, stage_y, where='post', label='Active jobs')
        ax2.legend(loc='best')

    filename = f'{workflow_name}-{workflow_size}-{workflow_version}.png'

    if display_only:
        plt.show()
    else:
        plt.savefig(filename)
        print(f"Chart saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='HyperFlow execution visualizer with tooltips and lane shading')
    parser.add_argument('-s', '--source', type=str, required=True, help='Directory with parsed logs')
    parser.add_argument('-d', '--show', action='store_true', default=False, help='Display plot instead of saving to file')
    parser.add_argument('-a', '--show-active-jobs', action='store_true', default=False, help='Display the number of active jobs subplot')
    parser.add_argument('-f', '--full-nodes-names', action='store_true', default=False, help='Display full nodes\' names')
    parser.add_argument('-i', '--interactive', action='store_true', default=False, help='Enable interactive hover tooltips')
    args = parser.parse_args()

    visualize_dir(args.source, args.show, args.show_active_jobs, args.full_nodes_names, args.interactive)


if __name__ == '__main__':
    main()
