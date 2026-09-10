"""The default plot styling every notebook opens with."""
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401  -- registers the 'science' style with matplotlib


def apply_style(dpi=500):
    """Apply the shared figure style: SciencePlots 'science' + 'no-latex', at `dpi`.

    Called explicitly rather than run at import time, so importing the package
    never mutates a notebook's rcParams behind its back.
    """
    plt.style.use(['science', 'no-latex'])
    plt.rcParams['figure.dpi'] = dpi
