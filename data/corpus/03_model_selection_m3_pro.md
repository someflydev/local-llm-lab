# Model Selection for M3 Pro 18GB

On an M3 Pro MacBook Pro with 18GB unified memory, 8B-class models are usually the practical sweet spot for local chat and small RAG tasks.

Start with conservative context settings like `num_ctx=4096`. If the machine stays responsive and memory pressure is acceptable, test `8192` carefully.

