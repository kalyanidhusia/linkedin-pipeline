# Tips — undergrad / early-grad bioinformatics gotchas

One tip per bullet. The LLM will pick one for a Type 2 post.

- Always check your column dtypes after a merge — pandas silently coerces
- Set a random seed in EVERY notebook, even exploratory ones
- Don't normalize before splitting train/test — you'll leak info
- Read the README before pip-installing a tool from a 2018 paper
- Version-pin your conda environments or your future self will weep
- Use git for analysis code from day one, not "after I clean it up"
- A 20GB BAM file does NOT mean you have 20GB of usable signal
- log-transform proteomics intensities before differential analysis, almost always
- Multiple testing correction matters more than your model choice
- Name your variables for biology, not for the algorithm — `protein_intensity_log2` not `X_train`
- Profile before you parallelize — most pipelines are I/O-bound, not CPU-bound
- Check the orientation of your matrix BEFORE you run PCA (samples x features, always)
- When merging gene/protein IDs across databases, expect 30% loss and plan for it
- Keep raw data read-only; never modify in place
- An ML model that's 99% accurate on imbalanced data is usually 99% useless
