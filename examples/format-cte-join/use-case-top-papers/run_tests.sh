#!/usr/bin/env bash
# Run from: examples/format-cte-join/use-case-top-papers/

cd /home/papagame/projects/digital-duck/SPL/examples/format-cte-join/use-case-top-papers/

# Preview token plan without running (free — no LLM call)
spl explain papers-by-top-prize-winners-recently_v1.spl \
    --log ./results/spl_explain.log \
    --output ./results/spl_explain.md

# SPL test using adapter=Claude CLI (free, no API key needed)
spl execute papers-by-top-prize-winners-recently_v1.spl \
    --adapter claude_cli \
    --tools "WebSearch,WebFetch" \
    --log ./results/spl_cli.log \
    --output ./results/spl_cli.json

# BENCHMARK — compare three models (requires OpenRouter API key)
splflow benchmark papers-by-top-prize-winners-recently_v1.spl \
    --adapter openrouter \
    --models "anthropic/claude-opus-4.6, openai/gpt-4o-2024-11-20, google/gemini-3-pro-preview, google/gemini-3-flash-preview, z-ai/glm-5, qwen/qwen3-235b-a22b, moonshotai/kimi-k2" \
    --log ./results/spl_benchmark-v2.log \
    --output ./results/spl_benchmark-v2.json

# splflow benchmark papers-by-top-prize-winners-recently_v1.spl \
#     --adapter openrouter \
#     --models "anthropic/claude-sonnet-4.5, openai/gpt-4o-2024-11-20, google/gemini-3-flash-preview" \
#     --log ./results/spl_benchmark.log \
#     --output ./results/spl_benchmark.json


splflow rerun results/spl_benchmark-v2.json --model z-ai/glm-4.7 --adapter openrouter --log ./results/spl_benchmark-v2.1.log --output ./results/spl_benchmark-v2.1.json

splflow rerun results/spl_benchmark-v2.json --model z-ai/glm-5 --adapter openrouter --log ./results/spl_benchmark-v2.2.log --output ./results/spl_benchmark-v2.2.json

splflow benchmark papers-by-top-prize-winners-recently_v1.spl \
    --adapter openrouter \
    --models "openrouter/auto" \
    --log ./results/spl_benchmark-auto.log \
    --output ./results/spl_benchmark-auto.json