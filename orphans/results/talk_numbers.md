# Numbers for the Mainz deck and script

Main: `results/tlhdig03_literature_C_filled` · comparison (with restorations): `results/tlhdig03_literature_A_filled`

| slide | number | value | source |
|---|---|---|---|
| bins | CTH 470 fragments of rituals: texts / median words | 1,920 / 10 | corpus_stats.json laroche_bins |
| bins | CTH 500 fragments of Kizzuwatna rituals: texts / median words | 479 / 16 | corpus_stats.json laroche_bins |
| bins | CTH 670 fragments of festivals: texts / median words | 3,506 / 9 | corpus_stats.json laroche_bins |
| bins | CTH 832 fragments of various content: texts / median words | 4,090 / 4 | corpus_stats.json laroche_bins |
| bins | CTH 390-469 rituals no study groups: texts / median words | 1,038 / 21 | corpus_stats.json laroche_bins |
| bins | EBo texts / median words | 1,151 / 4 | corpus_stats.json orphans |
| bins | EBo filed under 832 / 670 / 470 | 562 / 382 / 37 | corpus_stats.json orphans.ebo_filed_under |
| bins | CTH 470 + EBo manuscripts | 3,034 | corpus_stats.json orphans.orphans_total |
| theory | orphans with 5+ words | 2,023 | report.json corpus.orphans_used |
| frag44 | KBo 44.52 words that count | 50 | case_KBo_44_52.json legible_words |
| formula | idf of tai / sign an | 2.0 / 1.1 | case_KBo_44_52.json features.idf |
| formula | similarity nearest / runner-up | 0.42 (Syro-Mesopotamian (Hurrian)) / 0.31 (Kizzuwatna rituals) | case_KBo_44_52.json similarity |
| formula | lead / threshold | 0.113 / 0.026 | case_KBo_44_52.json margin; report.json E2_abstention.margin |
| formula | threshold 90% interval | [0.025, 0.028] | report.json E2_abstention.margin_90ci |
| formula | features (non-zero) / dimensions | 162 / 24,067 | case_KBo_44_52.json |
| formula | top decision features | tai +0.075, AZU +0.070, §AZU +0.064, §LÚ·AZU +0.061, §da·a·i +0.057, A-NA +0.050 | case_KBo_44_52.json decision_features |
| traditions / test1 | Hattian cult layer: reference MSS / held-out accuracy | 443 / 94% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Kizzuwatna–Lower Land (Hurrian): reference MSS / held-out accuracy | 297 / 77% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Kizzuwatna rituals: reference MSS / held-out accuracy | 211 / 88% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Mixed (Hurrian, Syrian, Luwian): reference MSS / held-out accuracy | 190 / 67% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Ḫuwaššanna festivals: reference MSS / held-out accuracy | 179 / 92% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Syro-Mesopotamian (Hurrian): reference MSS / held-out accuracy | 149 / 68% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Luwian rituals (Puriyanni, Kuwattalla): reference MSS / held-out accuracy | 57 / 81% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Luwian festivals (Ištanuwa, Lallupiya): reference MSS / held-out accuracy | 47 / 79% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Arzawa / western rituals: reference MSS / held-out accuracy | 32 / 88% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| traditions / test1 | Palaic festivals: reference MSS / held-out accuracy | 30 / 73% | test1_loo_placements.csv; report.json E1_historical.both.recall_by_class |
| test1 | accuracy / manuscripts | 83.0% / 1,634 | report.json E1_historical.both |
| test1 | largest-tradition baseline / shuffled labels | 27% / 16% | report.json E1_historical.both |
| test1 | with restorations: accuracy / manuscripts | 84.1% / 1,787 | tlhdig03_literature_A_filled/report.json E1_historical.both |
| test2 | compositions recovered | 72 / 94 | E10_report.json E10a |
| test2 | by tradition | Arzawa / western rituals 3/6; Hattian cult layer 25/25; Kizzuwatna rituals 24/26; Kizzuwatna–Lower Land (Hurrian) 3/8; Luwian festivals (Ištanuwa, Lallupiya) 2/4; Luwian rituals (Puriyanni, Kuwattalla) 6/6; Mixed (Hurrian, Syrian, Luwian) 3/4; Palaic festivals 0/5; Syro-Mesopotamian (Hurrian) 1/5; Ḫuwaššanna festivals 5/5 | E10_report.json E10a.by_tradition |
| test2 | CTH 404 | cth=404; tradition=Kizzuwatna rituals; texts=30; texts_correct=18; composition_pred=Kizzuwatna rituals; composition_correct=True; gap=0.0662 | E10a_leave_composition_out.csv |
| test2 | CTH 752 | cth=752; tradition=Palaic festivals; texts=2; texts_correct=0; composition_pred=Hattian cult layer; composition_correct=False; gap=0.0152 | E10a_leave_composition_out.csv |
| test2 | CTH 701 | cth=701; tradition=Syro-Mesopotamia (Hurrian); texts=108; texts_correct=0; composition_pred=Kizzuwatna rituals; composition_correct=False; gap=0.0144 | E10a_leave_composition_out.csv |
| size | KUB 29.4+ from word 200, 3 words | Arzawa / western rituals, lead 0.0015, placed False, right False | size_example_KUB_29.4.json |
| size | KUB 29.4+ from word 200, 10 words | Kizzuwatna rituals, lead 0.0057, placed False, right True | size_example_KUB_29.4.json |
| size | KUB 29.4+ from word 200, 40 words | Kizzuwatna rituals, lead 0.0408, placed True, right True | size_example_KUB_29.4.json |
| size | all traditions: right at 3 / 10 / 40 words | 45% / 59% / 76% | E2_coverage_curve.csv (both) |
| size | share of held-out windows placed / precision | 50% / 80% | report.json E2_abstention |
| scribes | vocabulary alone / logograms / foreign words | 67% / 69% / 79% (on 684 MSS) | E7_report.json E7a_layers |
| scribes | spelling habits (seven rates) / baseline | 38% / 27% | E7_report.json E7a_layers.orthographic_indices |
| scribes | words with 2+ spellings: kept / collapsed | 273 words: 50% / 54% | E7_report.json corpus, E7a_layers.spelling/collapsed |
| scribes | memai written plene | Arzawa / western rituals 2.6%; Hattian cult layer 12.5%; Kizzuwatna rituals 1.1%; Kizzuwatna–Lower Land (Hurrian) 17.9%; Luwian festivals (Ištanuwa, Lallupiya) 0.0%; Luwian rituals (Puriyanni, Kuwattalla) 3.0%; Mixed (Hurrian, Syrian, Luwian) 0.0%; Palaic festivals 0.0%; Syro-Mesopotamian (Hurrian) 0.5%; Ḫuwaššanna festivals 0.0% | E7_spelling_contrasts.csv |
| scribes | distinctive ZA.GÌN (Kizzuwatna rituals) z | 6.7 | E7_distinctive_features.csv |
| scribes | distinctive BE-EL (Ḫuwaššanna festivals) z | 13.8 | E7_distinctive_features.csv |
| scribes | distinctive GIŠ.INANNA (Hattian cult layer) z | 9.6 | E7_distinctive_features.csv |
| scribes | distinctive AZU (Syro-Mesopotamian (Hurrian)) z | 13.8 | E7_distinctive_features.csv |
| scribal | profile z Arzawa / western rituals | logogram_share -0.02, akkadogram_share -0.59, complement_rate -0.01, determinative_rate -0.21, plene_rate -0.41, cvc_share +0.28, u_acute_share -0.19 | E7_report.json E7b_index_profile_z |
| scribal | profile z Hattian cult layer | logogram_share -0.46, akkadogram_share -0.36, complement_rate +0.32, determinative_rate -0.05, plene_rate +0.50, cvc_share -0.21, u_acute_share +0.31 | E7_report.json E7b_index_profile_z |
| scribal | profile z Kizzuwatna rituals | logogram_share +0.09, akkadogram_share -0.22, complement_rate -0.12, determinative_rate -0.41, plene_rate -0.31, cvc_share +0.07, u_acute_share +0.08 | E7_report.json E7b_index_profile_z |
| scribal | profile z Kizzuwatna–Lower Land (Hurrian) | logogram_share +0.26, akkadogram_share +0.48, complement_rate -0.19, determinative_rate +0.04, plene_rate -0.28, cvc_share +0.04, u_acute_share -0.33 | E7_report.json E7b_index_profile_z |
| scribal | profile z Luwian festivals (Ištanuwa, Lallupiya) | logogram_share -0.12, akkadogram_share +0.36, complement_rate -0.28, determinative_rate +0.16, plene_rate -0.17, cvc_share +0.06, u_acute_share +0.26 | E7_report.json E7b_index_profile_z |
| scribal | profile z Luwian rituals (Puriyanni, Kuwattalla) | logogram_share -0.26, akkadogram_share -0.80, complement_rate +0.15, determinative_rate -0.71, plene_rate -0.14, cvc_share -0.20, u_acute_share +0.32 | E7_report.json E7b_index_profile_z |
| scribal | profile z Mixed (Hurrian, Syrian, Luwian) | logogram_share +0.29, akkadogram_share -0.01, complement_rate +0.02, determinative_rate +0.33, plene_rate -0.17, cvc_share +0.36, u_acute_share -0.08 | E7_report.json E7b_index_profile_z |
| scribal | profile z Palaic festivals | logogram_share -0.74, akkadogram_share -0.35, complement_rate +0.85, determinative_rate +0.08, plene_rate +0.04, cvc_share +0.13, u_acute_share -0.00 | E7_report.json E7b_index_profile_z |
| scribal | profile z Syro-Mesopotamian (Hurrian) | logogram_share +0.17, akkadogram_share +0.21, complement_rate -0.33, determinative_rate -0.00, plene_rate +0.22, cvc_share -0.15, u_acute_share -0.29 | E7_report.json E7b_index_profile_z |
| scribal | profile z Ḫuwaššanna festivals | logogram_share +0.39, akkadogram_share +0.53, complement_rate -0.21, determinative_rate +0.39, plene_rate -0.26, cvc_share +0.08, u_acute_share -0.12 | E7_report.json E7b_index_profile_z |
| tug44 | similarity / lead | 0.419 vs 0.306, lead 0.113, 4.4 x threshold | case_KBo_44_52.json |
| tug44 | word shares of the lead | tai +22%, AZU +20%, A-NA +12%, ḪAL +10%, BANŠUR +9%, natkan +8%, AD.KID +8%, SÍSKURma +6% | case_KBo_44_52.json word_shares |
| decide44 | common features' share of the decision | 28% | case_KBo_44_52.json decision_share_common_features |
| decide44 | corpus: common features share of similarity / decision | 47% / 12% | E11_report.json E11b |
| barcode | distinctive matches per tradition | Syro-Mesopotamian (Hurrian) 28; Mixed (Hurrian, Syrian, Luwian) 12; Kizzuwatna–Lower Land (Hurrian) 11; Luwian rituals (Puriyanni, Kuwattalla) 10; Kizzuwatna rituals 9; Ḫuwaššanna festivals 7; Arzawa / western rituals 5; Hattian cult layer 5; Palaic festivals 5; Luwian festivals (Ištanuwa, Lallupiya) 2 | barcode_KBo_44_52.json |
| nearest44 | 10 nearest manuscripts | KBo 59.165 (CTH 701, Syro-Mesopotamian (Hurrian), 0.34); KBo 60.215 (CTH 701, Syro-Mesopotamian (Hurrian), 0.33); ABoT 2.230 (CTH 701, Syro-Mesopotamian (Hurrian), 0.33); KUB 44.44 (CTH 500, CTH 500 Kizzuwatna fragments, 0.31); KBo 39.167 (CTH 706, Mixed (Hurrian, Syrian, Luwian), 0.31); KBo 40.35+ (CTH 701, Syro-Mesopotamian (Hurrian), 0.30); KBo 13.167 (CTH 500, CTH 500 Kizzuwatna fragments, 0.29); KBo 40.314+ (CTH 701, Syro-Mesopotamian (Hurrian), 0.29); KBo 33.110+ (CTH 701, Syro-Mesopotamian (Hurrian), 0.28); KBo 38.284 (CTH 500, CTH 500 Kizzuwatna fragments, 0.28) | case_KBo_44_52.json nearest_manuscripts |
| nearest44 | CTH 701 among the 10 nearest | 6 | case_KBo_44_52.json nearest_manuscripts |
| caution | KBo 57.54 without restorations | unplaced; nearest Syro-Mesopotamian (Hurrian) 0.220, runner-up Kizzuwatna rituals 0.203; lead 0.0169; 11 words; top features A-NA, §A·NA, našta, §NA | case_KBo_57_54.json |
| caution | KBo 57.54 with restorations | Luwian rituals (Puriyanni, Kuwattalla); nearest Luwian rituals (Puriyanni, Kuwattalla) 0.298, runner-up Kizzuwatna rituals 0.239; lead 0.0586; 13 words; top features §MUNUS·ŠU, §MUNUS·ŠU·GI, §ŠU·GI, §GI | case_KBo_57_54.json |
| caution | KBo 41.22 without restorations | Luwian rituals (Puriyanni, Kuwattalla); nearest Luwian rituals (Puriyanni, Kuwattalla) 0.274, runner-up Kizzuwatna rituals 0.245; lead 0.0289; 32 words; top features §GI, §MUNUS·ŠU, §MUNUS·ŠU·GI, §ŠU·GI | case_KBo_41_22.json |
| caution | KBo 41.22 with restorations | Luwian rituals (Puriyanni, Kuwattalla); nearest Luwian rituals (Puriyanni, Kuwattalla) 0.263, runner-up Kizzuwatna rituals 0.241; lead 0.0216; 33 words; top features §GI, §MUNUS·ŠU, §MUNUS·ŠU·GI, §EME | case_KBo_41_22.json |
| caution | threshold with restorations | 0.017 | tlhdig03_literature_A_filled/report.json E2_abstention.margin |
| caution / takeaways | orphans keeping their nearest tradition without restorations | 87% of 2,023 | E5_orphan_placement.csv, both runs |
| caution | placed only with restorations / of them Luwian rituals | 404 / 14 | E5_orphan_placement.csv, both runs |
| caution | of these, with a restored sign in MUNUS ŠU.GI (the Old Woman) | 14 of 14 | data/tokens_marks_filled.csv (status R in a ŠU.GI word) |
| test1 / fills | Luwian rituals reference MSS before / after filling | 10 / 57 | results/tlhdig03_literature_C (no fills) vs main, test1_loo_placements.csv |
| ebo / tie | EBo 133 words; without restorations | 19 words; Palaic festivals 0.2529 vs Ḫuwaššanna festivals 0.2463, lead 0.0065 | case_EBo_133.json |
| tie | EBo 133 with restorations | Ḫuwaššanna festivals 0.2781 vs Palaic festivals 0.2339, lead 0.0442 | tlhdig03_literature_A_filled/case/case_EBo_133.json |
| tie | pulling to nearest / against | 1-ŠU, §pár, §ke, §ir, §ši / takarmun, NINDA, §mu·un, §kar·mu·un | case_EBo_133.json |
| bread | takarmun: other MSS / reference MSS / Ḫuwaššanna / Palaic / CTH 670 | 143 / 62 / 54 / 2 / 37 | spread_takarmun.json |
| join | pool / passing all three checks | 19,197 / KBo 44.140 (rank 10, CTH 669, 37 words, SSSS....S.); DBH 46_2.139 (rank 16, CTH 750, 86 words, SSSS...S..) | joins_EBo_133.json |
| suggest | EBo 133 nearest manuscripts | KBo 21.51 (Mixed (Hurrian, Syrian, Luwian)); KBo 34.228 (Ḫuwaššanna festivals); DBH 46_2.139 (Palaic festivals); IBoT 4.273 (Kizzuwatna–Lower Land (Hurrian)); KBo 34.221 (Ḫuwaššanna festivals); KBo 19.157 (Palaic festivals); KBo 29.129 (Ḫuwaššanna festivals); KBo 29.113 (Ḫuwaššanna festivals) | case_EBo_133.json nearest_manuscripts |
| takeaways | orphans placed / scored | 457 / 2,023 | report.json E5_orphans, corpus |
| takeaways | with restorations: placed / scored | 842 / 2,036 | tlhdig03_literature_A_filled/report.json |
| takeaways | orphans placed by tradition | Kizzuwatna rituals 208; Hattian cult layer 73; Kizzuwatna–Lower Land (Hurrian) 46; Syro-Mesopotamian (Hurrian) 46; Luwian rituals (Puriyanni, Kuwattalla) 39; Mixed (Hurrian, Syrian, Luwian) 20; Arzawa / western rituals 11; Ḫuwaššanna festivals 11; Luwian festivals (Ištanuwa, Lallupiya) 3 | report.json E5_orphans.by_tradition |
| clay / fills | fill step | words without a lemma, legible: 135398 of 1277944 | filled from TLHdig: 94021 | filled from eDiAna: 1109; still without a lemma: 40268 | fill.log |
| clay | words that count | variant C: 958323 of 1002347 analysed words count; same-text support 47090 | variant.log |
