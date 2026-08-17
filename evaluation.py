import os
import pandas as pd
from datetime import datetime
from dateutil import relativedelta

# Core evaluation logic for FairTrace PoC

AXES = [
    'technical_uncertainty','novelty','stakeholder_complexity','impact_scope','responsibility_risk',
    'constraints','problem_discovery','execution_complexity','sustainability','reproducibility','ownership','unexpected_response'
]


def load_data(data_dir='data'):
    employees = pd.read_csv(os.path.join(data_dir, 'employees.csv'))
    goals = pd.read_csv(os.path.join(data_dir, 'goals.csv'))
    difficulties = pd.read_csv(os.path.join(data_dir, 'difficulties.csv'))
    contributions = pd.read_csv(os.path.join(data_dir, 'contributions.csv'))
    return employees, goals, difficulties, contributions


def compute_achievement_rate(baseline, target, actual, direction='increase'):
    """
    Compute achievement rate as percentage (0-100+). Return None when cannot compute.
    direction: 'increase' or 'decrease'
    """
    try:
        if pd.isna(baseline) or pd.isna(target) or pd.isna(actual):
            return None
        baseline = float(baseline)
        target = float(target)
        actual = float(actual)
    except Exception:
        return None

    # If baseline == target, cannot compute meaningful progress
    if abs(target - baseline) < 1e-9:
        return None

    if direction == 'increase' or direction == 'increasing':
        denom = target - baseline
        if abs(denom) < 1e-12:
            return None
        rate = (actual - baseline) / denom * 100.0
    else:
        # decrease goal: e.g., baseline 100, target 50, actual 80 -> (100-80)/(100-50)=20/50=40%
        denom = baseline - target
        if abs(denom) < 1e-12:
            return None
        rate = (baseline - actual) / denom * 100.0

    return rate


def qualitative_check(evidence_text):
    """
    Check presence and basic specificity of qualitative evidence.
    Returns (has_evidence: bool, specificity_score: float)
    Specificity is heuristic: length and presence of verbs/nouns; but keep simple.
    """
    if evidence_text is None:
        return (False, 0.0)
    s = str(evidence_text).strip()
    if s == '':
        return (False, 0.0)
    # naive specificity: length-based (but not used as score elsewhere)
    score = min(1.0, len(s) / 200.0)
    return (True, score)


def validate_difficulty_change(planned_scores: dict, actual_scores: dict, change_reason: str, change_evidence: str):
    """
    Validate that if there is any change between planned and actual scores, change_reason and evidence are provided.
    Returns True if valid, False if invalid (i.e., changed but missing reason/evidence).
    """
    for a in AXES:
        p = planned_scores.get(a)
        q = actual_scores.get(a)
        if p is None or q is None:
            continue
        if abs(float(p) - float(q)) > 1e-9:
            if not change_reason or str(change_reason).strip() == '':
                return False
            if not change_evidence or str(change_evidence).strip() == '':
                return False
    return True


def months_between(d1, d2):
    if pd.isna(d1) or pd.isna(d2):
        return None
    try:
        a = pd.to_datetime(d1)
        b = pd.to_datetime(d2)
        rd = relativedelta.relativedelta(b, a)
        return rd.years * 12 + rd.months
    except Exception:
        return None


def time_lag_check(contribution_date, evaluation_date, threshold_months=3):
    m = months_between(contribution_date, evaluation_date)
    if m is None:
        return False
    return m > threshold_months


def movement_check(moved_flag):
    # moved_flag is boolean indicating whether person changed department before evaluation
    return bool(moved_flag)


def ripple_effect_check(has_later_impact):
    # has_later_impact: boolean
    return bool(has_later_impact)


def analyze_case(goal_row, difficulty_row, contributions_df):
    """
    Build integrated summary for UI. Non-deterministic textual summaries simplified.
    """
    outcome = {}
    if goal_row['goal_type'] in ['quantitative','hybrid']:
        rate = compute_achievement_rate(goal_row['baseline_value'], goal_row['target_value'], goal_row['actual_value'], goal_row['direction'])
        outcome['achievement_rate'] = rate
        outcome['sustained_months'] = goal_row.get('sustained_months')
    if goal_row['goal_type'] in ['qualitative','hybrid']:
        ok, spec = qualitative_check(goal_row.get('evidence',''))
        outcome['qual_evidence_present'] = ok
        outcome['qual_specificity'] = spec

    difficulty = {}
    planned = {a: difficulty_row.get(f'planned_{a}') for a in AXES}
    actual = {a: difficulty_row.get(f'actual_{a}') for a in AXES}
    difficulty['planned_mean'] = sum([float(v) for v in planned.values()]) / len(AXES)
    difficulty['actual_mean'] = sum([float(v) for v in actual.values()]) / len(AXES)
    difficulty['validated_change'] = validate_difficulty_change(planned, actual, difficulty_row.get('change_reason',''), difficulty_row.get('change_evidence',''))

    contribution = {}
    # summarize contributions
    contribution['num_events'] = len(contributions_df)
    contribution['time_lag_flags'] = contributions_df.apply(lambda r: time_lag_check(r.get('contribution_date'), r.get('evaluation_date')), axis=1).tolist()
    contribution['moved_flags'] = contributions_df['moved_flag'].tolist()
    contribution['ripple_flags'] = contributions_df['later_impact'].tolist()

    organizational_value = {
        'standardization': difficulty_row.get('actual_standardization',''),
        'reusability': difficulty_row.get('actual_reusability',''),
    }

    return {
        'outcome': outcome,
        'difficulty': difficulty,
        'contribution': contribution,
        'organizational_value': organizational_value
    }
