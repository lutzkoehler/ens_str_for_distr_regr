## Script for evaluation of aggregation methods of NN methods

import os
import pickle

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats as ss

# Path for figures
pdf_path = "plots"

# Path of data
data_path = "data"

# Path of network ensemble data
data_ss_ens_path = os.path.join(data_path, "model")

# Path of aggregated network data
data_ss_agg_path = os.path.join(data_path, "agg")

# Models considered
scenario_vec = [1, 4]

# Number of simulations
n_sim = 10

# Vector of ensemble members
n_ens_vec = np.arange(2, 12, 2)

### Initialize ###
# Vector for plotting on [0,1]
x_plot = np.arange(0, 1, 0.001)
x_plot50 = np.arange(0, 50, 0.01)

# Evaluation measures
sr_eval = ["crps", "me", "lgt", "cov"]

# Skill scores
sr_skill = ["crps"]

# Network types
nn_vec = ["drn", "bqn"]

# Names of aggregation methods
agg_names = {
    "lp": "Linear Pool",
    "vi": "Vincentization",
    "vi-a": "Vincentization (a)",
    "vi-w": "Vincentization (w)",
    "vi-aw": "Vincentization (a, w)",
}
agg_abr = {
    "lp": r"$LP$",
    "vi": r"$V_0^=$",
    "vi-a": r"$V_a^=$",
    "vi-w": r"$V_0^w$",
    "vi-aw": r"$V_a^w$",
}

# Aggregation methods
agg_meths = list(agg_names.keys())

# Methods with coefficient estimation
coeff_meths = ["vi-a", "vi-w", "vi-aw"]

# Get colors
cols = sns.color_palette("Dark2", 8, as_cmap=True)
# Colors of aggregation methods
agg_col = {
    "lp": cols.colors[4],  # type: ignore
    "vi": cols.colors[5],  # type: ignore
    "vi-a": cols.colors[2],  # type: ignore
    "vi-w": cols.colors[0],  # type: ignore
    "vi-aw": cols.colors[3],  # type: ignore
    "ens": cols.colors[7],  # type: ignore
    "opt": cols.colors[1],  # type: ignore
}

# Line types of aggregation methods
agg_lty = {
    "lp": "dashed",
    "vi": "solid",
    "vi-a": "solid",
    "vi-w": "solid",
    "vi-aw": "solid",
    "ens": "dashdot",
    "opt": "dashdot",
}


def plot_example_aggregation():
    ### Section 2: Example aggregation ###
    # Evaluations for plotting
    n_plot = 1000

    # Aggregation methods to plot
    agg_meths_plot = ["lp", "vi", "vi-a", "vi-w", "vi-aw"]

    # Number of forecasts to aggregate
    n = 2

    # Lower and upper boundaries
    lower = 0.5
    upper = 13.5

    # Parameters of individual distributions
    mu_1 = 7
    mu_2 = 10
    sd_1 = 1
    sd_2 = 1

    # Data frame of distributions
    df_plot = pd.DataFrame()

    # Vector to plot on
    df_plot["y"] = np.linspace(start=lower, stop=upper, num=n_plot)

    # Calculate probabilities and densities of individual forecasts
    for temp in ["1", "2"]:
        df_plot[f"p_{temp}"] = ss.norm.cdf(
            x=df_plot["y"],
            loc=eval(f"mu_{temp}"),
            scale=eval(f"sd_{temp}"),
        )
        df_plot[f"d_{temp}"] = ss.norm.pdf(
            x=df_plot["y"],
            loc=eval(f"mu_{temp}"),
            scale=eval(f"sd_{temp}"),
        )

    # LP
    df_plot["p_lp"] = df_plot[["p_1", "p_2"]].mean(axis=1)
    df_plot["d_lp"] = df_plot[["d_1", "d_2"]].mean(axis=1)

    # For-Loop over Vincentization approaches
    for temp in [element for element in agg_meths_plot if "vi" in element]:
        # Intercept
        if temp in ["vi", "vi-w"]:
            a = 0
        else:  # temp in ["vi-a", "vi-aw"]:
            a = -6

        # Weights
        if temp in ["vi", "vi-a"]:
            w = 1 / n
        else:  # temp in ["vi-w", "vi-aw"]:
            w = 1 / n + 0.15

        # Calculate mean and sd
        mu_vi = a + w * sum([mu_1, mu_2])
        sd_vi = w * sum([sd_1, sd_2])

        # Calculate probabilities and densities
        df_plot[f"p_{temp}"] = ss.norm.cdf(
            x=df_plot["y"], loc=mu_vi, scale=sd_vi
        )

        df_plot[f"d_{temp}"] = ss.norm.pdf(
            x=df_plot["y"], loc=mu_vi, scale=sd_vi
        )

    # Name of PDF
    filename = os.path.join(pdf_path, "aggregation_methods.pdf")

    fig, axes = plt.subplots(1, 3, figsize=(20, 5))

    ## PDF
    # Empty plot
    axes[0].set_title("Probability density function (PDF)")
    axes[0].set_xlabel("y")
    axes[0].set_ylabel("f(y)")
    axes[0].set_ylim(bottom=0, top=max(df_plot[["d_1", "d_2"]].max()))
    axes[0].set_xlim(left=lower, right=upper)

    # Draw individual PDFs
    for i in range(1, n + 1):
        sns.lineplot(
            ax=axes[0],
            x=df_plot["y"],
            y=df_plot[f"d_{i}"],
            color=agg_col["ens"],
            linestyle=agg_lty["ens"],
        )

    # For-Loop over aggregation methods
    for temp in agg_meths_plot:
        sns.lineplot(
            ax=axes[0],
            x=df_plot["y"],
            y=df_plot[f"d_{temp}"],
            color=agg_col[temp],
            linestyle=agg_lty[temp],
        )

    ## CDF
    # Empty plot
    axes[1].set_title("Cumulative distribution function (CDF)")
    axes[1].set_xlabel("y")
    axes[1].set_ylabel("F(y)")
    axes[1].set_ylim(bottom=0, top=1)
    axes[1].set_xlim(left=lower, right=upper)

    # Draw individual CDFs
    for i in range(1, n + 1):
        sns.lineplot(
            ax=axes[1],
            x=df_plot["y"],
            y=df_plot[f"p_{i}"],
            color=agg_col["ens"],
            linestyle=agg_lty["ens"],
        )

    # For-Loop over aggregation methods
    for temp in agg_meths_plot:
        sns.lineplot(
            ax=axes[1],
            x=df_plot["y"],
            y=df_plot[f"p_{temp}"],
            color=agg_col[temp],
            linestyle=agg_lty[temp],
        )

    ## Quantile functions
    # Empty plot
    axes[2].set_title("Quantile function")
    axes[2].set_xlabel("p")
    axes[2].set_ylabel("Q(p)")
    axes[2].set_xlim(left=0, right=1)
    axes[2].set_ylim(bottom=lower, top=upper)

    # Draw individual quantile functions
    for i in range(1, n + 1):
        sns.lineplot(
            ax=axes[2],
            y=df_plot["y"],
            x=df_plot[f"p_{i}"],
            color=agg_col["ens"],
            linestyle=agg_lty["ens"],
        )

    # For-Loop over aggregation methods
    for temp in agg_meths_plot:
        sns.lineplot(
            ax=axes[2],
            y=df_plot["y"],
            x=df_plot[f"p_{temp}"],
            color=agg_col[temp],
            linestyle=agg_lty[temp],
        )

    # Add legend
    fig.legend()

    # Save fig
    fig.savefig(filename)
    print(f"Example aggregation saved to {filename}")


def plot_panel_model():
    ### Simulation: Load data ###
    with open(os.path.join(data_path, "eval_ss.pkl"), "rb") as f:
        df_scores = pickle.load(f)

    ### Simulation: Initialize ###

    ### Simulation: Score panel ###
    # Vector of scores/quantiles to plot
    score_vec = ["crps", "crpss", "me", "lgt", "cov", "a", "w"]

    # For-Loop over scenarios
    for i_scenario in scenario_vec:
        ### Initialization ###
        # Only scenario
        df_sc = df_scores[df_scores["model"] == i_scenario]

        ### Calculate quantities ###
        df_plot = pd.DataFrame()

        # For-Loop over quantities of interest
        for temp_sr in score_vec:
            # Consider special case CRPSS
            if temp_sr == "crpss":
                temp_out = "crps"
            else:
                temp_out = temp_sr

            # Get optimal score of scenario for CRPSS
            s_opt = 0
            if temp_sr not in ["a", "w"]:
                s_opt = df_sc[df_sc["type"] == "ref"][temp_out].mean()

            # For-Loop over network variants
            for temp_nn in nn_vec:
                # Only network type
                df_nn = df_sc[df_sc["nn"] == temp_nn]

                # For-Lop over ensemble sizes and aggregation methods
                for i_ens in n_ens_vec:
                    for temp_agg in ["opt", "ens"] + agg_meths:
                        # Skip ensemble for skill
                        if (temp_sr == "crpss") and (temp_agg == "ens"):
                            continue
                        elif (temp_sr == "crpss") and (temp_agg == "opt"):
                            continue
                        elif (temp_sr == "a") and (temp_agg == "opt"):
                            continue
                        elif (temp_sr == "w") and (temp_agg == "opt"):
                            continue

                        # Fill in data frame
                        new_row = {
                            "nn": temp_nn,
                            "metric": temp_sr,
                            "n_ens": i_ens,
                            "agg": temp_agg,
                        }

                        # Reference: Average score of ensemble members
                        s_ref = df_nn[
                            (df_nn["n_rep"] <= i_ens)
                            & (df_nn["type"] == "ind")
                        ][temp_out].mean()

                        # Special case: Average ensemble score
                        if temp_agg == "ens":
                            new_row["score"] = s_ref
                        elif temp_agg == "opt":
                            new_row["score"] = s_opt
                        else:
                            # Read out score
                            new_row["score"] = df_nn[
                                (df_nn["n_ens"] == i_ens)
                                & (df_nn["type"] == temp_agg)
                            ][temp_out].mean()

                            # Special case: CRPSS
                            if temp_sr == "crpss":
                                # Calcuate skill
                                new_row["score"] = (
                                    100
                                    * (s_ref - new_row["score"])
                                    / (s_ref - s_opt)
                                )

                            # Relative weight difference to equal weights in %
                            if temp_sr == "w":
                                new_row["score"] = 100 * (
                                    i_ens * new_row["score"] - 1
                                )

                        df_plot = pd.concat(
                            [
                                df_plot,
                                pd.DataFrame(new_row, index=[0]),
                            ],
                            ignore_index=True,
                        )

        ### Prepare data ###
        # Remove negative CRPSSS smaller than 5%
        df_plot = df_plot[
            (df_plot["metric"] != "crpss") | (df_plot["score"] >= -5)
        ]

        # Rename networks
        df_plot["nn"] = df_plot["nn"].str.upper()

        # Rename metrics
        score_labels = {
            "crps": "CRPS",
            "crpss": "CRPSS in %",
            "me": "Bias",
            "lgt": "PI length",
            "cov": "PI coverage in %",
            "a": "Intercept",
            "w": "Rel. weight diff. in %",
        }

        # Intercept values
        hline_vec0 = {
            "crpss": 0,
            "me": 0,
            "cov": 100 * 19 / 21,
            "a": 0,
            "w": 0,
        }

        # Minimal lower/upper limit: Per hand for each scenario
        # if i_scenario == 1:
        #     # Upper
        #     u_vec = {"crps": 1.15, "me": 0.01, "a": 0.01, "w": 1}
        #     # Lower
        #     l_vec = {"crps": 0.97, "a": -0.001}
        # elif i_scenario == 2:
        #     # Upper
        #     u_vec = {"crps": 2.32, "a": 0.07, "w": 1.1}
        #     # Lower
        #     l_vec = {"crps": 2.19, "a": -0.07, "w": -0.1}
        # elif i_scenario == 3:
        #     # Upper
        #     u_vec = {"crps": 0.7, "a": 0.01, "w": 2}
        #     # Lower
        #     l_vec = {"crps": 0.65, "a": -0.01}
        # elif i_scenario == 4:
        #     # Upper
        #     u_vec = {"crps": 0.64, "a": 0.01, "w": 0.5}
        #     # Lower
        #     l_vec = {"crps": 0.42, "a": -0.07}
        # else:
        #     u_vec = {}
        #     l_vec = {}

        # Legend labels
        leg_labels = {"ens": "DE", "opt": r"$F^*$", **agg_abr}

        ### PDF ###
        fig, axes = plt.subplots(
            len(score_labels), len(nn_vec), figsize=(8.27, 11.69)
        )

        # For-Loop over networks
        for i, temp_nn in enumerate([x.upper() for x in nn_vec]):
            if any(
                (df_plot["nn"] == temp_nn)
                & (df_plot["metric"] == "crpss")
                & (df_plot["score"] <= 1)
            ):
                hline_vec = {"crpss": 0, **hline_vec0}
            else:
                hline_vec = hline_vec0

            y_label = True
            if i > 0:
                y_label = False
            # For-Loop over metrics
            for j, metric in enumerate(score_labels.keys()):
                sns.lineplot(
                    ax=axes[j][i],
                    data=df_plot[
                        (df_plot["nn"] == temp_nn)
                        & (df_plot["metric"] == metric)
                    ],
                    x="n_ens",
                    y="score",
                    hue="agg",
                    palette=agg_col,
                )
                if metric not in ["crps", "lgt"]:
                    axes[j][i].axhline(y=hline_vec[metric], linestyle="dashed")
                if y_label:
                    axes[j][i].set_ylabel(score_labels[metric])
                else:
                    axes[j][i].set_ylabel("")
                if j == 0:
                    axes[j][i].title.set_text(temp_nn)  # type: ignore

        handles, labels = axes[0][0].get_legend_handles_labels()
        fig.legend(
            handles,
            [leg_labels[label] for label in labels],
            loc="upper center",
            ncol=len(score_labels),
        )
        fig.suptitle(f"Model {i_scenario}")
        for ax in axes.flatten():  # type: ignore
            ax.legend().set_visible(False)

        # Save fig
        filename = os.path.join(
            pdf_path, f"ss_gg_panel_model_{i_scenario}.pdf"
        )
        fig.savefig(filename)
        print(f"Panel saved to {filename}")


def plot_panel_boxplot():
    ### Simulation: CRPSS boxplot panel ###
    ### Simulation: Load data ###
    with open(os.path.join(data_path, "eval_ss.pkl"), "rb") as f:
        df_scores = pickle.load(f)
    # For-Loop over scenarios
    for i_scenario in scenario_vec:
        ### Initialization ###
        # Only scenario
        df_sc = df_scores[df_scores["model"] == i_scenario]

        ### Calculate quantities ###
        df_plot = pd.DataFrame()

        # For-Loop over network variants, ensemble sizes and aggregation
        # methods
        for temp_nn in nn_vec:
            for i_ens in n_ens_vec:
                for temp_agg in agg_meths:
                    # Get subset of scores data
                    df_sub = df_sc[
                        (df_sc["n_ens"] == i_ens)
                        & (df_sc["type"] == temp_agg)
                        & (df_sc["nn"] == temp_nn)
                    ]

                    new_row = {
                        "n_ens": i_ens,
                        "nn": temp_nn,
                        "agg": temp_agg,
                        "crpss": [list(100 * df_sub["crpss"])],
                    }

                    df_plot = pd.concat(
                        [df_plot, pd.DataFrame(new_row, index=[0])],
                        ignore_index=True,
                    )

        ### Prepare data ###
        # Minimal lower/upper limit: Per hand for each scenario
        # if i_scenario == 1:
        #     lu_vec = [-20, 40]
        # else:
        #     lu_vec = max(df_plot["crps"]) - min(df_plot["crps"])

        # Rename networks
        df_plot["nn"] = df_plot["nn"].str.upper()

        # Renamge aggregation methods
        # df_plot["agg"] = df_plot["agg"].replace(agg_abr)

        ### PDF ###
        # Make plot
        fig, axes = plt.subplots(
            len(nn_vec), len(agg_names.keys()), figsize=(15, 10)
        )
        sample_size = len(df_plot["crpss"].iloc[0])
        fig.suptitle(f"Model {i_scenario} - Sample size: {sample_size}")

        # For-Loop over networks
        for i, temp_nn in enumerate([x.upper() for x in nn_vec]):
            # For-Loop over metrics
            for j, agg_method in enumerate(agg_names.keys()):
                sns.boxplot(
                    data=df_plot[
                        (df_plot["nn"] == temp_nn)
                        & (df_plot["agg"] == agg_method)
                    ].explode("crpss"),
                    y="crpss",
                    x="n_ens",
                    color=agg_col[agg_method],
                    ax=axes[i][j],
                )

                axes[i][j].axhline(y=0, color="grey", linestyle="dashed")
                axes[i][j].set_xlabel("")
                if i == 0:
                    axes[i][j].set_title(agg_abr[agg_method])
                if j == 0:
                    axes[i][j].set_ylabel(f"{temp_nn}: CRPSS in %")
                else:
                    axes[i][j].set_ylabel("")

        # Save fig
        filename = os.path.join(
            pdf_path, f"ss_gg_panel_crpss_boxplots_model_{i_scenario}.pdf"
        )
        fig.savefig(filename)
        print(f"PIT saved to {filename}")


def plot_pit_ens():
    ### Simulation: PIT histograms ###
    ### Simulation: Load data ###
    with open(os.path.join(data_path, "eval_ss.pkl"), "rb") as f:
        df_scores = pickle.load(f)

    # Network ensemble size
    n_ens = 2

    # Number of bins in histogram
    n_bins = 21

    # For-Loop over scenarios
    for i_scenario in scenario_vec:
        ### Initialization ###
        # Only scenario
        df_sc = df_scores[df_scores["model"] == i_scenario]

        # Index vector for validation and testing
        i_valid = list(range(df_sc[df_sc["type"] != "ref"]["n_valid"].iloc[0]))
        i_test = [
            max(i_valid) + el
            for el in list(
                range(df_sc[df_sc["type"] != "ref"]["n_test"].iloc[0])
            )
        ]

        ### Get PIT values ###
        # List for PIT values
        pit_ls = {}

        # For-Loop over network variants
        for temp_nn in nn_vec:
            ### PIT values of ensemble member ###
            # Vector for PIT values
            temp_pit = []

            # For-Loop over ensemble member and simulation
            for i_rep in range(n_ens):
                for i_sim in range(n_sim):
                    # Load ensemble member
                    filename = f"{temp_nn}_scen_{i_scenario}_sim_{i_sim}_ens_{i_rep}.pkl"  # noqa: E501
                    with open(
                        os.path.join(data_ss_ens_path, filename), "rb"
                    ) as f:
                        [pred_nn, y_valid, y_test] = pickle.load(f)

                    # Read out
                    temp_pit.append(pred_nn["scores"]["pit"][i_test])

            # Save PIT
            pit_ls[f"{temp_nn}_ens"] = temp_pit

            ### Aggregation methods ###
            # For-Loop over aggregation methods
            for temp_agg in agg_meths:
                # Vector for PIT values
                temp_pit = []

                # For-Loop over simulations
                for i_sim in range(n_sim):
                    # Load aggregated forecasts
                    filename = f"{temp_nn}_scen_{i_scenario}_sim_{i_sim}_{temp_agg}_ens_{n_ens}.pkl"  # noqa: E501
                    with open(
                        os.path.join(data_ss_agg_path, filename), "rb"
                    ) as f:
                        pred_agg = pickle.load(f)

                    # Read out PIT-values
                    temp_pit.append(pred_agg["scores"]["pit"])

                # Save PIT
                pit_ls[f"{temp_nn}_{temp_agg}"] = temp_pit

        ### Calculate histograms ###
        df_plot = pd.DataFrame()

        # For-Loop over network variants and aggregation methods
        for temp_nn in nn_vec:
            for temp_agg in ["ens", *agg_meths]:
                # Calculate histogram and read out values (see pit function)
                temp_hist, temp_bin_edges = np.histogram(
                    pit_ls[f"{temp_nn}_{temp_agg}"], bins=n_bins, density=True
                )

                new_row = {
                    "nn": temp_nn,
                    "agg": temp_agg,
                    "breaks": [temp_bin_edges],
                    "pit": [temp_hist],
                }

                df_plot = pd.concat(
                    [df_plot, pd.DataFrame(new_row, index=[0])],
                    ignore_index=True,
                )

        ### Prepare data ###
        # Rename networks
        df_plot["nn"] = df_plot["nn"].str.upper()

        ### PDF ###
        # Limit of y-axis
        # if i_scenario == 1:
        #     y_lim = 1.5
        # elif i_scenario == 2:
        #     y_lim = 2.5
        # elif i_scenario == 3:
        #     y_lim = 1.5
        # elif i_scenario == 4:
        #     y_lim = 2
        # else:
        #     y_lim = None

        # Make plot
        fig, axes = plt.subplots(
            len(nn_vec), len(["ens", *agg_meths]), figsize=(15, 5)
        )
        fig.suptitle(f"Model {i_scenario}")

        leg_labels = {"ens": "DE", "opt": r"$F^*$", **agg_abr}

        # For-Loop over networks
        for i, temp_nn in enumerate([x.upper() for x in nn_vec]):

            # For-Loop over metrics
            for j, metric in enumerate(["ens", *agg_meths]):
                df_curr = df_plot[
                    (df_plot["nn"] == temp_nn) & (df_plot["agg"] == metric)
                ]

                axes[i][j].bar(
                    df_curr["breaks"].iloc[0][:-1],
                    df_curr["pit"].iloc[0],
                    width=np.diff(df_curr["breaks"].iloc[0]),
                )
                axes[i][j].axhline(y=1, linestyle="dashed", color="r")

                if i == 0:
                    axes[i, j].title.set_text(leg_labels[metric])
                if j == 0:
                    axes[i][j].set_ylabel(temp_nn)

        # Save fig
        filename = os.path.join(
            pdf_path, f"ss_gg_pit_ens_model_{i_scenario}.pdf"
        )
        fig.savefig(filename)
        print(f"PIT saved to {filename}")


if __name__ == "__main__":
    # plot_example_aggregation()

    plot_panel_model()
    plot_panel_boxplot()
    plot_pit_ens()
