import csv
import hashlib
import json

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import variance_calcs as vc
from parser import SIPParser
from portfolio import Portfolio
from sample_portfolios import RandomPortfolios


class TooltipManager:
    def __init__(self, ax, info_textbox=None, canvas=None):
        # Create MPL Artist to reference
        self.ax = ax
        self.fig = ax.figure
        self.info_textbox = info_textbox  # textbox reference for UI
        self.show_efficient_frontier = False

        self.asset_names = []

        # Create array of scatter-plot data
        self.scatters = []
        # Separate arrays for each dataset
        self.randpts = []
        self.effpts = []

        # Configure hovering tooltip
        self.annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                                 bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))

        # Tooltip visibility rules
        self.annot.set_visible(False)
        if canvas is None:
            self.canvas = self.fig.canvas
        else:
            self.canvas = canvas

        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)
        self.fig.canvas.mpl_connect("pick_event", self.on_pick)

    def display_info(self, text):
        if self.info_textbox is None:
            return  # UI not connected yet

        self.info_textbox.configure(state="normal")
        self.info_textbox.delete("1.0", "end")
        self.info_textbox.insert("end", text)
        self.info_textbox.insert("end", "\n\n")
        self.info_textbox.configure(state="disabled")

    def toggle_efficient_frontier(self):
        self.show_efficient_frontier = not self.show_efficient_frontier

    def format_weights(self, weights):
        lines = ["Weights:"]
        for i, w in enumerate(weights, start=1):
            name = self.asset_names[i - 1]
            lines.append(f"  {i}. {name:<20} {w * 100:.8f}%")
        return "\n".join(lines)

    def add_scatter(self, *args, **kwargs):
        """Add PathCollection to array, to be referenced by tooltip"""
        if "picker" not in kwargs:
            kwargs["picker"] = True
        sc = self.ax.scatter(*args, **kwargs)
        self.scatters.append(sc)
        return sc

    def update_annot(self, sc, ind):
        """Update hovering tooltip with current cursor data"""
        pos = sc.get_offsets()[ind["ind"][0]]
        self.annot.xy = pos
        xval = np.around(pos[0], 2)
        yval = np.around(pos[1], 2)
        try:
            ytext = format_currency(float(yval))
        except Exception:
            ytext = yval

        index = sc.format_cursor_data(ind["ind"] + 1)
        text = f"{index}\n({xval}, {ytext})"
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)

    def hover(self, event):
        """Control visibility of hovering tooltip"""
        vis = self.annot.get_visible()
        if event.inaxes == self.ax:
            for sc in self.scatters:
                cont, ind = sc.contains(event)
                if cont:
                    self.update_annot(sc, ind)
                    self.annot.set_visible(True)
                    self.fig.canvas.draw_idle()
                    return
            if vis:
                self.annot.set_visible(False)
                self.fig.canvas.draw_idle()

    def on_pick(self, event):
        """
        Handles displaying portfolio information from the graph
        If multiple portfolios exist in the same event, we pick the closest to the user's cursor position
        :param event: the event we get from the handler
        """
        try:
            artist = event.artist
            if not hasattr(event, "ind"):
                return
            inds = np.atleast_1d(event.ind)  # ensures array-like

            # get mouse click position in data coords (fallback if missing)
            me = getattr(event, "mouseevent", None)
            if me is None or me.xdata is None or me.ydata is None:
                # if mouse coords not available, just take the first index
                idx = int(inds[0])
            else:
                mx, my = me.xdata, me.ydata

                # get offsets for this artist (scatter)
                offsets = artist.get_offsets()
                if offsets is None or len(offsets) == 0:
                    idx = int(inds[0])
                else:
                    # extract candidate points' coordinates
                    cand = offsets[inds]  # shape (k, 2)
                    # compute squared distances in data space
                    d2 = np.sum((cand - np.array([mx, my])) ** 2, axis=1)
                    # pick index of smallest distance among candidates
                    best_rel = np.argmin(d2)
                    idx = int(inds[best_rel])

            # now idx is a single integer index we can safely use
            # determine which scatter was clicked and respond
            if len(self.scatters) >= 2 and artist == self.scatters[0]:
                # random portfolios
                if idx < len(self.randpts):
                    risk = np.around(np.sqrt(self.randpts[idx]['metadata']['Variance']), 2)
                    avreturn = np.around(self.randpts[idx]['metadata']['AverageReturn'], 2)
                    weights = self.randpts[idx]['weights']
                    # print(f"Random Portfolio #{idx + 1}:\nAverage Return: ${avreturn} | Risk (std dev): ${risk}\nAsset Weights: {weights}")
                    weight_text = self.format_weights(weights)
                    self.display_info(
                        f"Random Portfolio #{idx + 1}\n"
                        f"Average Return: {format_currency(avreturn)}\n"
                        f"Risk (Std Dev): {format_currency(risk)}\n\n"
                        f"{weight_text}"
                    )
            elif len(self.scatters) >= 2 and artist == self.scatters[1]:
                # efficient portfolios
                if idx < len(self.effpts):
                    avreturn = np.around(self.effpts[idx]['metadata']['AverageReturn'], 2)
                    risk = np.around(np.sqrt(self.effpts[idx]['metadata']['Variance']), 2)
                    weights = self.effpts[idx]['weights']
                    # print(f"Efficient Portfolio #{idx + 1}:\nAverage Return: ${avreturn} | Risk (std dev): ${risk}\nAsset Weights: {weights}")
                    weight_text = self.format_weights(weights)
                    self.display_info(
                        f"Efficient Portfolio #{idx + 1}\n"
                        f"Average Return: {format_currency(avreturn)}\n"
                        f"Risk (Std Dev): {format_currency(risk)}\n\n"
                        f"{weight_text}"
                    )

        except Exception as e:
            # Defensive: avoid crashing the app on unexpected pick-event structures
            print("Error in on_pick:", e)


def plot_rand(random_ports):
    """
    Plots [count] random portfolios generated by RandomPortfolios class, standard deviation vs average return
    :param random_ports: a RandomPortfolios object with n Dirichlet-random weighted portfolios
    """

    # Create arrays of points to plot
    xs = []
    ys = []
    count = len(random_ports)

    # Populate arrays with standard deviation and average return values of random ports
    for i in range(count):
        xs.append(np.sqrt(random_ports[i]['metadata']['Variance']))
        ys.append(random_ports[i]['metadata']['AverageReturn'])

    return xs, ys


def plot_frontier(group_data):
    """
    Plots the 'Markowitz bullet'/efficient frontier
    :param group_data: SIP trial data
    """

    a, b, c, ymax = vc.compute_coeffs(group_data)

    eff_points = []
    ymin = b / (2 * a)      # Ballpark min average return
    mus = np.linspace(ymin, ymax, 50)  # 50 = num of eff ports drawn
    for mu in mus:
        port = Portfolio()
        effpt = port.construct_port(group_data, 'e', mu)

        if np.all(effpt['weights'] >= 0):
            eff_points.append(effpt)

    # Filter out efficient ports below min variance port (fix bending)
    # Compute standard deviations for all points
    stds = [np.sqrt(p['metadata']['Variance']) for p in eff_points]

    # Find index of minimum variance (i.e. bottom of the U)
    min_var_idx = int(np.argmin(stds))

    # Keep only points ABOVE (to the right of) the min-var portfolio
    eff_points = eff_points[min_var_idx:]
    
    xs = []
    ys = []
    for i in range(len(eff_points)):
        xs.append(np.sqrt(eff_points[i]['metadata']['Variance']))
        ys.append(eff_points[i]['metadata']['AverageReturn'])

    # plt.plot(x, y, 'r', ls='--')
    return xs, ys, eff_points


def visualize_portfolios(group_data, count, info_textbox=None, plot=False, seed=None, show_frontier=True):
    """
    Generates random portfolios and plots them with efficient frontier.

    :param group_data: SIP trial data used to generate portfolios
    :param count: number of random portfolios to generate
    :param info_textbox: optional CustomTkinter textbox for displaying portfolio info
    :param plot: if True, displays plot immediately (for standalone testing)
    :param seed: optional integer seed for reproducible random generation
    :param show_frontier: initial visibility state for efficient frontier elements
    :return: (figure, TooltipManager, sample_ports, effpts, frontier_line, eff_scatter)
    """
    gen = RandomPortfolios(seed=seed)
    sample_ports = gen.generate_sample(group_data, count=count)

    # Always generate efficient frontier data
    ex, ey, effpts = plot_frontier(group_data)
    rx, ry = plot_rand(sample_ports)

    asset_names = [item['metadata']['Name'] for item in group_data]

    fig, ax = plt.subplots(dpi=150)
    tm = TooltipManager(ax, info_textbox)
    tm.asset_names = asset_names

    # Plot random portfolios (always visible)
    random_scatter = tm.add_scatter(rx, ry, c='b', s=15, picker=True, pickradius=5)

    # Plot efficient portfolios (visibility controlled by show_frontier parameter)
    eff_scatter = tm.add_scatter(ex, ey, c='r', marker='*', picker=True, pickradius=5)
    eff_scatter.set_visible(show_frontier)

    # Plot frontier line (visibility controlled by show_frontier parameter)
    # CRITICAL: ax.plot() returns a list; unpack to get the Line2D object
    frontier_line, = ax.plot(ex, ey, c='r', ls='--', visible=show_frontier)

    # Store portfolio data for tooltip system
    tm.randpts = sample_ports
    tm.effpts = effpts

    # Store references for external toggling (UI needs these)
    tm.eff_scatter = eff_scatter
    tm.frontier_line = frontier_line

    ax.set_xlabel("Risk (Std Dev)")
    ax.set_ylabel("Average Return ($)")

    # Currency formatter using your existing function
    currency_formatter = FuncFormatter(lambda x, pos: f"${x:,.0f}")

    ax.xaxis.set_major_formatter(currency_formatter)
    ax.yaxis.set_major_formatter(currency_formatter)

    
    ax.set_title(f"Random portfolios ({count} samples) & Efficient Frontier")
    ax.grid(ls="--")

    if plot:
        plt.show()

    return fig, tm, sample_ports, effpts, frontier_line, eff_scatter


def update_frontier_visibility(self):
    """Show or hide the efficient frontier curve without rebuilding the graph."""
    if hasattr(self, "frontier_line"):  # Ensure frontier exists
        self.frontier_line.set_visible(self.show_efficient_frontier)
        self.fig.canvas.draw_idle()


def toggle_efficient_frontier(self):
    self.show_efficient_frontier = not self.show_efficient_frontier
    self.update_frontier_visibility()

def format_currency(value):
    """Formats a number as currency with two decimal places and a dollar sign."""
    return f"${value:,.2f}"


""" def pareto_plot(group_data, count):
   gen = RandomPortfolios()
   sample_ports = gen.generate_sample(group_data, count=count)

   xs = []
   ys = []
   pfx = []
   pfy = []

   for port in sample_ports:
      if port['metadata']['IsParetoEff'] == True:
         pfx.append(port['metadata']['PercentileOM'])
         pfy.append(port['metadata']['AverageReturn'])
      else:
         xs.append(port['metadata']['PercentileOM'])
         ys.append(port['metadata']['AverageReturn'])
   
   plt.scatter(xs, ys, s=15)
   plt.scatter(pfx, pfy, marker='*')
   plt.show() """

def test_winds_plot():
    # create test case to test the parser functionality
    test_parser = SIPParser("data/mock_sipmath_v2.xlsx")

    test_winds_parser = SIPParser("data/Winds_of_Fortune_Template.xlsx")

    test_winds_sip_parser = SIPParser("data/Winds_of_Fortune_SIP.xlsx")

    # test winds application
    adjusted_sips = test_parser.apply_winds(
        simulated_groups=test_parser.investments,
        template_groups=test_winds_parser.investments,
        wind_groups=test_winds_sip_parser.investments)

    # group_data = adjusted_sips
    count = int(input("How many Dirichlet-random portfolios would you like to generate? "))
    visualize_portfolios(adjusted_sips, count=count, plot=True)

def export_portfolios_to_csv(filepath, random_ports, eff_ports):
    """
    Exports random and efficient portfolios to CSV file
    Rows formatted as:
        Portfolio Type, Average Return, Variance, Standard Dev, Weight 1, Weight 2, ..., Weight N
    :param filepath:
    :param random_ports:
    :param eff_ports:
    :return:
    """
    try:
        with open(filepath, 'w', newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write header
            max_weights = 0
            if random_ports:
                max_weights = max(max_weights, len(random_ports[0]['weights']))
            if eff_ports:
                max_weights = max(max_weights, len(eff_ports[0]['weights']))

            weight_headers = [f"Weight {i+1}" for i in range(max_weights)]

            writer.writerow([
                "Portfolio Type",
                "Index",
                "Average Return",
                "Variance",
                "Standard Deviation",
                *weight_headers
            ])

            # Write random portfolios
            for i, port in enumerate(random_ports):
                meta = port['metadata']
                weights = port['weights']
                row = [
                    "Random",
                    i + 1,
                    meta['AverageReturn'],
                    meta['Variance'],
                    np.sqrt(meta['Variance']),
                    *weights
                ]
                writer.writerow(row)

            # Write efficient portfolios
            for i, port in enumerate(eff_ports):
                meta = port['metadata']
                weights = port['weights']
                row = [
                    "Efficient",
                    i + 1,
                    meta['AverageReturn'],
                    meta['Variance'],
                    np.sqrt(meta['Variance']),
                    *weights
                ]
                writer.writerow(row)

        return True

    except Exception as e:
        print(f"Error opening file {filepath} for writing: {e}")
        return False

def test_seeded_randomness():
    SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
    data = SLURP.investments

    SEED = 5        # seed for RNG
    COUNT = 20      # number of random portfolios to generate

    def fingerprint(portfolios):
        """Create a footprint of portfolio weights"""
        payload = [
            [round(w, 10) for w in p['weights']]
            for p in portfolios
        ]
        blob = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()

    gen1 = RandomPortfolios(seed=SEED)
    ports1 = gen1.generate_sample(data, count=COUNT)

    gen2 = RandomPortfolios(seed=SEED)
    ports2 = gen2.generate_sample(data, count=COUNT)

    fp1 = fingerprint(ports1)
    fp2 = fingerprint(ports2)

    print("Fingerprint 1:", fp1)
    print("Fingerprint 2:", fp2)
    print("Match:", fp1 == fp2)

    # visual sanity check
    visualize_portfolios(data, count=COUNT, plot=True, seed=SEED, show_frontier=False)

# Test 1: Same seed produces identical results
def test_determinism():
    from parser import SIPParser

    SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
    data = SLURP.investments

    SEED = 42
    COUNT = 100

    # Run 1
    gen1 = RandomPortfolios(seed=SEED)
    ports1 = gen1.generate_sample(data, count=COUNT)

    # Run 2
    gen2 = RandomPortfolios(seed=SEED)
    ports2 = gen2.generate_sample(data, count=COUNT)

    # Verify identical weights
    for i in range(COUNT):
        assert np.allclose(ports1[i]['weights'], ports2[i]['weights'], rtol=1e-12)
        assert np.allclose(ports1[i]['trials'], ports2[i]['trials'], rtol=1e-12)

    print("✓ Determinism verified: Identical inputs produce identical outputs")

# Test 2: Different seeds produce different results
def test_seed_variation():
    SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
    data = SLURP.investments

    gen1 = RandomPortfolios(seed=1)
    ports1 = gen1.generate_sample(data, count=50)

    gen2 = RandomPortfolios(seed=2)
    ports2 = gen2.generate_sample(data, count=50)

    # Verify different weights
    different = False
    for i in range(50):
        if not np.allclose(ports1[i]['weights'], ports2[i]['weights']):
            different = True
            break

    assert different, "Different seeds should produce different results"
    print("✓ Seed variation verified: Different seeds produce different outputs")


if __name__ == "__main__":
    # SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
    # SLURP = SIPParser("data/small_SIP.xlsx")
    # group_data = SLURP.investments
    # count = int(input("How many Dirichlet-random portfolios would you like to generate? "))
    # seed = int(input("Enter an integer seed for RNG (or 0 for random): "))
    # if seed == 0:
    #     seed = None
    # visualize_portfolios(group_data, count=count, plot=True, seed=seed)
    # pareto_plot(group_data, count=count)
    # test_winds_plot()
    # test_seeded_randomness()
    test_determinism()
    test_seed_variation()
