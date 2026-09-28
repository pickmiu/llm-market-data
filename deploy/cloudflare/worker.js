export default {
  async scheduled(event, env, ctx) {
    const owner = env.GITHUB_OWNER;
    const repo = env.GITHUB_REPO;
    const workflowFile = env.WORKFLOW_FILE || "collector.yml";
    const pat = env.GITHUB_PAT;
    const branch = env.GITHUB_REF || env.GITHUB_BRANCH || "main";
    const maxRequests = env.MAX_REQUESTS_PER_RUN || "40";

    if (!owner || !repo || !pat) {
      const missing = [];
      if (!owner) missing.push("GITHUB_OWNER");
      if (!repo) missing.push("GITHUB_REPO");
      if (!pat) missing.push("GITHUB_PAT");
      throw new Error(`Missing required env vars: ${missing.join(", ")}`);
    }

    try {
      const payload = {
        ref: branch,
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
        throw new Error(`Failed to dispatch GitHub workflow: HTTP ${response.status} - ${errText}`);
      }

      console.log(`Successfully triggered ${workflowFile} on ${owner}/${repo}`);
    } catch (err) {
      console.error(`Dispatch error: ${err.message}`);
      throw err;
    }
  }
};
