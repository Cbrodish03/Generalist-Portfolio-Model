import csv
import hashlib
import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

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
        Handle a matplotlib pick event by identifying the clicked portfolio
        and displaying its formatted info in the Portfolio Information panel.
        When multiple points overlap, the one closest to the cursor is selected.

        :param event: matplotlib PickEvent — contains artist, ind, and mouseevent
        :side effects: Calls self.display_info() to update the UI textbox
        """
        try:
            artist = event.artist
            if not hasattr(event, "ind"):
                return
            inds = np.atleast_1d(event.ind)

            me = getattr(event, "mouseevent", None)
            if me is None or me.xdata is None or me.ydata is None:
                idx = int(inds[0])
            else:
                mx, my = me.xdata, me.ydata
                offsets = artist.get_offsets()
                if offsets is None or len(offsets) == 0:
                    idx = int(inds[0])
                else:
                    cand = offsets[inds]
                    d2 = np.sum((cand - np.array([mx, my])) ** 2, axis=1)
                    idx = int(inds[np.argmin(d2)])

            if len(self.scatters) >= 2 and artist == self.scatters[0]:
                if idx < len(self.randpts):
                    text = format_portfolio_info(
                        self.randpts[idx], idx + 1, "Random", self.asset_names
                    )
                    self.display_info(text)

            elif len(self.scatters) >= 2 and artist == self.scatters[1]:
                if idx < len(self.effpts):
                    text = format_portfolio_info(
                        self.effpts[idx], idx + 1, "Efficient", self.asset_names
                    )
                    self.display_info(text)

        except Exception as e:
            print("Error in on_pick:", e)


def plot_rand(random_ports):
    """
    Plots [count] random portfolios generated by RandomPortfolios class, standard deviation vs average return
    :param random_ports: a RandomPortfolios object with n Dirichlet-random weighted portfolios
    """
    # Create arrays of points to plot
    xs = []
    ys = []
    # Populate arrays with standard deviation and average return values of random ports
    for port in random_ports:
        xs.append(port['metadata']['PercentileOM'])
        ys.append(port['metadata']['AverageReturn'])
    return xs, ys


def plot_frontier(group_data):
    """
    Compute and return efficient frontier portfolio points.
    X-axis: P10 (10th percentile return in dollars).
    Y-axis: Average return in dollars.
    Only non-negative-weight portfolios are included.
    Portfolios below the minimum-variance portfolio are pruned to
    prevent the lower arc from appearing on the chart.

    :param group_data: List of SIP investment dicts (parsed trial data)
    :return: (xs, ys, eff_points)
        xs         — list of P10 values for each efficient portfolio
        ys         — list of average return values
        eff_points — list of portfolio dicts for tooltip/export use
    """
    a, b, c, ymax = vc.compute_coeffs(group_data)

    eff_points = []
    ymin = b / (2 * a)
    mus = np.linspace(ymin, ymax, 50)

    for mu in mus:
        port = Portfolio()
        effpt = port.construct_port(group_data, 'e', mu)
        if np.all(effpt['weights'] >= 0):
            eff_points.append(effpt)

    # Prune lower arc: keep only portfolios at or above minimum-variance point
    stds = [np.sqrt(p['metadata']['Variance']) for p in eff_points]
    min_var_idx = int(np.argmin(stds))
    eff_points = eff_points[min_var_idx:]

    xs = [p['metadata']['PercentileOM'] for p in eff_points]
    ys = [p['metadata']['AverageReturn'] for p in eff_points]

    return xs, ys, eff_points


def visualize_portfolios(group_data, count, info_textbox=None, plot=False, seed=None, show_frontier=True):
    """
    Generates random portfolios and plots them with the efficient frontier.

    :param group_data:    List of SIP investment dicts (parsed trial data)
    :param count:         Number of random portfolios to generate
    :param info_textbox:  Optional CTkTextbox for displaying portfolio info on click
    :param plot:          If True, calls plt.show() immediately (standalone testing only)
    :param seed:          Optional integer seed for reproducible generation
    :param show_frontier: Initial visibility state for efficient frontier elements
    :return: (fig, TooltipManager, sample_ports, effpts, frontier_line, eff_scatter)
    """
    gen = RandomPortfolios(seed=seed)
    sample_ports = gen.generate_sample(group_data, count=count)

    ex, ey, effpts = plot_frontier(group_data)
    rx, ry = plot_rand(sample_ports)

    asset_names = [item['metadata']['Name'] for item in group_data]

    fig, ax = plt.subplots(dpi=150)
    tm = TooltipManager(ax, info_textbox)
    tm.asset_names = asset_names

    random_scatter = tm.add_scatter(rx, ry, c='b', s=15, picker=True, pickradius=5)

    eff_scatter = tm.add_scatter(ex, ey, c='r', marker='*', picker=True, pickradius=5)
    eff_scatter.set_visible(show_frontier)

    frontier_line, = ax.plot(ex, ey, c='r', ls='--', visible=show_frontier)

    tm.randpts = sample_ports
    tm.effpts = effpts
    tm.eff_scatter = eff_scatter
    tm.frontier_line = frontier_line

    apply_axis_formatting(ax, count)

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

def format_portfolio_info(port, idx, port_type, asset_names):
    """
    Produce a formatted multi-line string describing a portfolio for display
    in the Portfolio Information panel.

    :param port:        Portfolio dict with 'metadata' and 'weights' keys
    :param idx:         1-based display index (shown to user)
    :param port_type:   Label string, e.g. "Random" or "Efficient"
    :param asset_names: Ordered list of asset name strings (matches weight indices)
    :return:            Formatted string ready for insertion into a CTkTextbox
    """
    meta = port['metadata']
    avg_return = float(meta.get('AverageReturn', float('nan')))
    p10 = meta.get('PercentileOM', None)
    std_dev = float(np.sqrt(meta.get('Variance', float('nan'))))
    weights = port['weights']

    lines = [
        f"{port_type} Portfolio #{idx}",
        f"{'─' * 30}",
        f"Average Return : {format_currency(avg_return)}",
        f"P10 (Risk)     : {format_currency(p10) if p10 is not None else 'N/A'}",
        f"Std Dev        : {format_currency(std_dev)}",
        f"",
        f"Weights:",
    ]

    for i, w in enumerate(weights):
        name = asset_names[i] if i < len(asset_names) else f"Asset {i + 1}"
        lines.append(f"  {i + 1}. {name:<22} {w * 100:.4f}%")

    return "\n".join(lines)

def apply_axis_formatting(ax, count):
    # Applies standard currency formatting and labels to a portfolio scatter plot axis
    currency_formatter = FuncFormatter(lambda x, pos: f"${x:,.0f}")
    ax.xaxis.set_major_formatter(currency_formatter)
    ax.yaxis.set_major_formatter(currency_formatter)
    ax.set_xlabel("Risk (P10)")
    ax.set_ylabel("Average Return ($)")
    ax.set_title(f"Random portfolios ({count} samples) & Efficient Frontier")
    ax.grid(ls="--")

# ==============================================================
# TESTS BELOW
# ==============================================================

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
