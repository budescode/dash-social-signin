import json
import os
import shutil
from importlib.resources import files
from typing import Dict, Iterable, List, Optional

from dash import html

ASSET_FILENAMES = [
    "dash-social-signin.js",
    "dash-social-signin.css",
]


def install_assets(target_assets_dir: str) -> List[str]:
    """Copy packaged JS/CSS assets into a Dash app assets directory."""
    os.makedirs(target_assets_dir, exist_ok=True)
    copied: List[str] = []

    for filename in ASSET_FILENAMES:
        src_path = files("dash_social_signin").joinpath("assets", filename)
        dest_path = os.path.join(target_assets_dir, filename)
        shutil.copyfile(src_path, dest_path)
        copied.append(dest_path)

    return copied


def build_container(config: Dict, id: str = "dss-root", className: Optional[str] = None):
    """Return a Dash HTML container with embedded config data."""
    attrs = {"data-dss-config": json.dumps(config)}
    return html.Div(id=id, className=className, **attrs)
