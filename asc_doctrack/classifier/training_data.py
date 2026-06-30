"""
Enhanced Training Data for ASC DocTrack AI Classifier
------------------------------------------------------
Expanded from 19 → 120+ samples across 8 document categories.
Includes Filipino/Tagalog terms, ASC-specific terminology,
and varied phrasing to improve real-world accuracy.
"""

TRAINING_SAMPLES = [

    # ── MEMORANDUM (25 samples) ───────────────────────────────────────────
    ("memorandum all faculty report attendance",                                    "Memorandum"),
    ("office memorandum re academic calendar adjustments",                          "Memorandum"),
    ("circular no implementation new policy guidelines",                            "Memorandum"),
    ("memo all department heads submission requirements deadline",                  "Memorandum"),
    ("memorandum all teaching non-teaching personnel",                              "Memorandum"),
    ("office order reassignment duties responsibilities",                           "Memorandum"),
    ("memo re mandatory attendance flag ceremony",                                  "Memorandum"),
    ("circular reminder submission liquidation reports",                            "Memorandum"),
    ("memorandum suspension classes typhoon signal",                                "Memorandum"),
    ("office memorandum conduct comprehensive examination",                         "Memorandum"),
    ("memo all concerned revised schedule enrollment",                              "Memorandum"),
    ("circular implementation executive order",                                     "Memorandum"),
    ("memorandum designation officer in charge",                                    "Memorandum"),
    ("memo re attendance graduation ceremony commencement",                         "Memorandum"),
    ("office circular new guidelines wearing uniform",                              "Memorandum"),
    ("memorandum conduct inventory equipment supplies",                             "Memorandum"),
    ("memo reminder submission annual report",                                      "Memorandum"),
    ("circular prohibition use social media during office hours",                   "Memorandum"),
    ("memorandum activation emergency response team",                               "Memorandum"),
    ("memo schedule mid-year performance review",                                   "Memorandum"),
    ("office order creation special committee",                                     "Memorandum"),
    ("memorandum strict implementation attendance monitoring",                      "Memorandum"),
    ("circular updated health and safety protocols campus",                         "Memorandum"),
    ("memo deadline submission ipcr opcr forms",                                    "Memorandum"),
    ("memorandum required documents promotion",                                     "Memorandum"),

    # ── REQUEST LETTER (20 samples) ──────────────────────────────────────
    ("request letter approval construction building renovation",                    "Request Letter"),
    ("letter request financial assistance scholarship indigent",                    "Request Letter"),
    ("application scholarship grant tuition fee waiver",                            "Request Letter"),
    ("request approval travel authority official business",                         "Request Letter"),
    ("letter endorsement application graduate studies",                             "Request Letter"),
    ("request purchase equipment laboratory supplies",                              "Request Letter"),
    ("letter request extension deadline submission",                                "Request Letter"),
    ("application faculty development program training abroad",                     "Request Letter"),
    ("request use gymnasium gymnasium venue event",                                 "Request Letter"),
    ("letter appeal reconsideration failing grade",                                 "Request Letter"),
    ("request honorarium resource speaker seminar",                                 "Request Letter"),
    ("letter request release budget allocation project",                            "Request Letter"),
    ("application doctoral fellowship research grant",                              "Request Letter"),
    ("request endorsement job application recommendation",                          "Request Letter"),
    ("letter request authority conduct survey data gathering",                      "Request Letter"),
    ("request approval conduct off-campus activity field trip",                     "Request Letter"),
    ("letter request additional personnel teaching items",                          "Request Letter"),
    ("application promotion next salary grade",                                     "Request Letter"),
    ("request waiver fees indigent student financial hardship",                     "Request Letter"),
    ("letter request copy official transcript records",                             "Request Letter"),

    # ── REPORT (20 samples) ──────────────────────────────────────────────
    ("accomplishment report quarter activities completed",                          "Report"),
    ("narrative report seminar training completed outcomes",                        "Report"),
    ("monthly report office performance indicators",                                "Report"),
    ("annual report college programs academic year",                                "Report"),
    ("terminal report project implementation outputs",                              "Report"),
    ("progress report ongoing construction infrastructure",                         "Report"),
    ("financial report budget utilization expenses",                                "Report"),
    ("incident report accident injury campus premises",                             "Report"),
    ("inspection report equipment condition assessment",                            "Report"),
    ("inventory report supplies materials stock",                                   "Report"),
    ("monitoring report program implementation status",                             "Report"),
    ("evaluation report faculty performance teaching",                              "Report"),
    ("audit report findings recommendations compliance",                            "Report"),
    ("status report enrollment statistics data",                                    "Report"),
    ("weekly report activities task update",                                        "Report"),
    ("end of day report operations summary",                                        "Report"),
    ("post activity report outcomes learnings participants",                        "Report"),
    ("report card academic performance students grades",                            "Report"),
    ("liquidation report expenses reimbursement receipts",                          "Report"),
    ("completion report project deliverables milestones achieved",                 "Report"),

    # ── RESEARCH PROPOSAL (20 samples) ───────────────────────────────────
    ("research proposal qualitative study implementation program",                  "Research Proposal"),
    ("project proposal funding community extension service",                        "Research Proposal"),
    ("research study assessment effectiveness teaching strategy",                   "Research Proposal"),
    ("proposal investigation indigenous knowledge practices",                       "Research Proposal"),
    ("research proposal development mobile application learning",                   "Research Proposal"),
    ("study correlation academic performance socioeconomic status",                 "Research Proposal"),
    ("proposal action research classroom intervention struggling students",         "Research Proposal"),
    ("research proposal utilization technology instruction higher education",       "Research Proposal"),
    ("project proposal livelihood training program community",                      "Research Proposal"),
    ("research proposal mental health awareness college students",                  "Research Proposal"),
    ("feasibility study establishment research center campus",                      "Research Proposal"),
    ("proposal comparative study outcomes face-to-face online learning",           "Research Proposal"),
    ("research proposal analysis food security farming communities",                "Research Proposal"),
    ("project proposal environmental awareness campaign watershed",                 "Research Proposal"),
    ("research proposal profiling out-of-school youth municipality",               "Research Proposal"),
    ("study impact scholarship program academic performance beneficiaries",         "Research Proposal"),
    ("proposal development training module disaster preparedness",                  "Research Proposal"),
    ("research proposal level digital literacy faculty members",                    "Research Proposal"),
    ("study effectiveness extension program farmers livelihood",                    "Research Proposal"),
    ("proposal evaluation curriculum relevance industry needs graduates",           "Research Proposal"),

    # ── CERTIFICATE (15 samples) ─────────────────────────────────────────
    ("certificate completion training seminar workshop",                            "Certificate"),
    ("certification employment service record",                                     "Certificate"),
    ("certificate appearance court hearing",                                        "Certificate"),
    ("certification no pending case administrative",                                "Certificate"),
    ("certificate good moral character conduct",                                    "Certificate"),
    ("certificate participation conference symposium",                              "Certificate"),
    ("certification salary compensation benefits",                                  "Certificate"),
    ("certificate eligibility civil service examination",                           "Certificate"),
    ("certification leave credits balance",                                         "Certificate"),
    ("certificate enrollment currently enrolled student",                           "Certificate"),
    ("certification rating performance evaluation",                                 "Certificate"),
    ("certificate graduation completion degree program",                            "Certificate"),
    ("certification authenticity documents records",                                "Certificate"),
    ("certificate recognition award outstanding performance",                       "Certificate"),
    ("certification no money accountability clearance",                             "Certificate"),

    # ── PURCHASE REQUEST (15 samples) ────────────────────────────────────
    ("purchase request supplies equipment office",                                  "Purchase Request"),
    ("procurement request laboratory materials chemicals reagents",                 "Purchase Request"),
    ("purchase request janitorial cleaning supplies",                               "Purchase Request"),
    ("request procurement computer equipment peripherals",                         "Purchase Request"),
    ("purchase request office furniture chairs tables",                             "Purchase Request"),
    ("procurement athletic sports equipment gymnasium",                             "Purchase Request"),
    ("purchase request printer ink toner cartridge",                               "Purchase Request"),
    ("request procurement books library references",                                "Purchase Request"),
    ("purchase request repair maintenance vehicle",                                 "Purchase Request"),
    ("procurement request air conditioning unit installation",                      "Purchase Request"),
    ("purchase request food catering seminar participants",                         "Purchase Request"),
    ("request procurement tarpaulin streamer printing",                             "Purchase Request"),
    ("purchase request medical supplies first aid kit",                             "Purchase Request"),
    ("procurement request construction materials repair building",                  "Purchase Request"),
    ("purchase request tokens certificates souvenirs participants",                 "Purchase Request"),

    # ── TRAVEL ORDER (10 samples) ────────────────────────────────────────
    ("travel order official business conference manila",                            "Travel Order"),
    ("itinerary travel seminar training baguio city",                               "Travel Order"),
    ("travel authority attend regional meeting department education",               "Travel Order"),
    ("order travel conduct monitoring field visit beneficiaries",                   "Travel Order"),
    ("travel order data gathering research municipality province",                  "Travel Order"),
    ("authority travel attend national convention association",                     "Travel Order"),
    ("travel order representing institution awarding ceremony",                     "Travel Order"),
    ("itinerary official travel international conference abroad",                   "Travel Order"),
    ("travel order inspection site construction project",                           "Travel Order"),
    ("authority travel attend hearing commission higher education",                 "Travel Order"),

    # ── LEAVE FORM (15 samples) ──────────────────────────────────────────
    ("leave application vacation sick absence",                                     "Leave Form"),
    ("leave form maternity paternity parental",                                     "Leave Form"),
    ("application sick leave medical certificate illness",                          "Leave Form"),
    ("vacation leave application family event",                                     "Leave Form"),
    ("leave of absence special emergency personal",                                 "Leave Form"),
    ("forced leave offsetting mandatory rest day",                                  "Leave Form"),
    ("application rehabilitation leave injury accident",                            "Leave Form"),
    ("leave request study examination bar board review",                            "Leave Form"),
    ("terminal leave retirement application monetization",                          "Leave Form"),
    ("leave application bereavement death immediate family",                        "Leave Form"),
    ("half day leave permission early dismissal",                                   "Leave Form"),
    ("leave without pay absence unauthorized",                                      "Leave Form"),
    ("application solo parent leave welfare act",                                   "Leave Form"),
    ("leave application gynecological surgery medical procedure",                   "Leave Form"),
    ("commutation leave credits cash monetization",                                 "Leave Form"),

]

# ── Label set for reference ───────────────────────────────────────────────────
LABELS = sorted(set(label for _, label in TRAINING_SAMPLES))

if __name__ == '__main__':
    from collections import Counter
    counts = Counter(label for _, label in TRAINING_SAMPLES)
    print(f"\nTotal samples: {len(TRAINING_SAMPLES)}")
    print(f"Categories: {len(LABELS)}\n")
    for label, count in sorted(counts.items()):
        bar = '█' * count
        print(f"  {label:<22} {bar} ({count})")


# ── PATCH SAMPLES — fixing weak spots found in real-world testing ─────────────

PATCH_SAMPLES = [

    # Filipino / Tagalog terms (Sulat-Kahilingan, etc.)
    ("sulat kahilingan paggamit auditorium",                "Request Letter"),
    ("kahilingan tulong pinansyal estudyante",              "Request Letter"),
    ("liham kahilingan pagpayag pangkalahatang pulong",     "Request Letter"),
    ("sulat endorso aplikasyon kurso",                      "Request Letter"),
    ("kahilingan pagbabago iskedyul klase",                 "Request Letter"),

    # PR abbreviation and requisition forms
    ("pr procurement desktop computer units",               "Purchase Request"),
    ("requisition catering services event activity",        "Purchase Request"),
    ("pr no request item quantity unit cost",               "Purchase Request"),
    ("requisition form supplies materials needed",          "Purchase Request"),
    ("purchase order items specification quantity",         "Purchase Request"),

    # Trip ticket and travel variations
    ("trip ticket itinerary monitoring field visit",        "Travel Order"),
    ("trip ticket driver destination purpose",              "Travel Order"),
    ("travel itinerary barangay monitoring visit",          "Travel Order"),
    ("authority travel inspection site survey",             "Travel Order"),

    # Post-activity narrative and similar reports
    ("post activity narrative report outcomes learnings",   "Report"),
    ("lakbay aral narrative report outcomes",               "Report"),
    ("after activity report documentation participants",    "Report"),
    ("summary report findings observations",                "Report"),
    ("documentation report program activity conducted",     "Report"),
]

TRAINING_SAMPLES = TRAINING_SAMPLES + PATCH_SAMPLES
