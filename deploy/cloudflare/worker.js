export default {
  async scheduled(event, env, ctx) {
    const owner = env.GITHUB_OWNER;
    const repo = env.GITHUB_REPO;
    const workflowFile = env.WORKFLOW_FILE || "collector.yml";
    const pat = env.GITHUB_PAT;
    const maxRequests = env.MAX_REQUESTS_PER_RUN || "40";

    if (!owner || !repo || !pat) {
      console.error("Missing required env vars: GITHUB_OWNER, GITHUB_REPO, GITHUB_PAT");
      return;
    }

    const payload = {
      ref: "main",
      inputs: {
        max_requests: maxRequests
      }
    };
    if (env.LOOKBACK_DAYS) {
      payload.inputs.lookback_days = env.LOOKBACK_DAYS;
    }

    const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflowFile}/dispatches`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${pat}`,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CF-Worker-Market-Scheduler"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(`Failed to dispatch GitHub workflow: HTTP ${response.status} - ${errText}`);
    } else {
      console.log(`Successfully triggered ${workflowFile} on ${owner}/${repo}`);
    }
  }
};
