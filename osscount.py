#!/usr/bin/env python3

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

import dateutil.parser
import ruamel.yaml


class Repo:
    def __init__(self, name, *, config, ref=None):
        self.config = config
        self.name = name
        assert re.fullmatch(r"[a-zA-Z0-9-]+/[a-zA-Z0-9._-]+", name)
        self.ref = ref

    @property
    def clone_url(self):
        return "https://github.com/{}.git".format(self.name)

    @property
    def repo_dir(self):
        return config.repos_dir / self.name

    def git(self, args, **kwargs):
        return subprocess.run(["git", "-C", self.repo_dir, *args], check=True, **kwargs)

    def clone(self):
        assert not self.repo_dir.exists()
        self.local_fname.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    self.clone_url,
                    self.repo_dir,
                    *(["--no-checkout"] if self.ref else []),
                ],
                check=True,
            )
            if self.ref:
                self.git(["checkout", self.ref])
        except Exception:
            try:
                shutil.rmtree(self.repo_dir)
            except FileNotFoundError:
                pass

    def pull(self):
        subprocess.run(["git", "-C", self.repo_dir, "fetch"], check=True)
        if self.ref:
            self.git(["checkout", self.ref])
        else:
            default_branch = (
                self.git(
                    ["symbolic-ref", "refs/remotes/origin/HEAD"],
                    check=True,
                    stdout=subprocess.PIPE,
                )
                .stdout.decode()
                .replace("refs/remotes/origin/", "")
            )
            self.git(
                ["checkout", "-B", default_branch, "origin/{}".format(default_branch)]
            )

    def __members(self):
        return (self.name, self.ref)

    def __eq__(self, other):
        return type(self) is type(other) and self.__members() == other.__members()

    def __hash__(self):
        return hash(self.__members())


class Project:
    def __init__(
        self, *, config, name, repos, ref_override=None, timeline_override=None
    ):
        self.config = config
        self.name = name
        self.repos = [Repo(name, config=config) for name in repos]
        self.ref_override = None
        self.timeline_override = None


class Config:
    def __init__(self, *, fname, workdir):
        self.load_from_file(fname)
        self.workdir = pathlib.Path(workdir).resolve()

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
                    config=self,
                    name=name,
                    repos=repos,
                    ref_override=ref_override,
                    timeline_override=timeline_override,
                )
            )
        self.validate()

    @property
    def repos_dir(self):
        return self.workdir / "repos"


def main():
    parser = argparse.ArgumentParser("osscount")
    parser.add_argument("-c", "--config", type=str, default="raxod502.yaml")
    parser.add_argument("-w", "--workdir", type=str, default="work")
    args = parser.parse_args()
    config = Config(fname=args.config, workdir=args.workdir)
    config.validate()


if __name__ == "__main__":
    main()
    sys.exit(0)
