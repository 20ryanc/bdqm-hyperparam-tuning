from functools import lru_cache

import optuna
from dotenv import dotenv_values

from ampopt.utils import ampopt_path


@lru_cache
def connection_string() -> str:
    """Construct DB connection string from .env file."""
    config = dotenv_values(ampopt_path / ".env")
    username = config["MYSQL_USERNAME"]
    password = config["MYSQL_PASSWORD"]
    node = config["MYSQL_NODE"]
    db = config["HPOPT_DB"]
    return f"mysql+pymysql://{username}:{password}@{node}/{db}"


def delete_study(study_name: str):
    optuna.delete_study(study_name=study_name, storage=connection_string())
    print(f"Deleted study {study_name}.")


def delete_studies(*study_names: str):
    for study_name in study_names:
        delete_study(study_name)


def get_study(study_name: str):
    return optuna.load_study(study_name=study_name, storage=connection_string())


def get_all_studies():
    return optuna.get_all_study_summaries(storage=connection_string())


def get_or_create_study(study_name: str, with_db: str, sampler: str, pruner: str):
    samplers = {
        "CmaEs": optuna.samplers.CmaEsSampler(n_startup_trials=10),
        "TPE": optuna.samplers.TPESampler(n_startup_trials=40),
        "Random": optuna.samplers.RandomSampler(),
        "Grid": optuna.samplers.GridSampler(
            search_space={"num_layers": range(3, 9), "num_nodes": range(4, 16)}
        ),
    }

    pruners = {
        "Hyperband": optuna.pruners.HyperbandPruner(),
        "Median": optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=10),
        "None": optuna.pruners.NopPruner(),
    }

    params = {
        "sampler": samplers[sampler],
        "pruner": pruners[pruner],
        "study_name": study_name,
    }

    if with_db:
        params["storage"] = connection_string()
        params["load_if_exists"] = True

    return optuna.create_study(**params)


def view_all_studies():
    ensure_mysql_running()

    studies = get_all_studies()
    for study in studies:
        print(f"Study {study.study_name}:")
        print(f"  Params:")
        for param in study.best_trial.params:
            print(f"    - {param}")
        print(f"  Best score: {study.best_trial.value}")
        print(f"  Num trials: {study.n_trials}")


def generate_report(study_name: str):
    ensure_mysql_running()
    report_dir = ampopt_path / "report" / study_name
    try:
        report_dir.mkdir(parents=True)
    except FileExistsError:
        print(f"Report directory {report_dir} already exists.")
        return

    study = get_study(study_name)
    fig = optuna.visualization.plot_contour(study, params=["num_layers", "num_nodes"])
    fig.write_image(report_dir / "contour_plot.png")

    optuna.visualization.plot_intermediate_values(study).write_image(
        report_dir / "intermediate.png"
    )

    print(f"Best params: {study.best_params} with MAE {study.best_value}")
    print(f"Report saved to {report_dir}")