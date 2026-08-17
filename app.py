import streamlit as st
import pandas as pd
import altair as alt
from evaluation import (
    load_data,
    compute_achievement_rate,
    qualitative_check,
    validate_difficulty_change,
    analyze_case,
)

st.set_page_config(page_title="FairTrace - HR Evaluation PoC", layout="wide")

st.title("FairTrace — 人事評価可視化 PoC")

# Load data
DATA_DIR = "data"
employees, goals, difficulties, contributions = load_data(DATA_DIR)

# Sidebar: select employee and goal
with st.sidebar:
    st.header("選択")
    emp_id = st.selectbox("社員", employees["employee_id"].tolist(), format_func=lambda x: f"{x} - {employees.set_index('employee_id').loc[x,'name']}")
    emp_goals = goals[goals["employee_id"] == emp_id]
    goal_id = st.selectbox("目標", emp_goals["goal_id"].tolist(), format_func=lambda x: f"{x} - {emp_goals.set_index('goal_id').loc[x,'title']}")

# Fetch selected records
emp = employees[employees["employee_id"] == emp_id].iloc[0]
goal = goals[goals["goal_id"] == goal_id].iloc[0]
proj = difficulties[difficulties["goal_id"] == goal_id].iloc[0]
contribs = contributions[contributions["goal_id"] == goal_id]

st.header(f"{emp['name']} — {goal['title']}")

# Left column: quantitative / qualitative
left, mid, right = st.columns([3,2,3])

with left:
    st.subheader("成果 (成果と定量・定性の表示)")
    if goal['goal_type'] == 'quantitative' or goal['goal_type']=='hybrid':
        st.markdown("**定量目標**")
        baseline = goal['baseline_value']
        target = goal['target_value']
        actual = goal['actual_value']
        unit = goal['unit']
        direction = goal['direction']
        rate = compute_achievement_rate(baseline, target, actual, direction)
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Baseline: {baseline} {unit}")
            st.write(f"Target: {target} {unit}")
            st.write(f"Actual: {actual} {unit}")
            if rate is None:
                st.warning("達成率を計算できません（基準値と目標値が同じ、未入力、または不十分なデータ）。")
            else:
                st.metric("達成率", f"{rate:.1f}%")
        with col2:
            df = pd.DataFrame({
                'value': [baseline, target, actual],
                'label': ['baseline','target','actual']
            })
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('value:Q', title=f'値 ({unit})'),
                y=alt.Y('label:N', sort=['baseline','target','actual'])
            )
            st.altair_chart(chart, use_container_width=True)
    if goal['goal_type'] == 'qualitative' or goal['goal_type']=='hybrid':
        st.markdown("**定性目標 (STAR)**")
        st.write("Situation:" , goal.get('situation',''))
        st.write("Task:" , goal.get('task',''))
        st.write("Action:" , goal.get('action',''))
        st.write("Result:" , goal.get('result',''))
        st.write("Evidence:" , goal.get('evidence',''))
        st.write("Reviewer note:" , goal.get('reviewer_note',''))
        ok, specificity = qualitative_check(goal.get('evidence',''))
        if not ok:
            st.warning("Evidence が不足しています — 具体的な根拠を追加してください。")
        else:
            st.success(f"Evidence が存在します（具体性スコア: {specificity}）")

with mid:
    st.subheader("難易度 (案件評価)")
    st.write("Planned score と Actual score の比較")
    axes = [
        'technical_uncertainty','novelty','stakeholder_complexity','impact_scope','responsibility_risk',
        'constraints','problem_discovery','execution_complexity','sustainability','reproducibility','ownership','unexpected_response'
    ]
    planned = [proj[f'planned_{a}'] for a in axes]
    actuals = [proj[f'actual_{a}'] for a in axes]
    df_axes = pd.DataFrame({
        'axis': axes,
        'planned': planned,
        'actual': actuals,
        'diff': [a - p for p,a in zip(planned, actuals)]
    })
    # Show top 3 hardest actual
    top3 = df_axes.sort_values('actual', ascending=False).head(3)
    st.write("特に難易度が高い上位3項目")
    st.table(top3[['axis','actual']].rename(columns={'axis':'項目','actual':'実績スコア'}))
    # Bar chart comparison
    df_long = df_axes.melt(id_vars=['axis'], value_vars=['planned','actual'], var_name='when', value_name='score')
    chart = alt.Chart(df_long).mark_bar().encode(
        x=alt.X('score:Q'),
        y=alt.Y('axis:N', sort=axes),
        color='when:N'
    )
    st.altair_chart(chart, use_container_width=True)
    st.write("変更理由:")
    st.write(proj.get('change_reason','(なし)'))
    if proj.get('planned_mean') != proj.get('actual_mean') and (not proj.get('change_reason') or not proj.get('change_evidence')):
        st.error("完了時にスコアが変更されています。change_reason と Evidence が必須です。")

with right:
    st.subheader("統合評価サマリ")
    summary = analyze_case(goal, proj, contribs)
    st.write("成果サマリ:")
    st.write(summary['outcome'])
    st.write("難易度サマリ:")
    st.write(summary['difficulty'])
    st.write("本人の貢献:")
    st.write(summary['contribution'])
    st.write("組織的価値:")
    st.write(summary['organizational_value'])

st.markdown("---")
st.caption("注意: 本システムは評価の参考材料と根拠を提示する支援ツールです。最終評価は人が決定してください。")
