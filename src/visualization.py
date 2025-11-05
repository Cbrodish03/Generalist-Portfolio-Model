import matplotlib.pyplot as plt
import numpy as np
import cvxpy as cp
import variance_calcs as vc
from parser import SIPParser
from portfolio import Portfolio
from sample_portfolios import RandomPortfolios

class TooltipManager:
   def __init__(self, ax, info_textbox=None, canvas=None):
      # Create MPL Artist to reference
      self.ax = ax
      self.fig = ax.figure
      self.info_textbox = info_textbox # textbox reference for UI

      self.asset_names = []

      # Create array of scatter-plot data
      self.scatters = []
      # Separate arrays for each dataset
      self.randpts = []
      self.effpts = []

      # Configure hovering tooltip
      self.annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))

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
         return # UI not connected yet

      self.info_textbox.configure(state="normal")
      self.info_textbox.delete("1.0", "end")
      self.info_textbox.insert("end", text)
      self.info_textbox.configure(state="disabled")

   def format_weights(self, weights):
      lines = ["Weights:"]
      for i, w in enumerate(weights, start=1):
         name = self.asset_names[i-1]
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
      index = sc.format_cursor_data(ind["ind"] + 1)
      text = f"{index}\n({xval}, {yval})"
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
               d2 = np.sum((cand - np.array([mx, my]))**2, axis=1)
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
                  f"Average Return: ${avreturn}\n"
                  f"Risk (Std Dev): ${risk}\n\n"
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
                  f"Average Return: ${avreturn}\n"
                  f"Risk (Std Dev): ${risk}\n\n"
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
   ymin = b / (2 * a)
   mus = np.linspace(ymin, ymax, 50)    # 50 = num of eff ports drawn
   for mu in mus:
      port = Portfolio()
      effpt = port.construct_port(group_data, 'e', mu)
      
      if np.all(effpt['weights'] >= 0):
         eff_points.append(effpt)
   
   xs = []
   ys = []
   for i in range(len(eff_points)):
      xs.append(np.sqrt(eff_points[i]['metadata']['Variance']))
      ys.append(eff_points[i]['metadata']['AverageReturn'])

   # plt.plot(x, y, 'r', ls='--')
   return xs, ys, eff_points

def visualize_portfolios(group_data, count, info_textbox=None):
   """
   Generates random portfolios and plots them with efficient frontier
   :param group_data: samples to generate with
   :param count: number of random portfolios to generate
   """
   gen = RandomPortfolios()
   sample_ports = gen.generate_sample(group_data, count=count)

   rx, ry = plot_rand(sample_ports)
   ex, ey, effpts = plot_frontier(group_data)

   asset_names = [item['metadata']['Name'] for item in group_data]
   
   fig, ax = plt.subplots(dpi=150)
   tm = TooltipManager(ax, info_textbox)
   tm.asset_names = asset_names
   tm.add_scatter(rx, ry, c='b', s=15, picker=True, pickradius=5)
   tm.add_scatter(ex, ey, c='r', marker='*', picker=True, pickradius=5)
   tm.randpts = sample_ports
   tm.effpts = effpts

   ax.plot(ex, ey, c='r', ls='--')
   ax.set_xlabel("Risk (Std Dev)")
   ax.set_ylabel("Average Return ($)")
   ax.set_title(f"Random portfolios ({count} samples) & Efficient Frontier")
   ax.grid(ls="--")

   # plt.xlabel("Risk (Std Dev)")
   # plt.ylabel("Average Return ($)")
   # plt.title(f"Random portfolios ({count} samples) & Efficient Frontier")
   # plt.grid(ls="--")
   # plt.show()   # swap to returning the figure for integration with UI
   return fig, tm, sample_ports, effpts

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

if __name__ == "__main__":
   SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
   # SLURP = SIPParser("data/small_SIP.xlsx")
   group_data = SLURP.investments
   count = int(input("How many Dirichlet-random portfolios would you like to generate? "))
   visualize_portfolios(group_data, count=count)
   # pareto_plot(group_data, count=count)
