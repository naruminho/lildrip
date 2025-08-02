"""Plotting utilities for lildrip."""

import matplotlib.pyplot as plt
import pandas as pd


def plot_comparison(original: pd.Series, disaggregated: pd.Series, title: str = 'Comparison') -> None:
    """Plot line comparison between original and disaggregated series."""
    plt.figure(figsize=(12, 5))
    plt.plot(original.index, original.values, label='Original', alpha=0.7)
    plt.plot(disaggregated.index, disaggregated.values, label='Disaggregated', alpha=0.7, linestyle='--')
    plt.title(title)
    plt.ylabel("Rainfall (mm)")
    plt.xlabel("Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('rainfall_comparison.png')
    plt.show()


def plot_comparison_bars(original: pd.Series, disaggregated: pd.Series, title: str = 'Comparison - Bars') -> None:
    """Plot bar comparison between original and disaggregated series."""
    plt.figure(figsize=(14, 6))
    bar_width = (original.index[1] - original.index[0]).total_seconds() / 60

    plt.bar(original.index, original.values, width=bar_width / 1440, label='Original', alpha=0.6, align='center')
    plt.bar(disaggregated.index, disaggregated.values, width=bar_width / 1440, label='Disaggregated', alpha=0.6, align='center')

    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Rainfall (mm)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('rainfall_comparison_bars.png')
    plt.show()
