## Q: Our diabetes research lab needs to measure mitochondrial function in patient PBMCs. Which Agilent instrument fits and which trials have used it?

**Route** (gpt-5.4-mini, 1.2s): clinical: The request is entirely about Agilent lab instrumentation and related clinical/research studies in diabetes, which falls within the Clinical Agent scope only. (confidence 0.98)

### Clinical Agent (27.4s)
*Sub-question:* For a diabetes research lab measuring mitochondrial function in patient PBMCs, which Agilent instrument fits best, and which clinical trials or patient studies have used that instrument for this kind of PBMC mitochondrial-function work?

Best fit: an Agilent Seahorse XF Analyzer—most specifically an XF Pro/XFe96-class system if the lab needs 96-well throughput for patient PBMC assays. It is designed for label-free, real-time measurement of cellular respiration, glycolysis and ATP production, and multiple diabetes/diabetes-adjacent clinical studies explicitly measured PBMC OCR/ECAR or mitochondrial respiration using Seahorse technology. Treat this as a research-use metabolic phenotyping platform, not a diagnostic IVD test, unless your local regulatory documentation says otherwise.

**Findings**
- (✅ confirmed) Agilent Seahorse XF analyzers measure cellular respiration, glycolysis and ATP production in a label-free format, matching PBMC mitochondrial-function assays that quantify oxygen consumption and glycolytic activity. [S8]
- (✅ confirmed) For patient PBMC mitochondrial-function work, Seahorse XF/XFe96 is the best match among the Agilent instruments retrieved; NanoZoomer is for whole-slide imaging and Artisan Link Pro is for special stains, not live-cell metabolic flux. [S7, S8, S9]
- (✅ confirmed) NCT04293224 measured change in OCR and ECAR in PBMCs using a Seahorse XF Analyzer, described as measuring glycolysis and oxidative phosphorylation simultaneously in the same cells. [S16]
- (✅ confirmed) NCT03078101 measured OCR and ECAR in PBMCs using a Seahorse Flux Analyzer in a diabetes/kidney-disease study context. [S17]
- (✅ confirmed) NCT05970601 measured mitochondrial respiration capacity in isolated PBMCs via Seahorse technology at baseline, 4 hours and 24 hours after salt intake in a study including diabetes. [S14, S23]
- (✅ confirmed) NCT03854656 measured respiratory and glycolytic capacities of isolated PBMCs using the Seahorse method in overweight individuals at high risk of type 2 diabetes. [S15]
- (✅ confirmed) NCT03441919, an innate-immune-system study in type 1 diabetes, measured intracellular metabolism by Seahorse respirometer using a mitochondrial stress test/OCR within 1 day after inclusion. [S13]
- (✅ confirmed) NCT04193566 measured peripheral blood monocyte mitochondrial function using a Seahorse X96 analyzer in a phase 4 type 1 diabetes study of acute SGLT2 inhibition. [S18, S21]

**Recommendations**
- **[high] Select an Agilent Seahorse XF platform, preferably XF Pro/XFe96-class if you expect moderate-to-high PBMC sample throughput and need OCR/ECAR-based mitochondrial stress testing.**: The target measurement—live-cell PBMC mitochondrial respiration and glycolysis—aligns directly with Seahorse XF capabilities and with diabetes-related patient studies using Seahorse XF/X96/Flux analyzers. [S8, S16, S17, S18]
- **[high] Design the PBMC assay around OCR plus ECAR endpoints, with mitochondrial stress-test parameters such as basal respiration, maximal respiration/spare capacity, and glycolytic response if scientifically justified.**: Clinical trial records show OCR/ECAR and mitochondrial respiration capacity are the common Seahorse endpoints used in PBMC or monocyte studies. [S14, S15, S16, S17]
- **[high] Plan the workflow as research-use metabolic phenotyping rather than a clinical diagnostic test.**: The retrieved Seahorse catalog entry supports metabolic analysis, while no IVD diagnostic clearance for PBMC diabetes diagnosis was identified in the retrieved Seahorse source; NanoZoomer was the retrieved IVD product, but it is for slide scanning, not PBMC flux assays. [S8, S9]
- **[medium] Benchmark your protocol against the PBMC/monocyte trials NCT04293224, NCT03078101, NCT05970601, NCT03854656 and NCT04193566.**: These records demonstrate real patient-study use of Seahorse technology for PBMC/monocyte mitochondrial function or OCR/ECAR measurements in diabetes or metabolic-risk contexts. [S14, S15, S16, S17, S18, S21, S23]
- **[medium] If sample volume is limited or PBMC yield is variable, run a pilot to optimize PBMC isolation, cryopreservation vs fresh-cell testing, cell number per well, assay media, and replicate count before locking the clinical-study protocol.**: Patient PBMC assays are sensitive to pre-analytical variability; the Long COVID PBMC study explicitly cryopreserved PBMCs before Seahorse analysis, showing this is a design variable to decide and validate. [S10]

**Next steps**
- Confirm whether the lab will run fresh PBMCs, cryopreserved PBMCs, or both.
- Estimate weekly patient sample volume and number of assay conditions to choose between lower-throughput vs 96-well Seahorse configurations.
- Define the primary endpoints: OCR only, OCR plus ECAR, ATP production, substrate oxidation, or full mitochondrial stress-test profile.
- Decide whether the study is exploratory research, CLIA/LDT-supporting research, or intended for regulated diagnostic claims.
- Request Agilent application support for PBMC Seahorse assay setup and consumables planning.
- Use the cited NCT protocols as precedent when drafting outcome measures and assay timepoints.

**Information needed from you**
- PBMC source and handling: fresh draw, cryopreserved biobank samples, or multi-site shipping.
- Expected sample throughput and number of assay conditions per participant.
- Whether monocytes, total PBMCs, or sorted immune-cell subsets are the target population.
- Required regulatory setting: RUO research only, CLIA-validated laboratory-developed workflow, or diagnostic submission intent.
- Budget range for instrument, service contract, assay kits and consumables.
- Available staff experience with cell culture, PBMC isolation and extracellular flux analysis.

**Risks and assumptions**
- Assumption: the lab’s primary need is live-cell metabolic flux measurement, not imaging, staining or molecular quantitation.
- Risk: PBMC isolation, viability, activation state and cryopreservation can introduce variability that may obscure disease-group effects.
- Risk: Seahorse results are research endpoints unless validated and regulated appropriately; they should not be used alone for patient diagnosis.
- Assumption: XF Pro/XFe96-class throughput is preferable for patient cohort work, but final model choice depends on throughput and budget.

**How to measure impact (KPIs)**
- Assay success rate: Percentage of PBMC samples producing analyzable OCR/ECAR traces that pass predefined QC criteria.
- Technical reproducibility: Coefficient of variation across technical replicates for basal OCR, maximal OCR and ECAR.
- Sample throughput: Number of patient PBMC samples completed per instrument run and per week.
- Pre-analytical stability: Compare fresh vs cryopreserved PBMC OCR/ECAR values and QC failure rates in a pilot set.
- Clinical-study endpoint completeness: Percentage of enrolled participants with complete Seahorse mitochondrial-function endpoint data.

**Confidence:** high: The instrument capability is directly supported by the Agilent product result, and multiple ClinicalTrials.gov records explicitly document Seahorse use for PBMC/monocyte OCR, ECAR or mitochondrial respiration in diabetes or metabolic-risk studies.

*Grounding:* 25 sources, 8 confirmed / 0 hypotheses, citation coverage 100%, grounding score 0.62
*Tools used:* `search_knowledge`, `recommend_products`, `instrument_usage`, `search_trials`

**Sources cited**
- **S7**: Catalog: Artisan Link Pro <https://www.agilent.com/en/product/special-stains>
- **S8**: Catalog: Seahorse XF analyzers (XF Pro) <https://www.agilent.com/about/newsroom/presrel/2023/07mar-ca23010.html>
- **S9**: Catalog: NanoZoomer Slide Scanner System IVD <https://www.agilent.com/en/product/digital-pathology/digital-pathology-scanners/nanozoomer-slide-scanner-system-4370282>
- **S10**: NCT07134673: Mitochondrial Function in Peripheral Blood Mononuclear Cells, Muscle, and Skin of Long COVID Patients <https://clinicaltrials.gov/study/NCT07134673>
- **S13**: NCT03441919: Activation Innate Immune System in Type 1 Diabetes <https://clinicaltrials.gov/study/NCT03441919>
- **S14**: NCT05970601: Effects of Sodium Chloride or Its Substitute Salt Potassium Chloride on Vascular Function <https://clinicaltrials.gov/study/NCT05970601>
- **S15**: NCT03854656: Effect of Time-restricted Eating on Behaviour and Metabolism in Overweight Individuals at High Risk of Type 2 Diabetes <https://clinicaltrials.gov/study/NCT03854656>
- **S16**: NCT04293224: Metabolic and Bio-behavioral Effects of Following Recommendations in the Dietary Guidelines for Americans <https://clinicaltrials.gov/study/NCT04293224>
- **S17**: NCT03078101: EMPRA (EMPagliflozin and RAs in Kidney Disease) <https://clinicaltrials.gov/study/NCT03078101>
- **S18**: NCT04193566: Acute Effects of SGLT2 Inhibition on Renal Oxygenation and Autonomic Function in Type 1 Diabetes <https://clinicaltrials.gov/study/NCT04193566>
- **S21**: NCT04193566: Acute Effects of SGLT2 Inhibition on Renal Oxygenation and Autonomic Function in Type 1 Diabetes <https://clinicaltrials.gov/study/NCT04193566>
- **S23**: NCT05970601: Effects of Sodium Chloride or Its Substitute Salt Potassium Chloride on Vascular Function <https://clinicaltrials.gov/study/NCT05970601>

*Total time: 28.6s*