# Used Materials

This register contains every external material that has actually informed a project task or output. Include materials even when they are CC0/public domain or their license does not require attribution. Do not treat a source as approved until its specific license explicitly permits commercial use of the resulting work and its conditions are compatible with the intended distribution.

## Recorded materials

When adding an entry, record:

- Material title and the specific part used (chapter, figure, page range, dataset/version, clip, or section).
- Direct source URL and, when applicable, author/publisher.
- License name and version, plus a direct link to the license terms.
- Evidence that the license permits commercial use of the resulting work and the intended derivative/distribution.
- Conditions to follow, including attribution text, share-alike, notices, or other requirements; write `none` only when verified.
- Date the source and its license were checked.
- Related project outputs or source identifiers (pose, segment, motion, rig, scene, render, or code).

Use this table for entries:

| Material / specific part | Source URL | License / version and terms URL | Commercial derivative permission and conditions | Checked on | Related outputs |
|---|---|---|---|---|---|
| OpenAI Codex configuration source, `AgentsToml` and agent-role configuration fields | https://github.com/openai/codex/blob/main/codex-rs/config/src/config_toml.rs | Apache-2.0; https://github.com/openai/codex/blob/main/LICENSE (repository license confirmation: https://github.com/openai/codex/blob/main/docs/license.md) | Apache-2.0 permits commercial use and derivatives; no source code copied, configuration behavior referenced. Preserve license/notice requirements if code is copied in future. | 2026-10-20 | `.codex/config.toml`; project agent configuration guidance |
| `hands-on-anatomy-2024`: Jacqueline Phillips and Michael O'Hara, *Hands-on Anatomy*, North Broad Press, copyright 2024; authored text on anatomical actions, skeletal landmarks, and ROM assessment in chapters 1–9. Used to define articulation coverage and anatomical terminology; no illustrations or photographs copied or measured. | https://temple.manifoldapp.org/projects/hands-on-anatomy (chapter links); copyright page: https://temple.manifoldapp.org/read/hands-on-anatomy-c6538f97-bc62-44ae-96ff-0f1f97d6c977/section/b0089167-fc78-425f-ab26-bbdf9dd0f7d3 | CC BY 4.0, except individually marked material; https://creativecommons.org/licenses/by/4.0/ | Publisher copyright page explicitly licenses all material unless otherwise noted; CC BY 4.0 permits commercial sharing and adaptation. Credit Phillips and O'Hara, title, publisher, year, source, and license; identify adaptation into skeletal requirements, retain notices, and imply no endorsement. Permission-only figures, including Alsup/Fox figures, and other separately licensed images are excluded; the book is not blanket clearance for them. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/specs/anatomical-skeleton/spec.md`; `openspec/changes/anatomical-human-skeleton/specs/joint-mobility/spec.md`; no generated asset yet |
| `wang-2024-segment-lengths`: Shiou-An Wang, Ming-Hua Lu, Ai-Teng Lee, Chao-Yu Chen, and Li-Wen Lee, *Performance of Microsoft Azure Kinect DK as a tool for estimating human body segment lengths*, Scientific Reports 14, 15811 (2024), DOI 10.1038/s41598-024-66798-0; mechanical-axis definitions on PDF p. 3 and adult DXA rows of Table 1 on p. 4. Used only for four limb-length ratios and their measurement definitions. | https://www.nature.com/articles/s41598-024-66798-0.pdf | CC BY 4.0; article permission statement on PDF p. 8; https://creativecommons.org/licenses/by/4.0/ | Article explicitly permits sharing and adaptation under CC BY 4.0, whose terms include commercial use. Credit Wang et al., title, journal/year/DOI and license; identify the symmetric adaptation: means of adult L/R ratios yield 0.1605, 0.1365, 0.2340, and 0.2155. Preserve notices; imply no endorsement. No participant images, restricted underlying data, SDK, or third-party asset is used. Ratios are not claimed as universal or whole-bone mesh lengths. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/specs/anatomical-skeleton/spec.md`, adult reference limb proportions; no generated asset yet |
| `faisal-2019-joint-monitoring`: Abu Ilius Faisal, Sumit Majumder, Tapas Mondal, David Cowan, Sasan Naseh, and M. Jamal Deen, *Monitoring Methods of Human Body Joints: State-of-the-Art and Research Challenges*, Sensors 19(11), 2629 (2019), DOI 10.3390/s19112629; Table 3 mean magnitudes for females and males aged 20–44. Used as an identified published reference table, not as evidence for individual maxima or coupled articulation. | https://pmc.ncbi.nlm.nih.gov/articles/PMC6603670/ (published article and copyright/license statement); https://doi.org/10.3390/s19112629 | CC BY 4.0; https://creativecommons.org/licenses/by/4.0/ | Article copyright statement explicitly licenses the work under CC BY 4.0; Table 3 has source citations and no separate restrictive permission notice. CC BY 4.0 permits commercial sharing and adaptation. Credit Faisal et al., title, journal/year/DOI, table, and license; identify the selected age-group columns and the relabeling of forearm and total-shoulder actions. Retain the table's cited-source context and do not imply endorsement. No figure or underlying participant dataset is used. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/specs/joint-mobility/spec.md`, reference mobility observations; no generated asset yet |

## Anatomical skeleton design references

### Implementation licensing references

| Material / specific part | Source URL | License / version and terms URL | Commercial derivative permission and conditions | Checked on | Related outputs |
|---|---|---|---|---|---|
| `apache-2-license-text`: Apache Software Foundation, Apache License 2.0, full standard license text | https://www.apache.org/licenses/LICENSE-2.0.txt | Apache-2.0; https://www.apache.org/licenses/LICENSE-2.0 | Standard license text reproduced unmodified to license project tooling; sections 2–4 permit commercial reproduction, derivatives and distribution subject to retaining license/notices and identifying modifications to licensed code. | 2026-10-20 | `LICENSE-CODE`; tooling license declaration |
| `cc-by-4-license-deed`: Creative Commons, Attribution 4.0 International deed; commercial adaptation and attribution conditions | https://creativecommons.org/licenses/by/4.0/ | CC BY 4.0 site notice; https://creativecommons.org/licenses/by/4.0/ ; controlling license: https://creativecommons.org/licenses/by/4.0/legalcode.en | Deed explicitly confirms commercial sharing/adaptation with attribution, license links, and identification of changes. Consulted for the project license notice; no illustrations or web layout copied. | 2026-10-20 | `LICENSE-DATA`; `THIRD-PARTY-NOTICES.md` |

The `three-vrm-humanoid-vocabulary` MIT notice was rechecked on 2026-10-20
against its recorded source and retained in `THIRD-PARTY-NOTICES.md` for the
planned mapping. The anatomical references below remain the cleared design
inputs; their incorporation into canonical data must retain their identifiers
and the same portion restrictions and attribution conditions.

The existing `hands-on-anatomy-2024`, `wang-2024-segment-lengths`, and `faisal-2019-joint-monitoring` entries also inform `openspec/changes/anatomical-human-skeleton/design.md`, within the same cleared portions and conditions. The following additional materials informed that design. No third-party anatomical mesh, illustration, participant dataset, or motion clip has been incorporated. Numerical curves marked authored approximations in the design are not presented as measurements from these sources.

Implementation update (2026-10-20): the cleared authored text in
`hands-on-anatomy-2024` and the four symmetric ratios/mechanical definitions in
`wang-2024-segment-lengths` now also inform the provisional canonical source
`rig/profiles/adult-reference-v1.yaml`. Expanded coordinates, procedural shape
parameters, neutral/rest frames and attachment records remain identified as
authored approximations except for those four ratios. The source records
retain the material identifiers and locators; `THIRD-PARTY-NOTICES.md` retains
attribution and license conditions. This updates the earlier planning-stage
"no generated asset yet" status for those two entries; there is still no
accepted Blender asset or review pack. No additional portions or third-party
figures were used. The corrected walking construction and its regression
tests are authored mathematical verification choices using the same approved
dossier, not newly imported gait data.

The same cleared portions of `hands-on-anatomy-2024`,
`faisal-2019-joint-monitoring`, `moromizato-2016-rom`,
`beczkowska-2022-spine-rom`, `bang-2025-shoulder-rhythm`,
`yu-2019-patellar-kinematics`, `brockett-chapman-2016-ankle`,
`tovaruela-2025-hallux`, and `parallel-manipulator-2024-wrist` now inform
`rig/mobility/adult-reference-v1.yaml`. Each source record identifies its
material and locator. Numeric operating bounds and reduced coupling curves
are identified as authored adaptations; the eleven Faisal observation rows
retain the selected cohort and both sex-specific means unchanged. Reference
means are not relabeled individual maxima. No extra source portions, figures,
participant data, or motion recordings were used.

The `three-vrm-humanoid-vocabulary` constants were rechecked on 2026-10-20
for `rig/humanoid-map.yaml`: 15 required identifiers, seven selected optional
proxies, and 33 explicit optional omissions. Only semantic identifiers were
adapted; no upstream runtime code or uncleared specification was imported.
The MIT copyright and permission notice remains in `THIRD-PARTY-NOTICES.md`.

| Material / specific part | Source URL | License / version and terms URL | Commercial derivative permission and conditions | Checked on | Related outputs |
|---|---|---|---|---|---|
| `moromizato-2016-rom`: Keiichi Moromizato, Ryosuke Kimura, Hitoshi Fukase, Kyoko Yamaguchi, Hajime Ishida, *Whole-body patterns of the range of joint motion in young adults: masculine type and feminine type*, Journal of Physiological Anthropology 35, 23 (2016), DOI 10.1186/s40101-016-0112-8; Table 1 and measurement context for passive wrist, hip, shoulder, and trunk mobility. | https://link.springer.com/article/10.1186/s40101-016-0112-8 | CC BY 4.0, publisher Rights and permissions; https://creativecommons.org/licenses/by/4.0/ | Publisher grants unrestricted reuse under CC BY 4.0, allowing commercial use and adaptation. Credit all authors, title, journal/year/DOI and license; identify reduced authored operating envelopes and retain notices. Passive cohort observations do not validate an individual body, active exercise limit, or coupled curve. No participant-level supplementary data used. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/design.md`, operating-envelope rationale |
| `beczkowska-2022-spine-rom`: Sylwia Agata Bęczkowska, Iwona Grabarek, Zuzanna Zysk, Katarzyna Gosek-Ferenc, *Physical Activity and Ecological Means of Transport—Functional Assessment Methodology*, IJERPH 19(15), 9211 (2022), DOI 10.3390/ijerph19159211; Table 3, regional spinal ranges. | https://www.mdpi.com/1660-4601/19/15/9211/xml | CC BY 4.0, article copyright notice; https://creativecommons.org/licenses/by/4.0/ | Explicit author/article CC BY 4.0 notice permits commercial reuse and adaptation. Attribute authors, title, DOI/year, table, license, and its cited-source context. Identify reduced operating ranges and uniform per-vertebra distribution as project choices, not measured distributions. No equipment images or study trajectories used. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/design.md`, regional spinal bounds and evidence context |
| `bang-2025-shoulder-rhythm`: Seok Jin Bang, Jung-Soo Lee, Dong Hyeon Song, Seung Yeob Ryu, Kwang Gi Kim, *Mechanical Analysis for Active Movement of Upper Limb Rehabilitation Robots to Alleviate Shoulder Pain in Patients with Stroke Hemiplegia and Frozen Shoulder*, Sensors 25(21), 6644 (2025), DOI 10.3390/s25216644; section 2.1 text about approximately 2:1 humeral/scapular coordination in abduction and participation of the clavicle. | https://doi.org/10.3390/s25216644 ; published article PDF inspected at https://pdfs.semanticscholar.org/f88f/121f8eb655d26c50d46e54262dea1ff73ffe.pdf | CC BY 4.0, published PDF p. 1; https://creativecommons.org/licenses/by/4.0/ | Explicit published article CC BY 4.0 notice permits commercial reuse and adaptation. Attribute authors, title, journal/year/DOI, section, and license. Design extrapolation to forward elevation and its extra clavicular/scapular channels are authored approximations; no claim that this paper measured those curves. No figure or robot model copied. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/design.md`, shoulder coordination rationale |
| `yu-2019-patellar-kinematics`: Zhenguo Yu, Jie Yao, Xingliang Wang, Xing Xin, Ke Zhang, Hong Cai, Yubo Fan, Bin Yang, *Research Methods and Progress of Patellofemoral Joint Kinematics: A Review*, Journal of Healthcare Engineering 2019, 9159267, DOI 10.1155/2019/9159267; sections 3.2–3.6 and 4.3 for patellar flexion trends, coordinate dependence, and initial tibial rotation. | https://doi.org/10.1155/2019/9159267 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC6451817/ | Creative Commons Attribution License, explicitly named by the publisher; version is not printed in the retrieved permission notice and is not inferred. Permission terms are in the publisher article's Details/copyright notice at https://doi.org/10.1155/2019/9159267 | Publisher explicitly grants unrestricted use, distribution, and reproduction with citation under CC Attribution; that grant has no non-commercial or no-derivatives condition. Commercial adaptation under the project's attribution license retains the original attribution and permission notice. Credit authors/title/DOI/year and identify the chosen 0.65 trend factor; translations, tilt samples, and tibial trajectory magnitudes are authored, not digitized research data. No figure or supplementary file used. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/design.md`, patellar/tibial coupling rationale |
| `brockett-chapman-2016-ankle`: Claire L. Brockett and Graham J. Chapman, *Biomechanics of the ankle*, Orthopaedics and Trauma 30(3), 232–238 (2016), DOI 10.1016/j.mporth.2016.04.015; motion-axis and ROM text on printed pp. 234–235. | https://doi.org/10.1016/j.mporth.2016.04.015 ; published PDF: https://eprints.whiterose.ac.uk/id/eprint/100704/9/1-s2.0-S1877132716300483-main.pdf | CC BY 4.0, published PDF copyright footer; https://creativecommons.org/licenses/by/4.0/ | Article explicitly licenses commercial reuse/adaptation under CC BY 4.0. Credit authors, title, DOI/year, pages, and license. Identify fixed-pivot/sagittal-axis and reduced-envelope approximations; reported oblique subtalar directions inform the design axis. No separately credited figure copied or traced. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/design.md`, ankle/hindfoot axis and rocker rationale |
| `tovaruela-2025-hallux`: Natalia Tovaruela-Carrión et al., *Exploring the Association of Hallux Limitus with Baropodometric Gait Pattern Changes*, Bioengineering 12(3), 316 (2025), DOI 10.3390/bioengineering12030316; introduction on first MTP dorsiflexion and terminal-stance function. | https://www.mdpi.com/2306-5354/12/3/316/xml | CC BY 4.0, article copyright notice; https://creativecommons.org/licenses/by/4.0/ | Explicit article CC BY 4.0 notice permits commercial sharing/adaptation. Attribute authors/title/DOI/year/section/license and indicate adaptation. This informs the role of forefoot articulation, not a measured five-toe shared-hinge model; 45-degree operating extension and the rocker are authored reductions. No participant measurements or device illustrations used. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/design.md`, forefoot operating envelope and approximation context |
| `parallel-manipulator-2024-wrist`: Tony Punnoose Valayil and Tanio K. Tanev, *A 3UPS/S Spherical Parallel Manipulator Designed for Robot-Assisted Hand Rehabilitation after Stroke*, Applied Sciences 14(11), 4457 (2024), MDPI, DOI 10.3390/app14114457; Table 2 wrist reference ranges, specifically radial and ulnar deviation. | https://www.mdpi.com/2076-3417/14/11/4457 | CC BY 4.0, article copyright notice; https://creativecommons.org/licenses/by/4.0/ | The retrieved published article and Table 2 state CC BY 4.0 and contain no separate restrictive table notice. Commercial reuse/adaptation is permitted with credit to the article's authors/title/DOI/year/table, source and license, retained notices, and identification of the reduced 15/25-degree design bounds. No manipulator geometry, code, or motion copied. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/design.md`, wrist deviation bounds |
| `three-vrm-humanoid-vocabulary`: pixiv Inc., three-vrm, `VRMHumanBoneName.ts` and `VRMRequiredHumanBoneName.ts`, accessed on `dev`; selected bone identifiers and required subset referring to VRMC_vrm 1.0. | https://raw.githubusercontent.com/pixiv/three-vrm/dev/packages/three-vrm-core/src/humanoid/VRMHumanBoneName.ts ; https://raw.githubusercontent.com/pixiv/three-vrm/dev/packages/three-vrm-core/src/humanoid/VRMRequiredHumanBoneName.ts | MIT; https://raw.githubusercontent.com/pixiv/three-vrm/dev/LICENSE | MIT expressly allows use, modification, distribution, sublicensing, and sale. Credit Copyright (c) 2019–2026 pixiv Inc.; preserve the MIT copyright and permission notice with any substantial copied code/vocabulary table. Only the semantic-name mapping is authored here; no runtime code is imported. The uncleared separate vrm-specification repository is not used as an implementation source. | 2026-10-20 | `openspec/changes/anatomical-human-skeleton/design.md`, humanoid semantic mapping and required-name coverage |

Action-direction audit (2026-10-21): `hands-on-anatomy-2024` authored chapter 1 anatomical-position/external/internal-rotation/pronation definitions (section `66f189d6-1135-49dc-801a-92b249a5deb5`) and chapter 3 brachioradialis/ROM neutral thumb-up description (section `e3dbe01c-3a95-4320-ac7c-52a650c86925`) informed correction of the hip, forearm, and tibial action-axis directions and absolute geometric tests. The recorded publisher copyright page was rechecked on 2026-10-21: CC BY 4.0 permits commercial derivatives with the same attribution and adaptation conditions above. Only authored text was used, no separately licensed figures. Related outputs: approved design/spec refinements, `rig/mobility/adult-reference-v1.yaml`, `tools/articulation.py`, `tools/measurements.py`, diagnostic derived trajectories, and direction checks/tests. Full chapter URLs use the recorded read base plus these section identifiers.

### Thoracic visual-rejection investigation (2026-10-21)

| Material / specific part | Source URL | License / version and terms URL | Commercial derivative permission and conditions | Checked on | Related outputs |
|---|---|---|---|---|---|
| `openstax-1e-thoracic-cage`: OpenStax, *Anatomy and Physiology*, first edition, section 7.4, text under Sternum, Parts of a Typical Rib, and Rib Classifications, retained by LibreTexts with a 2020 modification date. Used for the proposed anatomical relationships of the manubrium, ribs, posterior rib angle, and costal cartilages; no image copied, traced, or measured. | https://med.libretexts.org/Bookshelves/Anatomy_and_Physiology/Anatomy_and_Physiology_1e_(OpenStax)/Unit_2:_Support_and_Movement/07:_Axial_Skeleton/7.04:_The_Thoracic_Cage | CC BY 4.0, explicitly stated in this retained first-edition page's Contributors and Attributions and license metadata; https://creativecommons.org/licenses/by/4.0/ | This specific first-edition republication explicitly grants CC BY 4.0; the license permits commercial sharing and adaptation with attribution, a license link, retained notices, and identification of changes. Credit OpenStax, book/section title, first edition, and the LibreTexts republication. This clearance does not extend to currently published OpenStax editions or unrelated images. Proposed coordinates remain authored approximations, not measurements from the text. | 2026-10-21 | `openspec/changes/anatomical-human-skeleton/proposal.md`, `design.md`, both capability delta specs, and tasks for the confirmed thoracic planning revision; canonical geometry and new renders remain pending |

The already cleared authored text of `hands-on-anatomy-2024`, chapter 5,
section `8ff57319-f921-4deb-b896-585474a87763`, was rechecked for sternum,
clavicle, rib, and vertebral landmark relationships during this investigation.
The publisher copyright grant was rechecked on 2026-10-21. The same portion
restrictions apply: permission-only figures 5.1–5.5 were not used.

The user's comparison screenshot identifies a visual rejection of the existing
model. The watermarked third-party illustration on its right is not a cleared
anatomical source: no project coordinates, contours, or dimensions are derived
from it. No permission to reproduce it in repository outputs is assumed.

Thoracic implementation update (2026-10-21): the cleared O/H text portions above
now inform `rig/profiles/adult-reference-v1.yaml` and its structural/connection
verification. New numerical shapes and guide motion remain authored
approximations. `THIRD-PARTY-NOTICES.md` retains the OpenStax first-edition
attribution and CC BY 4.0 link. New prepared inputs/renders will record the
updated source hashes; the previous independent pack remains historical.

## Squat balance investigation (2026-10-21)

| Material and portion used | Source | License | Commercial/derivative clearance and conditions | Checked | Related outputs |
|---|---|---|---|---|---|
| `kasahara-2024-squat-com`: Satoshi Kasahara, Tomoya Ishida, Jiang Linjing, Ami Chiba, Mina Samukawa and Harukazu Tohyama, *Relationship among the COM Motion, the Lower Extremity and the Trunk during the Squat*, Journal of Human Kinetics 93, 29–39 (2024), DOI 10.5114/jhk/183066; abstract, discussion and conclusions about coordinated ankle/hip/knee motion and anteroposterior COM control. | https://doi.org/10.5114/jhk/183066 ; full published text: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11307177/fullTextXML | CC BY 4.0, explicit article permissions/license paragraph; https://creativecommons.org/licenses/by/4.0/ | Published XML explicitly permits commercial distribution, remixing and adaptation with credit. Copyright 2024 Academy of Physical Education in Katowice. Retain author/title/journal/DOI credit and license link; identify changes and do not imply endorsement. Qualitative interpretation only: no illustrations, participant trajectories, angle tables or segment-mass coefficients copied into the model. | 2026-10-21 | Investigation response to the human's squat-balance visual finding. No fixture, joint limit, implementation or acceptance criterion changed. |

The present squat's planted-foot and closed-chain checks do not measure a
whole-body center of mass or establish static/dynamic balance. The article
informs the qualitative investigation only; its experimental angles are not
adopted as this model's operating limits or exercise targets.

## Squat correction planning R3 (2026-10-21)

| Material and portion used | Source | License | Commercial/derivative clearance and conditions | Checked | Related outputs |
|---|---|---|---|---|---|
| `kudzia-2022-body-segments`: Pawel Kudzia, Erika Jackson and Genevieve Dumas, *Estimating body segment parameters from three-dimensional human body scans*, PLOS ONE 17(1), e0262296 (2022), DOI 10.1371/journal.pone.0262296; original Proposed columns of Tables 3 and 6: regional mean masses and proximal limb COM fractions. | https://doi.org/10.1371/journal.pone.0262296 ; published XML: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8730461/fullTextXML | CC BY 4.0, article copyright/permissions paragraph and linked license; https://creativecommons.org/licenses/by/4.0/ | Copyright 2022 Kudzia et al. Publisher notice explicitly permits unrestricted reuse with author/source credit; linked CC BY 4.0 permits commercial adaptation. Credit all three authors, title, journal/year, DOI and license; identify modifications and do not imply endorsement. Only original Proposed numerical columns used, excluding ECM, regression and cited literature Mean Value columns; no figures, participant scans, code, density tables or separately licensed repository data used. | 2026-10-21 | R3 squat numerical planning draft: equal-cohort coefficient blend, explicit normalization and three coefficient variants; limb fractions mapped to the authored skeleton, with head/trunk/pelvis/foot placements labeled approximations. The human approved the numerical R3 revision on 2026-10-21; now informs canonical mass records, squat diagnostics and independent balance/native measurements, tests and review overlays. |

The already cleared `brockett-chapman-2016-ankle` text and CC BY 4.0 footer
were rechecked on 2026-10-21. The printed p.235 ROM paragraph reports
10–20-degree dorsiflexion variability; it informs the proposed authored
20-degree operating ceiling, not a universal physiological maximum. No figure
is used. The existing Faisal reference observations remain unchanged.

`kasahara-2024-squat-com` continues to inform coordinated ankle/hip/knee
control qualitatively. The R3 point-mass check estimates static support
plausibility including unrendered tissues; neither the cohort blend nor
authored point placements represent one measured person, clinical validity,
or dynamic stability at animation playback tempos.
