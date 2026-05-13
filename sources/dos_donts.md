# Do / Don't pairs for Type 3 visual cards

Format: `DON'T: <pithy 1-liner> | DO: <pithy 1-liner>`

The LLM will pick one and shorten if needed. Keep entries short — they need to fit on a card.

- DON'T: Hardcode file paths in your scripts | DO: Use a config file or environment variables
- DON'T: Normalize before train/test split | DO: Fit normalizer on train only, then transform
- DON'T: Trust a 99% accurate model on imbalanced data | DO: Check precision and recall per class
- DON'T: Skip log-transformation for proteomics intensities | DO: log2-transform before differential analysis
- DON'T: Use `print()` for debugging long pipelines | DO: Use Python's `logging` module from day one
- DON'T: Re-run the whole notebook on every change | DO: Cache expensive steps with `joblib` or `dvc`
- DON'T: Merge gene IDs without checking version | DO: Pin Ensembl / UniProt versions in your config
- DON'T: Run PCA without standardizing first | DO: `StandardScaler().fit_transform(X)` first
- DON'T: Tune hyperparameters on the test set | DO: Use a separate validation split or cross-validation
- DON'T: Trust default thresholds in DE tools | DO: Justify every cutoff in writing
- DON'T: Start ML before you can plot the raw data | DO: Spend Day 1 on histograms and PCA
- DON'T: Pip-install into your base environment | DO: One conda env per project, always
