'use strict';

const BOT = 'dependabot[bot]';
const REPAIR_MESSAGE = 'fix(deps): synchronize the canonical lock and export';
const REPAIR_IDENTITY = {
  name: 'github-actions[bot]',
  email: '41898282+github-actions[bot]@users.noreply.github.com',
};
const GENERATED_FILES = new Set(['uv.lock', 'requirements.txt']);

const isRepairIdentity = person =>
  person.name === REPAIR_IDENTITY.name && person.email === REPAIR_IDENTITY.email;

async function isRepairOf(github, context, sha, parent) {
  const { data } = await github.rest.repos.getCommit({ ...context.repo, ref: sha });
  return (
    data.parents.length === 1 &&
    data.parents[0].sha === parent &&
    data.commit.message.trimEnd() === REPAIR_MESSAGE &&
    isRepairIdentity(data.commit.author) &&
    isRepairIdentity(data.commit.committer) &&
    data.files.length > 0 &&
    data.files.every(file => file.status === 'modified' && GENERATED_FILES.has(file.filename))
  );
}

async function identify({ github, context }) {
  const run = context.payload.workflow_run;
  const repository = `${context.repo.owner}/${context.repo.repo}`;
  const { data } = await github.rest.pulls.list({
    ...context.repo,
    state: 'open',
    head: `${context.repo.owner}:${run.head_branch}`,
  });
  const matches = data.filter(
    pr =>
      pr.user.login === BOT &&
      pr.head.repo.full_name === repository &&
      pr.head.ref === run.head_branch,
  );
  if (matches.length !== 1) return null;
  const [pr] = matches;
  const repair = { number: pr.number, branch: pr.head.ref, sha: pr.head.sha, base: pr.base.sha };
  if (pr.head.sha === run.head_sha) return { action: 'repair', ...repair };
  if (await isRepairOf(github, context, pr.head.sha, run.head_sha)) {
    return { action: 'dispatch', ...repair };
  }
  return null;
}

// A push made with the workflow token starts no CI, so the repaired head needs a dispatch.
async function ensureCi({ github, context, branch, sha }) {
  const { data: ref } = await github.rest.git.getRef({ ...context.repo, ref: `heads/${branch}` });
  if (ref.object.sha !== sha) return 'moved';
  const { data: runs } = await github.rest.actions.listWorkflowRuns({
    ...context.repo,
    workflow_id: 'ci.yml',
    head_sha: sha,
    per_page: 1,
  });
  if (runs.total_count > 0) return 'existing';
  await github.rest.actions.createWorkflowDispatch({ ...context.repo, workflow_id: 'ci.yml', ref: branch });
  return 'dispatched';
}

module.exports = { REPAIR_IDENTITY, REPAIR_MESSAGE, ensureCi, identify };
