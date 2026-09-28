async function triggerDispatch(env, customInputs = {}) {
  const owner = env.GITHUB_OWNER || "pickmiu";
  const repo = env.GITHUB_REPO || "llm-market-data";
  const workflowFile = env.WORKFLOW_FILE || "collector.yml";
  const pat = env.GITHUB_PAT;
  const branch = customInputs.branch || env.GITHUB_REF || env.GITHUB_BRANCH || "main";
  const maxRequests = customInputs.max_requests || env.MAX_REQUESTS_PER_RUN || "40";

  if (!pat) {
    throw new Error("Missing required env var: GITHUB_PAT (set via wrangler.toml [vars] or Cloudflare Secrets)");
  }

  const payload = {
    ref: branch,
    inputs: {
      max_requests: String(maxRequests)
    }
  };

  const lookback = customInputs.lookback_days || env.LOOKBACK_DAYS;
  if (lookback) {
    payload.inputs.lookback_days = String(lookback);
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

  return {
    status: "ok",
    message: `Successfully triggered ${workflowFile} on ${owner}/${repo}`,
    ref: branch,
    inputs: payload.inputs
  };
}

export default {
  // 1. 手动触发接口（支持浏览器访问或 HTTP POST/GET 接口调用）
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 解析入参（支持 URL Query 参数和 JSON Body）
    const customInputs = {};
    if (url.searchParams.has("max_requests")) {
      customInputs.max_requests = url.searchParams.get("max_requests");
    }
    if (url.searchParams.has("lookback_days")) {
      customInputs.lookback_days = url.searchParams.get("lookback_days");
    }
    if (url.searchParams.has("branch")) {
      customInputs.branch = url.searchParams.get("branch");
    }

    if (request.method === "POST" && request.headers.get("content-type")?.includes("application/json")) {
      try {
        const body = await request.json();
        Object.assign(customInputs, body);
      } catch (_) {
        // ignore invalid JSON
      }
    }

    try {
      const result = await triggerDispatch(env, customInputs);
      return new Response(JSON.stringify(result, null, 2), {
        status: 200,
        headers: { "Content-Type": "application/json; charset=utf-8" }
      });
    } catch (err) {
      console.error(`Manual dispatch error: ${err.message}`);
      return new Response(JSON.stringify({ status: "error", error: err.message }, null, 2), {
        status: 500,
        headers: { "Content-Type": "application/json; charset=utf-8" }
      });
    }
  },

  // 2. 定时任务触发（Cron Trigger: 每日 00:30 UTC）
  async scheduled(event, env, ctx) {
    try {
      const result = await triggerDispatch(env);
      console.log(`Cron dispatch success: ${result.message}`);
    } catch (err) {
      console.error(`Cron dispatch error: ${err.message}`);
      throw err;
    }
  }
};
