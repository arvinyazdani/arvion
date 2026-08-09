"""Curated English placement bank. Choices are stored with the correct answer first."""

BANK_VERSION = 4

SECTIONS = (
    ("grammar", "گرامر", "Grammar", 32, 8),
    ("vocabulary", "واژگان", "Vocabulary", 32, 8),
    ("reading", "درک مطلب", "Reading", 32, 8),
    ("use-of-english", "کاربرد زبان", "Use of English", 32, 8),
    ("listening", "مهارت شنیداری", "Listening", 32, 8),
    ("writing-objective", "مهارت‌های نوشتاری", "Writing Objective", 20, 5),
    ("advanced", "ساختارهای پیشرفته", "Advanced Structures", 20, 5),
)


def q(section, prompt, correct, *wrong, difficulty=3, subskill="", question_type=None,
      suggested_seconds=None, explanation=""):
    explanation = explanation or f"‘{correct}’ is the only option that is grammatically and contextually appropriate."
    wrong_explanations = tuple(
        f"‘{choice}’ does not fit the grammar, meaning, register, or cohesion required here." for choice in wrong
    )
    return {
        "section": section, "prompt": prompt, "choices": (correct,) + wrong,
        "difficulty": difficulty, "subskill": subskill or section,
        "question_type": question_type or ("writing_objective" if section == "writing-objective" else "single_choice"),
        "suggested_seconds": suggested_seconds or (180 if section == "writing-objective" else 75),
        "explanation": explanation,
        "choice_explanations_fa": (explanation,) + wrong_explanations,
        "choice_explanations_en": (explanation,) + wrong_explanations,
    }


QUESTIONS = [
q("grammar","She ___ coffee every morning.","drinks","drink","is drink","drinking",difficulty=1),
q("grammar","They ___ in Tehran since 2020.","have lived","lived","are living","live",difficulty=2),
q("grammar","If it rains, we ___ at home.","will stay","stayed","would stay","stay will",difficulty=2),
q("grammar","I ___ him yesterday.","saw","have seen","see","was see",difficulty=1),
q("grammar","This book ___ by millions of people.","has been read","has read","is reading","was readed",difficulty=3),
q("grammar","By next June, she ___ her degree.","will have completed","will complete","completed","has completed",difficulty=4),
q("grammar","I wish I ___ more time.","had","have","will have","would have had",difficulty=3),
q("grammar","Neither the manager nor the employees ___ available.","were","was","is","has been",difficulty=3),
q("grammar","He asked me where I ___ the file.","had saved","save","have saved","will save",difficulty=4),
q("grammar","You ___ have told me; I already knew.","needn't","mustn't","couldn't","shouldn't",difficulty=4),
q("grammar","The woman ___ car was stolen called the police.","whose","who","which","whom",difficulty=3),
q("grammar","Hardly ___ the meeting started when the alarm rang.","had","has","did","was",difficulty=5),
q("grammar","If I ___ the warning, I would have acted differently.","had understood","understood","would understand","have understood",difficulty=4),
q("grammar","Not only ___ late, but he also forgot the documents.","was he","he was","did he was","he did",difficulty=5),
q("grammar","She suggested that he ___ a specialist.","consult","consults","consulted","will consult",difficulty=5),
q("vocabulary","‘Rapid’ is closest in meaning to ___.","fast","quiet","careful","late",difficulty=1),
q("vocabulary","The instructions were so ___ that everyone understood them.","clear","scarce","rough","narrow",difficulty=2),
q("vocabulary","We need a ___ solution that can work in practice.","feasible","fragile","remote","casual",difficulty=3),
q("vocabulary","The new policy may ___ small businesses.","affect","effect","infect","reflect",difficulty=3),
q("vocabulary","Her explanation was ___; it covered every important detail.","comprehensive","temporary","reluctant","arbitrary",difficulty=4),
q("vocabulary","The evidence was not sufficient to ___ the claim.","substantiate","postpone","diminish","allocate",difficulty=5),
q("vocabulary","A person who is willing to consider new ideas is ___.","open-minded","short-sighted","self-conscious","absent-minded",difficulty=3),
q("vocabulary","The company decided to ___ the outdated process.","phase out","bring up","look after","turn in",difficulty=4),
q("vocabulary","His comments were ___ to the topic under discussion.","relevant","dependent","capable","identical",difficulty=3),
q("vocabulary","The results should be interpreted with ___.","caution","permission","fortune","ambition",difficulty=4),
q("reading","Mina cycles to work because it is faster than driving in rush hour. Why does she cycle?","It saves time.","It costs more.","She dislikes exercise.","Her car is broken.",difficulty=1),
q("reading","The library closes at six on weekdays, but remains open until eight on Thursdays. When is it open latest?","Thursday","Monday","Saturday","Every weekday",difficulty=1),
q("reading","Although the product sold well initially, demand declined after competitors introduced cheaper alternatives. What caused the decline?","Cheaper competing products","Poor initial sales","A lack of advertising","Higher product quality",difficulty=2),
q("reading","Remote work can increase autonomy, yet it may also reduce informal learning between colleagues. What contrast is presented?","Independence versus informal learning","Salary versus working hours","Technology versus travel","Management versus recruitment",difficulty=3),
q("reading","The study found a correlation between sleep and performance, but did not establish causation. What can be concluded?","The variables are related, but cause is unproven.","Sleep definitely causes success.","Performance reduces sleep.","No relationship exists.",difficulty=4),
q("reading","The proposal is ambitious; nevertheless, its budget assumptions appear unrealistic. What is the writer's view?","The aim is impressive but the finances are doubtful.","The entire proposal is realistic.","The budget is too generous.","The aim lacks ambition.",difficulty=4),
q("reading","Unlike earlier models, the device processes data locally, thereby reducing latency and limiting exposure of personal information. What are two benefits?","Faster response and better privacy","Lower quality and higher cost","Remote storage and advertising","Longer delays and data sharing",difficulty=4),
q("reading","Some critics dismiss the reform as symbolic, whereas supporters argue that symbols can reshape public expectations. What do supporters believe?","Symbolic action can influence attitudes.","The reform has no meaning.","Critics support the reform.","Expectations never change.",difficulty=5),
q("reading","The author concedes that automation displaces certain tasks but rejects the assumption that it inevitably reduces total employment. What does the author dispute?","That automation must reduce overall employment","That tasks can be automated","That employment changes over time","That technology affects work",difficulty=5),
q("reading","Because the sample was small and self-selected, the findings should be treated as preliminary. Why is caution needed?","The sample may not represent the wider population.","The study lasted too long.","The findings were duplicated.","The population was too large.",difficulty=5),
q("use-of-english","Could you ___ me a favour?","do","make","give","take",difficulty=1),
q("use-of-english","I look forward to ___ from you.","hearing","hear","have heard","be heard",difficulty=2),
q("use-of-english","The meeting was ___ because the manager was ill.","put off","put out","put up","put through",difficulty=3),
q("use-of-english","Please let me know if you need ___ information.","further","farther","furthest","far",difficulty=3),
q("use-of-english","She is responsible ___ managing the team.","for","to","of","with",difficulty=2),
q("use-of-english","I'd rather you ___ that information confidential.","kept","keep","will keep","have kept",difficulty=4),
q("use-of-english","The project was completed ___ schedule.","ahead of","in front","before of","forward of",difficulty=3),
q("use-of-english","His argument doesn't ___ up under close examination.","hold","keep","stand","take",difficulty=4),
q("use-of-english","We must take all relevant factors ___ account.","into","in","on","at",difficulty=4),
q("use-of-english","The report falls ___ of explaining the root cause.","short","down","away","off",difficulty=5),
q("advanced","Were the market to decline, the company ___ its expansion.","would reconsider","will reconsider","reconsidered","has reconsidered",difficulty=5),
q("advanced","The data is inconclusive, ___ further research is warranted.","hence","despite","whereas","unless",difficulty=5),
q("advanced","No sooner had she arrived ___ the discussion began.","than","when","then","that",difficulty=5),
q("advanced","The policy, ___ well-intentioned, may create unintended costs.","albeit","therefore","provided","otherwise",difficulty=5),
q("advanced","It is imperative that every applicant ___ the declaration.","sign","signs","signed","will sign",difficulty=5),
]

# Human-authored rationales for the original 50-item core. Keeping these
# separate makes their alignment reviewable and prevents silent fallback to a
# generic “only option” explanation when a new core item is added.
CORE_RATIONALES = (
    "With the third-person singular subject ‘she’, the present-simple verb takes -s: ‘drinks’.",
    "‘Since 2020’ marks a starting point continuing to the present, so the present perfect ‘have lived’ is required.",
    "A real future result in a first conditional uses present simple after ‘if’ and ‘will’ in the result clause.",
    "‘Yesterday’ is a finished past-time marker, so the irregular past form ‘saw’ is correct.",
    "The book receives the action and the reading has present relevance, requiring present perfect passive ‘has been read’.",
    "‘By next June’ sets a future deadline before which completion will occur, so future perfect is appropriate.",
    "‘I wish’ about a present situation uses past simple to express an unreal present: ‘had more time’.",
    "With ‘neither … nor’, agreement follows the nearer plural noun ‘employees’, giving ‘were’.",
    "The saving happened before the past act of asking, so reported speech uses past perfect ‘had saved’.",
    "‘Needn’t have’ means the action was unnecessary; the second clause explains that telling was not needed.",
    "‘Whose’ is the possessive relative pronoun connecting the woman to her car.",
    "A clause beginning with ‘Hardly’ uses inversion and past perfect: ‘Hardly had the meeting started …’.",
    "This unreal past condition needs past perfect in the if-clause: ‘If I had understood …’.",
    "‘Not only’ at the start triggers subject–auxiliary inversion, producing ‘was he late’.",
    "After verbs of recommendation such as ‘suggest’, formal English uses the mandative base form ‘consult’.",
    "‘Rapid’ describes high speed, making ‘fast’ its closest synonym here.",
    "If everyone understood the instructions, they were ‘clear’; the other choices do not express comprehensibility.",
    "A solution that can work in practice is ‘feasible’, meaning practical and achievable.",
    "‘Affect’ is the verb meaning influence; ‘effect’ is usually a noun in this context.",
    "‘Comprehensive’ means covering all important aspects, exactly matching the detail in the second clause.",
    "To ‘substantiate’ a claim is to support it with evidence, which is what insufficient evidence cannot do.",
    "‘Open-minded’ specifically describes willingness to consider unfamiliar ideas.",
    "To ‘phase out’ a process is to discontinue it gradually, fitting the removal of an outdated practice.",
    "Comments connected to the topic are ‘relevant’; the remaining adjectives require different complements or meanings.",
    "‘Interpret with caution’ is the conventional collocation when results may have limitations.",
    "The passage directly compares cycling with rush-hour driving and says cycling is faster, so it saves time.",
    "Thursday is the only stated day with an 8 p.m. closing time; weekdays otherwise close at six.",
    "Demand fell after competitors offered cheaper alternatives, identifying price competition as the cause.",
    "The sentence contrasts greater autonomy with reduced informal learning: independence is gained while peer learning may fall.",
    "Correlation shows an association between sleep and performance, but the passage explicitly says causation was not established.",
    "‘Ambitious’ is positive about the aim, while ‘nevertheless’ introduces doubt about the budget assumptions.",
    "Local processing reduces latency and limits personal-data exposure, corresponding to faster response and better privacy.",
    "Supporters argue that symbols reshape public expectations, meaning symbolic action can influence attitudes.",
    "The author accepts task displacement but rejects inevitability of lower total employment; that inevitability is the disputed claim.",
    "A small self-selected sample may differ systematically from the wider population, limiting generalization.",
    "English uses the fixed expression ‘do someone a favour’, not ‘make’ or ‘take’ a favour.",
    "‘Look forward to’ contains the preposition ‘to’, so it is followed by a gerund: ‘hearing’.",
    "‘Put off’ means postpone, which fits delaying a meeting because the manager was ill.",
    "‘Further information’ means additional information; ‘farther’ normally refers to physical distance.",
    "The adjective ‘responsible’ takes the preposition ‘for’ before a noun or gerund.",
    "‘I’d rather you …’ uses a past form for a present or future preference, hence ‘kept’.",
    "‘Ahead of schedule’ is the standard phrase for completion earlier than planned.",
    "An argument that ‘holds up’ remains valid under examination; ‘doesn’t hold up’ means it fails scrutiny.",
    "The fixed phrase is ‘take something into account’, meaning consider it in a decision.",
    "‘Fall short of’ means fail to reach a required standard, here failing to explain the root cause.",
    "The inverted conditional ‘Were the market to decline’ is hypothetical and pairs with ‘would reconsider’.",
    "‘Hence’ signals a result: because the data is inconclusive, further research is warranted.",
    "The correlative construction is ‘no sooner … than’, with inversion after ‘no sooner’.",
    "‘Albeit’ means although and introduces the concession that the policy is well-intentioned.",
    "After ‘It is imperative that’, formal mandative usage takes the base verb ‘sign’.",
)

if len(CORE_RATIONALES) != len(QUESTIONS):
    raise RuntimeError("Every core English question must have a reviewed rationale")
for question, rationale in zip(QUESTIONS, CORE_RATIONALES):
    question["explanation"] = rationale
    question["choice_explanations_fa"] = (rationale,) + question["choice_explanations_fa"][1:]
    question["choice_explanations_en"] = (rationale,) + question["choice_explanations_en"][1:]

from .english_v2_additions import ADDITIONAL_QUESTIONS  # noqa: E402
from .english_listening import QUESTIONS as LISTENING_QUESTIONS  # noqa: E402

QUESTIONS.extend(ADDITIONAL_QUESTIONS)
QUESTIONS.extend(LISTENING_QUESTIONS)
