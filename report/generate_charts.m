%% OpenRouter Market Analysis: OpenAI GPT-6 Luna vs GPT-5.6 Luna
% MATLAB script to visualize price elasticity, capabilities, and market expansion.
% Run this script in MATLAB or GNU Octave to export all high-resolution figures.

clear; clc; close all;

output_dir = fullfile(fileparts(mfilename('fullpath')), 'images');
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

set(0, 'DefaultAxesFontSize', 10);
set(0, 'DefaultAxesFontName', 'Helvetica');

%% -------------------------------------------------------------------------
% Figure 1: Pricing Reduction vs. Intelligence Score Parity
% -------------------------------------------------------------------------
fig1 = figure('Name', 'Pricing and Capability Parity', 'Position', [100, 100, 1100, 450], 'Color', 'w');

% Subplot 1: Token Pricing
subplot(1, 2, 1);
categories = {'Prompt', 'Completion', 'Cache Read', 'Cache Write'};
p_gpt56 = [0.20, 1.20, 0.02, 0.25];
p_gpt6  = [0.10, 0.50, 0.01, 0.125];

b = bar([p_gpt56; p_gpt6]', 'grouped');
b(1).FaceColor = [0.31, 0.27, 0.90]; % Indigo (#4f46e5)
b(2).FaceColor = [0.06, 0.73, 0.51]; % Emerald (#10b981)

set(gca, 'XTickLabel', categories);
ylabel('USD per 1 Million Tokens ($/1M)', 'FontWeight', 'bold');
title('Token Pricing: 50% ~ 58% Cost Cut', 'FontSize', 12, 'FontWeight', 'bold');
legend({'GPT-5.6 Luna', 'GPT-6 Luna (New)'}, 'Location', 'northwest');
grid on;
box on;

% Add percentage reduction annotations
text(1 + 0.15, p_gpt6(1) + 0.04, '-50.0%', 'Color', [0.02, 0.59, 0.41], 'FontWeight', 'bold', 'FontSize', 9);
text(2 + 0.15, p_gpt6(2) + 0.04, '-58.3%', 'Color', [0.02, 0.59, 0.41], 'FontWeight', 'bold', 'FontSize', 9);
text(3 + 0.15, p_gpt6(3) + 0.04, '-50.0%', 'Color', [0.02, 0.59, 0.41], 'FontWeight', 'bold', 'FontSize', 9);
text(4 + 0.15, p_gpt6(4) + 0.04, '-50.0%', 'Color', [0.02, 0.59, 0.41], 'FontWeight', 'bold', 'FontSize', 9);

% Subplot 2: Artificial Analysis Intelligence Parity
subplot(1, 2, 2);
models = {'GPT-5.6 Luna', 'GPT-6 Luna'};
scores = [37.3, 37.3];
b2 = bar(scores, 0.45);
b2.FaceColor = 'flat';
b2.CData(1, :) = [0.31, 0.27, 0.90];
b2.CData(2, :) = [0.06, 0.73, 0.51];

set(gca, 'XTickLabel', models);
ylabel('Artificial Analysis Intelligence Score', 'FontWeight', 'bold');
title('Intelligence Benchmark: Identical 37.3 Score', 'FontSize', 12, 'FontWeight', 'bold');
ylim([0, 50]);
grid on;
box on;

text(1, scores(1) + 1.8, sprintf('%.1f pts\n(Exact Match)', scores(1)), 'HorizontalAlignment', 'center', 'FontWeight', 'bold');
text(2, scores(2) + 1.8, sprintf('%.1f pts\n(Exact Match)', scores(2)), 'HorizontalAlignment', 'center', 'FontWeight', 'bold');

saveas(fig1, fullfile(output_dir, 'matlab_fig1_price_intelligence.png'));

%% -------------------------------------------------------------------------
% Figure 2: Median Cost per Session Across Interaction Depths
% -------------------------------------------------------------------------
fig2 = figure('Name', 'Session Cost Comparison', 'Position', [150, 150, 950, 480], 'Color', 'w');

buckets = {'Single Turn', 'Short Session (2-5)', 'Core Agent Session', 'Long Deep Agent'};
cost_56 = [0.00268, 0.00912, 0.04416, 0.32434];
cost_6  = [0.00113, 0.00316, 0.02333, 0.21865];

b_sess = bar([cost_56; cost_6]', 'grouped');
b_sess(1).FaceColor = [0.39, 0.40, 0.95];
b_sess(2).FaceColor = [0.02, 0.71, 0.83];

set(gca, 'YScale', 'log');
set(gca, 'XTickLabel', buckets);
ylabel('Median Session Cost (USD, Log Scale)', 'FontWeight', 'bold');
title('Session Cost Reduction Across Interaction Depths', 'FontSize', 12, 'FontWeight', 'bold');
legend({'GPT-5.6 Luna Median', 'GPT-6 Luna Median'}, 'Location', 'northwest');
grid on;
box on;

reductions = {'-57.8%', '-65.3%', '-47.2%', '-32.6%'};
for i = 1:4
    text(i + 0.15, cost_6(i) * 1.25, reductions{i}, 'Color', [0.05, 0.45, 0.56], 'FontWeight', 'bold', 'FontSize', 9);
end

saveas(fig2, fullfile(output_dir, 'matlab_fig2_session_cost.png'));

%% -------------------------------------------------------------------------
% Figure 3: Request Velocity Surge (Daily Run Rate Acceleration)
% -------------------------------------------------------------------------
fig3 = figure('Name', 'Request Acceleration', 'Position', [200, 200, 1000, 450], 'Color', 'w');

subplot(1, 2, 1);
tot_req = [24.87, 22.23]; % Millions
b_tot = bar(tot_req, 0.45);
b_tot.FaceColor = 'flat';
b_tot.CData(1, :) = [0.51, 0.55, 0.97];
b_tot.CData(2, :) = [0.20, 0.83, 0.60];
set(gca, 'XTickLabel', {'GPT-5.6 (80 Days)', 'GPT-6 (6 Days)'});
ylabel('Cumulative Requests (Millions)', 'FontWeight', 'bold');
title('Cumulative Volume: 6 Days ≈ 80 Days', 'FontSize', 11, 'FontWeight', 'bold');
ylim([0, 30]);
grid on; box on;
text(1, tot_req(1) + 0.8, '24.87M', 'HorizontalAlignment', 'center', 'FontWeight', 'bold');
text(2, tot_req(2) + 0.8, '22.23M', 'HorizontalAlignment', 'center', 'FontWeight', 'bold');

subplot(1, 2, 2);
daily_req = [0.311, 3.705]; % Millions / Day
b_daily = bar(daily_req, 0.45);
b_daily.FaceColor = 'flat';
b_daily.CData(1, :) = [0.39, 0.40, 0.95];
b_daily.CData(2, :) = [0.06, 0.73, 0.51];
set(gca, 'XTickLabel', {'GPT-5.6 Luna', 'GPT-6 Luna'});
ylabel('Daily Request Velocity (Millions / Day)', 'FontWeight', 'bold');
title('Adoption Velocity: 11.9x Surge', 'FontSize', 11, 'FontWeight', 'bold');
ylim([0, 4.5]);
grid on; box on;
text(1, daily_req(1) + 0.15, '0.311M / day', 'HorizontalAlignment', 'center', 'FontWeight', 'bold');
text(2, daily_req(2) + 0.15, '3.705M / day', 'HorizontalAlignment', 'center', 'FontWeight', 'bold');

saveas(fig3, fullfile(output_dir, 'matlab_fig3_velocity_surge.png'));

%% -------------------------------------------------------------------------
% Figure 4: Task Market Share & Category Penetration
% -------------------------------------------------------------------------
fig4 = figure('Name', 'Task Market Share', 'Position', [250, 250, 900, 500], 'Color', 'w');

tasks = {
    'Code: DevOps Config', ...
    'Code: General Impl', ...
    'Code: Security Review', ...
    'Code: Debugging', ...
    'Translation', ...
    'Data: Transformation', ...
    'Agent: Tool Dispatch'
};
shares = [24.56, 24.49, 20.60, 16.47, 11.92, 10.96, 10.52];
deltas = [15.43, 13.01, 9.53, 8.88, 4.77, 3.33, 2.34];

% Invert order for horizontal bar
tasks = fliplr(tasks);
shares = fliplr(shares);
deltas = fliplr(deltas);

b_task = barh(shares, 0.6);
b_task.FaceColor = [0.23, 0.51, 0.96]; % Blue
set(gca, 'YTickLabel', tasks);
xlabel('Token Consumption Share in Category (%)', 'FontWeight', 'bold');
title('Luna Token Consumption Share in High-Value Workflows', 'FontSize', 12, 'FontWeight', 'bold');
xlim([0, 32]);
grid on; box on;

for i = 1:length(shares)
    text(shares(i) + 0.5, i, sprintf('%.1f%% (+%.1f%% delta)', shares(i), deltas(i)), ...
        'VerticalAlignment', 'middle', 'FontWeight', 'bold', 'FontSize', 9, 'Color', [0.11, 0.31, 0.85]);
end

saveas(fig4, fullfile(output_dir, 'matlab_fig4_task_share.png'));

fprintf('\n[+] All MATLAB figures generated and saved to %s\n', output_dir);
