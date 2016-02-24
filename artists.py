'''
Tools for visualizing data.
'''


### import ####################################################################


import os
import collections

import numpy as np
from numpy import r_

import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.gridspec as grd
import matplotlib.colors as mplcolors
matplotlib.rcParams['contour.negative_linestyle'] = 'solid'
matplotlib.rcParams['font.size'] = 14

import kit  # legacy...
import kit as wt_kit


### artist helpers ############################################################


def _title(fig, title, subtitle, margin=1):
    fig.suptitle(title, fontsize=20)
    height = fig.get_figheight()  # inches
    distance = margin / 2.  # distance from top of plot, in inches
    ratio = 1 - distance/height
    fig.text(0.5, ratio, subtitle, fontsize=18, ha='center', va='top')


def corner_text(text, distance=0.075, ax=None, corner='UL', factor=200, 
                fontsize=None, background_alpha=0.75):
    '''
    Place some text in the corner of the figure.
    
    Parameters
    ----------
    text : str
        The text to use.
    distance : number (optional)
        Distance from the corner. Default is 0.05.
    ax : axis (optional)
        The axis object to label. If None, uses current axis. Default is None.
    corner : {'UL', 'LL', 'UR', 'LR'} (optional)
        The corner to label. Upper left, Lower left etc. Default is UL.
    factor : number (optional)
        Scaling factor. Default is 200.
    fontsize : number (optional)
        Text fontsize. If None, uses the matplotlib default. Default is None.
    background_alpha : number (optional)
        Transparency of background bounding box. Default is 0.75. Set to one
        to make box opaque.
    
    Returns
    -------
    text
        The matplotlib text object.
    '''
    # get axis
    if ax is None:
        ax = plt.gca()
    [h_scaled, v_scaled], [va, ha] = get_scaled_bounds(ax, corner, distance, factor)
    # apply text
    props = dict(boxstyle='square', facecolor='white', alpha=background_alpha)
    args = [v_scaled, h_scaled, text]
    kwargs = {}
    kwargs['fontsize'] = fontsize
    kwargs['verticalalignment'] = va
    kwargs['horizontalalignment'] = ha
    kwargs['bbox'] = props
    kwargs['transform'] = ax.transAxes
    if 'zlabel' in ax.properties().keys():  # axis is 3D projection
        out = ax.text2D(*args, **kwargs)
    else:
        out = ax.text(*args, **kwargs)
    return out


def create_figure(width='single', nrows=1, cols=[1, 'cbar'], margin=1.,
                  hspace=0.25, wspace=0.25, cbar_width=0.25, aspects=[]):
    '''
    Re-parameterization of matplotlib figure creation tools, exposing variables
    convinient for the Wright Group.

    Figures are defined primarily by their width. Height is defined by the
    aspect ratios of the subplots contained within. hspace, wspace, and
    cbar_width are defined in inches, making it easier to make consistent
    plots. Margins are enforced to be equal around the entire plot, starting
    from the edges of the subplots.

    Parameters
    ----------
    width : {'single', 'double'} or float (optional)
        The total width of the generated figure. Can be given in inches
        directly, or can be specified using keys. Default is 'single' (6.5
        inches).
    nrows : int (optional)
        The number of subplot rows in the figure. Default is 1.
    cols : list (optional)
        A list of numbers, defining the number and width-ratios of the
        figure columns. May also contain the special string 'cbar', defining
        a column as a colorbar-containing column. Default is [1, 'cbar'].
    margin : float (optional)
        Margin in inches. Margin is applied evenly around the figure, starting
        from the subplot boundaries (so that ticks and labels appear in the
        margin). Default is 1.
    hspace : float (optional)
        The 'height space' (space seperating two subplots vertically), in
        inches. Default is 0.25.
    wspace : float (optional)
        The 'width space' (space seperating two subplots horizontally), in
        inches. Default is 0.25.
    cbar_width : float (optional)
        The width of the colorbar in inches. Default is 0.25.
    aspects : list of lists (optional)
        Define the aspect ratio of individual subplots. List of lists, each
        sub-ist having the format [[row, col], aspect]. The figure will expand
        vertically to acomidate the defined aspect ratio. Aspects are V/H so
        aspects larger than 1 will be taller than wide and vice-versa for
        aspects smaller than 1. You may only define the aspect for one subplot
        in each row. If no aspect is defined for a particular row, the leftmost
        subplot will have an aspect of 1. Default is [].

    Returns
    -------
    tuple
        (matplotlib.figure.Figure, matplotlib.gridspec.GridSpec). GridSpec
        contains SubplotSpec objects that can have axes placed into them.
        The SubplotSpec objects can be accessed through indexing: [row, col].
        Slicing works, for example ``cax = plt.subplot(gs[:, -1])``. See
        `matplotlib documentation <http://matplotlib.org/1.4.0/users/gridspec.html#gridspec-and-subplotspec>`_
        for more information.

    Notes
    -----
    To ensure the margins work as expected, save the fig with
    the same margins (``pad_inches``) as specified in this function. Common
    savefig call:
    ``plt.savefig(plt.savefig(output_path, dpi=300, transparent=True,
    pad_inches=1))``

    See also
    --------
    wt.artists.plot_margins
        Plot lines to visualize the figure edges, margins, and centers. For
        debug and design purposes.
    wt.artsits.subplots_adjust
        Enforce margins for figure generated elsewhere.
    '''
    # get width
    if width == 'double':
        figure_width = 14.
    elif width == 'single':
        figure_width = 6.5
    else:
        figure_width = float(width)
    # check if aspect constraints are valid
    rows_in_aspects = [item[0][0] for item in aspects]
    if not len(rows_in_aspects) == len(set(rows_in_aspects)):
        raise Exception('can only specify aspect for one plot in each row')
    # get width avalible to subplots (not including colorbars)
    total_subplot_width = figure_width - 2*margin
    total_subplot_width -= (len(cols)-1) * wspace  # whitespace in width
    total_subplot_width -= cols.count('cbar') * cbar_width  # colorbar width
    # converters
    def in_to_mpl(inches, total, n):
        return (inches*n)/(total-inches*n+inches)
    def mpl_to_in(mpl, total, n):
        return (total/(n+mpl*(n-1)))*mpl
    # calculate column widths, width_ratio
    subplot_ratios = np.array([i for i in cols if not i == 'cbar'], dtype=np.float)
    subplot_ratios /= sum(subplot_ratios)
    subplot_widths = total_subplot_width * subplot_ratios
    width_ratios = []
    cols_idxs = []
    i = 0
    for col in cols:
        if not col == 'cbar':
            width_ratios.append(subplot_widths[i])
            cols_idxs.append(i)
            i += 1
        else:
            width_ratios.append(cbar_width)
            cols_idxs.append(np.nan)
    # calculate figure height, height_ratios, figure height
    subplot_heights = []
    for row_index in range(nrows):
        if row_index in rows_in_aspects:
            aspect = aspects[rows_in_aspects.index(row_index)][1]
            col_index = aspects[rows_in_aspects.index(row_index)][0][1]
            height = subplot_widths[col_index] * aspect
            subplot_heights.append(height)
        else:
            # make the leftmost (zero indexed) plot square as default
            subplot_heights.append(subplot_widths[0])
    height_ratios = subplot_heights
    figure_height = sum(subplot_heights)
    figure_height += (nrows-1) * hspace
    figure_height += 2*margin
    # make figure
    fig = plt.figure(figsize=[figure_width, figure_height])
    # get hspace, wspace in relative units
    hspace = in_to_mpl(hspace, figure_height-2*margin, nrows)
    wspace = in_to_mpl(wspace, figure_width-2*margin, len(cols))
    # make gridpsec
    gs = grd.GridSpec(nrows, len(cols), hspace=hspace, wspace=wspace,
                      width_ratios=width_ratios, height_ratios=height_ratios)
    # finish
    subplots_adjust(fig, inches=margin)
    return fig, gs


def diagonal_line(xi, yi, ax=None, c='k', ls=':', lw=1):
    '''
    Plot a diagonal line.
    
    Parameters
    ----------
    xi : 1D array-like
        The x axis points.
    yi : 1D array-like
        The y axis points.
    ax : axis (optional)
        Axis to plot on. If none is supplied, the current axis is used.
    c : string (optional)
        Line color. Default is k.
    ls : string (optional)
        Line style. Default is : (dotted).
    lw : float (optional)
        Line width. Default is 1.
    
    Returns
    -------
    matplotlib.lines.Line2D object
        The plotted line.
    '''
    # get axis
    if ax is None:
        ax = plt.gca()
    # make plot
    diag_min = max(min(xi), min(yi))
    diag_max = min(max(xi), max(yi))
    line = ax.plot([diag_min, diag_max], [diag_min, diag_max], c=c, ls=ls, lw=lw)
    return line


def get_color_cycle(n, cmap='rainbow', rotations=3):
    '''
    Get a list of RGBA colors. Useful for plotting lots of elements, keeping
    the color of each unique.

    Parameters
    ----------
    n : integer
        The number of colors to return.
    cmap : string (optional)
        The colormap to use in the cycle. Default is rainbow.
    rotations : integer (optional)
        The number of times to repeat the colormap over the cycle. Default is
        3.
    
    Returns
    -------
    list
        List of RGBA lists.
    '''
    cmap = colormaps[cmap]
    if np.mod(n, rotations) == 0:
        per = np.floor_divide(n, rotations)
    else:
        per = np.floor_divide(n, rotations) + 1
    vals = list(np.linspace(0, 1, per))
    vals = vals * rotations
    vals = vals[:n]
    print vals
    out = cmap(vals)
    return out


def get_constant_text(constants):
    string_list = [constant.get_label(show_units = True, points = True) for constant in constants]
    text = '    '.join(string_list)
    return text


def get_scaled_bounds(ax, position, distance=0.1, factor=200):
    # get bounds
    x0, y0, width, height = ax.bbox.bounds
    width_scaled = width/factor
    height_scaled = height/factor
    # get scaled postions
    if position == 'UL':
        v_scaled = distance/width_scaled
        h_scaled = 1-(distance/height_scaled)
        va = 'top'
        ha = 'left'
    elif position == 'LL':
        v_scaled = distance/width_scaled
        h_scaled = distance/height_scaled
        va = 'bottom'
        ha = 'left'
    elif position == 'UR':
        v_scaled = 1-(distance/width_scaled)
        h_scaled = 1-(distance/height_scaled)
        va = 'top'
        ha = 'right'
    elif position == 'LR':
        v_scaled = 1-(distance/width_scaled)
        h_scaled = distance/height_scaled
        va = 'bottom'
        ha = 'right'
    else:
        print 'corner not recognized'
        v_scaled = h_scaled = 1.
        va = 'center'
        ha = 'center'
    return [h_scaled, v_scaled], [va, ha]


def make_cubehelix(gamma=1.0, s=0.5, r=-1.5, h=0.5,
                   lum_rev=False, darkest=0.8, plot=False):
    '''
    Define cubehelix type colorbars. \n
    gamma intensity factor, s start color, 
    r rotations, h 'hue' saturation factor \n
    Returns white to black LinearSegmentedColormap. \n
    Written by Dan \n
    For more information see http://arxiv.org/abs/1108.5083 .
    '''
    # isoluminescent curve--helical color cycle
    def get_color_function(p0, p1):
        def color(x):
            # Apply gamma factor to emphasise low or high intensity values
            #xg = x ** gamma

            # Calculate amplitude and angle of deviation from the black
            # to white diagonal in the plane of constant
            # perceived intensity.
            xg = darkest * x**gamma
            lum = 1-xg  # starts at 1
            if lum_rev:
                lum = lum[::-1]
            a = lum.copy()  # h * lum*(1-lum)/2.
            a[lum<0.5] = h * lum[lum<0.5]/2.
            a[lum>=0.5] = h * (1-lum[lum>=0.5])/2.
            phi = 2 * np.pi * (s / 3 + r * x)
            out = lum + a * (p0 * np.cos(phi) + p1 * np.sin(phi))
            return out
        return color
    rgb_dict = {'red':   get_color_function(-0.14861, 1.78277),
                'green': get_color_function(-0.29227, -0.90649),
                'blue':  get_color_function(1.97294, 0.0)}
    cbar = matplotlib.colors.LinearSegmentedColormap('cubehelix', rgb_dict)
    if plot:
        plot_colormap(cbar)
    return cbar
    

def make_colormap(seq, name='CustomMap', plot=False):
    '''
    Return a LinearSegmentedColormap
    seq: a sequence of floats and RGB-tuples. The floats should be increasing
    and in the interval (0,1). \n
    from http://nbviewer.ipython.org/gist/anonymous/a4fa0adb08f9e9ea4f94#
    '''
    seq = [(None,) * 3, 0.0] + list(seq) + [1.0, (None,) * 3]
    cdict = {'red': [], 'green': [], 'blue': []}
    for i, item in enumerate(seq):
        if isinstance(item, float):
            r1, g1, b1 = seq[i - 1]
            r2, g2, b2 = seq[i + 1]
            cdict['red'].append([item, r1, r2])
            cdict['green'].append([item, g1, g2])
            cdict['blue'].append([item, b1, b2])
    cmap = mplcolors.LinearSegmentedColormap(name, cdict)
    if plot:
        plot_colormap(cmap)
    return cmap
    

def nm_to_rgb(nm):
    '''
    returns list [r, g, b] (zero to one scale) for given input in nm \n
    original code - http://www.physics.sfasu.edu/astro/color/spectra.html
    '''

    w = int(nm)

    # color -------------------------------------------------------------------

    if w >= 380 and w < 440:
        R = -(w - 440.) / (440. - 350.)
        G = 0.0
        B = 1.0
    elif w >= 440 and w < 490:
        R = 0.0
        G = (w - 440.) / (490. - 440.)
        B = 1.0
    elif w >= 490 and w < 510:
        R = 0.0
        G = 1.0
        B = -(w - 510.) / (510. - 490.)
    elif w >= 510 and w < 580:
        R = (w - 510.) / (580. - 510.)
        G = 1.0
        B = 0.0
    elif w >= 580 and w < 645:
        R = 1.0
        G = -(w - 645.) / (645. - 580.)
        B = 0.0
    elif w >= 645 and w <= 780:
        R = 1.0
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0

    # intensity correction ----------------------------------------------------

    if w >= 380 and w < 420:
        SSS = 0.3 + 0.7*(w - 350) / (420 - 350)
    elif w >= 420 and w <= 700:
        SSS = 1.0
    elif w > 700 and w <= 780:
        SSS = 0.3 + 0.7*(780 - w) / (780 - 700)
    else:
        SSS = 0.0
    SSS *= 255

    return [float(int(SSS*R)/256.),
            float(int(SSS*G)/256.),
            float(int(SSS*B)/256.)]


def pcolor_helper(xi, yi, zi):
    '''
    accepts xi, yi, zi as the normal rectangular arrays
    that would be given to contorf etc \n
    returns list [X, Y, Z] appropriate for feeding directly
    into matplotlib.pyplot.pcolor so that the pixels are centered correctly. \n
    '''

    x_points = np.zeros(len(xi)+1)
    y_points = np.zeros(len(yi)+1)

    for points, axis in [[x_points, xi], [y_points, yi]]:
        for j in range(len(points)):
            if j == 0:  # first point
                points[j] = axis[0] - (axis[1] - axis[0])
            elif j == len(points)-1:  # last point
                points[j] = axis[-1] + (axis[-1] - axis[-2])
            else:
                points[j] = np.average([axis[j], axis[j-1]])

    X, Y = np.meshgrid(x_points, y_points)

    return X, Y, zi


def plot_colormap(cmap):
    plt.figure(figsize=[8, 4])
    gs = grd.GridSpec(2, 1, height_ratios=[1, 10], hspace=0.05)
    # colorbar
    ax = plt.subplot(gs[0])
    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))
    ax.imshow(gradient, aspect='auto', cmap=cmap, vmin=0., vmax=1.)
    ax.set_axis_off()
    # components
    ax = plt.subplot(gs[1])
    x = gradient[0]
    r = cmap._segmentdata['red'](x)
    g = cmap._segmentdata['green'](x)
    b = cmap._segmentdata['blue'](x)
    k = .3*r + .59*g + .11*b
    plt.plot(x, r, 'r', linewidth=5, alpha=0.6)
    plt.plot(x, g, 'g', linewidth=5, alpha=0.6)
    plt.plot(x, b, 'b', linewidth=5, alpha=0.6)
    plt.plot(x, k, 'k:', linewidth=5, alpha=0.6)
    # finish
    plt.grid()
    plt.xlabel('value', fontsize=17)
    plt.ylabel('intensity', fontsize=17)


def plot_margins(fig=None, inches=1., centers=True, edges=True):
    '''
    Add lines onto a figure indicating the margins, centers, and edges. Useful
    for ensuring your figure design scripts work as intended, and for laying
    out figures.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure object (optional)
        The figure to plot onto. If None, gets current figure. Default is None.
    inches : float (optional)
        The size of the figure margin, in inches. Default is 1.
    centers : bool (optional)
        Toggle for plotting lines indicating the figure center. Default is
        True.
    edges : bool (optional)
        Toggle for plotting lines indicating the figure edges. Default is True.
    '''
    if fig is None:
        fig = plt.gcf()
    size = fig.get_size_inches()  # [H, V]
    trans_vert = inches/size[0]
    left = matplotlib.lines.Line2D([trans_vert, trans_vert], [0, 1], transform=fig.transFigure, figure=fig)
    right = matplotlib.lines.Line2D([1-trans_vert, 1-trans_vert], [0, 1], transform=fig.transFigure, figure=fig)
    trans_horz = inches/size[1]
    bottom = matplotlib.lines.Line2D([0, 1], [trans_horz, trans_horz], transform=fig.transFigure, figure=fig)
    top = matplotlib.lines.Line2D([0, 1], [1-trans_horz, 1-trans_horz], transform=fig.transFigure, figure=fig)      
    fig.lines.extend([left, right, bottom, top])
    if centers:
        vert = matplotlib.lines.Line2D([0.5, 0.5], [0, 1], transform=fig.transFigure, figure=fig, c='r')
        horiz = matplotlib.lines.Line2D([0, 1], [0.5, 0.5], transform=fig.transFigure, figure=fig, c='r')
        fig.lines.extend([vert, horiz])
    if edges:
        left = matplotlib.lines.Line2D([0, 0], [0, 1], transform=fig.transFigure, figure=fig, c='k')
        right = matplotlib.lines.Line2D([1, 1], [0, 1], transform=fig.transFigure, figure=fig, c='k')
        bottom = matplotlib.lines.Line2D([0, 1], [0, 0], transform=fig.transFigure, figure=fig, c='k')
        top = matplotlib.lines.Line2D([0, 1], [1, 1], transform=fig.transFigure, figure=fig, c='k')
        fig.lines.extend([left, right, bottom, top])


def subplots_adjust(fig=None, inches=1):
    '''
    Enforce margin to be equal around figure, starting at subplots.

    You probably should be using wt.artists.create_figure instead.

    See also
    --------
    wt.artists.plot_margins
        Visualize margins, for debugging / layout.
    wt.artists.create_figure
        Convinience method for creating well-behaved figures.
    '''
    if fig is None:
        fig = plt.gcf()
    size = fig.get_size_inches()
    vert = inches/size[0]
    horz = inches/size[1]
    fig.subplots_adjust(vert, horz, 1-vert, 1-horz)


### color maps ################################################################


cubehelix = make_cubehelix(gamma=0.5, s=0.25, r=-6/6., h=1.25, 
                           lum_rev=False, darkest=0.7)

experimental = ['#FFFFFF',
                '#0000FF',
                '#0080FF',
                '#00FFFF',
                '#00FF00',
                '#FFFF00',
                '#FF8000',
                '#FF0000',
                '#881111']

greenscale = ['#000000',  # black
              '#00FF00']  # green

greyscale = ['#FFFFFF',  # white
             '#000000']  # black

invisible = ['#FFFFFF',  # white
             '#FFFFFF']  # white
             
# isoluminant colorbar based on the research of Kindlmann et al.
# http://dx.doi.org/10.1109/VISUAL.2002.1183788
c = mplcolors.ColorConverter().to_rgb
isoluminant = make_colormap([
    c(r_[1.000,1.000,1.000]), c(r_[0.847,0.057,0.057]), 1/6.,
    c(r_[0.847,0.057,0.057]), c(r_[0.527,0.527,0.000]), 2/6.,
    c(r_[0.527,0.527,0.000]), c(r_[0.000,0.592,0.000]), 3/6.,
    c(r_[0.000,0.592,0.000]), c(r_[0.000,0.559,0.559]), 4/6.,
    c(r_[0.000,0.559,0.559]), c(r_[0.316,0.316,0.991]), 5/6.,
    c(r_[0.316,0.316,0.991]), c(r_[0.718,0.000,0.718])],
    name='isoluminant')

isoluminant2 = make_colormap([
    c(r_[1.000,1.000,1.000]), c(r_[0.718,0.000,0.718]), 1/6.,
    c(r_[0.718,0.000,0.718]), c(r_[0.316,0.316,0.991]), 2/6.,
    c(r_[0.316,0.316,0.991]), c(r_[0.000,0.559,0.559]), 3/6.,
    c(r_[0.000,0.559,0.559]), c(r_[0.000,0.592,0.000]), 4/6.,
    c(r_[0.000,0.592,0.000]), c(r_[0.527,0.527,0.000]), 5/6.,
    c(r_[0.527,0.527,0.000]), c(r_[0.847,0.057,0.057])],
    name='isoluminant2')
    
isoluminant3 = make_colormap([
    c(r_[1.000,1.000,1.000]), c(r_[0.316,0.316,0.991]), 1/5.,
    c(r_[0.316,0.316,0.991]), c(r_[0.000,0.559,0.559]), 2/5.,
    c(r_[0.000,0.559,0.559]), c(r_[0.000,0.592,0.000]), 3/5.,
    c(r_[0.000,0.592,0.000]), c(r_[0.527,0.527,0.000]), 4/5.,
    c(r_[0.527,0.527,0.000]), c(r_[0.847,0.057,0.057])],
    name='isoluminant3')

signed = ['#0000FF',  # blue
          '#002AFF',
          '#0055FF',
          '#007FFF',
          '#00AAFF',
          '#00D4FF',
          '#00FFFF',
          '#FFFFFF',  # white
          '#FFFF00',
          '#FFD400',
          '#FFAA00',
          '#FF7F00',
          '#FF5500',
          '#FF2A00',
          '#FF0000']  # red

signed_old = ['#0000FF',  # blue
              '#00BBFF',  # blue-aqua
              '#00FFFF',  # aqua
              '#FFFFFF',  # white
              '#FFFF00',  # yellow
              '#FFBB00',  # orange
              '#FF0000']  # red

skyebar = ['#FFFFFF',  # white
           '#000000',  # black
           '#0000FF',  # blue
           '#00FFFF',  # cyan
           '#64FF00',  # light green
           '#FFFF00',  # yellow
           '#FF8000',  # orange
           '#FF0000',  # red
           '#800000']  # dark red

skyebar_d = ['#000000',  # black
             '#0000FF',  # blue
             '#00FFFF',  # cyan
             '#64FF00',  # light green
             '#FFFF00',  # yellow
             '#FF8000',  # orange
             '#FF0000',  # red
             '#800000']  # dark red
           
skyebar_i = ['#000000',  # black
             '#FFFFFF',  # white
             '#0000FF',  # blue
             '#00FFFF',  # cyan
             '#64FF00',  # light green
             '#FFFF00',  # yellow
             '#FF8000',  # orange
             '#FF0000',  # red
             '#800000']  # dark red

wright = ['#FFFFFF',
          '#0000FF',
          '#00FFFF',
          '#00FF00',
          '#FFFF00',
          '#FF0000',
          '#881111']

colormaps = collections.OrderedDict()
colormaps['CMRmap'] = plt.get_cmap('CMRmap_r')
colormaps['cubehelix'] = plt.get_cmap('cubehelix_r')
colormaps['default'] = cubehelix
colormaps['experimental'] = mplcolors.LinearSegmentedColormap.from_list('experimental', experimental)
colormaps['flag'] = plt.get_cmap('flag')
colormaps['earth'] = plt.get_cmap('gist_earth')
colormaps['gnuplot2'] = plt.get_cmap('gnuplot2_r')
colormaps['greenscale'] = mplcolors.LinearSegmentedColormap.from_list('greenscale', greenscale)
colormaps['greyscale'] = mplcolors.LinearSegmentedColormap.from_list('greyscale', greyscale)
colormaps['invisible'] = mplcolors.LinearSegmentedColormap.from_list('invisible', invisible)
colormaps['isoluminant'] = isoluminant
colormaps['isoluminant2'] = isoluminant2
colormaps['isoluminant3'] = isoluminant3
colormaps['ncar'] = plt.get_cmap('gist_ncar')
colormaps['paried'] = plt.get_cmap('Paired')
colormaps['prism'] = plt.get_cmap('prism')
colormaps['rainbow'] = plt.get_cmap('rainbow')
colormaps['seismic'] = plt.get_cmap('seismic')
colormaps['signed'] = mplcolors.LinearSegmentedColormap.from_list('signed', signed)
colormaps['signed_old'] = mplcolors.LinearSegmentedColormap.from_list('signed', signed_old)
colormaps['skyebar'] = mplcolors.LinearSegmentedColormap.from_list('skyebar', skyebar)
colormaps['skyebar_d'] = mplcolors.LinearSegmentedColormap.from_list('skyebar dark', skyebar_d)
colormaps['skyebar_i'] = mplcolors.LinearSegmentedColormap.from_list('skyebar inverted', skyebar_i)
colormaps['spectral'] = plt.get_cmap('nipy_spectral')
colormaps['wright'] = mplcolors.LinearSegmentedColormap.from_list('wright', wright)


### general purpose artists ###################################################


class mpl_1D:

    def __init__(self, data, xaxis = 0, at = {}, verbose = True):
        # import data
        self.data = data
        self.chopped = self.data.chop(xaxis, at, verbose = False)
        if verbose:
            print 'mpl_1D recieved data to make %d plots'%len(self.chopped)
        # defaults
        self.font_size = 15

    def plot(self, channel=0, local=False, autosave=False, output_folder=None,
             fname=None, lines=True, verbose=True):
        fig = None
        if len(self.chopped) > 10:
            if not autosave:
                print 'too many images will be generated ({}): forcing autosave'.format(len(self.chopped))
                autosave = True
        # prepare output folders
        if autosave:
            if output_folder:
                pass
            else:
                if len(self.chopped) == 1:
                    output_folder = os.getcwd()
                    if fname:
                        pass
                    else:
                        fname = self.data.name
                else:
                    folder_name = 'mpl_1D ' + kit.get_timestamp()
                    os.mkdir(folder_name)
                    output_folder = folder_name
        # chew through image generation
        for i in range(len(self.chopped)):
            if fig and autosave:
                plt.close(fig)
            aspects = [[[0, 0], 0.5]]
            fig, gs = create_figure(width='single', nrows=1, cols=[1], aspects=aspects)
            current_chop = self.chopped[i]
            axes = current_chop.axes
            channels = current_chop.channels
            constants = current_chop.constants
            axis = axes[0]
            xi = axes[0].points
            zi = channels[channel].values
            plt.plot(xi, zi, lw=2)
            plt.scatter(xi, zi, color='grey', alpha=0.5, edgecolor='none')
            plt.grid()
            # variable marker lines
            if lines:
                for constant in constants:
                        if constant.units_kind == 'energy':
                            if axis.units == constant.units:
                                plt.axvline(constant.points, color='k', linewidth=4, alpha=0.25)
            # limits
            if local:
                pass
            else:
                plt.ylim(channels[channel].zmin, channels[channel].zmax)
            # label axes
            plt.xlabel(axes[0].get_label(), fontsize=18)
            plt.ylabel(channels[channel].name, fontsize=18)
            plt.xticks(rotation=45)
            plt.xlim(xi.min(), xi.max())
            # title
            title_text = self.data.name
            constants_text = '\n' + get_constant_text(constants)
            plt.suptitle(title_text + constants_text, fontsize=20)
            # save
            if autosave:
                if fname:
                    file_name = fname + ' ' + str(i).zfill(3)
                else:
                    file_name = str(i).zfill(3)
                fpath = os.path.join(output_folder, file_name + '.png')
                plt.savefig(fpath, transparent = True)
                plt.close()

                if verbose:
                    print 'image saved at', fpath


class mpl_2D:

    def __init__(self, data, xaxis = 1, yaxis = 0, at = {}, verbose = True):
        # import data
        self.data = data
        self.chopped = self.data.chop(yaxis, xaxis, at, verbose = False)
        if verbose:
            print 'mpl_2D recieved data to make %d plots'%len(self.chopped)
        # defaults
        self._xsideplot = False
        self._ysideplot = False
        self._xsideplotdata = []
        self._ysideplotdata = []
        self._onplotdata = []

    def sideplot(self, data, x = True, y = True):
        data = data.copy()
        if x:
            if self.chopped[0].axes[1].units_kind == data.axes[0].units_kind:
                data.convert(self.chopped[0].axes[1].units)
                self._xsideplot = True
                self._xsideplotdata.append([data.axes[0].points, data.channels[0].values])
            else:
                print 'given data ({0}), does not aggree with x ({1})'.format(data.axes[0].units_kind, self.chopped[0].axes[1].units_kind)
        if y: 
            if self.chopped[0].axes[0].units_kind == data.axes[0].units_kind:
                data.convert(self.chopped[0].axes[0].units)
                self._ysideplot = True
                self._ysideplotdata.append([data.axes[0].points, data.channels[0].values])
            else:
                print 'given data ({0}), does not aggree with y ({1})'.format(data.axes[0].units_kind, self.chopped[0].axes[0].units_kind)

    def onplot(self, xi, yi, c='k', lw=5, alpha=0.3, **kwargs):
        kwargs['c'] = c
        kwargs['lw'] = lw
        kwargs['alpha'] = alpha
        self._onplotdata.append((xi, yi, kwargs))

    def plot(self, channel=0,
             contours=9, pixelated=True, lines=True, cmap='default', 
             facecolor='w', dynamic_range = False, local=False, 
             contours_local=True, normalize_slices='both',  xbin= False, 
             ybin=False, xlim=None, ylim=None, autosave=False, 
             output_folder=None, fname=None, verbose=True):
        '''
        Draw the plot(s).
        
        Parameters
        ----------
        channel : int or string (optional)
            The index or name of the channel to plot. Default is 0.
        contours : int (optional)
            The number of black contour lines to add to the plot. You may set
            contours to 0 to use no contours in your plot. Default is 9.
        pixelated : bool (optional)
            Toggle between pclolormesh and contourf (deulaney) as plotting
            method. Default is True.
        lines : bool (optional)
            Toggle attempt to plot lines showing value of 'corresponding'
            color dimensions. Default is True.
        cmap : str (optional)
            A key to the colormaps dictionary found in artists module. Default
            is 'default'.
        facecolor : str (optional)
            Facecolor. Default is 'w'.
        dyanmic_range : bool (optional)
            Force the colorbar to use all of its colors. Only changes behavior
            for signed data. Default is False.
        local : bool (optional)
            Toggle plotting locally. Default is False.
        contours_local : bool (optional)
            Toggle plotting contours locally. Default is True.
        normalize_slices : {'both', 'horizontal', 'vertical'} (optional)
            Normalization strategy. Default is both.
        xbin : bool (optional)
            Plot xbin. Default is False.
        ybin : bool (optional)
            Plot ybin. Default is False.
        xlim : float (optional)
            Control limit of plot in x. Default is None (data limit).
        ylim : float (optional)
            Control limit of plot in y. Default is None (data limit).
        autosave : bool (optional)
            Autosave.
        output_folder : str (optional)
            Output folder.
        fname : str (optional)
            File name.
        verbose : bool (optional)
            Toggle talkback. Default is True.
        '''
        # get channel index
        if type(channel) in [int, float]:
            channel_index = int(channel)
        elif type(channel) == str:
            channel_index = self.chopped[0].channel_names.index(channel)
        else:
            print 'channel type not recognized in mpl_2D!'
        # prepare figure
        fig = None
        if len(self.chopped) > 10:
            if not autosave:
                print 'too many images will be generated: forcing autosave'
                autosave = True
        # prepare output folder
        if autosave:
            if output_folder:
                pass
            else:
                if len(self.chopped) == 1:
                    output_folder = os.getcwd()
                    if fname:
                        pass
                    else:
                        fname = self.data.name
                else:
                    folder_name = 'mpl_2D ' + kit.get_timestamp()
                    os.mkdir(folder_name)
                    output_folder = folder_name
        # chew through image generation
        for i in range(len(self.chopped)):
            # get data to plot ------------------------------------------------
            current_chop = self.chopped[i]
            axes = current_chop.axes
            channels = current_chop.channels
            constants = current_chop.constants
            xaxis = axes[1]
            yaxis = axes[0]
            channel = channels[channel_index]
            zi = channel.values
            zi = np.ma.masked_invalid(zi)
            # normalize slices ------------------------------------------------
            if normalize_slices == 'both':
                pass
            elif normalize_slices == 'horizontal':
                nmin = channel.znull
                #normalize all x traces to a common value
                maxes = zi.max(axis=1)
                numerator = (zi - nmin)
                denominator = (maxes - nmin)
                for j in range(zi.shape[0]):
                    zi[j] = numerator[j]/denominator[j]
                channel.zmax = zi.max()
                channel.zmin = zi.min()
                channel.znull = 0
            elif normalize_slices == 'vertical':
                nmin = channel.znull
                maxes = zi.max(axis=0)
                numerator = (zi - nmin)
                denominator = (maxes - nmin)
                for j in range(zi.shape[1]):
                    zi[:,j] = numerator[:,j] / denominator[j]
                channel.zmax = zi.max()
                channel.zmin = zi.min()
                channel.znull = 0
            # create figure ---------------------------------------------------
            if fig and autosave:
                plt.close(fig)
            fig, gs = create_figure(width='single', nrows=1, cols=[1, 'cbar'])
            subplot_main = plt.subplot(gs[0])
            subplot_main.patch.set_facecolor(facecolor)
            # levels ----------------------------------------------------------
            if channel.signed:
                if dynamic_range:
                    limit = min(abs(channel.znull - channel.zmin), abs(channel.znull - channel.zmax))
                else:
                    limit = max(abs(channel.znull - channel.zmin), abs(channel.znull - channel.zmax))
                levels = np.linspace(-limit + channel.znull, limit + channel.znull, 200)
            else:
                if local:
                    levels = np.linspace(channel.znull, np.nanmax(zi), 200)
                else:
                    if channel.zmax < channel.znull:
                        levels = np.linspace(channel.zmin, channel.znull, 200)
                    else:
                        levels = np.linspace(channel.znull, channel.zmax, 200)
            # main plot -------------------------------------------------------
            # get colormap
            mycm = colormaps[cmap]
            mycm.set_bad([0.75, 0.75, 0.75], 1.)
            mycm.set_under(facecolor)
            # fill in main data environment
            # always plot pcolormesh
            X, Y, Z = pcolor_helper(xaxis.points, yaxis.points, zi)
            cax = plt.pcolormesh(X, Y, Z, cmap=mycm,
                                 vmin=levels.min(), vmax=levels.max())
            plt.xlim(xaxis.points.min(), xaxis.points.max())
            plt.ylim(yaxis.points.min(), yaxis.points.max())
            # overlap with contourf if not pixelated
            if not pixelated:
                cax = subplot_main.contourf(xaxis.points, yaxis.points, zi,
                                            levels, cmap=mycm)
            plt.xticks(rotation=45, fontsize=14)
            plt.yticks(fontsize=14)
            plt.xlabel(xaxis.get_label(), fontsize=18)
            plt.ylabel(yaxis.get_label(), fontsize=17)
            # variable marker lines -------------------------------------------
            if lines:
                for constant in constants:
                        if constant.units_kind == 'energy':
                            #x axis
                            if xaxis.units == constant.units:
                                plt.axvline(constant.points, color = 'k', linewidth = 4, alpha = 0.25)
                            #y axis
                            if yaxis.units == constant.units:
                                plt.axhline(constant.points, color = 'k', linewidth = 4, alpha = 0.25)
            # grid ------------------------------------------------------------
            plt.grid(b = True)
            if xaxis.units == yaxis.units:
                # add diagonal line
                if xlim:
                    x = xlim
                else:
                    x = xaxis.points
                if ylim:
                    y = ylim
                else:
                    y = yaxis.points
                diag_min = max(min(x), min(y))
                diag_max = min(max(x), max(y))
                plt.plot([diag_min, diag_max],[diag_min, diag_max],'k:')
            # contour lines ---------------------------------------------------
            if contours:
                if contours_local:
                    # force top and bottom contour to be just outside of data range
                    # add two contours
                    contours_levels = np.linspace(channel.znull-1e-10, np.nanmax(zi)+1e-10, contours+2)
                else:
                    contours_levels = contours
                subplot_main.contour(xaxis.points, yaxis.points, zi,
                                     contours_levels, colors = 'k')
            # finish main subplot ---------------------------------------------
            if xlim:
                subplot_main.set_xlim(xlim[0], xlim[1])
            else:
                subplot_main.set_xlim(xaxis.points[0], xaxis.points[-1])
            if ylim:
                subplot_main.set_ylim(ylim[0], ylim[1])
            else:
                subplot_main.set_ylim(yaxis.points[0], yaxis.points[-1])
            # sideplots -------------------------------------------------------
            divider = make_axes_locatable(subplot_main)
            if xbin or self._xsideplot:
                axCorrx = divider.append_axes('top', 0.75, pad=0.0, sharex=subplot_main)
                axCorrx.autoscale(False)
                axCorrx.set_adjustable('box-forced')
                plt.setp(axCorrx.get_xticklabels(), visible=False)
                plt.setp(axCorrx.get_yticklabels(), visible=False)
                plt.grid(b = True)
                if channel.signed:
                    axCorrx.set_ylim([-1.1,1.1])
                else:
                    axCorrx.set_ylim([0,1.1])
                # bin
                if xbin:
                    x_ax_int = np.nansum(zi, axis=0) - channel.znull * len(yaxis.points)
                    x_ax_int[x_ax_int==0] = np.nan
                    # normalize (min is a pixel)
                    xmax = max(np.abs(x_ax_int))
                    x_ax_int = x_ax_int / xmax
                    axCorrx.plot(xaxis.points,x_ax_int, lw = 2)
                    axCorrx.set_xlim([xaxis.points.min(), xaxis.points.max()])
                # data
                if self._xsideplot:
                    for s_xi, s_zi in self._xsideplotdata:
                        xlim =  axCorrx.get_xlim()
                        min_index = np.argmin(abs(s_xi - min(xlim)))
                        max_index = np.argmin(abs(s_xi - max(xlim)))
                        s_zi_in_range = s_zi[min(min_index, max_index):max(min_index, max_index)]
                        s_zi = s_zi - min(s_zi_in_range)
                        s_zi_in_range = s_zi[min(min_index, max_index):max(min_index, max_index)]
                        s_zi = s_zi / max(s_zi_in_range)
                        axCorrx.plot(s_xi, s_zi, lw = 2)
                # line
                if lines:
                    for constant in constants:
                        if constant.units_kind == 'energy':
                            if xaxis.units == constant.units:
                                axCorrx.axvline(constant.points, color = 'k', linewidth = 4, alpha = 0.25)
            if ybin or self._ysideplot:
                axCorry = divider.append_axes('right', 0.75, pad=0.0, sharey=subplot_main)
                axCorry.autoscale(False)
                axCorry.set_adjustable('box-forced')
                plt.setp(axCorry.get_xticklabels(), visible=False)
                plt.setp(axCorry.get_yticklabels(), visible=False)
                plt.grid(b = True)
                if channel.signed:
                    axCorry.set_xlim([-1.1,1.1])
                else:
                    axCorry.set_xlim([0,1.1])
                # bin
                if ybin:
                    y_ax_int = np.nansum(zi, axis=1) - channel.znull * len(xaxis.points)
                    y_ax_int[y_ax_int==0] = np.nan
                    # normalize (min is a pixel)
                    ymax = max(np.abs(y_ax_int))
                    y_ax_int = y_ax_int / ymax
                    axCorry.plot(y_ax_int, yaxis.points, lw = 2)
                    axCorry.set_ylim([yaxis.points.min(), yaxis.points.max()])
                # data
                if self._ysideplot:
                    for s_xi, s_zi in self._ysideplotdata:
                        xlim =  axCorry.get_ylim()
                        min_index = np.argmin(abs(s_xi - min(xlim)))
                        max_index = np.argmin(abs(s_xi - max(xlim)))
                        s_zi_in_range = s_zi[min(min_index, max_index):max(min_index, max_index)]
                        s_zi = s_zi - min(s_zi_in_range)
                        s_zi_in_range = s_zi[min(min_index, max_index):max(min_index, max_index)]
                        s_zi = s_zi / max(s_zi_in_range)
                        axCorry.plot(s_zi, s_xi, lw = 2)
                # line
                if lines:
                    for constant in constants:
                        if constant.units_kind == 'energy':
                            if yaxis.units == constant.units:
                                axCorry.axvline(constant.points, color = 'k', linewidth = 4, alpha = 0.25)
            # onplot ----------------------------------------------------------
            for xi, yi, kwargs in self._onplotdata:
                subplot_main.plot(xi, yi, **kwargs)
            # colorbar --------------------------------------------------------
            subplot_cb = plt.subplot(gs[1])
            cbar_ticks = np.linspace(levels.min(), levels.max(), 11)
            cbar = plt.colorbar(cax, cax=subplot_cb, cmap=mycm, ticks=cbar_ticks, format='%.3f')
            cbar.set_label(channel.name, fontsize=18)
            cbar.ax.tick_params(labelsize=14)
            # title -----------------------------------------------------------
            title_text = self.data.name
            constants_text = get_constant_text(constants)            
            _title(fig, title_text, constants_text)
            # save figure -----------------------------------------------------
            if autosave:
                if fname:
                    file_name = fname + ' ' + str(i).zfill(3)
                else:
                    file_name = str(i).zfill(3)
                fpath = os.path.join(output_folder, file_name + '.png')
                plt.savefig(fpath, facecolor='none', dpi=300)
                plt.close()
                if verbose:
                    print 'image saved at', fpath


### specific artists ##########################################################


class absorbance:

    def __init__(self, data):

        if not type(data) == list:
            data = [data]

        self.data = data

    def plot(self, channel_index = 0, xlim = None, ylim = None,
             yticks = True, derivative = True, n_smooth = 10,):

        # prepare plot environment --------------------------------------------

        self.font_size = 14

        if derivative:
            aspects = [[[0, 0], 0.35], [[1, 0], 0.35]]
            hspace = 0.1
            fig, gs = create_figure(width='single', cols=[1], hspace=hspace, nrows=2, aspects=aspects)
            self.ax1 = plt.subplot(gs[0])
            plt.ylabel('OD', fontsize=18)
            plt.grid()
            plt.setp(self.ax1.get_xticklabels(), visible=False)
            self.ax2 = plt.subplot(gs[1], sharex = self.ax1)
            plt.grid()
            plt.ylabel('2nd der.', fontsize=18)
        else:
            aspects = [[[0, 0], 0.35]]
            fig, gs = create_figure(width='single', cols=[1], aspects=aspects)
            self.ax1 = plt.subplot(111)
            plt.ylabel('OD', fontsize=18)
            plt.grid()
        
        plt.xticks(rotation=45)

        for data in self.data:

            # import data -----------------------------------------------------

            xi = data.axes[0].points
            zi = data.channels[channel_index].values

            # scale -----------------------------------------------------------

            if xlim:
                plt.xlim(xlim[0], xlim[1])

                min_index = np.argmin(abs(xi - min(xlim)))
                max_index = np.argmin(abs(xi - max(xlim)))

                zi_truncated = zi[min(min_index,max_index):max(min_index, max_index)]
                zi -= zi_truncated.min()

                zi_truncated = zi[min(min_index,max_index):max(min_index, max_index)]
                zi /= zi_truncated.max()

            # plot absorbance -------------------------------------------------

            self.ax1.plot(xi, zi, lw = 2)

            # now plot 2nd derivative -----------------------------------------

            if derivative:
                # compute second derivative
                xi2, zi2= self._smooth(np.array([xi,zi]), n_smooth)
                plotData = kit.diff(xi2, zi2, order = 2)
                # plot the data!
                self.ax2.plot(plotData[0], plotData[1], lw = 2)
                self.ax2.grid(b=True)
                plt.xlabel(data.axes[0].get_label(), fontsize=18)

        # legend --------------------------------------------------------------

        #self.ax1.legend([data.name for data in self.data])

        # ticks ---------------------------------------------------------------

        if not yticks: self.ax1.get_yaxis().set_ticks([])
        if derivative:
            self.ax2.get_yaxis().set_ticks([])
            self.ax2.axhline(0, color = 'k', ls = ':')

        # title ---------------------------------------------------------------

        if len(self.data) == 1: #only attempt this if we are plotting one data object
            title_text = self.data[0].name
            print title_text
            plt.suptitle(title_text, fontsize = self.font_size)

        # finish --------------------------------------------------------------

        if xlim:
            plt.xlim(xlim[0], xlim[1])
            for axis, xi, zi in [[self.ax1, xi, zi], [self.ax2, plotData[0], plotData[1]]]:
                min_index = np.argmin(abs(xi - min(xlim)))
                max_index = np.argmin(abs(xi - max(xlim)))
                zi_truncated = zi[min_index:max_index]
                extra = (zi_truncated.max() - zi_truncated.min())*0.1
                axis.set_ylim(zi_truncated.min() - extra, zi_truncated.max() + extra)

        if ylim:
            self.ax1.set_ylim(ylim)

    def _smooth(self, dat1, n=20, window_type='default'):
        '''
        data is an array of type [xlis,ylis] \n
        smooth to prevent 2nd derivative from being noisy
        '''
        for i in range(n, len(dat1[1])-n):
            # change the x value to the average
            window = dat1[1][i-n:i+n].copy()
            dat1[1][i] = window.mean()
        return dat1[:][:,n:-n]


class difference_2D():

    def __init__(self, minuend, subtrahend, xaxis=1, yaxis=0, at={}, 
                 verbose=True):
        '''
        plot the difference between exactly two datasets in 2D \n
        both data objects must have the same axes with the same name \n
        axes do not need to be in the same order or have the same points \n
        '''
        self.minuend = minuend.copy()
        self.subtrahend = subtrahend.copy()
        # check if axes are valid - same axis names in both data objects
        minuend_counter = collections.Counter(self.minuend.axis_names)
        subrahend_counter = collections.Counter(self.subtrahend.axis_names)
        if minuend_counter == subrahend_counter:
            pass
        else:
            print 'axes are not equivalent - difference_2D cannot initialize'
            print '  minuhend axes -', self.minuend.axis_names
            print '  subtrahend axes -', self.subtrahend.axis_names
            raise RuntimeError('axes incompataible')
        # transpose subrahend to agree with minuend
        transpose_order = [self.minuend.axis_names.index(name) for name in self.subtrahend.axis_names]
        self.subtrahend.transpose(transpose_order, verbose=False)
        # map subtrahend axes onto minuend axes
        for i in range(len(self.minuend.axes)):            
            self.subtrahend.axes[i].convert(self.minuend.axes[i].units)
            self.subtrahend.map_axis(i, self.minuend.axes[i].points)
        # chop
        self.minuend_chopped = self.minuend.chop(yaxis, xaxis, at, verbose = False)
        self.subtrahend_chopped = self.subtrahend.chop(yaxis, xaxis, at, verbose = False)
        if verbose:
            print 'difference_2D recieved data to make %d plots'%len(self.minuend_chopped)
        # defaults
        self.font_size = 18

    def plot(self, channel_index=0,
         contours=9, pixelated=True, cmap='default', facecolor='grey',
         dynamic_range = False, local = False, contours_local = True,
         xlim=None, ylim=None,
         autosave=False, output_folder=None, fname=None,
         verbose=True):
        '''
        set contours to zero to turn off

        dynamic_range forces the colorbar to use all of its colors (only matters
        for signed data)
        '''
        fig = None
        if len(self.minuend_chopped) > 10:
            if not autosave:
                print 'too many images will be generated: forcing autosave'
                autosave = True
        
        # prepare output folder
        if autosave:
            plt.ioff()
            if output_folder:
                pass
            else:
                if len(self.minuend_chopped) == 1:
                    output_folder = os.getcwd()
                    if fname:
                        pass
                    else:
                        fname = self.minuend.name
                else:
                    folder_name = 'difference_2D ' + kit.get_timestamp()
                    os.mkdir(folder_name)
                    output_folder = folder_name

        # chew through image generation
        for i in range(len(self.minuend_chopped)):
            
            # create figure ---------------------------------------------------

            if fig:
                plt.close(fig)

            fig = plt.figure(figsize=(22, 7))

            gs = grd.GridSpec(1, 6, width_ratios=[20, 20, 1, 1, 20, 1], wspace=0.1)

            subplot_main = plt.subplot(gs[0])
            subplot_main.patch.set_facecolor(facecolor)

            # levels ----------------------------------------------------------

            '''
            if channel.signed:

                if dynamic_range:
                    limit = min(abs(channel.znull - channel.zmin), abs(channel.znull - channel.zmax))
                else:
                    limit = max(abs(channel.znull - channel.zmin), abs(channel.znull - channel.zmax))
                levels = np.linspace(-limit + channel.znull, limit + channel.znull, 200)

            else:

                if local:
                    levels = np.linspace(channel.znull, zi.max(), 200)
                else:
                    levels = np.linspace(channel.znull, channel.zmax, 200)
            '''
            levels = np.linspace(0, 1, 200)

            # main plot -------------------------------------------------------

            #get colormap
            mycm = colormaps[cmap]
            mycm.set_bad(facecolor)
            mycm.set_under(facecolor)

            for j in range(2):
                
                if j == 0:
                    current_chop = chopped = self.minuend_chopped[i]
                elif j == 1:
                    current_chop = self.subtrahend_chopped[i]
                
                axes = current_chop.axes
                channels = current_chop.channels
                constants = current_chop.constants
    
                xaxis = axes[1]
                yaxis = axes[0]
                channel = channels[channel_index]
                zi = channel.values

                plt.subplot(gs[j])

                #fill in main data environment
                if pixelated:
                    xi, yi, zi = pcolor_helper(xaxis.points, yaxis.points, zi)
                    cax = plt.pcolormesh(xi, yi, zi, cmap=mycm,
                                         vmin=levels.min(), vmax=levels.max())
                    plt.xlim(xaxis.points.min(), xaxis.points.max())
                    plt.ylim(yaxis.points.min(), yaxis.points.max())
                else:
                    cax = subplot_main.contourf(xaxis.points, yaxis.points, zi,
                                                levels, cmap=mycm)
    
                plt.xticks(rotation = 45)
                #plt.xlabel(xaxis.get_label(), fontsize = self.font_size)
                #plt.ylabel(yaxis.get_label(), fontsize = self.font_size)

                # grid --------------------------------------------------------
    
                plt.grid(b = True)
    
                if xaxis.units == yaxis.units:
                    # add diagonal line
                    if xlim:
                        x = xlim
                    else:
                        x = xaxis.points
                    if ylim:
                        y = ylim
                    else:
                        y = yaxis.points
    
                    diag_min = max(min(x), min(y))
                    diag_max = min(max(x), max(y))
                    plt.plot([diag_min, diag_max],[diag_min, diag_max],'k:')
    
                # contour lines -----------------------------------------------
    
                if contours:
                    if contours_local:
                        # force top and bottom contour to be just outside of data range
                        # add two contours
                        contours_levels = np.linspace(channel.znull-1e-10, np.nanmax(zi)+1e-10, contours+2)
                    else:
                        contours_levels = contours
                    plt.contour(xaxis.points, yaxis.points, zi,
                                contours_levels, colors = 'k')
    
                # finish main subplot -----------------------------------------
    
                if xlim:
                    subplot_main.set_xlim(xlim[0], xlim[1])
                else:
                    subplot_main.set_xlim(xaxis.points[0], xaxis.points[-1])
                if ylim:
                    subplot_main.set_ylim(ylim[0], ylim[1])
                else:
                    subplot_main.set_ylim(yaxis.points[0], yaxis.points[-1])

            
            # colorbar --------------------------------------------------------

            subplot_cb = plt.subplot(gs[2])
            cbar_ticks = np.linspace(levels.min(), levels.max(), 11)
            cbar = plt.colorbar(cax, cax=subplot_cb, ticks=cbar_ticks)

            # difference ------------------------------------------------------

            #get colormap
            mycm = colormaps['seismic']
            mycm.set_bad(facecolor)
            mycm.set_under(facecolor)
                
            dzi = self.minuend_chopped[i].channels[0].values - self.subtrahend_chopped[i].channels[0].values
                  
            dax = plt.subplot(gs[4])
            plt.subplot(dax)
            
            X, Y, Z = pcolor_helper(xaxis.points, yaxis.points, dzi)
            
            largest = np.nanmax(np.abs(dzi))
            
            dcax = dax.pcolor(X, Y, Z, vmin=-largest, vmax=largest, cmap=mycm)
            
            dax.set_xlim(xaxis.points.min(), xaxis.points.max())
            dax.set_ylim(yaxis.points.min(), yaxis.points.max())            
            
            differenc_cb = plt.subplot(gs[5])
            dcbar = plt.colorbar(dcax, cax=differenc_cb)
            dcbar.set_label(self.minuend.channels[channel_index].name +
                            ' - ' + self.subtrahend.channels[channel_index].name)
            
            # title -----------------------------------------------------------

            title_text = self.minuend.name + ' - ' + self.subtrahend.name

            constants_text = '\n' + get_constant_text(constants)
            
            plt.suptitle(title_text + constants_text, fontsize = self.font_size)

            plt.figtext(0.03, 0.5, yaxis.get_label(), fontsize = self.font_size, rotation = 90)
            plt.figtext(0.5, 0.01, xaxis.get_label(), fontsize = self.font_size, horizontalalignment = 'center')            

            # cleanup ---------------------------------------------------------


            fig.subplots_adjust(left=0.075, right=1-0.075, top=0.90, bottom=0.15)

            plt.setp(plt.subplot(gs[1]).get_yticklabels(), visible=False)
            plt.setp(plt.subplot(gs[4]).get_yticklabels(), visible=False)

            # save figure -----------------------------------------------------

            if autosave:
                if fname:
                    file_name = fname + ' ' + str(i).zfill(3)
                else:
                    file_name = str(i).zfill(3)
                fpath = os.path.join(output_folder, file_name + '.png')
                plt.savefig(fpath, facecolor = 'none')
                plt.close()

                if verbose:
                    print 'image saved at', fpath
        
        plt.ion()

