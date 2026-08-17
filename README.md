# FairTrace

FairTrace は人事評価で見落とされがちな貢献を可視化するプロトタイプ（PoC）です。

## 追加された機能

- 目標タイプを区別: quantitative / qualitative / hybrid
- 定量目標: baseline, target, actual, unit, direction (increase/decrease), measurement source, review schedule, sustained months
- 定性目標: STAR 形式 (Situation, Task, Action, Result) と Evidence、Reviewer note。Evidence の有無と具体性を確認します。
- 案件難易度: 12軸（各1-5）を planned / actual として保存。変更がある場合は change_reason と change_evidence が必須。
- 難易度の可視化: Altair を使った比較チャート、上位3項目の表示
- 統合評価画面: 成果、難易度、本人の貢献、組織的価値 を一画面で表示

## データ定義 (data/*.csv)

- employees.csv: employee_id, name, department
- goals.csv: goal_id, employee_id, title, goal_type, baseline_value, target_value, actual_value, unit, direction, measurement_source, review_schedule, sustained_months, situation, task, action, result, evidence, reviewer_note
- difficulties.csv: goal_id, change_reason, change_evidence, planned_* (12 axes), actual_* (12 axes), actual_standardization, actual_reusability
- contributions.csv: contribution_id, goal_id, contribution_date, evaluation_date, moved_flag, later_impact

## 起動方法

1. 依存関係をインストール

pip install -r requirements.txt

requirements.txt には streamlit, pandas, altair, python-dateutil が含まれます。

2. サービス起動

streamlit run app.py

3. テスト

python -m unittest discover -s tests -v

## 判定ルール・制約

- 計算は参考値のみを提供します。最終評価や自動加点は行いません。
- 性別、年齢などの属性は評価スコアの加点・減点に使用しません。
- Evidence は存在の有無と簡易的な具体性スコアで評価します（長さに基づくヒューリスティック）。
- 難易度の平均だけで評価を確定しません。変更時は理由と証拠が必要です。

