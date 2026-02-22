# Base imports
import os

# Additional imports
import pandas as pd
import matplotlib.pyplot as plt
import yaml
from path import SC2_VOID_BOT_HOME

class Plotter:

    def __init__(self, log_path) -> None:
        # Class vars
        self._log_dir = log_path
        self._plot_dir = os.path.join(log_path, "plots")
        self._data = {}
        
        # Plot vars
        self._plot_csts = {}

        # Init
        self._initialize()

    def _initialize(self) -> None:
        # Make plot dir
        os.makedirs(self._plot_dir, exist_ok=True)

        # Get the plot constants into a dict from the yaml
        try:
            plot_yaml_file_path = os.path.join(SC2_VOID_BOT_HOME, "config", "plot.yaml")
            with open(plot_yaml_file_path, 'r') as file:
                self._plot_csts = yaml.safe_load(file)
        except FileNotFoundError:
            print("Error: config.yaml not found.")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")

        # Combine all the dfs here
        for file in os.listdir(self._log_dir):
            if file.endswith(".parquet"):

                # Create game name
                game_name = file.split(".parquet")[0]
    
                # Load data
                full_file_path = os.path.join(self._log_dir, file)
                df = pd.read_parquet(full_file_path)
                self._data[game_name] = self._downsample_data(df)

    def _downsample_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        ds = int(self._plot_csts["downsample_sec"])

        # Compute bin starts 0, ds, 2*ds, ...
        df["bin"] = (df["game_time"] // ds) * ds

        # Exclude original game_time from the aggregation to avoid duplicate columns
        numeric_cols = df.select_dtypes(include="number").columns
        numeric_cols = numeric_cols.drop("game_time", errors="ignore")

        out = (df.groupby("bin", as_index=False)[numeric_cols]
                .mean())

        out = out.rename(columns={"bin": "game_time"})
        out = out.sort_values("game_time").reset_index(drop=True)

        # Optional extra guard: ensure unique column names
        out = out.loc[:, ~out.columns.duplicated()]
        return out

    def _plot_minerals_rate(self) -> None:
        # Setup
        fig, ax = plt.subplots(figsize=(self._plot_csts["figure_width"], self._plot_csts["figure_height"]), dpi=self._plot_csts["dpi"])

        # Actual plot
        for game in self._data:
            ax.plot(self._data[game]["game_time"], self._data[game]["collection_rate_minerals"], label=game)

        # Labels
        ax.set_title("Minerals Rate", fontsize=self._plot_csts["title_font_size"])
        ax.set_xlabel("Time (s)", fontsize=self._plot_csts["label_font_size"])
        ax.set_ylabel("Minerals Rate", fontsize=self._plot_csts["label_font_size"])

        # Limits
        ax.set_xlim(min(self._data[game]["game_time"].min() for self._data[game] in self._data.values()),
                    max(self._data[game]["game_time"].max() for self._data[game] in self._data.values()))
        ax.set_ylim(min(self._data[game]["collection_rate_minerals"].min() for self._data[game] in self._data.values()),
                    max(self._data[game]["collection_rate_minerals"].max() for self._data[game] in self._data.values()))
        
        # Legend below the axes, fully outside
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.15),   # (x, y) in axes coords; y<0 puts it below
            ncol=2,
            frameon=False
        )

        # Tick and grid
        ax.tick_params(axis="both", which="major", labelsize=self._plot_csts["label_font_size"])
        ax.grid(True, linestyle="--", alpha=0.6)

        # Final spacing
        fig.subplots_adjust(bottom=0.25)
        fig.tight_layout()
        plt.savefig(os.path.join(self._plot_dir, "minerals_rate.png"))

    def _plot_gas_rate(self) -> None:
        # Setup
        fig, ax = plt.subplots(figsize=(self._plot_csts["figure_width"], self._plot_csts["figure_height"]), dpi=self._plot_csts["dpi"])

        # Actual plot
        for game in self._data:
            ax.plot(self._data[game]["game_time"], self._data[game]["collection_rate_vespene"], label=game)

        # Labels
        ax.set_title("Gas Rate", fontsize=self._plot_csts["title_font_size"])
        ax.set_xlabel("Time (s)", fontsize=self._plot_csts["label_font_size"])
        ax.set_ylabel("Gas Rate", fontsize=self._plot_csts["label_font_size"])

        # Limits
        ax.set_xlim(min(self._data[game]["game_time"].min() for self._data[game] in self._data.values()),
                    max(self._data[game]["game_time"].max() for self._data[game] in self._data.values()))
        ax.set_ylim(min(self._data[game]["collection_rate_vespene"].min() for self._data[game] in self._data.values()),
                    max(self._data[game]["collection_rate_vespene"].max() for self._data[game] in self._data.values()))
        
        # Legend below the axes, fully outside
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.15),   # (x, y) in axes coords; y<0 puts it below
            ncol=2,
            frameon=False
        )

        # Tick and grid
        ax.tick_params(axis="both", which="major", labelsize=self._plot_csts["label_font_size"])
        ax.grid(True, linestyle="--", alpha=0.6)

        # Final spacing
        fig.subplots_adjust(bottom=0.25)
        fig.tight_layout()
        plt.savefig(os.path.join(self._plot_dir, "gas_rate.png"))

    def _plot_apm(self) -> None:
        # Setup
        fig, ax = plt.subplots(figsize=(self._plot_csts["figure_width"], self._plot_csts["figure_height"]), dpi=self._plot_csts["dpi"])

        # Actual plot
        for game in self._data:
            ax.plot(self._data[game]["game_time"], self._data[game]["current_apm"], label=game)

        # Labels
        ax.set_title("APM", fontsize=self._plot_csts["title_font_size"])
        ax.set_xlabel("Time (s)", fontsize=self._plot_csts["label_font_size"])
        ax.set_ylabel("APM", fontsize=self._plot_csts["label_font_size"])

        # Limits
        ax.set_xlim(min(self._data[game]["game_time"].min() for self._data[game] in self._data.values()),
                    max(self._data[game]["game_time"].max() for self._data[game] in self._data.values()))
        ax.set_ylim(min(self._data[game]["current_apm"].min() for self._data[game] in self._data.values()),
                    max(self._data[game]["current_apm"].max() for self._data[game] in self._data.values()))
        
        # Legend below the axes, fully outside
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.15),   # (x, y) in axes coords; y<0 puts it below
            ncol=2,
            frameon=False
        )

        # Tick and grid
        ax.tick_params(axis="both", which="major", labelsize=self._plot_csts["label_font_size"])
        ax.grid(True, linestyle="--", alpha=0.6)

        # Final spacing
        fig.subplots_adjust(bottom=0.25)
        fig.tight_layout()
        plt.savefig(os.path.join(self._plot_dir, "apm.png"))

    def _plot_army_size(self) -> None:
        pass

    def _plot_technology(self) -> None:
        pass

    def _log_columns(self) -> None:
        # Save columns to text file
        first_key = next(iter(self._data))
        with open('columns.txt', 'w') as f:
            for col in self._data[first_key].columns:
                f.write(f"{col}\n")

    def plot(self) -> None:
        # Create all plots
        self._plot_minerals_rate()
        self._plot_gas_rate()
        self._plot_apm()
        self._plot_army_size()
        self._plot_technology()

        # Create log columns
        self._log_columns()

if __name__ == "__main__":
    path = os.path.join(SC2_VOID_BOT_HOME, "logs")

    # Data
    plotter = Plotter(path)
    plotter.plot()
