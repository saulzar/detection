
from scripts.load_figures import make_chart, paired
from scripts.datasets import load_dataset, get_counts
from os import path

from tools import *
import tools.window as window


import datetime
import random

from matplotlib.patches import Patch
from matplotlib.lines import Line2D

import matplotlib.pyplot as plt

import numpy as np
import torch

import csv


base_path = '/home/oliver/storage/export/'


def subset(text, image_counts):
    return [count for count in image_counts if text in count.image_file]

def plot_estimate(images, colour, style="-", estimates=True):
    estimate_points = transpose_structs(pluck('estimate', images))
    times = pluck('time', images)

    mask = torch.ByteTensor([1 if i.category != 'discard' else 0 for i in images])

    def f(xs):
        return window.masked_mean(torch.Tensor(xs), mask=mask, window=7, clamp=False).numpy()

    # middle = window.rolling_window(torch.Tensor(estimates.middle), window=5).mean(1).numpy()
    estimate_points = estimate_points._map(f)
    plt.plot(times, estimate_points.middle, colour, linestyle=style)

    if estimates:
        plt.fill_between(times, estimate_points.upper, estimate_points.lower, facecolor=colour, alpha=0.4)


def plot_points(images, colour, marker, fill='none', key=lambda i: i.truth):
    truth = list(map(key, images))
    times = pluck('time', images)

    plt.scatter(times, truth, marker=marker, edgecolors=colour, facecolors=fill)


def pick(images, classes):
    return [i for i in images if i.category in classes]


def plot_subset(images, colour, style="-", estimates=True):

    plot_estimate(images, colour=colour, style=style, estimates=estimates)

    plot_points(pick(images, ['train']), colour,   '^')
    plot_points(pick(images, ['validate']), colour, 's')
    plot_points(pick(images, ['discard']), colour,  'o', key=lambda i: i.estimate.middle)

    plot_points(pick(images, ['test']), colour,    'P', fill='g')


def plot_runs(*runs, loc='upper left', estimates=True):
  
    def run_legend(run):
        return Line2D([0], [0], color=run.colour, linestyle=run.get('style', '-'), label=run.label)

    legend = list(map(run_legend, runs)) + [
        Line2D([0], [0], marker='P', color='g', markeredgecolor='y', linestyle='None', label='test'),

        Line2D([0], [0], marker='^', color='none',  markeredgecolor='y', linestyle='None', label='train'),
        Line2D([0], [0], marker='s', color='none', markeredgecolor='y', linestyle='None', label='validate'),

        Line2D([0], [0], marker='o', color='none', markeredgecolor='y', linestyle='None', label='discard')
    ]

    fig, ax = make_chart(size =(20, 10))



    plt.xlabel("date")
    plt.ylabel("count")

    plt.gcf().autofmt_xdate()

    for run in runs:
        plot_subset(run.data, run.colour, style=run.get('style', '-'), estimates=estimates)

    ax.set_ylim(ymin=0)


    ax.legend(handles=legend, loc=loc)
    return fig




def load(filename):
    return load_dataset(path.join(base_path, filename))




datasets = struct(
    scott_base = 'scott_base.json',
    scott_base_100 = 'scott_base_100.json',
    seals      = 'seals.json',
    seals_102  = 'seals_102.json',

    seals_shanelle  = 'seals_shanelle.json',
)


def flatten_dict(dd, separator='_', prefix=''):
    return { prefix + separator + k if prefix else k : v
             for kk, vv in dd.items()
             for k, v in flatten_dict(vv, separator, kk).items()
             } if isinstance(dd, dict) else { prefix : dd }


def export_csv(file, fields, rows):

    with open(file, mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row._to_dicts())

def export_counts(file, counts):

    fields = ['image_file', 'time', 'truth', 'category', 'lower', 'estimate', 'upper']

    def f(counts):
        return struct(
            image_file=counts.image_file, 
            time= counts.time.strftime("%Y-%m-%d %H:%M:%S"), 
            truth=None if counts.category=='new' else counts.truth, 
            category=counts.category,
            lower = counts.estimate.upper,
            estimate  = counts.estimate.middle,
            upper = counts.estimate.lower
        )

    export_csv(file, fields, list(map(f, counts)))

def plot_together(figure_path, loaded):


    scott_base = get_counts(loaded['scott_base'])
    scott_base_100 = get_counts(loaded['scott_base_100'])

    images_100 = {image.image_file:image for image in scott_base_100 if image.category != 'new'}

    def hide_duplicate(image):
        return image._extend(category = 'ignore' 
            if (image.image_file in images_100) and (image.category != 'discard')
            else image.category)
            

    scott_base = list(map(hide_duplicate, scott_base))

    cam_b_100  = subset("CamB", scott_base_100)
    cam_c_100  = subset("CamC", scott_base_100)

    cam_b  = subset("CamB", scott_base)
    cam_c  = subset("CamC", scott_base)

    fig = plot_runs(
        struct(data = cam_b_100, colour='tab:olive', style="--", label="camera b (100)"),
        struct(data = cam_b, colour='forestgreen', label="camera b"),

        struct(data = cam_c_100, colour='skyblue', style="--", label="camera c (100)" ),
        struct(data = cam_c, colour='royalblue', label="camera c" ),        
        estimates=False
    )

    fig.savefig(path.join(figure_path, "scott_base_combined.pdf"), bbox_inches='tight')



def plot_counts(loaded):
    figure_path = "/home/oliver/sync/figures/seals/"
    plot_together(figure_path, loaded)

    for k in ['scott_base', 'scott_base_100']:
        scott_base = get_counts(loaded[k])

        cam_b  = subset("CamB", scott_base)
        cam_c  = subset("CamC", scott_base)

        fig = plot_runs(
            struct(data = cam_b, colour='g', label="camera b"),
            struct(data = cam_c, colour='y', label="camera c" ),
        )

        fig.savefig(path.join(figure_path, k + ".pdf"), bbox_inches='tight')
        export_counts(path.join(figure_path, k + "_cam_b.csv"), cam_b)
        export_counts(path.join(figure_path, k + "_cam_c.csv"), cam_c)


    for k in ['seals', 'seals_102', 'seals_shanelle']:
        seals_total = get_counts(loaded[k])
        seals_pairs = get_counts(loaded[k], class_id = 1)

        fig = plot_runs(
            struct(data = seals_total, colour='y', label="total"),
            struct(data = seals_pairs, colour='c', label="pairs"),

            loc='upper right'
        )

        fig.savefig(path.join(figure_path, k + ".pdf"), bbox_inches='tight')
        export_counts(path.join(figure_path, k + ".csv"), seals_total)
        export_counts(path.join(figure_path, k + "_pairs.csv"), seals_pairs)   


def show_errors(loaded):

    # print ("--------" + k + "--------")
    truth = {image.image_file:image.truth
        for image in get_counts(loaded['seals']) if image.category=='test'}

    truth2 = {image.image_file:image.truth
        for image in get_counts(loaded['seals_shanelle']) if image.category=='test'}

    estimate = {image.image_file:image.estimate.middle 
        for image in get_counts(loaded['seals']) if image.category=='test'}

    # [(k, truth[k] - estimate[k], truth[k] - truth2[k]) for k in truth.keys()]

    errors = struct (
        human_human = [abs(truth[k] - truth2[k]) for k in truth.keys()],
        human_estimate = [abs(truth[k] - estimate[k]) for k in truth.keys()],
        human_estimate2 = [abs(truth2[k] - estimate[k]) for k in truth.keys()]
    )

    print(errors._map(np.mean))


    

if __name__ == '__main__':
      
    loaded = datasets._map(load)

    plot_counts(loaded)
    show_errors(loaded)




    # plot_counts(path.join())
