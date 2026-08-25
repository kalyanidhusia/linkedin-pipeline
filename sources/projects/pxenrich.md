# pxEnrich series

- ORIGIN | ProteomeXchange 2026 made me ask whether FAIR and public proteomics data are actually biologically reusable. Published anchor: 64,330 submitted datasets; 47% submitted in the previous three years.

- METADATA GAP | Preliminary scan of 962 human breast-cancer PRIDE datasets: molecular subtype was recoverable from free text in 32.4%, but structurally exposed in only 0.3%. Message: the metadata often exists, but machines cannot reliably see it.

- FIRST BENCHMARK | 18-dataset proof of concept. Regex precision 0.78, recall 0.70, correct abstention 0.88. Initial LLM precision 0.71, recall 0.50, correct abstention 0.75. Do not frame as universal model performance.

- ERBETA TRAP | PXD000499 discussed ERβ/ESR2. An off-the-shelf LLM inferred clinical ER-positive disease with confidence 1.0. Biological lesson: ERβ/ESR2 is not equivalent to clinical ERα/ESR1 receptor status.

- MIXED COHORTS | PXD000029 contains multiple breast-cancer subtypes. PXD000246 contains cell lines pooled according to ER/HER2 status. Correct dataset-level annotation is mixed, not a single subtype.

- DESIGN PIVOT | pxEnrich changed from text → LLM → metadata into source evidence → AI assertion → biological rules → proteome check → expert adjudication → evidence-qualified metadata.

- PROTEOME CHECK | PXD000260 is explicitly TNBC. ERBB2 and PGR marker percentiles were low and proteomically concordant with the annotation. Say proteome-concordant, never clinical receptor diagnosis.

- NRP SMOKE V1 | Same five challenge datasets, same prompt, same schema and rules across gpt-oss, qwen3, gemma and kimi. Structured-output completion varied substantially. Do not frame as a model leaderboard; inference configuration and token budget were major factors.

- REPRODUCIBILITY | Every LLM call records model, actual returned model, raw output, parsed JSON, schema status, latency, tokens, hashes, prompt version, Git commit, SDK version and retries.

- PYTHON VS NEXTFLOW | Python holds the scientific logic: retrieve, extract, normalize, validate, score and proteome-check. Nextflow provides parallelism, resume, provenance and scale.

- EVIDENCE GRAPH | Knowledge-graph edges should not automatically be truth. Each biological assertion should carry source evidence, extraction method, model/version, confidence, proteome status and expert disposition.

- FINAL QUESTION | The real success metric is not how many fields an LLM fills. It is whether previously isolated public datasets become biologically stratifiable and usable together.
