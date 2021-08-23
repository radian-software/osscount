#!/usr/bin/env python3

import argparse
import sys

import dateutil.parser
import ruamel.yaml


class Project:
    def __init__(self, *, name, repos, ref_override=None, timeline_override=None):
        self.name = name
        self.repos = repos
        self.ref_override = None
        self.timeline_override = None


class Config:
    def __init__(self, fname):
        self.load_from_file(fname)

    def load_from_file(self, fname):
        yaml = ruamel.yaml.YAML(typ="safe")
        with open(fname) as f:
            config = yaml.load(f)
        self.projects = []
        for project_config in config["projects"]:
            name = project_config["name"]
            repos = project_config["repo"]
            if not isinstance(repos, list):
                repos = [repos]
            ref_override = project_config.get("ref")
            timeline_override = None
            if project_config.get("timeline"):
                timeline_override = (
                    dateutil.parser.parse(project_config["timeline"]["linear"]["from"]),
                    dateutil.parser.parse(project_config["timeline"]["linear"]["to"]),
                )
            self.projects.append(
                Project(
                    name=name,
                    repos=repos,
                    ref_override=ref_override,
                    timeline_override=timeline_override,
                )
            )


def main():
    parser = argparse.ArgumentParser("osscount")
    parser.add_argument("-c", "--config", type=str, default="raxod502.yaml")
    args = parser.parse_args()
    config = Config(args.config)


if __name__ == "__main__":
    main()
    sys.exit(0)
