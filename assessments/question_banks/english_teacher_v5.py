"""High-selectivity English teacher-screening upgrade for bank version 5.

The legacy bank remains the source of calibration items and audio assets.  This
module returns fresh dictionaries, replaces weak items with C1/C2-oriented
language analysis, and makes every selection quota explicit in ``english.py``.
"""

from copy import deepcopy


def item(section, prompt, correct, wrong1, wrong2, wrong3, *, difficulty, subskill,
         explanation, seconds=105, question_type="single_choice"):
    wrong = (wrong1, wrong2, wrong3)
    return {
        "section": section,
        "prompt": prompt,
        "choices": (correct,) + wrong,
        "difficulty": difficulty,
        "subskill": subskill,
        "question_type": question_type,
        "teacher_v5_curated": True,
        "suggested_seconds": seconds,
        "explanation": explanation,
        "choice_explanations_fa": (explanation,) + tuple(
            f"‘{choice}’ misses a grammatical, semantic, pragmatic, or discourse constraint in this context."
            for choice in wrong
        ),
        "choice_explanations_en": (explanation,) + tuple(
            f"‘{choice}’ misses a grammatical, semantic, pragmatic, or discourse constraint in this context."
            for choice in wrong
        ),
    }


GRAMMAR = [
    item("grammar", "Choose the sentence in which the modal perfect expresses a criticism of a past action rather than an uncertain deduction.",
         "You should have checked the figures before publishing them.", "She may have left before the announcement.",
         "They must have misunderstood the instructions.", "He could have taken the earlier train, for all we know.",
         difficulty=3, subskill="modal-perfect-meaning", explanation="‘Should have checked’ evaluates an unperformed past obligation and therefore conveys criticism; the other modal perfects express degrees of possibility or inference."),
    item("grammar", "Which version preserves the intended narrow scope: only the recommendation—not the supporting evidence—was challenged?",
         "It was only the recommendation that the panel challenged, not the evidence supporting it.",
         "Only the panel challenged the recommendation and the supporting evidence.",
         "The panel only challenged the recommendation, and not supporting evidence.",
         "It was the panel that challenged only, the recommendation not the evidence.",
         difficulty=3, subskill="focus-and-scope", explanation="The cleft places ‘only’ directly over ‘the recommendation’ and the contrast explicitly excludes the supporting evidence."),
    item("grammar", "A learner writes: ‘Had I knew about the delay, I would call you.’ Which correction accurately expresses an unreal past condition and its past result?",
         "Had I known about the delay, I would have called you.", "Had I knew about the delay, I would have called you.",
         "If I would know about the delay, I called you.", "Knowing about the delay, I would call you yesterday.",
         difficulty=2, subskill="learner-error-diagnosis", explanation="An inverted third conditional uses ‘Had + subject + past participle’ and a modal perfect in the result: ‘would have called’."),
    item("grammar", "Which sentence uses agreement most defensibly in edited formal English?",
         "More than one explanation has been proposed, but none has yet proved adequate.",
         "More than one explanations have been proposed, but none have yet proved adequate.",
         "More than one explanation have been proposed, but none has yet prove adequate.",
         "More than one explanation were proposed, but none are yet proving adequate.",
         difficulty=4, subskill="complex-agreement", explanation="‘More than one + singular noun’ conventionally takes a singular verb, and singular ‘none has’ is defensible when the sense is ‘not one’."),
    item("grammar", "Which continuation makes the counterfactual time relationship unambiguous? ‘If the safeguards had been implemented last year, ...’",
         "the system would be considerably more resilient now.", "the system will have been considerably more resilient now.",
         "the system had been considerably more resilient tomorrow.", "the system would have being considerably resilient now.",
         difficulty=4, subskill="mixed-counterfactuals", explanation="A past unreal condition can have a present hypothetical result, expressed by ‘would be ... now’."),
    item("grammar", "Which sentence correctly reports a belief that was current at the earlier reporting time but is now known to be false?",
         "The investigators believed that the leak originated inside the network.",
         "The investigators believed that the leak has originated inside the network.",
         "The investigators had believed that the leak originates inside the network yesterday.",
         "The investigators believed the leak would have originated now inside the network.",
         difficulty=4, subskill="reported-time-reference", explanation="Backshift to ‘originated’ locates the supposed origin relative to the past belief without implying that the belief remains valid."),
    item("grammar", "Which sentence is acceptable only if ‘any’ is interpreted as a free-choice item rather than a negative-polarity item?",
         "Any qualified reviewer can identify the inconsistency.", "I doubt that any reviewer noticed the inconsistency.",
         "Hardly any reviewer noticed the inconsistency.", "The report was submitted without any supporting appendix.",
         difficulty=5, subskill="polarity-and-quantification", explanation="In the affirmative generic sentence, ‘any’ means ‘whichever qualified reviewer’; the other instances are licensed by negative or downward-entailing contexts."),
    item("grammar", "Which sentence makes the manager—not the assistant—the understood subject of ‘leaving early’?",
         "The manager, rather than the assistant, admitted leaving early.",
         "The manager discussed the assistant leaving early.", "The manager objected to the assistant's leaving early.",
         "The manager heard that the assistant was leaving early.",
         difficulty=5, subskill="control-and-reference", explanation="With ‘admit + gerund’, the gerund’s understood subject is normally the matrix subject, while the parenthetical does not change that reference."),
    item("grammar", "Which sentence exhibits negative inversion without changing the proposition’s temporal meaning?",
         "At no point did the witness claim to have seen the driver.", "At no point the witness did claim to see the driver.",
         "At no point had the witness claimed seeing the driver tomorrow.", "The witness at no point claimed did have seen the driver.",
         difficulty=5, subskill="negative-inversion", explanation="A fronted negative adjunct requires auxiliary–subject inversion; ‘did ... claim to have seen’ preserves the past claim and prior seeing relation."),
    item("grammar", "A student changes ‘I regret telling her’ to ‘I regret to tell her’ and says the meaning is unchanged. Which analysis is accurate?",
         "The first regrets a completed act; the second conventionally introduces regrettable news being delivered now.",
         "Both forms refer only to a future act.", "The infinitive always describes a completed memory.",
         "The gerund makes ‘regret’ an impersonal reporting verb.",
         difficulty=5, subskill="complement-meaning", explanation="The gerund complement looks back at an action, whereas ‘regret to inform/tell’ is a formal performative used while giving bad news."),
]


VOCABULARY = [
    item("vocabulary", "The reviewer was not ___; she had no personal stake in the outcome and evaluated both proposals impartially.",
         "disinterested", "uninterested", "apathetic", "indifferent to accuracy", difficulty=2,
         subskill="near-synonym-discrimination", explanation="In careful usage, ‘disinterested’ means impartial or free from self-interest; ‘uninterested’ means lacking interest."),
    item("vocabulary", "The apology was so ___ that several employees suspected it was intended to flatter rather than acknowledge harm.",
         "fulsome", "terse", "equivocal", "perfunctory", difficulty=5, subskill="evaluative-nuance",
         explanation="‘Fulsome’ can describe praise or apology that is excessively flattering or insincere, matching the suspicion in the second clause."),
    item("vocabulary", "The difference is ___ rather than stylistic: one formulation imposes a duty while the other merely recommends action.",
         "substantive", "cosmetic", "incidental", "ornamental", difficulty=3, subskill="argumentative-precision",
         explanation="A ‘substantive’ difference affects the content or practical effect of a rule, as the contrast between obligation and recommendation does here."),
    item("vocabulary", "Although the objection sounded plausible, it rested on a ___ analogy between statistical noise and deliberate falsification.",
         "specious", "cogent", "salient", "judicious", difficulty=5, subskill="argument-evaluation",
         explanation="A ‘specious’ analogy appears convincing but is actually misleading or unsound."),
    item("vocabulary", "The committee treated the point as ___ because the disputed policy had already been withdrawn.",
         "moot", "immutable", "tacit", "incumbent", difficulty=4, subskill="legal-academic-register",
         explanation="A question is ‘moot’ when changed circumstances have deprived it of practical significance."),
    item("vocabulary", "The new evidence does not refute the theory, but it does ___ the confidence with which its strongest version can be asserted.",
         "attenuate", "exacerbate", "vindicate", "foreclose", difficulty=4, subskill="degree-and-stance",
         explanation="‘Attenuate’ means reduce the force or intensity of something, here the warranted confidence in a strong claim."),
    item("vocabulary", "Her response was deliberately ___: it acknowledged the concern without committing the organisation to a remedy.",
         "noncommittal", "incontrovertible", "forthcoming", "categorical", difficulty=3, subskill="pragmatic-stance",
         explanation="A noncommittal response avoids expressing a definite position or promise, exactly matching the described strategy."),
    item("vocabulary", "The author’s apparently modest qualifier is ___; without it, the claim would be demonstrably false.",
         "load-bearing", "ornamental", "interchangeable", "gratuitous", difficulty=4, subskill="metaphorical-academic-usage",
         explanation="‘Load-bearing’ is used metaphorically for an element essential to an argument’s validity rather than a decorative qualification."),
]


READING = [
    item("reading", "Read the passage. A school reported that students using its new vocabulary app improved twice as much as non-users. App use, however, was voluntary; users also attended optional workshops more often and had higher baseline scores. The report controls for baseline score but not workshop attendance. Which conclusion is best supported?",
         "The app may be beneficial, but unmeasured differences in engagement still weaken a causal claim.",
         "The app alone caused exactly twice as much improvement.", "Baseline adjustment eliminates every source of selection bias.",
         "Workshop attendance cannot influence vocabulary learning.", difficulty=3, subskill="confounding-and-causality", seconds=150,
         explanation="Controlling for baseline ability removes one difference, but voluntary uptake and unequal workshop attendance leave engagement as a plausible confounder."),
    item("reading", "Read the passage. The policy’s defenders describe the fall in reported incidents as proof of success. Yet the reporting portal was unavailable for six weeks, and anonymous submissions—previously one third of reports—were discontinued. The author does not claim that incidents increased. What is the author’s main objection?",
         "The observed decline cannot be interpreted confidently without accounting for changes in how incidents could be reported.",
         "The policy certainly increased the true number of incidents.", "Anonymous reporting is always more accurate than named reporting.",
         "A six-week outage proves that every remaining report was false.", difficulty=4, subskill="measurement-validity", seconds=150,
         explanation="The author challenges the measurement process, not the policy directly: reduced reporting access can lower recorded incidents without lowering actual incidents."),
    item("reading", "Read the passage. ‘The model is admirably transparent: every variable and weight can be inspected. Transparency, though, should not be mistaken for neutrality. The choice of what to measure—and what to leave unmeasured—embeds a view of what counts as success.’ Which statement best captures the author’s position?",
         "Inspectability helps scrutiny but does not remove value judgments from model design.",
         "Transparent models contain no subjective choices.", "Opaque models are necessarily more neutral.",
         "A model becomes neutral when all its weights are published.", difficulty=4, subskill="qualified-author-position", seconds=145,
         explanation="The praise for inspectability is explicitly qualified: feature selection still encodes normative assumptions about success."),
    item("reading", "Read the passage. A historian notes that the absence of complaints in official archives has often been read as evidence of consent. She counters that the same archives record penalties for petitioning and exclude most oral testimony. She therefore treats silence as ambiguous rather than affirmative. What methodological principle guides her reasoning?",
         "Evidence of absence must be interpreted in light of whether the record-making system allowed dissent to appear.",
         "Official archives should always be rejected as fabricated.", "Oral testimony is automatically more reliable than written evidence.",
         "A lack of documents proves that no historical conclusion is possible.", difficulty=4, subskill="source-criticism", seconds=155,
         explanation="The historian evaluates archival silence against the mechanisms that suppressed or excluded dissent, so silence cannot straightforwardly indicate consent."),
    item("reading", "Read the passage. The trial found no statistically significant difference between the two treatments. The confidence interval, however, includes both a modest benefit and a modest harm. The authors conclude that the treatments are equivalent. Which criticism is strongest?",
         "Failure to detect a difference is not evidence of equivalence unless the study was designed and powered to test an equivalence margin.",
         "Any confidence interval containing zero proves both treatments are harmful.", "Statistical significance is unnecessary in every comparison.",
         "The treatments are equivalent whenever their sample means differ.", difficulty=5, subskill="statistical-argument", seconds=165,
         explanation="A non-significant superiority test may reflect imprecision; equivalence requires a pre-specified margin and sufficiently narrow interval."),
    item("reading", "Read the passage. ‘To call the reform unprecedented is rhetorically useful but historically careless. Earlier schemes pursued the same objective through different institutions. What is new is not the ambition but the administrative machinery—and perhaps the confidence placed in it.’ What does ‘perhaps’ primarily do?",
         "It marks the final claim about confidence as more tentative than the preceding claim about machinery.",
         "It casts doubt on whether any earlier schemes existed.", "It signals that the author fully endorses the reform.",
         "It makes every proposition in the passage equally uncertain.", difficulty=5, subskill="stance-and-hedging", seconds=150,
         explanation="The hedge attaches locally to the claim about confidence, distinguishing it from the firmer historical and institutional assertions."),
    item("reading", "Read the passage. A university replaces oral examinations with automated quizzes to improve consistency. Scores become more reproducible across markers, but students increasingly study isolated facts and avoid synthesising arguments. The change succeeds by the institution’s reliability metric while weakening the ability the course claims to value most. Which concept best explains the outcome?",
         "The proxy became the target and displaced the broader educational goal.", "Inter-rater reliability necessarily measures synthesis better.",
         "Automated assessment prevents any factual learning.", "The course goal changed because students preferred quizzes.", difficulty=5,
         subskill="proxy-measurement", seconds=155, explanation="Optimising a reproducible quiz score rewards what the proxy captures while crowding out unmeasured synthesis—the classic target–proxy problem."),
    item("reading", "Read the passage. The editor calls the essay ‘carefully argued, if ultimately unpersuasive.’ Later she praises its evidence but says its conclusion requires an assumption the evidence cannot establish. Which interpretation best preserves her stance?",
         "She respects the essay’s method and evidence while rejecting the inferential step needed for its conclusion.",
         "She thinks careless reasoning invalidates all of the evidence.", "She is persuaded by the conclusion despite weak evidence.",
         "She uses ‘if’ to state a condition under which the essay will be published.", difficulty=5, subskill="evaluative-concession", seconds=145,
         explanation="The concessive ‘if’ allows positive evaluation of the argument’s care while the later sentence identifies a specific inferential gap."),
    item("reading", "Read the passage. After a city introduced congestion pricing, weekday traffic fell while weekend traffic rose. Supporters cite the weekday fall; critics cite the weekend rise. Fuel sales across the whole month declined slightly. Which additional evidence would most help determine whether driving was displaced rather than reduced?",
         "Trip-level data linking former weekday journeys to journeys at other times or outside the priced area.",
         "A larger photograph of weekday traffic.", "Drivers’ opinions about whether congestion is unpleasant.",
         "The number of traffic lights installed before the policy.", difficulty=5, subskill="evidence-selection", seconds=165,
         explanation="Displacement is a change in time or place of the same journeys; linked trip-level patterns directly test that mechanism."),
    item("reading", "Read the passage. ‘We should be wary of explaining the novelist’s ambiguity as indecision. The unresolved ending does not merely withhold an answer; it makes the reader experience the uncertainty that constrains the characters.’ What function does the second sentence serve?",
         "It replaces a psychological explanation of the author with a functional account of the text’s effect.",
         "It proves that the novelist forgot to write an ending.", "It restates ‘indecision’ as a synonym for reader uncertainty.",
         "It argues that all ambiguous endings have the same purpose.", difficulty=5, subskill="rhetorical-function", seconds=150,
         explanation="The writer rejects speculation about authorial indecision and explains ambiguity through what it makes readers experience."),
    item("reading", "Read the passage. A review says the book ‘offers a useful map of the debate, though maps simplify the terrain they help us navigate.’ The reviewer then identifies two schools of thought that the book groups together despite important differences. What is the metaphor doing?",
         "It grants the book orienting value while preparing a criticism of its simplification.",
         "It claims the book is literally about geography.", "It dismisses summaries as invariably useless.",
         "It suggests the debate has a single uncontested route.", difficulty=5, subskill="metaphor-and-evaluation", seconds=150,
         explanation="A map is useful because it orients, yet necessarily selective; the metaphor carries both the qualified praise and the coming criticism."),
    item("reading", "Read the passage. Researchers observe that bilingual children outperform monolingual peers on a switching task, but the advantage disappears when family income and parental education are matched. They warn against concluding that bilingualism has no cognitive effects. Why is that warning justified?",
         "Removing one apparent association does not establish the absence of every effect, especially beyond the measured task and sample.",
         "Matching variables proves bilingualism harms cognition.", "A disappearing group difference confirms the original causal claim.",
         "Cognitive effects can never be studied empirically.", difficulty=5, subskill="limits-of-null-findings", seconds=165,
         explanation="The adjusted result narrows one claim about one task; it cannot support the universal conclusion that bilingualism has no cognitive effects."),
    item("reading", "Read the passage. ‘The minister’s promise was precise enough to be quoted and elastic enough to survive contradiction: “frontline spending will be protected.” Whether outsourced services counted as frontline activity was left conveniently unspecified.’ Which feature of the promise is being criticised?",
         "Its key category is strategically underdefined, allowing incompatible outcomes to be presented as compliance.",
         "Its wording contains too many numerical targets.", "It explicitly excludes all outsourced services.",
         "It is too technical for journalists to quote.", difficulty=5, subskill="strategic-ambiguity", seconds=150,
         explanation="The apparently clear pledge depends on an undefined category, giving the speaker flexibility to redefine compliance after the fact."),
    item("reading", "Read the passage. A teacher notices that learners produce accurate relative clauses in controlled exercises but avoid them in spontaneous discussion. She concludes that the form has been learned but not acquired. What assumption does this conclusion rely on?",
         "Spontaneous availability is a stronger indicator of integrated competence than success under tightly cued conditions.",
         "Controlled exercises can never reveal any grammatical knowledge.", "Avoidance proves learners do not understand the form’s meaning.",
         "Accuracy and acquisition are identical whenever a prompt is provided.", difficulty=5, subskill="language-assessment-inference", seconds=155,
         explanation="The distinction assumes that knowledge demonstrated only under explicit prompting is less integrated than form–meaning access during spontaneous production."),
]


USE_OF_ENGLISH = [
    item("use-of-english", "The evidence is compatible with the hypothesis, but it does not ___ amount to confirmation.", "thereby", "therein", "whereby", "thereafter",
         difficulty=3, subskill="discourse-adverbials", explanation="‘Thereby’ means ‘by that fact or means’; compatibility alone does not by that fact constitute confirmation."),
    item("use-of-english", "The board approved the plan, ___ two members’ reservations about the timetable.", "notwithstanding", "whereas", "inasmuch as", "lest",
         difficulty=3, subskill="concessive-linking", explanation="‘Notwithstanding’ can directly introduce the noun phrase that did not prevent approval."),
    item("use-of-english", "Her criticism is all the more persuasive ___ she acknowledges the strongest objection to it.", "because", "although", "unless", "whereby",
         difficulty=4, subskill="comparative-correlative", explanation="The construction ‘all the more ... because’ identifies the reason the quality is intensified."),
    item("use-of-english", "The revised account is not so much a retraction ___ a narrowing of the original claim.", "as", "than", "but rather than", "like",
         difficulty=4, subskill="contrastive-framing", explanation="The idiomatic contrast is ‘not so much X as Y’, reframing rather than simply negating the first description."),
    item("use-of-english", "___ compelling the anecdote may be, it cannot substitute for representative evidence.", "However", "Whatever", "Although of", "Despite how",
         difficulty=4, subskill="concessive-degree", explanation="‘However + adjective + subject + may be’ concedes any degree of compellingness while preserving the main limitation."),
    item("use-of-english", "The explanation is plausible only ___ we overlook two counterexamples identified in the appendix.", "insofar as", "lest", "notwithstanding that", "whereupon",
         difficulty=4, subskill="conditional-limitation", explanation="‘Insofar as’ limits the explanation’s plausibility to the extent that the counterexamples are ignored."),
    item("use-of-english", "The proposal is ___ coherent, but whether it is workable is another matter.", "internally", "inwardly", "intrinsically to", "interiorly",
         difficulty=5, subskill="academic-collocation", explanation="‘Internally coherent’ means consistent within its own assumptions, which can be true even when practical feasibility remains doubtful."),
    item("use-of-english", "The author stops ___ accusing the agency of misconduct, but the implication is difficult to miss.", "short of", "away from", "under", "beside",
         difficulty=5, subskill="pragmatic-idiom", explanation="To ‘stop short of’ something is to approach it without explicitly doing it, matching an implied but unstated accusation."),
    item("use-of-english", "The exception does not invalidate the pattern; if anything, it brings the governing constraint into sharper ___.", "relief", "focus on", "outline", "exposure",
         difficulty=5, subskill="idiomatic-metaphor", explanation="To bring something ‘into sharper relief’ is to make it more noticeable through contrast."),
    item("use-of-english", "The apparently neutral wording ___ a distinction between legitimate and illegitimate users.", "smuggles in", "hands over", "falls through", "makes out",
         difficulty=5, subskill="evaluative-phrasal-verb", explanation="‘Smuggles in’ metaphorically describes introducing a contestable assumption without openly arguing for it."),
    item("use-of-english", "Far ___ it from the reviewers to reject innovation; their objection concerns the unsupported claim of novelty.", "be", "is", "being", "been",
         difficulty=5, subskill="fixed-subjunctive", explanation="‘Far be it from ...’ is a fixed formula using the base-form subjunctive to deny an attributed attitude."),
    item("use-of-english", "The two findings are difficult to reconcile, ___ they were produced by nominally identical procedures.", "the more so because", "much as though", "even if only", "not least despite",
         difficulty=5, subskill="reason-intensification", explanation="‘The more so because’ says the difficulty is intensified by the surprising fact that the procedures were supposedly identical."),
]


WRITING = [
    item("writing-objective", "Which revision best distinguishes the observed result from the proposed explanation? ‘The intervention reduced absences because it improved morale.’",
         "Absences fell after the intervention; improved morale is one possible explanation for the change.",
         "The intervention proved that morale alone controls every absence.", "Because absences fell, morale unquestionably improved.",
         "The observed explanation reduced morale after the intervention.", difficulty=4, subskill="fact-versus-inference", seconds=210,
         question_type="writing_objective", explanation="The semicolon separates the measured change from a cautiously framed causal hypothesis rather than presenting the hypothesis as observed fact."),
    item("writing-objective", "A report moves from evidence to recommendation. Which sentence makes the warrant explicit without overstating certainty?",
         "Because the pilot reduced processing time without increasing error rates, a monitored expansion is justified.",
         "The pilot was successful, so nationwide adoption cannot fail.", "Processing time fell; therefore every operational risk has been eliminated.",
         "Expansion is recommended because recommendations should be expanded.", difficulty=4, subskill="argument-warrant", seconds=210,
         question_type="writing_objective", explanation="The sentence links both observed outcomes to a proportionate next step and preserves monitoring rather than claiming guaranteed success."),
    item("writing-objective", "Which edit resolves the misplaced modifier without changing the intended emphasis? ‘The analyst presented the projected losses to the board using three scenarios.’",
         "Using three scenarios, the analyst presented the projected losses to the board.",
         "The analyst presented, using three scenarios, the board to projected losses.",
         "The projected losses presented the analyst to the board using three scenarios.",
         "The analyst using the board presented three projected loss scenarios to.", difficulty=4, subskill="modifier-attachment", seconds=200,
         question_type="writing_objective", explanation="Fronting the participial phrase makes the analyst its unambiguous agent and keeps ‘projected losses’ as the object presented."),
    item("writing-objective", "Which version uses parallel structure while preserving the distinction between process and outcome?",
         "The review examined how decisions were documented, how exceptions were approved, and whether outcomes were independently verified.",
         "The review examined decision documentation, how exceptions were approved, and independent verifying outcomes.",
         "The review examined documenting decisions, exception approval, and whether outcomes independently.",
         "The review examined how decisions documented, approving exceptions, and outcomes were verification.", difficulty=4, subskill="complex-parallelism", seconds=205,
         question_type="writing_objective", explanation="All three objects are finite interrogative clauses, while ‘how’ appropriately describes processes and ‘whether’ tests the verification outcome."),
    item("writing-objective", "Which sentence most appropriately reports a null result in an academic abstract?",
         "We found no detectable effect within the study’s pre-specified precision bounds.",
         "We proved that the intervention has absolutely no effect anywhere.", "The intervention failed because the p-value was not significant.",
         "Nothing happened, which confirms the null hypothesis forever.", difficulty=5, subskill="precision-and-null-results", seconds=220,
         question_type="writing_objective", explanation="The revision states what the design could detect and avoids converting a null result into universal proof of no effect."),
    item("writing-objective", "Which revision removes the nominalisation while retaining an appropriately formal tone? ‘The committee conducted an evaluation of the implementation of the policy.’",
         "The committee evaluated how the policy was implemented.", "The committee did an evaluation thing about policy implementation.",
         "The policy had its implementation evaluation conducted by committee.", "There was an evaluation of implementation by the committee of the policy.",
         difficulty=4, subskill="nominalisation-control", seconds=195, question_type="writing_objective",
         explanation="‘Evaluated’ restores the main action to the verb, and the embedded clause identifies the object precisely without sacrificing formality."),
    item("writing-objective", "Which pair creates the clearest old-to-new information flow?",
         "The first experiment revealed an unexpected interaction. This interaction motivated a second study of age-related effects.",
         "An interaction motivated effects. The first experiment was unexpected and second.",
         "A second study existed. This first experiment reveals an interaction without relation.",
         "Age was studied. Unexpectedly, the second first interaction experiment motivated it.", difficulty=5, subskill="information-structure", seconds=215,
         question_type="writing_objective", explanation="The second sentence begins with the established interaction and then introduces the new consequence, producing a coherent given-to-new progression."),
    item("writing-objective", "A teacher wants feedback that identifies both error and remedy. Which comment is most diagnostically useful?",
         "Your claim is broader than your evidence: restrict it to the surveyed group or add evidence from other populations.",
         "This is unclear—rewrite everything.", "Good idea, but the paragraph feels wrong.",
         "Never make claims in academic writing.", difficulty=5, subskill="pedagogical-feedback", seconds=210,
         question_type="writing_objective", explanation="The comment names the scope mismatch and offers two concrete, valid revision strategies instead of giving a vague judgment."),
]


ADVANCED = [
    item("advanced", "A learner says ‘I have seen her yesterday.’ Which explanation is most likely to produce durable understanding?",
         "‘Yesterday’ closes the time period, so use past simple: ‘I saw her yesterday’; present perfect links an event to an unfinished or unspecified time frame.",
         "Present perfect is never used with people.", "Replace ‘yesterday’ with ‘before yesterday’ and keep every other context unchanged.",
         "Memorise that ‘have’ cannot occur before a past participle.", difficulty=4, subskill="pedagogical-grammar-explanation", seconds=150,
         explanation="The correction connects tense choice to temporal viewpoint, making the rule transferable beyond this sentence."),
    item("advanced", "A C1 learner repeatedly writes grammatically accurate essays that sound overly categorical. Which intervention best targets the problem?",
         "Use a corpus-guided noticing task comparing certainty markers and hedges across claims with different evidence strength.",
         "Repeat elementary subject–verb agreement drills.", "Ban all modal verbs from future assignments.",
         "Ask the learner to replace every verb with a synonym.", difficulty=5, subskill="advanced-pedagogy", seconds=155,
         explanation="The problem is pragmatic calibration of stance; authentic comparisons and noticing connect linguistic choices to evidential strength."),
    item("advanced", "Which learner error most clearly indicates transfer from a language that permits null subjects?",
         "‘Is important to review the evidence before deciding.’", "‘The evidences are convincing.’",
         "‘I look forward to hear from you.’", "‘She explained me the procedure.’", difficulty=5, subskill="error-source-diagnosis", seconds=145,
         explanation="Omission of the dummy subject ‘it’ is consistent with transfer from a pro-drop system; the other errors concern countability, complementation, and valency."),
    item("advanced", "A placement item is answered correctly by 98% of advanced candidates and 91% of intermediate candidates. What is its main weakness for selecting the strongest teachers?",
         "It has little discriminatory power at the upper end, even if it is reliable as a basic mastery check.",
         "Its correct answer must be factually wrong.", "High accuracy proves the item distinguishes every proficiency level.",
         "It is invalid solely because more than half answered correctly.", difficulty=4, subskill="assessment-literacy", seconds=155,
         explanation="When both target groups answer correctly at nearly the same high rate, the item contributes little information for ranking high performers."),
    item("advanced", "During a speaking task, a learner self-corrects ‘He go—he goes every day’ without prompting. Which interpretation is most defensible?",
         "The target form is available to monitoring, although the initial slip shows it is not fully automatic in production.",
         "The learner has no knowledge of third-person agreement.", "Self-correction proves native-like automaticity.",
         "The first form should be ignored because only final output contains evidence.", difficulty=5, subskill="performance-analysis", seconds=150,
         explanation="Unprompted repair shows awareness and monitoring; the initial error still provides evidence about processing automaticity."),
    item("advanced", "Which question best tests pragmatic competence rather than only grammatical form?",
         "A colleague says ‘It’s getting late’ during a meeting. What responses would appropriately recognise the implied request to finish?",
         "Choose the past tense of ‘leave’.", "Underline the subject in ‘The meeting ended’.",
         "Spell ‘colleague’ correctly.", difficulty=5, subskill="pragmatic-assessment", seconds=150,
         explanation="Interpreting and responding to an indirect speech act requires contextual pragmatic competence, not just formal grammar recognition."),
    item("advanced", "A teacher corrects every spoken error immediately. Fluency falls and learners begin avoiding complex forms. Which adjustment is best supported by the evidence in this scenario?",
         "Reserve immediate correction for errors that block meaning and use delayed, selective feedback for other recurring patterns.",
         "Increase the number of interruptions until no learner speaks spontaneously.", "Stop providing all feedback permanently.",
         "Correct only pronunciation because grammar never affects communication.", difficulty=5, subskill="feedback-timing", seconds=155,
         explanation="Selective timing protects communicative flow while preserving focused feedback on high-impact and recurring errors."),
    item("advanced", "Two learners receive the same score. One answers consistently across skills; the other excels in reading but performs poorly in listening. Why should a selection report preserve subscores?",
         "The identical total masks different competence profiles and therefore different teaching risks or development needs.",
         "Subscores guarantee that every item is perfectly valid.", "A total score has no mathematical relationship to item responses.",
         "Listening should always count more than every other skill.", difficulty=4, subskill="score-interpretation", seconds=145,
         explanation="A compensatory total can hide a serious weakness, while skill-level evidence supports a more defensible staffing decision."),
    item("advanced", "Which correction addresses a discourse error rather than a sentence-level grammatical error?",
         "Move the concession before the main claim so ‘however’ clearly contrasts the two propositions.",
         "Add -s to a third-person singular present-tense verb.", "Replace an incorrect plural with a singular noun.",
         "Change ‘in Monday’ to ‘on Monday’.", difficulty=5, subskill="discourse-diagnosis", seconds=145,
         explanation="The placement and reference of a connective concern relations between propositions; the other corrections are local morphology or preposition choices."),
    item("advanced", "A learner knows that ‘Would you mind opening the window?’ is a request but responds ‘Yes’ while opening it. What should feedback prioritise?",
         "Explain how English polarity in responses to ‘mind’ can conflict with the speaker’s intended acceptance, and practise unambiguous replies such as ‘Not at all.’",
         "Teach the spelling of ‘window’ again.", "Explain that the original request is ungrammatical.",
         "Ban indirect requests because they have no conventional meaning.", difficulty=5, subskill="pragmatic-polarity", seconds=155,
         explanation="The learner understood the action but not the response convention; feedback should target pragmatic polarity and safer formulae."),
    item("advanced", "Which evidence most strongly supports the claim that a vocabulary item measures depth rather than mere recognition?",
         "Candidates must choose the word that fits the passage’s meaning, register, and collocational constraints among plausible near-synonyms.",
         "Candidates report having seen the word before.", "The target word is printed in a larger font.",
         "Every distractor is an obviously unrelated beginner word.", difficulty=5, subskill="construct-validity", seconds=150,
         explanation="Depth involves nuanced semantic, register, and combinatorial knowledge; plausible near-synonyms require those dimensions to be integrated."),
    item("advanced", "A test labels a candidate C2 solely from multiple-choice grammar and vocabulary. What is the most important validity concern?",
         "The score underrepresents productive, interactive, and discourse abilities required by the broader proficiency construct.",
         "Multiple-choice scoring can never be reliable.", "Grammar and vocabulary have no relationship to proficiency.",
         "C2 candidates should receive no structured assessment.", difficulty=5, subskill="construct-underrepresentation", seconds=150,
         explanation="Selected-response items can measure valuable receptive knowledge but cannot alone substantiate claims about the full range of productive and interactive C2 performance."),
]


LISTENING_SPECS = [
    # clip01 — B2+/C1 calibration
    ("What must a Bath passenger update and what must remain unchanged?", "Use platform six but remain on the Bristol service.", "Use platform four and change trains immediately.", "Move to platform ten and wait for a Bath-only service.", "Leave the station because the route no longer serves Bath.", "instruction-synthesis", "The platform changes from four to six, while Bath passengers are explicitly told to remain on the same train."),
    ("Which detail explains the revised departure time without implying a route change?", "A signalling problem has caused an approximately ten-minute delay.", "Bath has been removed from the service.", "The train itself is damaged beyond use.", "Platform six is closed for ten minutes.", "cause-versus-consequence", "The signalling problem explains the delay; the instruction to Bath passengers confirms that the route remains relevant."),
    ("What is the announcement’s main operational purpose?", "To coordinate a platform change, a short delay, and onward travel for Bath passengers.", "To cancel all travel to Bristol and Bath.", "To advertise a new express route from platform four.", "To ask passengers to report a signalling fault.", "global-purpose", "A correct summary must integrate the new platform, expected delay, and instruction for Bath passengers."),
    # clip02 — B2+/C1 calibration
    ("Which constraint created the need for rescheduling?", "The dentist’s professional commitment conflicts with the original appointment.", "The patient asked to change dentists permanently.", "The clinic no longer offers appointments on Fridays.", "The original appointment has already taken place.", "cause-inference", "Attendance at a conference makes the dentist unavailable for the Thursday appointment."),
    ("Which response would fully satisfy the caller’s request?", "Contact the clinic before five today and choose between Friday morning and Monday afternoon.", "Arrive on Thursday and decide after the conference.", "Reply tomorrow and request Friday at four.", "Wait for the clinic to cancel both alternatives.", "constraint-integration", "The caller provides two specific alternatives and a same-day response deadline; both constraints must be recognised."),
    ("Why does the message give two replacement times before stating the deadline?", "To make prompt confirmation possible by pairing the problem with actionable alternatives.", "To imply that both appointments have already been booked for the patient.", "To avoid explaining why the original time changed.", "To announce that the clinic will close at five permanently.", "discourse-organisation", "The message moves from cause to alternatives and then to the required response, supporting efficient resolution."),
    # clip03
    ("Which statement best distinguishes the two schedule decisions?", "The product launch is unchanged, but promotion begins later.", "Both the launch and promotion move two days.", "The launch moves while promotion remains fixed.", "Both schedules have been cancelled.", "contrastive-synthesis", "The speaker explicitly preserves the launch date while moving only the marketing campaign."),
    ("What unresolved dependency presents the clearest immediate delivery risk?", "The payment integration is still being tested.", "The mobile screens have not been started.", "The launch date has not been selected.", "The marketing team has cancelled the product.", "risk-inference", "Finished screens remove one uncertainty, while incomplete payment testing remains a core-path delivery risk."),
    ("What is the speaker primarily doing?", "Separating completed work, remaining risk, and a limited schedule change.", "Announcing that the entire product has failed.", "Requesting that the mobile design be abandoned.", "Explaining why payment will launch after marketing.", "discourse-purpose", "The update contrasts completed design with ongoing testing and clarifies that only the campaign timing changes."),
    # clip04
    ("Which summary most accurately describes tonight’s service disruption?", "One area closes early, while core study and computer facilities remain available.", "The whole library closes at six.", "Only book returns remain available after six.", "Electrical maintenance closes every area until tomorrow.", "qualified-summary", "The closure is limited to the west wing; the main reading room and computer area remain open until nine."),
    ("Why is the late-fee exception pragmatically relevant to the announcement?", "It compensates borrowers for disruption associated with the maintenance closure.", "It permanently abolishes all return deadlines.", "It requires users to enter the closed wing.", "It extends computer access beyond nine.", "pragmatic-inference", "The one-day waiver reduces the burden on borrowers affected by the restricted access."),
    ("A student needs a computer from seven to eight. What follows from the announcement?", "The student can still use the computer area.", "The student must wait until tomorrow.", "The west wing is the only place with computers.", "All electrical services stop at six.", "applied-inference", "The computer area remains open until nine, despite the separate west-wing closure."),
    # clip05
    ("How did the speaker’s first-year work differ from the expected role?", "It replaced a mainly analytical focus with direct customer discovery.", "It replaced customer research with isolated data analysis.", "It moved from tool design to conference planning.", "It eliminated documentation from the role.", "contrastive-synthesis", "The speaker expected data analysis but actually interviewed customers and documented problems."),
    ("Which assumption about good design does the speaker now reject?", "That designers can reliably infer user needs without direct evidence.", "That data can ever contribute to design.", "That customers can describe practical problems.", "That tools should solve real user needs.", "stance-inference", "The speaker explicitly contrasts evidence from customers with designing around assumptions."),
    ("What causal link does the speaker make?", "Customer exposure improved the relevance of later design decisions.", "Tool design made customer contact unnecessary.", "Documenting problems reduced awareness of user needs.", "Data analysis caused the speaker to leave the company.", "causal-synthesis", "First-hand customer evidence is presented as the reason later tools address real needs."),
    # clip06
    ("When had boarding originally been scheduled to begin?", "Six twenty.", "Six forty.", "Seven o’clock.", "Twenty minutes before six.", "temporal-calculation", "Boarding now begins at 6:40, twenty minutes later than scheduled, so the original time was 6:20."),
    ("Why are some customers asked to approach the desk before general boarding?", "So assistance can be arranged without competing with the main boarding flow.", "Because they must change the departure gate.", "Because their flight leaves twenty minutes earlier.", "So they can avoid presenting travel documents.", "service-inference", "The timing separates assistance needs from general boarding, enabling staff to support those customers first."),
    ("Which combination captures all operational changes and instructions?", "Use gate B12, expect later boarding, and request assistance early if needed.", "Use gate A12 and expect an earlier departure.", "Wait at the assistance desk instead of boarding.", "Change flights because gate B12 is closed.", "multi-detail-synthesis", "The announcement combines a gate assignment, a twenty-minute delay, and an accessibility instruction."),
    # clip07
    ("Which travel plan responds most precisely to the forecast?", "Allow extra time if using the northern bridge in the windy evening period.", "Avoid the bridge all morning because of snow.", "Expect the strongest winds before noon.", "Assume afternoon improvement removes every later risk.", "decision-inference", "The explicit travel warning is tied to strong evening winds, not the lighter morning rain."),
    ("What contrast makes the evening warning easy to overlook?", "Afternoon improvement is followed by a different hazard later.", "Morning sunshine is followed by afternoon snow.", "The coast improves permanently after noon.", "The bridge closes before the weather changes.", "temporal-contrast", "Listeners must not treat afternoon improvement as the day’s final condition because strong winds arrive in the evening."),
    ("What is the discourse function of the final sentence?", "It converts a general forecast into targeted advice for a specific journey.", "It withdraws the earlier forecast as inaccurate.", "It reports that the bridge has already closed.", "It explains the scientific cause of coastal wind.", "discourse-purpose", "The final sentence applies the forecast to drivers using a named route and recommends extra time."),
    # clip08
    ("Which apparent inconsistency does the message resolve?", "A stale tracking page does not mean the promised Friday delivery has changed.", "The damaged charger and replacement are the same parcel.", "Express delivery always arrives before tracking begins.", "A Friday delivery was cancelled yesterday.", "reassurance-inference", "The speaker separates delayed tracking visibility from the unchanged delivery expectation."),
    ("What burden has the seller explicitly removed from the customer?", "Returning the faulty charger.", "Checking the tracking page tonight.", "Receiving the replacement on Friday.", "Calling the shop before dispatch.", "pragmatic-detail", "The customer is directly told that the damaged charger need not be returned."),
    ("What is the message’s primary communicative purpose?", "To reassure the customer that replacement fulfilment remains on course despite limited tracking information.", "To ask the customer to place a new order.", "To announce that express delivery failed.", "To request payment for returning the charger.", "global-purpose", "Dispatch has occurred and Friday remains expected; the tracking caveat is framed to prevent unnecessary concern."),
    # clip09
    ("Which causal possibility is explicitly raised besides a hidden common cause?", "The apparent direction of influence may be reversed.", "Both variables must be measurement errors.", "Correlation prevents either variable from changing.", "Experimental design can remove every uncertainty automatically.", "alternative-causality", "The recording names both third-variable influence and reverse direction as alternatives to the first causal interpretation."),
    ("Why does the speaker move from correlation to experimental design?", "To show what additional method is needed to discriminate among causal explanations.", "To argue that correlated variables should no longer be measured.", "To prove every experiment establishes one-way causation.", "To redefine correlation as a random coincidence.", "argument-structure", "The final recommendation follows from the underdetermination of causal direction and confounding in correlational evidence."),
    # clip10
    ("How did the criterion for the garden’s success change?", "It broadened from material output to include social connection.", "It narrowed from social effects to vegetable weight alone.", "It shifted from neighbour participation to paid employment.", "It excluded every unintended outcome.", "construct-shift", "The initial production goal remains relevant, but stronger relationships become the garden’s greatest perceived impact."),
    ("Why does the speaker call the social result unexpected?", "It emerged from interactions around the project rather than its original production objective.", "Neighbours had been hired specifically to avoid speaking.", "The harvest failed completely and ended the project.", "Sharing tools was prohibited in the original plan.", "emergent-outcome", "The garden began as a food-production project; social capital arose as an unplanned consequence."),
    # clip11
    ("Which delivery principle is the speaker applying?", "Stabilise the demonstrable core before optional breadth and polish.", "Complete visual polish before testing login.", "Treat every feature as equally urgent.", "Replace the demonstration with a final product.", "prioritisation-principle", "The speaker protects login and reporting, defers exports, and conditions polish on core stability."),
    ("What would most clearly violate the instruction?", "Spending Tuesday morning polishing visuals while the login flow remains unreliable.", "Showing a functional but not final demonstration.", "Deferring exports to the next sprint.", "Testing the reporting dashboard before Tuesday.", "constraint-application", "Visual refinements are permitted only after core paths are stable, so polishing while login is unreliable reverses the stated priority."),
    # clip12
    ("Under what condition does the target cease to be a trustworthy guide?", "When people can improve the measured number while neglecting the valued outcome.", "When the measured outcome is genuinely valued.", "When invisible work becomes visible to managers.", "When staff understand the organisation’s goal.", "proxy-failure", "The speaker warns that optimisation of a proxy can diverge from the underlying goal."),
    ("Which example best instantiates the speaker’s warning?", "A support team closes easy tickets rapidly while leaving complex customer problems unresolved.", "A clinic measures and improves patient recovery.", "A school checks whether students can apply what they learned.", "A team revises a metric after finding it misaligned.", "principle-application", "Fast closure counts can rise while meaningful support deteriorates, illustrating optimisation of what is counted rather than what matters."),
]


# Concise keys remove test-wise cues without weakening the underlying construct.
# Each remains semantically identical to the authored rationale.
READING_KEYS = (
    "Residual engagement differences still weaken the causal claim.",
    "Reporting changes undermine confidence in the recorded decline.",
    "Inspectability does not eliminate value judgments in model design.",
    "Archival silence depends on whether dissent could enter the record.",
    "A non-significant difference does not establish equivalence.",
    "It makes only the claim about confidence tentative.",
    "The proxy displaced the broader educational goal.",
    "She accepts the method but rejects the conclusion’s key inference.",
    "Linked trip data across times and locations.",
    "It replaces author psychology with a functional textual account.",
    "It offers orientation while foreshadowing a simplification critique.",
    "One null result cannot exclude every cognitive effect.",
    "An undefined category permits incompatible claims of compliance.",
    "Spontaneous availability indicates more integrated competence.",
)

LISTENING_KEYS = (
    "Platform six; stay on the Bristol train.",
    "A signalling fault caused the ten-minute delay.",
    "To coordinate platform, delay, and Bath travel instructions.",
    "The dentist’s conference conflicts with the appointment.",
    "Call before five and choose an offered time.",
    "To pair the problem with actionable alternatives.",
    "The launch stays fixed; promotion starts later.",
    "Payment integration remains under test.",
    "To separate completed work, remaining risk, and schedule change.",
    "Only one area closes; core facilities remain available.",
    "It compensates borrowers for disruption from maintenance.",
    "The computer area remains available then.",
    "Expected analysis became direct customer discovery.",
    "Designers cannot infer needs reliably without direct evidence.",
    "Customer exposure improved later design relevance.",
    "Six twenty.",
    "To arrange assistance before the main boarding flow.",
    "Use B12, expect delay, and request assistance early.",
    "Allow extra time on the bridge during evening winds.",
    "Afternoon improvement precedes a different evening hazard.",
    "It turns a forecast into journey-specific advice.",
    "Delayed tracking does not change Friday delivery.",
    "Returning the faulty charger.",
    "To reassure the customer that delivery remains on course.",
    "The apparent causal direction may be reversed.",
    "To distinguish among competing causal explanations.",
    "Success broadened from produce to social connection.",
    "Social connection emerged outside the original production goal.",
    "Stabilise the core before optional breadth and polish.",
    "Polishing visuals while login remains unreliable.",
    "When the metric improves while the valued outcome deteriorates.",
    "Closing easy tickets while complex problems remain unresolved.",
)

WRITING_CHOICES = (
    ("Absences fell; improved morale is one possible explanation.", "Absences fell, which establishes morale as the sole causal mechanism.", "Morale improved, although the available measure records only absence.", "The intervention preceded the decline, so alternative explanations are unnecessary."),
    ("The pilot supports a monitored expansion because time fell without more errors.", "The pilot supports immediate expansion because short-term results guarantee durability.", "The time reduction justifies expansion even if later error data are unavailable.", "The unchanged error rate matters, but it cannot inform an expansion decision."),
    ("Using three scenarios, the analyst presented the projected losses to the board.", "The analyst presented the board’s projected losses using three scenarios.", "The analyst presented projected losses using a board of three scenarios.", "Using three scenarios, the projected losses were what the board presented."),
    ("The review examined how decisions were documented, how exceptions were approved, and whether outcomes were verified.", "The review examined decision documentation, how exceptions were approved, and whether outcomes had verification.", "The review examined how decisions were documented, exception approval, and independently verified outcomes.", "The review examined documenting decisions, approving exceptions, and whether outcomes were independently verified."),
    ("No effect was detectable within the pre-specified precision bounds.", "The non-significant estimate demonstrates that the intervention has no meaningful effect.", "The study confirms the null because the confidence interval includes zero.", "No average effect was detected, so subgroup effects can be excluded."),
    ("The committee evaluated how the policy was implemented.", "The committee undertook an evaluation regarding the policy’s implementation process.", "The implementation of the policy was subject to the committee’s evaluating activity.", "The committee made an evaluation of how implementation was being implemented."),
    ("The first study found an interaction. This finding motivated a study of age effects.", "An interaction appeared in the first study. Age effects therefore caused that interaction.", "The second study examined age effects. This interaction had already motivated the first study.", "The first study motivated an interaction. This age effect was then treated as established."),
    ("Your claim exceeds the evidence; narrow its population or add broader evidence.", "Your conclusion is plausible, so the mismatch between sample and population needs no revision.", "Your evidence is relevant; strengthen the prose without changing the claim’s scope.", "Your claim should be deleted because academic writing should avoid generalisation entirely."),
)

ADVANCED_CHOICES = (
    ("Use past simple with the closed time marker: ‘I saw her yesterday.’", "Keep present perfect because ‘yesterday’ specifies when the experience occurred.", "Use past perfect because the seeing precedes the present moment of speaking.", "Change only ‘yesterday’ to ‘before yesterday’; tense choice is otherwise unaffected."),
    ("Compare corpus hedges across claims supported by different evidence strengths.", "Assign more tense drills because categorical tone usually reflects inaccurate time reference.", "Teach a fixed list of formal synonyms without comparing their stance effects.", "Focus only on paragraph order because sentence-level certainty cannot affect register."),
    ("‘Is important to review ...’ omits the required dummy subject ‘it’.", "‘The evidences in the appendix are convincing’ pluralises an uncountable noun.", "‘I look forward to hear from you’ selects an infinitive after a preposition.", "‘She explained me the procedure’ transfers a different verb-complement pattern."),
    ("It offers little discrimination among stronger candidates.", "It indicates inadequate content coverage despite otherwise stable scoring.", "It is too difficult for the intended advanced population to interpret.", "It shows negative discrimination because intermediate candidates outperform advanced ones."),
    ("Monitoring is available, but agreement is not fully automatic.", "The self-repair demonstrates fully automatic control despite the initial production slip.", "The initial form shows the agreement rule is entirely absent from the learner’s system.", "The correction is evidence of external prompting rather than self-monitoring."),
    ("Interpreting an indirect request and selecting a contextually appropriate response.", "Selecting the grammatically correct past-tense form in an isolated sentence.", "Identifying the syntactic subject and predicate of a direct statement.", "Distinguishing two spellings without any interactional context."),
    ("Correct meaning-blocking errors immediately; delay feedback on other recurring patterns.", "Delay every correction until the course ends so spontaneous fluency is never interrupted.", "Correct each form error after every turn, regardless of communicative consequence.", "Correct only preselected grammar targets even when another error prevents understanding."),
    ("The total masks different skill profiles relevant to teaching risk.", "Subscores prove that every task measures its intended construct equally well.", "Separate skill scores remove the need to interpret uncertainty in the total score.", "Listening should receive greater weight whenever two candidates share a total."),
    ("Reposition ‘however’ so its contrast between propositions is unambiguous.", "Add agreement marking to a singular present-tense verb in the first clause.", "Replace a count noun with its singular form to match the determiner.", "Change a time preposition while leaving the relation between clauses untouched."),
    ("Target response polarity and practise unambiguous replies such as ‘Not at all.’", "Teach that ‘yes’ accepts every request regardless of the predicate’s polarity.", "Replace indirect requests with direct imperatives before discussing response conventions.", "Treat the completed action as sufficient evidence that the verbal response was appropriate."),
    ("Use plausible near-synonyms constrained by meaning, register, and collocation.", "Ask candidates whether they recognise the word without requiring contextual use.", "Use direct translation pairs while holding register and collocation constant.", "Contrast the target only with unrelated words that can be rejected by topic."),
    ("It omits productive, interactive, and extended-discourse performance.", "The selected-response format necessarily makes every resulting score unreliable.", "Grammar and vocabulary evidence cannot contribute to any proficiency inference.", "A C2 claim is invalid only when fewer than fifty items are administered."),
)


def _replace_choices(questions, choices):
    if len(questions) != len(choices):
        raise RuntimeError("English v5 balanced-choice map is incomplete")
    for question, balanced in zip(questions, choices):
        question["choices"] = tuple(balanced)


def _replace(section_questions, positions, replacements):
    if len(positions) != len(replacements):
        raise RuntimeError("English v5 replacement map is incomplete")
    for position, replacement in zip(positions, replacements):
        section_questions[position] = replacement


def _upgrade_listening(questions):
    # Reserve two clips for B2+/C1 calibration, four for synthesis, and six for
    # upper-tail inference. All prompts are curated even though the source audio
    # assets and content-group identifiers remain unchanged.
    advanced_specs = iter(LISTENING_SPECS)
    for question in questions:
        clip = question.get("content_group", "")
        clip_number = int(clip.removeprefix("clip"))
        question["difficulty"] = 3 if clip_number <= 2 else 4 if clip_number <= 6 else 5
        question["suggested_seconds"] = 120 if clip_number <= 2 else 145
        prompt, correct, wrong1, wrong2, wrong3, subskill, explanation = next(advanced_specs)
        wrong = (wrong1, wrong2, wrong3)
        question.update({
            "prompt": prompt,
            "choices": (correct,) + wrong,
            "subskill": subskill,
            "teacher_v5_curated": True,
            "explanation": explanation,
            "choice_explanations_fa": (explanation,) + tuple(
                f"‘{choice}’ conflicts with the recording’s details, implication, or discourse purpose."
                for choice in wrong
            ),
            "choice_explanations_en": (explanation,) + tuple(
                f"‘{choice}’ conflicts with the recording’s details, implication, or discourse purpose."
                for choice in wrong
            ),
        })


def upgrade_bank(source_questions):
    questions = deepcopy(source_questions)
    by_section = {}
    for question in questions:
        by_section.setdefault(question["section"], []).append(question)

    # Positions refer to the stable v4 source order. Replacements deliberately
    # occupy former lower-information slots, leaving historical DB rows intact.
    _replace(by_section["grammar"], (0, 1, 2, 3, 4, 6, 15, 16, 17, 18), GRAMMAR)
    _replace(by_section["vocabulary"], (0, 1, 2, 6, 10, 11, 12, 13), VOCABULARY)
    _replace(by_section["reading"], tuple(range(14)), READING)
    _replace(by_section["use-of-english"], tuple(range(12)), USE_OF_ENGLISH)
    _replace(by_section["writing-objective"], (0, 1, 2, 3, 4, 5, 6, 7), WRITING)
    _replace(by_section["advanced"], tuple(range(12)), ADVANCED)
    _upgrade_listening(by_section["listening"])
    for question, correct in zip(READING, READING_KEYS):
        question["choices"] = (correct,) + question["choices"][1:]
    for question, correct in zip(by_section["listening"], LISTENING_KEYS):
        question["choices"] = (correct,) + question["choices"][1:]
    _replace_choices(WRITING, WRITING_CHOICES)
    _replace_choices(ADVANCED, ADVANCED_CHOICES)

    # Legacy material remains in the source bank for historical traceability,
    # but cannot enter the v5 D2-D5 blueprint unless it passed this curation.
    for section_questions in by_section.values():
        for question in section_questions:
            if question.get("teacher_v5_curated"):
                question["suggested_seconds"] = {
                    2: 60,
                    3: 60,
                    4: 70,
                    5: 70,
                }[question["difficulty"]]
            else:
                question["difficulty"] = 1

    # Preserve the original global order used by seed snapshots.
    offsets = {section: 0 for section in by_section}
    upgraded = []
    for original in questions:
        section = original["section"]
        upgraded.append(by_section[section][offsets[section]])
        offsets[section] += 1
    return upgraded
