async function triggerDispatch(env, customInputs = {}) {
  const owner = env.GITHUB_OWNER || "pickmiu";
  const repo = env.GITHUB_REPO || "llm-market-data";
  const workflowFile = env.WORKFLOW_FILE || "collector.yml";
  const pat = env.GITHUB_PAT || env.GH_TOKEN;
  const branch = customInputs.branch || env.GITHUB_REF || env.GITHUB_BRANCH || "main";
  const maxRequests = customInputs.max_requests || env.MAX_REQUESTS_PER_RUN || "40";

  if (!pat) {
    throw new Error("Missing required env var: GITHUB_PAT (or GH_TOKEN). Please set it in wrangler.toml or Cloudflare Secrets.");
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
  // 1. 定时触发核心逻辑 (Cron Trigger: 每日 00:30 UTC)
  async scheduled(event, env, ctx) {
    const rawCron = event.cron || "";
    const cron = rawCron.trim().replace(/\s+/g, " ");
    console.log(`[Cron Triggered] 收到表达式: "${rawCron}", 归一化: "${cron}"`);

    try {
      const result = await triggerDispatch(env);
      console.log(`[Cron Dispatch] 成功触发数据同步: ${result.message}`);
    } catch (err) {
      console.error(`[Cron Dispatch] 触发异常: ${err.message}`);
      throw err;
    }
  },

  // 2. HTTP 访问与手动触发接口
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 忽略浏览器自动请求的 favicon.ico
    if (url.pathname === "/favicon.ico") {
      return new Response(null, { status: 204 });
    }

    // CORS 预检支持
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        }
      });
    }

    // 手动触发接口：支持 /trigger, /trigger/sync, /trigger/collector
    if (
      url.pathname === "/trigger" ||
      url.pathname === "/trigger/sync" ||
      url.pathname === "/trigger/collector"
    ) {
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
          headers: {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*"
          }
        });
      } catch (err) {
        console.error(`[Manual Dispatch Error]: ${err.message}`);
        return new Response(JSON.stringify({ status: "error", error: err.message }, null, 2), {
          status: 500,
          headers: {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }
    }

    // 根路径：仅展示运行状态与说明信息，不触发任何 GitHub Actions
    return new Response(
      `LLM Market Data Scheduler is Running!\n\n` +
      `Repository: ${env.GITHUB_OWNER || "pickmiu"}/${env.GITHUB_REPO || "llm-market-data"}\n` +
      `Workflow:   ${env.WORKFLOW_FILE || "collector.yml"}\n\n` +
      `Manual test endpoints:\n` +
      `- Trigger:       ${url.origin}/trigger\n` +
      `- Trigger sync:  ${url.origin}/trigger/sync\n` +
      `- With params:   ${url.origin}/trigger/sync?max_requests=40&lookback_days=30\n`,
      {
        status: 200,
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Access-Control-Allow-Origin": "*"
        }
      }
    );
  }
};
