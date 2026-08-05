"""Listening items for English bank v3. Each clip may be played at most twice."""


def clip_questions(clip, transcript, specs):
    questions = []
    for prompt, correct, wrong1, wrong2, wrong3, difficulty, subskill, explanation in specs:
        wrong = (wrong1, wrong2, wrong3)
        questions.append({
            "section": "listening", "prompt": prompt, "choices": (correct,) + wrong,
            "difficulty": difficulty, "subskill": subskill, "question_type": "listening",
            "suggested_seconds": 90, "audio_path": f"assessments/audio/{clip}.wav",
            "transcript": transcript, "max_plays": 2, "content_group": clip,
            "explanation": explanation,
            "choice_explanations_fa": (explanation,) + tuple(
                f"‘{choice}’ conflicts with a detail, implication, or purpose in the recording." for choice in wrong
            ),
            "choice_explanations_en": (explanation,) + tuple(
                f"‘{choice}’ conflicts with a detail, implication, or purpose in the recording." for choice in wrong
            ),
        })
    return questions


CLIP_01 = "Attention passengers. The eight fifteen train to Bristol will depart from platform six instead of platform four. The service is running approximately ten minutes late because of a signalling problem. Passengers for Bath should remain on this train."
CLIP_02 = "Hi, this is Green Dental Clinic calling for Ms Patel. Your appointment on Thursday at three thirty needs to be moved because the dentist will be attending a conference. We can offer Friday at ten in the morning or Monday at four. Please call us before five today."
CLIP_03 = "Before we begin, a quick update on the product launch. The design team has finished the mobile screens, but the payment integration is still being tested. We will keep the original launch date, although the marketing campaign will now start two days later."
CLIP_04 = "The west wing of the library will close at six this evening for electrical maintenance. The main reading room and computer area will remain open until nine. Any books due today may be returned tomorrow without a late fee."
CLIP_05 = "When I joined the company, I expected to work mainly on data analysis. In practice, I spent my first year speaking with customers and documenting their problems. That experience proved valuable because I now design tools around real user needs rather than assumptions."
CLIP_06 = "Passengers travelling on flight 274 to Seattle should proceed to gate B twelve. Boarding will begin at six forty, twenty minutes later than scheduled. Customers requiring assistance are invited to approach the desk before general boarding begins."
CLIP_07 = "Tomorrow morning will be cool and cloudy across the coast, with light rain likely before noon. Conditions should improve during the afternoon, but strong winds are expected in the evening. Drivers crossing the northern bridge should allow extra time."
CLIP_08 = "Thank you for calling North Street Electronics. Your replacement item was dispatched yesterday by express delivery. The tracking page may not update until tonight, but the parcel is still expected on Friday. You do not need to return the damaged charger."
CLIP_09 = "A correlation tells us that two variables change together, but it does not by itself establish why they do so. A third factor may influence both variables, or the direction of influence may be the reverse of what we first assume. Careful experimental design is therefore essential."
CLIP_10 = "Our community garden initially focused on producing vegetables. We soon discovered that its greatest impact was social: neighbours who had rarely spoken began sharing tools and advice. The harvest mattered, but the stronger relationships were the unexpected result."
CLIP_11 = "The client needs a working demonstration by Tuesday, not the final polished product. Please prioritise the login flow and reporting dashboard. Export features can wait until the following sprint, and visual refinements should only be attempted if the core paths are stable."
CLIP_12 = "Efficiency targets can improve performance when they measure outcomes that people genuinely value. Problems arise when the metric becomes a substitute for the goal itself. Staff may then optimise what is counted while neglecting important work that remains invisible."


QUESTIONS = []
QUESTIONS += clip_questions("clip01", CLIP_01, [
    ("Which platform should Bristol passengers use?", "Platform six", "Platform four", "Platform eight", "Platform ten", 1, "detail", "The announcement changes the departure platform from four to six."),
    ("Why is the train delayed?", "A signalling problem", "Bad weather", "A staff shortage", "A damaged train", 2, "detail", "The speaker explicitly attributes the ten-minute delay to a signalling problem."),
    ("What should passengers for Bath do?", "Stay on this train", "Change at platform four", "Take a bus", "Wait for the next service", 2, "instruction", "The final instruction tells Bath passengers to remain on the train."),
])
QUESTIONS += clip_questions("clip02", CLIP_02, [
    ("Why must the appointment be moved?", "The dentist will attend a conference", "Ms Patel requested a new dentist", "The clinic is closing permanently", "The appointment was already completed", 2, "detail", "The dentist’s conference conflicts with the original Thursday appointment."),
    ("Which replacement time is offered?", "Friday at ten", "Friday at four", "Monday at ten", "Thursday at five", 2, "detail", "The first offered alternative is Friday at ten in the morning."),
    ("By when should Ms Patel respond?", "Before five today", "Before noon tomorrow", "By Thursday morning", "After the conference", 2, "instruction", "The caller asks for a response before five on the same day."),
])
QUESTIONS += clip_questions("clip03", CLIP_03, [
    ("Which work is still incomplete?", "Testing the payment integration", "Designing the mobile screens", "Choosing a launch date", "Writing the marketing copy", 3, "detail", "The mobile designs are finished, while payment integration testing continues."),
    ("What will happen to the launch date?", "It will remain unchanged", "It will move two days later", "It will be cancelled", "It will move one week earlier", 3, "contrast", "The product keeps its original launch date despite another schedule change."),
    ("What is being delayed?", "The marketing campaign", "The payment tests", "The mobile design", "The product launch", 3, "detail", "The marketing campaign, not the product launch, begins two days later."),
])
QUESTIONS += clip_questions("clip04", CLIP_04, [
    ("Which part of the library closes at six?", "The west wing", "The main reading room", "The computer area", "The entire building", 1, "detail", "Only the west wing closes at six for maintenance."),
    ("How late will the computer area remain open?", "Until nine", "Until six", "Until tomorrow", "Until noon", 1, "detail", "The main reading room and computer area remain open until nine."),
    ("What happens to books due today?", "They may be returned tomorrow without a fine", "They must be returned before six", "Their due date cannot change", "They should be left in the west wing", 3, "instruction", "The announcement grants a one-day extension without a late fee."),
])
QUESTIONS += clip_questions("clip05", CLIP_05, [
    ("What work did the speaker initially expect?", "Data analysis", "Customer support", "Tool design", "Conference planning", 2, "detail", "The speaker expected the role to focus mainly on data analysis."),
    ("What did the speaker actually do in the first year?", "Spoke with customers and documented problems", "Built tools without user contact", "Managed the finance department", "Worked only with datasets", 3, "contrast", "The actual first-year work centered on customer conversations and problem documentation."),
    ("Why was that experience valuable?", "It grounded later designs in real user needs", "It eliminated the need for research", "It confirmed every initial assumption", "It led to a different company", 5, "inference", "Customer exposure helped the speaker replace assumptions with evidence about real needs."),
])
QUESTIONS += clip_questions("clip06", CLIP_06, [
    ("Where should passengers for Seattle go?", "Gate B twelve", "Gate B twenty", "Gate A twelve", "The assistance desk only", 1, "detail", "The announcement assigns flight 274 to gate B twelve."),
    ("When will boarding begin?", "Six forty", "Six twenty", "Seven forty", "Twenty minutes before six", 2, "detail", "Boarding is scheduled for six forty, twenty minutes later than planned."),
    ("Who should approach the desk early?", "Customers requiring assistance", "Only customers without luggage", "All general-boarding passengers", "Passengers changing flights", 2, "instruction", "Passengers needing assistance are invited to speak with staff before general boarding."),
])
QUESTIONS += clip_questions("clip07", CLIP_07, [
    ("When is light rain most likely?", "Before noon", "Late afternoon", "After midnight", "Throughout the evening only", 2, "detail", "The forecast places light rain in the morning before noon."),
    ("How should conditions change in the afternoon?", "They should improve", "They should become stormy", "They should remain unchanged", "Snow should begin", 2, "sequence", "The speaker expects conditions to improve during the afternoon."),
    ("Why should drivers allow extra time?", "Strong evening winds may affect the northern bridge", "The bridge will close all day", "Morning snow will block the coast", "A train is delayed", 3, "inference", "The warning links extra travel time to strong evening winds on the northern bridge."),
])
QUESTIONS += clip_questions("clip08", CLIP_08, [
    ("What was sent yesterday?", "A replacement item", "A refund cheque", "A tracking device", "The damaged charger", 2, "detail", "The message says the replacement item was dispatched yesterday."),
    ("When is the parcel expected?", "Friday", "Tonight", "Yesterday", "Next Monday", 2, "detail", "Although tracking may update tonight, delivery is still expected Friday."),
    ("What should the customer do with the damaged charger?", "Keep it; no return is required", "Return it before Friday", "Send it by express delivery", "Take it to the tracking office", 3, "instruction", "The message explicitly says the damaged charger does not need to be returned."),
])
QUESTIONS += clip_questions("clip09", CLIP_09, [
    ("What does correlation establish?", "That two variables change together", "That one variable definitely causes the other", "That no third factor exists", "That the direction of influence is known", 4, "main-idea", "Correlation establishes co-variation, not a causal mechanism."),
    ("Why is careful experimental design necessary?", "To distinguish causal explanations from alternatives", "To guarantee every correlation is strong", "To remove the need for measurement", "To reverse every relationship", 5, "inference", "Experiments help evaluate third variables and direction of causation."),
])
QUESTIONS += clip_questions("clip10", CLIP_10, [
    ("What was the garden's unexpected main impact?", "Stronger relationships among neighbours", "A much larger vegetable harvest", "Lower tool prices", "Professional farming jobs", 4, "main-idea", "The speaker identifies social connection as the greatest and unexpected impact."),
    ("What behaviour demonstrates this impact?", "Neighbours began sharing tools and advice", "Neighbours stopped growing vegetables", "The garden hired outside workers", "The harvest was sold abroad", 3, "evidence", "Sharing tools and advice is the evidence of stronger local relationships."),
])
QUESTIONS += clip_questions("clip11", CLIP_11, [
    ("What must be ready by Tuesday?", "A working demonstration", "The final polished product", "All export features", "Every visual refinement", 3, "detail", "The client expects a functional demo rather than the finished product."),
    ("What should the team prioritise?", "Login and reporting core paths", "Export and visual polish", "Marketing and billing", "Documentation only", 5, "priority", "The speaker explicitly prioritises login and reporting, while deferring export and polish."),
])
QUESTIONS += clip_questions("clip12", CLIP_12, [
    ("When can efficiency targets be helpful?", "When they measure outcomes people genuinely value", "Whenever they count visible activity", "When invisible work is ignored", "Only when staff choose the easiest metric", 4, "condition", "Targets help when the metric remains aligned with valued outcomes."),
    ("What risk does the speaker identify?", "People may optimise the metric instead of the real goal", "Targets always reduce performance", "Important work is always easy to count", "Metrics prevent any staff action", 5, "main-idea", "The warning concerns proxy optimisation: improving what is counted while neglecting the true objective."),
])
