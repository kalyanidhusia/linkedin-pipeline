# cardio-bagchi series

NOTE: As of 2026-10-22, this project is mostly planned, not shipped. Every
milestone below should be read as "intended" or "design choice," not "already
done." Do not let posts claim results that have not been produced. When the
first real data comes in, add new tagged milestones and update the dated line
at the bottom of the file.

- ORIGIN | pxEnrich showed that AI-assisted metadata enrichment with evidence qualification works on breast-cancer proteomics. Dr. Bagchi (heart research PI) asked whether the same approach could unlock cardiovascular datasets sitting in public repositories without usable sample metadata. Same shape, different biology.

- WHY CARDIO | Cardiovascular proteomics and transcriptomics datasets have the same metadata problem as breast cancer — sample provenance, disease state, tissue origin, and intervention context are often buried in free-text descriptions. If pxEnrich's architecture generalizes, cardio should be the next proof.

- PLANNED DESIGN | Reuse the pxEnrich pattern: source evidence → AI assertion → biological rules → omics check → expert adjudication → evidence-qualified metadata. Replace the ER/HER2/PGR breast-cancer rules with cardio-specific marker rules (cardiac troponins, natriuretic peptides, tissue-specific expression patterns). Do not promise this works until it is tested.

- SCOPING QUESTIONS | Which public repositories carry the cardio datasets worth enriching — PRIDE, ProteomeCentral, GEO, cBioPortal cardio sections? Which disease states are the first targets — ischemic cardiomyopathy, heart failure with preserved vs. reduced ejection fraction, post-MI remodeling? These are open and must be settled with Dr. Bagchi before the first dataset is pulled.

- ANCHOR DATASET | Pick one cardio dataset the way PXD000260 anchored the TNBC proof in pxEnrich. The anchor dataset should have unambiguous, expert-confirmed clinical annotation so proteome-check and expert adjudication can be calibrated against ground truth before scaling.

- WHAT NOT TO CLAIM | Nothing has been benchmarked yet. Do not reuse pxEnrich's regex vs. LLM numbers (0.78 / 0.71 precision) as if they apply here — those are breast-cancer-specific. Any post about cardio-bagchi should either describe the approach as planned or wait for real cardio numbers.

- WHAT ERβ TAUGHT US | pxEnrich hit the ERβ/ESR2 trap: a fluent, confident LLM assertion that was biologically wrong. Cardio will have its own version — likely around troponin isoform specificity, or confusing cardiomyocyte markers with vascular endothelial markers. Design the biological-rules layer with that failure mode already in mind.

- PROTEOME CHECK | Same principle as pxEnrich — never report a clinical receptor diagnosis from proteomic data. Say "proteome-concordant with annotation" or "proteome-discordant, flagged for expert review." Cardio needs its own version of the ER/HER2/PGR marker-percentile logic.

- REPRODUCIBILITY | Carry over the full pxEnrich logging: model, actual returned model, raw output, parsed JSON, schema status, latency, tokens, hashes, prompt version, Git commit, SDK version, retries. This is non-negotiable from day one, not something to add later.

- STUDENT HANDOFF POTENTIAL | If cardio-bagchi reaches the state pxEnrich did, it could serve the same role as a student-extensible AI product with an MCP server exposing cardio-evidence tools. Flag for AR INBRE course design — one more domain for CS students to extend without needing cardio expertise themselves.

- OPEN QUESTION | Does the biology of cardiac tissue (lower cellular heterogeneity than tumor tissue, different sample preparation standards, different protein abundance ranges) make the same architecture easier or harder than cancer? Worth being honest about this in the first real post — it is a research question, not a settled design.

Last updated: 2026-10-22. All milestones above are planning or design intent.
