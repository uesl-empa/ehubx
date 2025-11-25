import os
import shutil


DIRNAME_TMPTESTMODEL: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "_tmp_model")
)
DIRNAME_EXAMPLES: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, "examples")
)


def init_tmp_model(example_model_dir: str):
    # Create or clear model directory
    model_dir = os.path.join(os.path.dirname(__file__), DIRNAME_TMPTESTMODEL)
    if os.path.isdir(model_dir):
        shutil.rmtree(model_dir)
    os.mkdir(model_dir)

    # Copy inputs of example model to temporary model directory
    input_dir = os.path.join(model_dir, "inputs")
    example_input_dir = os.path.join(example_model_dir, "inputs")
    shutil.copytree(example_input_dir, input_dir)


def clear_tmp_model():
    model_dir = os.path.join(os.path.dirname(__file__), DIRNAME_TMPTESTMODEL)
    if os.path.isdir(model_dir):
        shutil.rmtree(model_dir)
