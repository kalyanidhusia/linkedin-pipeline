# ProteoVar series

- ORIGIN | Started as a frustration with how proteomics pipelines handle sample-specific variation. Standard workflows search mass spectra against a reference proteome FASTA, which systematically misses variant peptides unique to the sample being studied — exactly the peptides that matter most for cancer and personalized medicine.

- CORE IDEA | Build a sample-specific variant FASTA database from the sample's own matched RNA-Seq and genomic data, then search the mass spec against that. Variant peptides stop being invisible. Nextflow DSL2 holds the pipeline together: parallelism, resume, provenance, scale.

- WHY NEXTFLOW | Python holds the scientific logic (variant calling, FASTA construction, mass-spec search configuration). Nextflow provides the engineering: parallel execution across samples, automatic resume on partial failure, full provenance tracking, portability from laptop to HPC to cloud. Same split as pxEnrich — language-level logic in Python, workflow-level logic in Nextflow.

- INVENTION DISCLOSURE | ProteoVar (also known as Somatika in the invention-disclosure filing) was filed with UAMS BioVentures. The disclosure protects the specific architecture — matched-sample variant FASTA construction integrated with proteomics search — not the individual tools, which are all open source and standard in the field.

- INPUTS | Matched RNA-Seq (FASTQ or BAM) and mass spec (RAW or mzML) per sample. Optional: matched WGS/WES for germline-vs-somatic variant separation. Reference proteome FASTA and genome FASTA. Standard Nextflow samplesheet with per-sample row entries.

- VARIANT CALLING | RNA-Seq variants called with a standard caller (not the research contribution). The novelty is downstream: how called variants translate into FASTA entries that are compatible with mass-spec search engines and don't blow up the search space.

- SEARCH-SPACE DISCIPLINE | A naive sample-specific FASTA quickly becomes too large to search without astronomical false discovery rates. ProteoVar enforces discipline on which variants earn a FASTA entry — expression evidence from the RNA-Seq, minimum variant allele frequency, exclusion of synonymous changes. Trade-offs documented, not hidden.

- REPRODUCIBILITY | Every run produces a provenance bundle: Nextflow trace, exact tool versions (via containers), input hashes, output hashes, Git commit of the pipeline, parameter configuration. Rerunning a sample on a different machine produces byte-identical results. This is table stakes for anything that touches clinical data.

- WHAT IT IS NOT | ProteoVar is not a variant caller, not a mass-spec search engine, not a database. It is the pipeline that connects them for a specific scientific use case. Posts that claim otherwise overstate the contribution.

- FAILURE MODES | Low RNA-Seq coverage of a variant-containing region produces a FASTA entry with no supporting peptides in the mass spec — not evidence of absence, just evidence of insufficient coverage. The pipeline must distinguish "no variant peptide found" from "variant peptide not searchable." This is where most sample-specific proteogenomics gets it wrong.

- NF-TEST PATTERN | Pipeline testing uses a small synthetic dataset with known variants and known peptides, run as part of CI. Catches regressions where a change to one process silently drops variant entries from the output FASTA. The synthetic dataset is also useful for teaching students what the pipeline actually does.

- NEXT STEP | Expand from proteogenomics-for-cancer into proteogenomics-for-populations: run the same pipeline across cohort-level data to build population-aware variant FASTA references. The invention disclosure covers the single-sample case; the population case is an open extension that needs its own biological validation before it's claimed.
