import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configure styling
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#f0f0f0'
plt.rcParams['grid.linestyle'] = '--'

output_dir = Path(__file__).resolve().parent / "images"
output_dir.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# Chart 1: Pricing vs Intelligence Parity
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

metrics = ['Prompt ($/1M)', 'Completion ($/1M)', 'Cache Read ($/1M)', 'Cache Write ($/1M)']
gpt56_prices = [0.20, 1.20, 0.02, 0.25]
gpt6_prices = [0.10, 0.50, 0.01, 0.125]
reductions = ['-50.0%', '-58.3%', '-50.0%', '-50.0%']

x = np.arange(len(metrics))
width = 0.35

rects1 = ax1.bar(x - width/2, gpt56_prices, width, label='GPT-5.6 Luna', color='#4f46e5', alpha=0.85)
rects2 = ax1.bar(x + width/2, gpt6_prices, width, label='GPT-6 Luna (New)', color='#10b981', alpha=0.85)

ax1.set_ylabel('USD per 1 Million Tokens', fontsize=11, fontweight='bold')
ax1.set_title('Token Pricing: ~50% to 58% Cost Cut', fontsize=13, fontweight='bold', pad=12)
ax1.set_xticks(x)
ax1.set_xticklabels(metrics, rotation=15, ha='right', fontsize=9)
ax1.legend(frameon=True, facecolor='#ffffff', edgecolor='#e5e7eb')
ax1.grid(True, axis='y')

for i in range(len(metrics)):
    h = gpt6_prices[i]
    ax1.text(x[i] + width/2, h + 0.03, reductions[i], ha='center', va='bottom', fontsize=9, fontweight='bold', color='#059669')

# Subplot 2: Capability Parity (AA Score)
models = ['GPT-5.6 Luna', 'GPT-6 Luna (New)']
scores = [37.3, 37.3]
bar_colors = ['#4f46e5', '#10b981']

bars = ax2.bar(models, scores, color=bar_colors, width=0.45, alpha=0.85)
ax2.set_ylabel('Artificial Analysis Score', fontsize=11, fontweight='bold')
ax2.set_title('Intelligence Parity: Identical 37.3 Score', fontsize=13, fontweight='bold', pad=12)
ax2.set_ylim(0, 50)
ax2.grid(True, axis='y')

for bar in bars:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 1.0, f'{yval:.1f} pts\n(Exact Match)', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / "fig1_price_intelligence_comparison.png")
plt.close()

# -------------------------------------------------------------
# Chart 2: Cost per Session Reduction Across Turn Depths
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

buckets = ['Single Turn\n(Fast Prompt)', 'Short Session\n(2-5 turns)', 'Core Session\n(Agent Workflow)', 'Long Session\n(Deep Coding Agent)']
gpt56_session = [0.00268, 0.00912, 0.04416, 0.32434]
gpt6_session = [0.00113, 0.00316, 0.02333, 0.21865]
session_cuts = ['-57.8%', '-65.3%', '-47.2%', '-32.6%']

x = np.arange(len(buckets))
width = 0.35

r1 = ax.bar(x - width/2, gpt56_session, width, label='GPT-5.6 Luna Median Cost', color='#6366f1')
r2 = ax.bar(x + width/2, gpt6_session, width, label='GPT-6 Luna Median Cost', color='#06b6d4')

ax.set_yscale('log')
ax.set_ylabel('Median Cost per Session (USD, Log Scale)', fontsize=11, fontweight='bold')
ax.set_title('Session Cost Reduction Across Interaction Depths', fontsize=13, fontweight='bold', pad=12)
ax.set_xticks(x)
ax.set_xticklabels(buckets, fontsize=10)
ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e5e7eb')
ax.grid(True, which='both', axis='y')

for i in range(len(buckets)):
    ax.text(x[i] + width/2, gpt6_session[i] * 1.15, session_cuts[i], ha='center', va='bottom', fontsize=9, fontweight='bold', color='#0e7490')

plt.tight_layout()
plt.savefig(output_dir / "fig2_session_cost_curve.png")
plt.close()

# -------------------------------------------------------------
# Chart 3: Request Velocity Surge (Daily Run Rate Acceleration)
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

models_req = ['GPT-5.6 Luna\n(80 days on market)', 'GPT-6 Luna\n(6 days on market)']
total_reqs = [24.87, 22.23] # millions
daily_rate = [0.311, 3.705] # millions per day

# Subplot 1: Total requests
bars_tot = ax1.bar(models_req, total_reqs, color=['#818cf8', '#34d399'], width=0.45)
ax1.set_ylabel('Cumulative Requests (Millions)', fontsize=11, fontweight='bold')
ax1.set_title('Cumulative Requests: 6 Days ≈ 80 Days', fontsize=12, fontweight='bold', pad=12)
ax1.set_ylim(0, 30)
ax1.grid(True, axis='y')

for bar in bars_tot:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.6, f'{yval:.2f}M', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Subplot 2: Daily velocity
bars_vel = ax2.bar(models_req, daily_rate, color=['#6366f1', '#10b981'], width=0.45)
ax2.set_ylabel('Average Daily Requests (Millions / Day)', fontsize=11, fontweight='bold')
ax2.set_title('Daily Adoption Velocity: 11.9x Surge', fontsize=12, fontweight='bold', pad=12)
ax2.set_ylim(0, 4.5)
ax2.grid(True, axis='y')

for bar in bars_vel:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f'{yval:.3f}M / day', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax2.annotate('11.9x Surge\n(1,190% Velocity)', xy=(1, 3.705), xytext=(0.5, 4.0),
             arrowprops=dict(facecolor='#059669', shrink=0.08, width=2, headwidth=8),
             fontsize=10, fontweight='bold', color='#059669', ha='center')

plt.tight_layout()
plt.savefig(output_dir / "fig3_daily_request_acceleration.png")
plt.close()

# -------------------------------------------------------------
# Chart 4: Task Market Share & Growth Momentum
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)

tasks = [
    'Code: DevOps Config',
    'Code: General Impl',
    'Code: Security Review',
    'Code: Debugging',
    'Translation',
    'Data: Transformation',
    'Agent: Tool Dispatch'
]
shares = [24.56, 24.49, 20.60, 16.47, 11.92, 10.96, 10.52]
deltas = [15.43, 13.01, 9.53, 8.88, 4.77, 3.33, 2.34]

y_pos = np.arange(len(tasks))

bars = ax.barh(y_pos, shares, align='center', color='#3b82f6', alpha=0.85, label='Token Market Share (%)')
ax.set_yticks(y_pos)
ax.set_yticklabels(tasks, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel('Token Consumption Share in Category (%)', fontsize=11, fontweight='bold')
ax.set_title('Luna Token Consumption Share in High-Value Workflows', fontsize=13, fontweight='bold', pad=12)
ax.set_xlim(0, 32)
ax.grid(True, axis='x')

for i, bar in enumerate(bars):
    w = bar.get_width()
    ax.text(w + 0.6, bar.get_y() + bar.get_height()/2, f'{w:.1f}% (+{deltas[i]:.1f}% delta)',
            va='center', fontsize=9, fontweight='bold', color='#1d4ed8')

plt.tight_layout()
plt.savefig(output_dir / "fig4_task_token_market_share.png")
plt.close()

print("[+] All charts successfully generated in report/images/")
