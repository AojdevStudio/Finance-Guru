"""The dependency repair workflow reruns safely after a push whose CI dispatch failed."""

import json
import os
import subprocess
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[2] / "scripts/qa/dependency_repair.cjs"
BRANCH = "dependabot/uv/grouped"
REPO = {"owner": "AojdevStudio", "repo": "Finance-Guru"}
DRIVER = """
const helper = require(process.env.HELPER);
const state = JSON.parse(process.env.STATE);
const dispatches = [];
const github = { rest: {
  pulls: { list: async () => ({ data: state.pulls }) },
  repos: { getCommit: async ({ ref }) => {
    if (!state.commits[ref]) throw Object.assign(new Error('Not Found'), { status: 404 });
    return { data: state.commits[ref] };
  } },
  git: { getRef: async ({ ref }) => ({ data: { object: { sha: state.refs[ref] } } }) },
  actions: {
    listWorkflowRuns: async ({ workflow_id, head_sha }) => {
      const runs = state.ci.filter(sha => workflow_id === 'ci.yml' && sha === head_sha);
      return { data: { total_count: runs.length, workflow_runs: runs.map(sha => ({ head_sha: sha })) } };
    },
    createWorkflowDispatch: async request => {
      if (state.dispatchFails) throw new Error('HTTP 500: dispatch failed');
      dispatches.push(request);
    },
  },
} };
const context = { repo: state.repo, payload: { workflow_run: state.run } };
const operation = process.env.OPERATION === 'identify'
  ? helper.identify({ github, context })
  : helper.ensureCi({ github, context, ...JSON.parse(process.env.ARGUMENTS) });
operation.then(
  result => console.log(JSON.stringify({ result, dispatches })),
  error => console.log(JSON.stringify({ error: error.message, dispatches })),
);
"""


def pull(
    sha: str,
    author: str = "dependabot[bot]",
    repository: str = "AojdevStudio/Finance-Guru",
) -> dict:
    return {
        "number": 209,
        "user": {"login": author},
        "head": {"sha": sha, "ref": BRANCH, "repo": {"full_name": repository}},
        "base": {"sha": "base"},
    }


def commit(
    sha: str, parent: str, files=("uv.lock", "requirements.txt"), **overrides
) -> dict:
    identity = {
        "name": "github-actions[bot]",
        "email": "41898282+github-actions[bot]@users.noreply.github.com",
    }
    details = {
        "message": "fix(deps): synchronize the canonical lock and export",
        "author": dict(identity),
        "committer": dict(identity),
    }
    details.update(overrides)
    return {
        "sha": sha,
        "parents": [{"sha": parent}],
        "commit": details,
        "files": [{"filename": name, "status": "modified"} for name in files],
    }


def scenario(head: str, commits=(), ci=(), dispatch_fails=False, pulls=None) -> dict:
    return {
        "repo": REPO,
        "run": {"head_branch": BRANCH, "head_sha": "dependabot"},
        "pulls": [pull(head)] if pulls is None else pulls,
        "commits": {item["sha"]: item for item in commits},
        "refs": {f"heads/{BRANCH}": head},
        "ci": list(ci),
        "dispatchFails": dispatch_fails,
    }


def helper(operation: str, state: dict, **arguments) -> dict:
    completed = subprocess.run(
        ["bun", "-e", DRIVER],
        env={
            **os.environ,
            "HELPER": str(HELPER),
            "STATE": json.dumps(state),
            "OPERATION": operation,
            "ARGUMENTS": json.dumps(arguments),
        },
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_rerun_after_push_with_failed_dispatch_runs_ci_on_the_repair_head():
    first = helper("identify", scenario("dependabot"))["result"]
    assert first == {
        "action": "repair",
        "number": 209,
        "branch": BRANCH,
        "sha": "dependabot",
        "base": "base",
    }

    repair = commit("repair", parent="dependabot")
    pushed = scenario("repair", commits=[repair], dispatch_fails=True)
    failed = helper("ensureCi", pushed, branch=BRANCH, sha="repair")
    assert failed == {"error": "HTTP 500: dispatch failed", "dispatches": []}

    rerun = scenario("repair", commits=[repair])
    recognized = helper("identify", rerun)["result"]
    assert recognized == {
        "action": "dispatch",
        "number": 209,
        "branch": BRANCH,
        "sha": "repair",
        "base": "base",
    }
    dispatched = helper("ensureCi", rerun, branch=BRANCH, sha="repair")
    assert dispatched == {
        "result": "dispatched",
        "dispatches": [{**REPO, "workflow_id": "ci.yml", "ref": BRANCH}],
    }

    again = helper(
        "ensureCi",
        scenario("repair", commits=[repair], ci=["repair"]),
        branch=BRANCH,
        sha="repair",
    )
    assert again == {"result": "existing", "dispatches": []}


def test_ci_is_not_dispatched_when_the_branch_moved_past_the_repair():
    state = scenario("newer", commits=[commit("repair", parent="dependabot")])
    assert helper("ensureCi", state, branch=BRANCH, sha="repair") == {
        "result": "moved",
        "dispatches": [],
    }


@pytest.mark.parametrize(
    "state",
    [
        scenario(
            "other",
            commits=[commit("other", parent="dependabot", message="chore: tweak")],
        ),
        scenario(
            "other",
            commits=[
                commit(
                    "other",
                    parent="dependabot",
                    author={"name": "x", "email": "x@example.invalid"},
                )
            ],
        ),
        scenario(
            "other",
            commits=[
                commit(
                    "other", parent="dependabot", files=("uv.lock", "pyproject.toml")
                )
            ],
        ),
        scenario("other", commits=[commit("other", parent="older")]),
        scenario("dependabot", pulls=[pull("dependabot", author="someone")]),
        scenario(
            "dependabot", pulls=[pull("dependabot", repository="fork/Finance-Guru")]
        ),
        scenario("dependabot", pulls=[pull("dependabot"), pull("dependabot")]),
    ],
    ids=[
        "foreign-message",
        "foreign-author",
        "touches-project-files",
        "stale-event-for-older-head",
        "not-dependabot",
        "fork",
        "ambiguous-pull",
    ],
)
def test_an_event_never_relabels_a_head_it_did_not_produce(state):
    assert helper("identify", state)["result"] is None
