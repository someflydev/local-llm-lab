# Common Failure Mode: Context Overflow

If too much text is packed into a prompt, useful evidence may be truncated or diluted. Large context windows also increase memory pressure and can slow responses.

This lab keeps chunk sizes and `num_ctx` conservative by default to avoid context overflow and swap-heavy runs.

