from calendar import monthrange
from datetime import UTC, date, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.child import Child
from app.models.development import ChildDevelopmentObservation, ChildDevelopmentObservationResponse, DevelopmentIndicator
from app.models.role import Role
from app.models.user import User
from app.schemas.development import ObservationCreate, ObservationUpdate
from app.services.permission_service import has_permission


CATEGORIES = [
    "Personal Hygiene & Cleanliness", "Discipline & Responsibility", "Social Behavior", "Emotional Wellbeing",
    "Confidence & Communication", "Learning Behavior", "Talent & Interests", "Physical Activity & Sports",
    "Digital Behavior & Screen Awareness", "Safety & Risk Indicators", "Spiritual / Moral Development",
    "Career / Field Suitability Indicators", "Support Needs", "Positive Strengths",
]
RATING = ["1 Poor", "2 Needs Improvement", "3 Satisfactory", "4 Good", "5 Excellent"]
SAFE_DESCRIPTION = "Structured welfare observation for support and guidance. This is not a medical or psychological assessment."
INPUT_TYPE_ALIASES = {"rating": "rating_1_to_5"}


RAW_INDICATORS: list[tuple[str, str, str, list[str] | None, bool]] = [
("Personal Hygiene & Cleanliness","Personal cleanliness","rating_1_to_5",RATING,False),("Personal Hygiene & Cleanliness","Clothes neatness","rating_1_to_5",RATING,False),("Personal Hygiene & Cleanliness","Regular bathing / hygiene routine","dropdown",["Regular","Sometimes irregular","Often irregular","Needs supervision"],False),("Personal Hygiene & Cleanliness","Dental hygiene","dropdown",["Good","Needs reminder","Needs support","Not observed"],False),("Personal Hygiene & Cleanliness","Bed/locker cleanliness","rating_1_to_5",RATING,False),("Personal Hygiene & Cleanliness","Self-care independence","dropdown",["Independent","Needs occasional help","Needs regular help","Needs close supervision"],False),
("Discipline & Responsibility","Punctuality","rating_1_to_5",RATING,False),("Discipline & Responsibility","Follows daily routine","dropdown",["Consistently","Usually","Sometimes","Rarely"],False),("Discipline & Responsibility","Follows instructions","rating_1_to_5",RATING,False),("Discipline & Responsibility","Completes assigned tasks","dropdown",["Always","Usually","Sometimes","Rarely"],False),("Discipline & Responsibility","Respect for rules","rating_1_to_5",RATING,False),("Discipline & Responsibility","Responsibility for personal belongings","rating_1_to_5",RATING,False),("Discipline & Responsibility","Honesty / truthfulness","dropdown",["Consistently honest","Usually honest","Needs guidance","Concern observed"],False),
("Social Behavior","Interaction with peers","dropdown",["Friendly","Cooperative","Reserved","Often isolated","Often conflicts"],False),("Social Behavior","Group participation","dropdown",["Active","Moderate","Low","Avoids group activities"],False),("Social Behavior","Cooperation","rating_1_to_5",RATING,False),("Social Behavior","Empathy toward others","rating_1_to_5",RATING,False),("Social Behavior","Sharing and helping behavior","rating_1_to_5",RATING,False),("Social Behavior","Conflict handling","dropdown",["Handles calmly","Needs guidance","Gets angry quickly","Avoids conflict","Escalates conflict"],False),("Social Behavior","Leadership tendency","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Social Behavior","Bullying risk indicator","dropdown",["No concern observed","Minor concern","Repeated concern","Needs immediate review"],True),("Social Behavior","Being bullied / victimization concern","dropdown",["No concern observed","Possible concern","Repeated concern","Needs immediate review"],True),
("Emotional Wellbeing","General mood","dropdown",["Generally happy","Calm","Sad/withdrawn","Anxious","Irritable","Variable"],True),("Emotional Wellbeing","Anger control","dropdown",["Good","Needs reminders","Frequent difficulty","Needs counselor review"],True),("Emotional Wellbeing","Fearfulness / insecurity","dropdown",["No concern","Mild","Moderate","High"],True),("Emotional Wellbeing","Emotional expression","dropdown",["Expresses appropriately","Reserved","Overreacts","Does not express feelings"],True),("Emotional Wellbeing","Coping with stress","dropdown",["Good","Needs support","Struggles often","Needs counselor review"],True),("Emotional Wellbeing","Motivation level","rating_1_to_5",RATING,False),("Emotional Wellbeing","Self-confidence","rating_1_to_5",RATING,False),("Emotional Wellbeing","Sudden behavior change observed","yes_no",None,True),
("Confidence & Communication","Shyness level","dropdown",["Very shy","Somewhat shy","Balanced","Confident","Very bold"],False),("Confidence & Communication","Boldness / initiative","rating_1_to_5",RATING,False),("Confidence & Communication","Public speaking comfort","dropdown",["Comfortable","Developing","Avoids","Not observed"],False),("Confidence & Communication","Communication clarity","rating_1_to_5",RATING,False),("Confidence & Communication","Asks questions","dropdown",["Frequently","Sometimes","Rarely","Never observed"],False),("Confidence & Communication","Expresses needs clearly","rating_1_to_5",RATING,False),("Confidence & Communication","Respectful speech","rating_1_to_5",RATING,False),
("Learning Behavior","Attention span","dropdown",["Strong","Good","Average","Short","Very short"],False),("Learning Behavior","Curiosity","rating_1_to_5",RATING,False),("Learning Behavior","Memory / recall","rating_1_to_5",RATING,False),("Learning Behavior","Problem solving","rating_1_to_5",RATING,False),("Learning Behavior","Reading interest","rating_1_to_5",RATING,False),("Learning Behavior","Mathematics interest","rating_1_to_5",RATING,False),("Learning Behavior","Science interest","rating_1_to_5",RATING,False),("Learning Behavior","Computer / IT interest","rating_1_to_5",RATING,False),("Learning Behavior","Homework/study consistency","dropdown",["Consistent","Usually","Irregular","Needs support"],False),("Learning Behavior","Classroom behavior","dropdown",["Excellent","Good","Average","Disruptive","Withdrawn","Not applicable"],False),
("Talent & Interests","Drawing / art interest","rating_1_to_5",RATING,False),("Talent & Interests","Writing / storytelling interest","rating_1_to_5",RATING,False),("Talent & Interests","Sports interest","rating_1_to_5",RATING,False),("Talent & Interests","Technical / hands-on skill interest","rating_1_to_5",RATING,False),("Talent & Interests","Computer skill interest","rating_1_to_5",RATING,False),("Talent & Interests","Religious studies interest","rating_1_to_5",RATING,False),("Talent & Interests","Leadership activities interest","rating_1_to_5",RATING,False),("Talent & Interests","Helping others / social work interest","rating_1_to_5",RATING,False),("Talent & Interests","Business / entrepreneurship interest","rating_1_to_5",RATING,False),("Talent & Interests","Public speaking / debate interest","rating_1_to_5",RATING,False),
("Physical Activity & Sports","Physical activity level","dropdown",["High","Moderate","Low","Very low"],False),("Physical Activity & Sports","Team sports participation","dropdown",["Active","Sometimes","Avoids","Not available"],False),("Physical Activity & Sports","Fine motor skills / handwork","rating_1_to_5",RATING,False),("Physical Activity & Sports","Energy level","dropdown",["Normal","High","Low","Variable"],False),("Physical Activity & Sports","Fatigue concern","dropdown",["No concern","Occasional","Frequent","Needs medical review"],True),
("Digital Behavior & Screen Awareness","Screen time concern","dropdown",["No concern","Mild concern","Moderate concern","High concern","Not applicable"],True),("Digital Behavior & Screen Awareness","Internet safety awareness","dropdown",["Good","Needs guidance","Low awareness","Not applicable"],False),("Digital Behavior & Screen Awareness","Mobile/game overuse concern","dropdown",["No concern","Mild","Moderate","High","Not applicable"],True),("Digital Behavior & Screen Awareness","Cyberbullying concern","dropdown",["No concern observed","Possible concern","Repeated concern","Needs immediate review"],True),
("Safety & Risk Indicators","Repeated aggression","dropdown",["No concern","Occasional","Repeated","Needs immediate review"],True),("Safety & Risk Indicators","Self-harm talk or gesture observed","yes_no",None,True),("Safety & Risk Indicators","Running away / absconding risk","dropdown",["No concern","Mild concern","Moderate concern","High concern"],True),("Safety & Risk Indicators","Substance use concern","dropdown",["No concern","Possible concern","Confirmed concern","Needs immediate review"],True),("Safety & Risk Indicators","Unsafe friendship/group influence","dropdown",["No concern","Mild concern","Moderate concern","High concern"],True),("Safety & Risk Indicators","Sleep difficulty observed","dropdown",["No concern","Occasional","Frequent","Needs review"],True),("Safety & Risk Indicators","Appetite/eating concern","dropdown",["No concern","Occasional","Frequent","Needs review"],True),
("Spiritual / Moral Development","Participation in moral/religious activities","dropdown",["Regular","Sometimes","Rarely","Not applicable"],False),("Spiritual / Moral Development","Respect for elders","rating_1_to_5",RATING,False),("Spiritual / Moral Development","Sense of responsibility","rating_1_to_5",RATING,False),("Spiritual / Moral Development","Helping weaker children","rating_1_to_5",RATING,False),("Spiritual / Moral Development","Truthfulness and trustworthiness","rating_1_to_5",RATING,False),
("Career / Field Suitability Indicators","Academic studies suitability","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Career / Field Suitability Indicators","Technical/vocational suitability","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Career / Field Suitability Indicators","Sports suitability","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Career / Field Suitability Indicators","Arts/design suitability","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Career / Field Suitability Indicators","IT/computer suitability","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Career / Field Suitability Indicators","Religious education suitability","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Career / Field Suitability Indicators","Leadership/social work suitability","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Career / Field Suitability Indicators","Business/entrepreneurship suitability","dropdown",["Strong","Moderate","Emerging","Not observed"],False),("Career / Field Suitability Indicators","Healthcare/caregiving interest","dropdown",["Strong","Moderate","Emerging","Not observed"],False),
("Support Needs","Needs academic support","checkbox",None,False),("Support Needs","Needs hygiene support","checkbox",None,False),("Support Needs","Needs counseling support","checkbox",None,True),("Support Needs","Needs medical review","checkbox",None,True),("Support Needs","Needs speech/communication support","checkbox",None,False),("Support Needs","Needs confidence-building activities","checkbox",None,False),("Support Needs","Needs sports/physical activity encouragement","checkbox",None,False),("Support Needs","Needs close supervision","checkbox",None,True),("Support Needs","Needs family/guardian contact review","checkbox",None,True),
("Positive Strengths","Kindness observed","checkbox",None,False),("Positive Strengths","Leadership observed","checkbox",None,False),("Positive Strengths","Creativity observed","checkbox",None,False),("Positive Strengths","Strong discipline observed","checkbox",None,False),("Positive Strengths","Helping others observed","checkbox",None,False),("Positive Strengths","Academic improvement observed","checkbox",None,False),("Positive Strengths","Sports improvement observed","checkbox",None,False),("Positive Strengths","Confidence improvement observed","checkbox",None,False),("Positive Strengths","Communication improvement observed","checkbox",None,False),
]


URGENT_TEXT = {"Needs immediate review", "High concern", "Confirmed concern", "Repeated", "High"}
SELF_HARM = "Self-harm talk or gesture observed"


def code_for(index: int, name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in name.upper()).strip("_")
    return f"DEV_{index:03d}_{cleaned[:40]}"


def normalize_indicator_input_type(value: str | None) -> str | None:
    return INPUT_TYPE_ALIASES.get(value, value)


def normalize_indicator_record(indicator: DevelopmentIndicator | None) -> DevelopmentIndicator | None:
    if indicator is not None:
        indicator.input_type = normalize_indicator_input_type(indicator.input_type)
    return indicator


def normalize_observation_indicators(item: ChildDevelopmentObservation) -> ChildDevelopmentObservation:
    for response in item.responses:
        normalize_indicator_record(response.indicator)
    return item


def seed_development_indicators(db: Session) -> None:
    existing_items = db.scalars(select(DevelopmentIndicator)).all()
    existing_by_code = {item.indicator_code: item for item in existing_items}
    for item in existing_items:
        normalize_indicator_record(item)
    for index, (category, name, input_type, options, sensitive) in enumerate(RAW_INDICATORS, start=1):
        code = code_for(index, name)
        normalized_input_type = normalize_indicator_input_type(input_type)
        existing = existing_by_code.get(code)
        if existing is None:
            db.add(DevelopmentIndicator(indicator_code=code, indicator_name=name, category=category, description=SAFE_DESCRIPTION, input_type=normalized_input_type, options_json=options, is_required=False, is_active=True, is_sensitive=sensitive, sort_order=index))
        else:
            existing.input_type = normalize_indicator_input_type(existing.input_type)
    db.flush()


def roles(user: User) -> set[str]:
    return {role.name for role in user.roles}


def can_view_sensitive(user: User) -> bool:
    return has_permission(user, "development.sensitive_notes.view") or bool(roles(user) & {"Admin", "Manager", "Counselor"})


def clean_observation(item: ChildDevelopmentObservation, user: User) -> ChildDevelopmentObservation:
    normalize_observation_indicators(item)
    if not can_view_sensitive(user):
        item.private_notes = None
        item.responses = [response for response in item.responses if not response.indicator or not response.indicator.is_sensitive]
    return item


def detect_urgent(db: Session, responses: list[Any]) -> bool:
    indicators = {item.id: item for item in db.scalars(select(DevelopmentIndicator).where(DevelopmentIndicator.id.in_([r.indicator_id for r in responses] or [-1]))).all()}
    for response in responses:
        indicator = indicators.get(response.indicator_id)
        values = [response.value_text, response.note]
        if response.value_boolean is True and indicator and indicator.indicator_name == SELF_HARM:
            return True
        if any(value in URGENT_TEXT for value in values if value):
            return True
    return False


def validate_responses(db: Session, responses: list[Any]) -> list[DevelopmentIndicator]:
    ids = [item.indicator_id for item in responses]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Duplicate indicator response in observation")
    indicators = list(db.scalars(select(DevelopmentIndicator).where(DevelopmentIndicator.id.in_(ids))).all()) if ids else []
    if len(indicators) != len(ids):
        raise HTTPException(422, "Unknown development indicator")
    return indicators


def apply_responses(db: Session, observation: ChildDevelopmentObservation, responses: list[Any]) -> None:
    validate_responses(db, responses)
    observation.responses.clear()
    for payload in responses:
        observation.responses.append(ChildDevelopmentObservationResponse(**payload.model_dump()))


def create_observation(db: Session, payload: ObservationCreate, user: User) -> ChildDevelopmentObservation:
    if db.get(Child, payload.child_id) is None:
        raise HTTPException(404, "Child not found")
    if payload.observation_frequency == "Monthly":
        existing = db.scalar(select(ChildDevelopmentObservation.id).where(ChildDevelopmentObservation.child_id == payload.child_id, ChildDevelopmentObservation.observation_frequency == "Monthly", extract("year", ChildDevelopmentObservation.observation_date) == payload.observation_date.year, extract("month", ChildDevelopmentObservation.observation_date) == payload.observation_date.month, ChildDevelopmentObservation.review_status != "Archived").limit(1))
        if existing:
            raise HTTPException(409, "Monthly observation already exists for this child and month")
    urgent = detect_urgent(db, payload.responses)
    if urgent and not payload.recommended_support:
        raise HTTPException(422, "Urgent observations require recommended support and counselor/manager review")
    item = ChildDevelopmentObservation(**payload.model_dump(exclude={"responses"}), observed_by_user_id=user.id, created_by_user_id=user.id, updated_by_user_id=user.id, urgent_flag=urgent)
    db.add(item)
    db.flush()
    apply_responses(db, item, payload.responses)
    return item


def update_observation(db: Session, item: ChildDevelopmentObservation, payload: ObservationUpdate, user: User) -> ChildDevelopmentObservation:
    if item.review_status in {"Closed", "Archived"} and not has_permission(user, "development.review"):
        raise HTTPException(409, "Closed or archived observations cannot be edited")
    data = payload.model_dump(exclude_unset=True, exclude={"responses"})
    for key, value in data.items():
        setattr(item, key, value)
    if payload.responses is not None:
        urgent = detect_urgent(db, payload.responses)
        if urgent and not (payload.recommended_support or item.recommended_support):
            raise HTTPException(422, "Urgent observations require recommended support and counselor/manager review")
        item.urgent_flag = urgent
        apply_responses(db, item, payload.responses)
    item.updated_by_user_id = user.id
    item.updated_at = datetime.now(UTC)
    return item


def development_summary(db: Session, child_id: int, user: User) -> dict[str, Any]:
    observations = list(db.scalars(select(ChildDevelopmentObservation).options(selectinload(ChildDevelopmentObservation.responses).selectinload(ChildDevelopmentObservationResponse.indicator)).where(ChildDevelopmentObservation.child_id == child_id, ChildDevelopmentObservation.review_status != "Archived").order_by(ChildDevelopmentObservation.observation_date.desc())).all())
    latest = observations[0] if observations else None
    today = date.today()
    month_reviewed = any(item.observation_frequency == "Monthly" and item.observation_date.year == today.year and item.observation_date.month == today.month for item in observations)
    strengths: list[str] = []
    support: list[str] = []
    talents: list[str] = []
    risks: list[str] = []
    latest_support = latest.recommended_support if latest and latest.recommended_support else "Not recorded"
    for item in observations[:3]:
        if item.urgent_flag:
            risks.append("Follow-up recommended")
        for response in item.responses:
            indicator = response.indicator
            if not indicator or (indicator.is_sensitive and not can_view_sensitive(user)):
                continue
            positive = response.value_boolean is True or response.value_number in (4, 5) or response.value_text in {"Strong", "High", "Good", "Excellent", "Active"}
            if "Positive Strengths" in indicator.category and positive:
                strengths.append(indicator.indicator_name)
            if "Support Needs" in indicator.category and response.value_boolean is True:
                support.append(indicator.indicator_name)
            if ("Talent" in indicator.category or "Suitability" in indicator.category) and positive:
                talents.append(indicator.indicator_name)
            if item.urgent_flag and indicator.is_sensitive:
                risks.append(indicator.indicator_name)
    strengths = sorted(set(strengths))[:8]
    support = sorted(set(support))[:8]
    talents = sorted(set(talents))[:8]
    risks = sorted(set(risks))[:8]
    if latest is None:
        summary_text = "No development observation has been recorded yet."
    else:
        strength_text = ", ".join(strengths[:3]) if strengths else "current observed strengths"
        support_text = ", ".join(support[:3]) if support else "continued routine support"
        talent_text = ", ".join(talents[:3]) if talents else "areas of interest to observe further"
        summary_text = f"Latest observations show strengths in {strength_text}. The child may benefit from {support_text}. Possible areas of interest include {talent_text}. Review is recommended as scheduled."
    return {
        "child_id": child_id,
        "latest_observation_date": latest.observation_date if latest else None,
        "review_status": latest.review_status if latest else "Not recorded",
        "monthly_review_status": "Reviewed this month" if month_reviewed else "Monthly review pending",
        "positive_strengths": strengths,
        "strongest_positive_strengths": strengths,
        "support_needs": support,
        "possible_areas_of_interest": talents,
        "talent_indicators": talents,
        "recommended_support": latest_support,
        "risk_flags_requiring_review": risks,
        "next_review_date": latest.next_review_date if latest else None,
        "summary_text": summary_text,
        "urgent_flag_safe_summary": "Follow-up required" if risks else "No urgent follow-up flag in visible summary",
        "observation_count": len(observations),
    }


def missing_monthly_rows(db: Session, month: int, year: int, district: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    reviewed = set(db.scalars(select(ChildDevelopmentObservation.child_id).where(ChildDevelopmentObservation.observation_frequency == "Monthly", ChildDevelopmentObservation.observation_date.between(start, end), ChildDevelopmentObservation.review_status != "Archived")).all())
    latest_dates = dict(db.execute(select(ChildDevelopmentObservation.child_id, func.max(ChildDevelopmentObservation.observation_date)).where(ChildDevelopmentObservation.review_status != "Archived").group_by(ChildDevelopmentObservation.child_id)).all())
    child_query = select(Child).order_by(Child.full_name)
    if district:
        child_query = child_query.where(Child.district.ilike(f"%{district}%"))
    if status:
        child_query = child_query.where(Child.status == status)
    children = db.scalars(child_query).all()
    return [
        {
            "id": child.id,
            "child_id": child.id,
            "child_code": child.child_id,
            "full_name": child.full_name,
            "district": child.district,
            "status": child.status,
            "last_observation_date": latest_dates.get(child.id),
            "month": f"{year}-{month:02d}",
        }
        for child in children
        if child.id not in reviewed
    ]
