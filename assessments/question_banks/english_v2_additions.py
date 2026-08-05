"""Additional English A1-C1 and objective-writing items for bank version 2."""


def build(section, specs, question_type="single_choice", seconds=75):
    questions = []
    for prompt, correct, wrong1, wrong2, wrong3, difficulty, subskill, explanation in specs:
        wrong = (wrong1, wrong2, wrong3)
        questions.append({
            "section": section, "prompt": prompt, "choices": (correct,) + wrong,
            "difficulty": difficulty, "subskill": subskill, "question_type": question_type,
            "suggested_seconds": seconds, "explanation": explanation,
            "choice_explanations_fa": (explanation,) + tuple(
                f"‘{choice}’ does not satisfy the grammar, meaning, register, or cohesion required here."
                for choice in wrong
            ),
            "choice_explanations_en": (explanation,) + tuple(
                f"‘{choice}’ does not satisfy the grammar, meaning, register, or cohesion required here."
                for choice in wrong
            ),
        })
    return questions


GRAMMAR = build("grammar", [
    ("There ___ two chairs in the room.", "are", "is", "be", "has", 1, "be-present", "A plural noun phrase takes ‘are’ in this existential construction."),
    ("My brother can ___ very well.", "swim", "swims", "swimming", "to swim", 1, "modals", "A modal verb is followed by the bare infinitive."),
    ("We ___ dinner when the phone rang.", "were having", "had", "have", "are having", 2, "past-continuous", "Past continuous describes the activity in progress when the shorter event occurred."),
    ("She has worked here ___ three years.", "for", "since", "during", "from", 2, "time-prepositions", "‘For’ introduces a duration; ‘since’ introduces a starting point."),
    ("This exercise is ___ than the previous one.", "more difficult", "most difficult", "difficulter", "as difficult", 2, "comparatives", "Long adjectives normally form the comparative with ‘more’."),
    ("I don't have ___ information yet.", "much", "many", "a few", "several", 2, "quantifiers", "‘Information’ is uncountable, so ‘much’ is appropriate in a negative sentence."),
    ("The keys ___ on the desk belong to Sam.", "lying", "lie", "are lain", "have lied", 3, "participle-clauses", "The present participle ‘lying’ reduces the relative clause ‘that are lying’."),
    ("You won't pass unless you ___ regularly.", "study", "will study", "studied", "would study", 3, "conditionals", "A present form follows ‘unless’ when referring to a real future condition."),
    ("I would rather ___ at home tonight.", "stay", "to stay", "staying", "stayed", 3, "verb-patterns", "‘Would rather’ is followed by the bare infinitive when the subject is unchanged."),
    ("The room needs ___.", "cleaning", "to cleaning", "clean", "being clean", 3, "gerunds", "‘Needs cleaning’ is a standard passive-meaning gerund construction."),
    ("He denied ___ the confidential file.", "opening", "to open", "open", "having open", 3, "verb-patterns", "‘Deny’ is followed by a gerund; ‘opening’ is the correct form."),
    ("The bridge ___ before the inspection began.", "had been repaired", "has repaired", "was repairing", "is repaired", 4, "past-perfect-passive", "Past perfect passive marks a completed repair before another past event."),
    ("If she were here, she ___ what to do.", "would know", "will know", "knew", "would have known", 4, "second-conditional", "The hypothetical present condition requires ‘would’ plus the base verb in the result clause."),
    ("He speaks as though he ___ everything.", "knew", "knows always", "has know", "will knew", 4, "unreal-comparison", "Past form ‘knew’ expresses an unreal or doubtful present comparison after ‘as though’."),
    ("Only after the audit ___ the extent of the problem.", "did we understand", "we understood", "we did understand", "understood we", 5, "inversion", "A fronted restrictive adverbial triggers subject–auxiliary inversion."),
    ("Had the data been available, we ___ a different decision.", "might have made", "might make", "made", "will have made", 5, "mixed-conditionals", "The inverted third conditional requires a past modal perfect in the result."),
    ("So complex ___ that several reviewers missed the flaw.", "was the calculation", "the calculation was", "did the calculation", "the calculation did", 5, "inversion", "Fronted ‘so + adjective’ requires inversion: ‘so complex was the calculation’."),
])


VOCABULARY = build("vocabulary", [
    ("A person who repairs water pipes is a ___.", "plumber", "carpenter", "pharmacist", "cashier", 1, "occupations", "A plumber installs and repairs water and drainage pipes."),
    ("If a shop is ___, it is not open.", "closed", "crowded", "local", "cheap", 1, "everyday-adjectives", "‘Closed’ means not open for business."),
    ("Please ___ the light before you leave.", "turn off", "turn over", "turn into", "turn around", 2, "phrasal-verbs", "‘Turn off’ means stop a light or device from operating."),
    ("The train was delayed ___ heavy snow.", "due to", "although", "unless", "despite of", 2, "cause", "‘Due to’ correctly introduces the noun phrase giving the cause."),
    ("Her answer was brief but ___.", "accurate", "ordinary", "generous", "anxious", 2, "adjectives", "‘Accurate’ means correct and fits a description of an answer."),
    ("We need to ___ a decision by Friday.", "reach", "arrive", "achieve to", "catch", 3, "collocations", "‘Reach a decision’ is the standard collocation."),
    ("The two reports are broadly ___.", "consistent", "obedient", "vacant", "edible", 3, "academic-vocabulary", "‘Consistent’ means compatible or not contradictory."),
    ("The manager tried to ___ concerns about job security.", "address", "deliver", "attend", "obtain", 3, "collocations", "To ‘address concerns’ means to deal with them directly."),
    ("The new evidence ___ doubt on the original conclusion.", "casts", "throws up", "puts down", "makes", 3, "collocations", "‘Cast doubt on’ is the established expression for making something seem uncertain."),
    ("Sales remained ___ despite the advertising campaign.", "sluggish", "vivid", "rigidly", "plentifully", 4, "business-vocabulary", "‘Sluggish’ describes activity or growth that is slower than expected."),
    ("The committee reached a ___ after hours of debate.", "consensus", "controversy", "constraint", "deficit", 4, "formal-vocabulary", "A consensus is a broadly shared agreement."),
    ("The rule was applied ___, without considering individual circumstances.", "indiscriminately", "tentatively", "coherently", "implicitly", 4, "adverbs", "‘Indiscriminately’ means without careful distinction."),
    ("The policy aims to ___ the effects of rising prices.", "mitigate", "evoke", "compile", "concede", 4, "academic-vocabulary", "‘Mitigate’ means make something harmful less severe."),
    ("His account of the incident was internally ___.", "coherent", "abundant", "subordinate", "inevitable", 4, "formal-vocabulary", "An internally coherent account is logically connected and consistent."),
    ("The findings are ___ with earlier research.", "compatible", "capable", "dependent to", "reliant of", 4, "academic-collocations", "‘Compatible with’ means able to exist together without contradiction."),
    ("The agreement was deliberately left ___.", "ambiguous", "transparent", "unanimous", "empirical", 4, "precision", "‘Ambiguous’ means open to more than one interpretation."),
    ("The minister sought to ___ responsibility for the failure.", "evade", "derive", "compile", "retain to", 5, "advanced-verbs", "To ‘evade responsibility’ means avoid accepting it."),
    ("The apparent contradiction can be ___ by examining the methodology.", "reconciled", "refrained", "repealed", "reciprocated", 5, "academic-vocabulary", "To reconcile a contradiction is to show how the conflicting points can be made consistent."),
    ("The author presents a ___ critique rather than rejecting the theory entirely.", "nuanced", "negligent", "redundant", "sporadic", 5, "advanced-adjectives", "A nuanced critique recognizes subtle distinctions and qualifications."),
    ("The evidence remains ___; it supports more than one interpretation.", "equivocal", "impeccable", "exhaustive", "inherent", 5, "advanced-adjectives", "‘Equivocal’ describes evidence that is uncertain or open to multiple interpretations."),
    ("The exception does not ___ the general principle.", "invalidate", "evaporate", "reimburse", "disclose to", 5, "argumentation", "To invalidate a principle is to show that it is not valid."),
    ("The reform may have ___ consequences for smaller institutions.", "far-reaching", "short-livedly", "well-worn", "high-mindedly", 5, "advanced-collocations", "‘Far-reaching consequences’ have a broad and significant effect."),
])


READING = build("reading", [
    ("Leila packed an umbrella even though the sky was clear because the forecast predicted afternoon rain. Why did she take it?", "She expected the weather might change.", "It was already raining.", "She wanted shade indoors.", "The forecast promised sunshine.", 1, "explicit-detail", "The forecast of afternoon rain explains why she prepared for a change in weather."),
    ("The café offers breakfast until 11:00, while lunch begins at noon. Amir arrived at 11:30. What was available?", "Neither the breakfast nor lunch menu yet.", "Only breakfast.", "Only lunch.", "Both menus.", 1, "time-detail", "At 11:30 breakfast had ended and lunch had not yet begun."),
    ("Nora chose the bus because parking near the venue is expensive and limited. What influenced her choice?", "The difficulty and cost of parking.", "The bus was free.", "She cannot drive.", "The venue was closed to cars.", 2, "cause-effect", "The sentence explicitly identifies expensive, limited parking as the reason."),
    ("The software update is optional this week but will become mandatory on Monday. What changes on Monday?", "Users will be required to install it.", "The update will be removed.", "It will become free.", "Users may ignore it indefinitely.", 2, "explicit-detail", "‘Mandatory’ means required rather than optional."),
    ("Despite being smaller, the new battery lasts longer because it uses energy more efficiently. What is surprising?", "Its smaller size does not reduce its operating time.", "It consumes more energy.", "It is larger than the old battery.", "It cannot hold a charge.", 2, "contrast", "The contrast is between smaller physical size and longer battery life."),
    ("The museum waived admission fees, leading to a sharp rise in visitors. What does ‘waived’ mean here?", "Did not require payment", "Increased", "Delayed", "Collected twice", 3, "vocabulary-in-context", "Waiving a fee means choosing not to charge it."),
    ("The report praises the program's reach but notes that its long-term impact remains uncertain. What is the writer's position?", "The program reached many people, but lasting effects are unclear.", "The program certainly failed.", "Its impact is already permanent.", "Very few people joined it.", 3, "main-idea", "The writer balances a positive observation about reach with uncertainty about durability."),
    ("A company shortened meetings from an hour to thirty minutes. Employees reported greater focus, although some complex issues required follow-up sessions. What was the trade-off?", "Better focus but occasional need for additional discussion", "Longer meetings and less focus", "Fewer issues and no follow-up", "Lower attendance but higher costs", 3, "synthesis", "Shorter meetings improved focus, but complex topics sometimes needed another session."),
    ("The city added cycle lanes, but usage rose only after secure bicycle parking was installed. What does this suggest?", "Infrastructure must address more than the route itself.", "Cycle lanes always reduce cycling.", "Parking had no effect.", "Residents opposed bicycles.", 4, "inference", "The later increase implies that secure storage was also necessary for adoption."),
    ("The survey included only customers who renewed their subscriptions. Consequently, satisfaction may appear higher than it is across all customers. What is the main concern?", "Selection bias", "A calculation error", "A spelling mistake", "Random assignment", 4, "critical-reading", "Excluding customers who did not renew selects a group likely to be more satisfied."),
    ("Managers assumed remote staff were less productive, yet output data showed no meaningful difference. What challenged the assumption?", "Measured performance", "Employee location", "Office rent", "A new assumption", 4, "evidence", "Objective output data contradicted the managers’ belief."),
    ("The article does not oppose regulation; rather, it argues that rules should be proportionate to risk. What does the author support?", "Risk-based regulation", "No regulation", "Identical rules for every activity", "Banning all risky activity", 4, "author-position", "The author accepts regulation while advocating rules calibrated to risk."),
    ("Because the trial lacked a control group, improvements cannot confidently be attributed to the treatment. Why not?", "Other factors could have caused the improvement.", "The treatment had no participants.", "Control groups guarantee failure.", "No improvement was measured.", 4, "research-literacy", "Without a comparison group, alternative explanations cannot be ruled out."),
    ("The policy reduced average waiting times, but the median changed very little. What might explain this?", "A few extremely long waits became shorter.", "Every wait became identical.", "The median is always larger than the average.", "No waiting time changed.", 5, "quantitative-inference", "Reducing a few extreme values can substantially affect the mean while leaving the median stable."),
    ("The author describes the proposal as ‘elegant in theory but brittle in practice.’ What is implied?", "It is conceptually attractive but fails under real conditions.", "It is unattractive and robust.", "It has already succeeded widely.", "Its theory is impossible to understand.", 5, "tone-inference", "The contrast between elegant and brittle distinguishes theoretical appeal from practical resilience."),
    ("An apparent increase in disease followed improved testing. Researchers caution that detection, not prevalence, may have changed. What distinction matters?", "More recorded cases do not necessarily mean more actual cases.", "Testing always causes disease.", "Prevalence and detection are identical.", "Researchers stopped collecting data.", 5, "causal-reasoning", "Better detection can raise recorded case counts even if underlying prevalence stays constant."),
    ("The review calls the evidence ‘suggestive rather than conclusive.’ How strong is the claim?", "It indicates a possibility but does not establish certainty.", "It proves the claim beyond doubt.", "It rejects all evidence.", "It reports no relationship at all.", 4, "hedging", "‘Suggestive’ signals limited support, while ‘not conclusive’ explicitly withholds certainty."),
    ("The system was designed for efficiency under normal loads, leaving little spare capacity during sudden demand. What weakness is identified?", "Limited resilience to spikes", "High cost during normal use", "Excess unused capacity", "Inability to operate normally", 4, "inference", "Minimal spare capacity makes the system vulnerable when demand rises unexpectedly."),
    ("Although the samples came from different regions, their chemical profiles were virtually indistinguishable. What can be inferred?", "Geographic origin did not produce a detectable difference in the measured profiles.", "The samples were collected in one place.", "Chemical testing was not performed.", "Every region has different chemistry.", 5, "inference", "Virtually indistinguishable profiles mean the measured chemistry did not vary detectably by region."),
    ("The author acknowledges the model's simplicity as both a limitation and a source of transparency. What dual effect is described?", "It omits detail but is easier to understand.", "It is detailed and impossible to inspect.", "It removes all limitations.", "It is accurate only because it is complex.", 5, "synthesis", "Simplicity can reduce realism while making assumptions and mechanisms more visible."),
    ("The intervention worked in tightly controlled trials, but scaling it required local staff to adapt procedures. What does this show?", "Effectiveness at scale depended on contextual adaptation.", "Controlled trials were unnecessary.", "Local staff prevented success.", "Procedures remained identical everywhere.", 5, "synthesis", "The need for local adaptation shows that trial efficacy alone did not guarantee scaled effectiveness."),
    ("Critics argue the metric rewards visible activity rather than meaningful outcomes. What is their concern?", "People may optimize what is counted instead of what matters.", "Outcomes are too visible.", "No activity can be measured.", "The metric rewards inactivity.", 5, "critical-reading", "The criticism is that measurement incentives can shift behavior toward the proxy rather than the true goal."),
])


USE_OF_ENGLISH = build("use-of-english", [
    ("How often do you ___ yoga?", "do", "make", "play", "go", 1, "collocations", "‘Do yoga’ is the standard activity collocation."),
    ("I'm interested ___ learning Spanish.", "in", "on", "at", "for", 1, "prepositions", "The adjective ‘interested’ takes the preposition ‘in’."),
    ("Could I ___ your phone for a moment?", "borrow", "lend", "owe", "rent to", 2, "word-choice", "The receiver borrows an object; the owner lends it."),
    ("We ran ___ milk, so I went to the shop.", "out of", "away from", "up to", "over with", 2, "phrasal-verbs", "‘Run out of’ means use all of a supply."),
    ("She apologized ___ being late.", "for", "to", "about to", "with", 2, "prepositions", "‘Apologize for’ introduces the reason for the apology."),
    ("The event will take ___ on Saturday.", "place", "part", "over", "after", 2, "fixed-expressions", "‘Take place’ means happen."),
    ("I can't ___ the difference between these two versions.", "tell", "say", "speak", "talk", 3, "collocations", "‘Tell the difference’ is the established expression for distinguishing things."),
    ("The company is looking ___ the complaint.", "into", "after", "up", "forward", 3, "phrasal-verbs", "‘Look into’ means investigate."),
    ("There is no point ___ about the decision now.", "complaining", "to complain", "complain", "complained", 3, "verb-patterns", "‘There is no point’ is followed by a gerund."),
    ("The changes will come ___ effect next month.", "into", "in", "to", "for", 3, "fixed-expressions", "Rules ‘come into effect’ when they begin to apply."),
    ("She has a talent ___ explaining complex ideas clearly.", "for", "of", "to", "with", 3, "prepositions", "‘A talent for’ is the correct noun–preposition pattern."),
    ("We should not take their support ___ granted.", "for", "as", "to", "by", 3, "fixed-expressions", "To ‘take something for granted’ means fail to appreciate or question it."),
    ("The outcome depends ___ whether funding is approved.", "on", "from", "of", "at", 3, "prepositions", "The verb ‘depend’ takes ‘on’."),
    ("He eventually came ___ with a workable solution.", "up", "out", "across", "through", 3, "phrasal-verbs", "‘Come up with’ means produce an idea or solution."),
    ("The decision is likely to give rise ___ further debate.", "to", "for", "with", "into", 4, "formal-collocations", "The fixed expression is ‘give rise to’."),
    ("The explanation is at odds ___ the available evidence.", "with", "to", "from", "against of", 4, "formal-collocations", "‘At odds with’ means inconsistent or in conflict with."),
    ("The report draws attention ___ several unresolved issues.", "to", "on", "at", "for", 4, "formal-collocations", "The phrase is ‘draw attention to’."),
    ("We need to distinguish correlation ___ causation.", "from", "with", "against", "to", 4, "prepositions", "‘Distinguish A from B’ is the standard pattern."),
    ("The final result bears little resemblance ___ the original design.", "to", "with", "from", "of", 4, "formal-collocations", "The noun ‘resemblance’ takes ‘to’."),
    ("Her argument hinges ___ a questionable assumption.", "on", "at", "from", "into", 4, "formal-collocations", "To ‘hinge on’ means depend critically on."),
    ("The evidence does not rule ___ alternative explanations.", "out", "off", "away", "down", 4, "phrasal-verbs", "‘Rule out’ means eliminate as a possibility."),
    ("His account should be taken with a grain of ___.", "salt", "sugar", "doubt", "care", 5, "idioms", "Taking something ‘with a grain of salt’ means treating it with skepticism."),
])


WRITING_OBJECTIVE = build("writing-objective", [
    ("Choose the clearest revision: ‘The meeting was cancelled due to the fact that the manager was ill.’", "The meeting was cancelled because the manager was ill.", "Due to the manager, the meeting, which was ill, was cancelled.", "The meeting was cancelled owing to the fact of illness by manager.", "Because illness, therefore the meeting was cancelled.", 2, "conciseness", "‘Because’ expresses the reason directly and removes the wordy phrase ‘due to the fact that’."),
    ("Which sentence is punctuated correctly?", "After reviewing the data, the team revised its recommendation.", "After reviewing the data the team, revised its recommendation.", "After reviewing, the data the team revised its recommendation.", "After reviewing the data the team revised, its recommendation.", 2, "punctuation", "An introductory participial phrase is followed by a comma, with no comma separating the verb from its object."),
    ("Choose the best topic sentence for a paragraph about the benefits of regular backups.", "Regular backups reduce the operational impact of accidental data loss.", "Yesterday, one file had a long name.", "Some offices have blue walls.", "Backups are a word used in computing.", 2, "topic-sentences", "The sentence clearly states the paragraph’s controlling idea: backups reduce the harm caused by data loss."),
    ("Which sentence is most appropriate in a formal email to a client?", "Could you please confirm whether the revised schedule is acceptable?", "Hey, tell me if the new dates work, okay?", "You must answer about those dates now.", "What about the schedule thing?", 2, "formal-register", "The selected sentence is polite, specific, and appropriately formal."),
    ("Choose the sentence with clear pronoun reference.", "Sara told Mina that the report needed another review.", "When Sara spoke to Mina, she said it was wrong.", "She told her that it needed that.", "After it was discussed, she changed it for her.", 3, "clarity", "Naming the participants and the report avoids ambiguous pronouns."),
    ("Which transition best completes the paragraph? ‘The first trial produced encouraging results. ___, the sample was too small to support a firm conclusion.’", "However", "Similarly", "For example", "Therefore", 3, "cohesion", "‘However’ signals the contrast between encouraging results and an important limitation."),
    ("Choose the best concluding sentence for a paragraph showing that flexible hours improved retention and reduced absence.", "Overall, flexible scheduling appears to benefit both employee continuity and attendance.", "Flexible is an adjective.", "The office also bought new chairs.", "There are many kinds of schedules in dictionaries.", 3, "conclusions", "The sentence synthesizes both pieces of evidence without introducing an unrelated idea."),
    ("Which revision removes the dangling modifier? ‘Driving to work, the rain became heavier.’", "While I was driving to work, the rain became heavier.", "Driving to work, heavier was the rain.", "The rain, driving to work, became heavier.", "To work driving, it became rainier by itself.", 3, "sentence-structure", "The revision supplies ‘I’ as the person driving, so the modifier has a logical subject."),
    ("Choose the most coherent order. (1) Finally, the team deployed the fix. (2) First, engineers reproduced the failure. (3) Next, they identified the faulty query.", "2 – 3 – 1", "1 – 2 – 3", "3 – 1 – 2", "2 – 1 – 3", 3, "paragraph-order", "The sequence moves logically from reproducing the problem to finding its cause and deploying the fix."),
    ("Which sentence maintains parallel structure?", "The role requires analyzing data, writing reports, and presenting findings.", "The role requires analyzing data, to write reports, and presentations.", "The role requires data analysis, writing reports, and to present findings.", "The role requires to analyze, reports, and presenting.", 3, "parallelism", "All three coordinated items use gerund phrases: analyzing, writing, and presenting."),
    ("Choose the most precise revision: ‘The system went bad when many people used it.’", "The system became unresponsive under heavy concurrent traffic.", "The system was not good with lots of stuff.", "Many people did things and it went somehow bad.", "The system had a thing when usage happened.", 3, "precision", "The revision identifies the observable failure and the specific condition that triggered it."),
    ("Which sentence best connects the evidence to the claim?", "Because error rates fell after validation was added, the change likely improved input quality.", "Validation exists, and errors are things.", "The claim is true because it is the claim.", "Errors fell; unrelatedly, validation has letters.", 4, "evidence-linking", "The sentence explicitly explains how the observed evidence supports the stated inference."),
    ("Choose the best revision to avoid overclaiming: ‘The pilot proves the policy will work everywhere.’", "The pilot suggests the policy may work in similar settings.", "The pilot unquestionably proves all future outcomes.", "The policy works everywhere because one pilot happened.", "No further evidence could ever change the conclusion.", 4, "academic-hedging", "‘Suggests’ and ‘may’ accurately reflect the limited generalizability of a single pilot."),
    ("Which sentence uses an appropriately neutral academic tone?", "The results do not provide sufficient evidence to support the hypothesis.", "The hypothesis was obviously ridiculous from the start.", "Everyone knows the results totally destroy the idea.", "The researchers somehow messed everything up.", 4, "academic-register", "The selected sentence evaluates the evidence precisely without emotional or personal language."),
    ("Choose the clearest way to combine the sentences: ‘The update improved speed. It increased memory use.’", "Although the update improved speed, it increased memory use.", "The update improved speed, because memory increased although.", "Improving speed and memory use increased by the update.", "The update, it improved speed, it increased memory.", 4, "sentence-combining", "‘Although’ clearly presents the benefit and cost as a contrast in one grammatical sentence."),
    ("Which sentence should be removed from a paragraph explaining password security?", "The company cafeteria serves lunch from noon.", "Long, unique passwords reduce the risk of credential reuse.", "Password managers can generate and store unique credentials.", "Multi-factor authentication adds protection if a password is exposed.", 3, "paragraph-unity", "The cafeteria sentence is unrelated to the paragraph’s controlling topic of password security."),
    ("Choose the best executive-summary sentence.", "Customer cancellations fell 12% after onboarding was simplified, indicating that early guidance affected retention.", "We changed some onboarding screens and many things happened afterward.", "This report has numbers and discusses customers in several places.", "Onboarding is important, very important, and cancellation is also a topic.", 4, "executive-writing", "The sentence concisely states the intervention, measurable result, and business implication."),
    ("Which revision correctly limits the claim? ‘Remote work increases productivity.’", "In this survey, remote work was associated with higher self-reported productivity.", "Remote work always makes every employee more productive.", "Productivity is caused only by remote work.", "No remote employee can have low productivity.", 5, "claim-scope", "The revision identifies the study context, uses associative rather than causal language, and states how productivity was measured."),
    ("Choose the most coherent pair of sentences.", "The model performs well on common cases. Nevertheless, rare inputs still require manual review.", "The model performs well. For example, rare inputs always fail, therefore common means manual.", "Rare inputs require review. Similarly, the model has no relationship to common cases.", "The model is common; meanwhile review is a rare noun.", 4, "cohesion", "‘Nevertheless’ accurately links strong general performance with the remaining exception."),
    ("Which revision best separates fact from interpretation?", "Response time fell by 18%; this improvement may reflect the new caching strategy.", "Caching definitely caused the 18% change, and no other factor is possible.", "Response time fell because the writer believes caching is good.", "The 18% figure is an opinion proving the strategy.", 5, "evidence-and-inference", "The semicolon separates the measured fact from a cautious interpretation that does not overstate causality."),
], question_type="writing_objective", seconds=180)


ADVANCED = build("advanced", [
    ("Little ___ that the decision would trigger such opposition.", "did they anticipate", "they anticipated", "had they anticipate", "they did anticipated", 5, "inversion", "Fronted negative ‘little’ requires subject–auxiliary inversion with ‘did’."),
    ("___ the evidence been disclosed earlier, the outcome might have differed.", "Had", "If", "Were", "Should", 5, "inverted-conditionals", "‘Had the evidence been disclosed’ is the inverted form of a third conditional if-clause."),
    ("The report is valuable, not least ___ it challenges a common assumption.", "because", "despite", "unless", "whereas of", 5, "discourse-connectors", "‘Not least because’ introduces an especially important reason."),
    ("The findings are robust, ___ the relatively small sample.", "notwithstanding", "therefore", "provided that", "inasmuch", 5, "concession", "‘Notwithstanding’ means despite and can directly precede a noun phrase."),
    ("She objected not to the proposal itself ___ to the way it had been presented.", "but", "rather", "and neither", "as", 5, "correlative-structure", "The contrastive structure is ‘not X but Y’."),
    ("It was the lack of transparency that ___ most concern.", "caused", "did caused", "was cause", "having caused", 4, "cleft-sentences", "The cleft sentence requires the finite past verb ‘caused’ after the focused subject."),
    ("The mechanism remains poorly understood, ___ its effects are well documented.", "even though", "because of", "in case", "so as", 4, "concession", "‘Even though’ introduces the surprising contrast between limited understanding and strong documentation."),
    ("The recommendation is contingent ___ further funding being secured.", "on", "to", "with", "for", 5, "advanced-collocations", "‘Contingent on’ means dependent on a condition."),
    ("What the analysis fails to account ___ is the variation between regions.", "for", "of", "with", "to", 4, "prepositions", "The phrasal verb ‘account for’ means explain or include."),
    ("Rarely ___ such a rapid change in public opinion.", "have researchers observed", "researchers have observed", "did researchers observed", "researchers observed have", 5, "inversion", "Fronted ‘rarely’ triggers inversion with the present perfect auxiliary before the subject."),
    ("The data lends itself ___ several competing interpretations.", "to", "for", "with", "into", 5, "advanced-collocations", "The fixed pattern is ‘lend itself to’, meaning be suitable or open to."),
    ("Be that ___, the practical constraints cannot be ignored.", "as it may", "it may as", "as may it", "may it be", 5, "fixed-concession", "‘Be that as it may’ is a fixed concessive expression meaning nevertheless."),
    ("The changes were introduced gradually, thereby ___ disruption.", "minimizing", "to minimize", "minimized", "having minimize", 4, "participle-clauses", "‘Thereby’ is followed by a gerund to express the result of the preceding action."),
    ("So compelling ___ that the committee reversed its position.", "was the evidence", "the evidence was", "did the evidence", "the evidence did", 5, "inversion", "Fronted ‘so + adjective’ requires inversion: ‘so compelling was the evidence’."),
    ("The policy is unlikely to succeed without local support, ___ substantial the funding may be.", "however", "whatever", "although of", "despite", 5, "concession", "‘However + adjective + subject + may be’ expresses concession about degree."),
])


ADDITIONAL_QUESTIONS = GRAMMAR + VOCABULARY + READING + USE_OF_ENGLISH + WRITING_OBJECTIVE + ADVANCED
