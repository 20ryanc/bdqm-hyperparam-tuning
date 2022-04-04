import warnings
from functools import partial
from uuid import uuid4

import numpy as np
from amptorch.trainer import AtomsTrainer
from ase.io import Trajectory
from optuna.integration.skorch import SkorchPruningCallback
from sklearn.metrics import mean_absolute_error
from torch import nn

from hpopt.utils import bdqm_hpopt_path, gpus

data_path = bdqm_hpopt_path / "data"

valid_imgs = Trajectory(data_path / "valid.traj")
y_valid = np.array([img.get_potential_energy() for img in valid_imgs])

warnings.simplefilter("ignore")


def get_param_dict(params, trial, name, low, *args, **kwargs):
    """
    Get value of parameter as dictionary, either from params dictionary or from trial.

    Args:
        params: dict str -> int|float mapping param name to value
        trial: optuna trial
        name: name of param
        *args, **kwargs: arguments for trial.suggest_int or trial.suggest_float

    Returns:
        dictionary str -> int|float mapping `name` to its value.
    """
    try:
        val = params[name]
    except KeyError:
        param_type = type(low).__name__
        method = getattr(trial, f"suggest_{param_type}")
        val = method(name, low, *args, **kwargs)

    return {name: val}


def mk_objective(verbose, epochs, **params):
    def objective(trial):
        get = partial(get_param_dict, params, trial)
        config = {
            "model": {
                **get("num_layers", 3, 8),
                **get("num_nodes", 4, 15),
                "name": "singlenn",
                "get_forces": False,
                **get("batchnorm", 0, 1),
                "dropout": 1,
                **get("dropout_rate", 0.0, 1.0),
                "initialization": "xavier",
                "activation": nn.Tanh,
            },
            "optim": {
                "gpus": gpus,
                **get("lr", 1e-5, 1e-2, log=True),
                "scheduler": {
                    "policy": "StepLR",
                    "params": {
                        **get("step_size", 1, 30, 5),
                        **get("gamma", 1e-5, 1e-1, log=True),
                    },
                },
                **get("batch_size", 100, 500, 50),
                "loss": "mae",
                "epochs": epochs,
            },
            "dataset": {
                "lmdb_path": [str(data_path / "train.lmdb")],
                "cache": "full",
                # "val_split": 0.1,
            },
            "cmd": {
                # "debug": True, # prevents logging to checkpoints
                "seed": 12,
                "identifier": str(uuid4()),
                "dtype": "torch.DoubleTensor",
                "verbose": verbose,
                "custom_callback": SkorchPruningCallback(trial, "train_energy_mae"),
            },
        }

        trainer = AtomsTrainer(config)
        trainer.train()

        return mean_absolute_error(trainer.predict(valid_imgs)["energy"], y_valid)

    return objective
