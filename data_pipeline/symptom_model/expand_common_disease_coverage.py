from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
CASES_PATH = DATA_DIR / "naver_kin_symptom_cases.csv"
QUESTIONS_PATH = DATA_DIR / "disease_question_map.csv"

CASE_COLUMNS = [
    "case_id",
    "source_url",
    "raw_text",
    "cleaned_text",
    "symptom_keywords",
    "symptom_group",
    "department",
    "suspected_disease",
    "severity_level",
]

QUESTION_COLUMNS = [
    "question_id",
    "suspected_disease",
    "symptom_group",
    "question",
    "positive_keywords",
    "risk_score",
    "required_resource_code",
    "importance",
]

COMMON_DISEASES = [
    ("감기", "respiratory", "이비인후과", 1, "목아픔;콧물;기침;미열;재채기", "목이 아프고 콧물이 나며 기침이 있습니다."),
    ("독감", "respiratory", "호흡기내과", 3, "39도;고열;몸살;기침;근육통", "39도 고열과 몸살, 기침이 심합니다."),
    ("코로나19", "respiratory", "호흡기내과", 3, "열;기침;후각저하;미각저하;인후통", "열이 나고 기침이 있으며 냄새를 잘 못 맡겠습니다."),
    ("편도염", "respiratory", "이비인후과", 2, "목통증;침삼킴곤란;편도;고열;인후통", "목이 너무 아프고 침 삼키기 힘듭니다."),
    ("기관지염", "respiratory", "호흡기내과", 2, "기침;가래;2주;기관지;흉부불편", "기침이 2주째 계속되고 가래가 나옵니다."),
    ("폐렴", "respiratory", "호흡기내과", 4, "고열;기침;가슴통증;가래;숨참", "고열이 있고 기침할 때 가슴이 아픕니다."),
    ("천식", "respiratory", "호흡기내과", 4, "숨참;쌕쌕;천명;호흡곤란;기침", "숨이 차고 쌕쌕거리는 소리가 납니다."),
    ("알레르기 비염", "respiratory", "이비인후과", 1, "재채기;콧물;코막힘;가려움;알레르기", "재채기와 콧물이 계속 납니다."),
    ("중이염", "ent", "이비인후과", 2, "귀통증;청력저하;귀먹먹;발열;이통", "귀가 아프고 잘 들리지 않습니다."),
    ("결막염", "eye", "안과", 1, "눈충혈;눈곱;가려움;눈물;결막", "눈이 충혈되고 눈곱이 많이 낍니다."),
    ("편두통", "neuro", "신경과", 2, "한쪽머리;욱신;빛;구역;두통", "한쪽 머리가 욱신거리고 빛을 보면 심해집니다."),
    ("긴장성 두통", "neuro", "신경과", 1, "조이는두통;띠두른느낌;압박감;스트레스;목어깨", "머리가 띠를 두른 것처럼 조여옵니다."),
    ("뇌수막염", "neuro", "응급의학과", 5, "고열;심한두통;목뻣뻣;구토;의식저하", "고열과 심한 두통, 목이 뻣뻣합니다."),
    ("치매 초기", "neuro", "신경과", 1, "기억저하;건망증;최근기억;길잃음;인지저하", "최근 기억이 자꾸 나지 않습니다."),
    ("공황장애", "psychiatric", "정신건강의학과", 2, "심장두근;숨막힘;불안;공포;발작", "갑자기 심장이 뛰고 숨쉬기 힘들어졌습니다."),
    ("우울증", "psychiatric", "정신건강의학과", 2, "우울;무기력;흥미저하;식욕변화;수면변화", "아무것도 하기 싫고 계속 우울합니다."),
    ("불면증", "psychiatric", "정신건강의학과", 1, "잠들기어려움;자주깸;수면부족;불면;피로", "잠들기 어렵고 자주 깹니다."),
    ("역류성 식도염", "abdominal", "소화기내과", 1, "속쓰림;신물;가슴쓰림;역류;트림", "속이 쓰리고 신물이 올라옵니다."),
    ("위염", "abdominal", "소화기내과", 1, "명치쓰림;속불편;소화불량;메스꺼움;위통", "명치가 쓰리고 속이 불편합니다."),
    ("위궤양", "abdominal", "소화기내과", 2, "식후명치통증;속쓰림;위통;검은변;구토", "식사 후 명치 통증이 심합니다."),
    ("장염", "abdominal", "소화기내과", 2, "설사;복통;구토;열;장염", "설사와 복통이 계속됩니다."),
    ("과민성대장증후군", "abdominal", "소화기내과", 1, "긴장;복통;설사;변비;반복", "긴장하면 배가 아프고 설사를 합니다."),
    ("맹장염", "abdominal", "외과", 4, "오른쪽아랫배;복통;구역;발열;충수염", "오른쪽 아랫배가 심하게 아픕니다."),
    ("담석증", "abdominal", "소화기내과", 3, "오른쪽윗배;구역;담석;기름진음식;복통", "오른쪽 윗배가 아프고 구역질이 납니다."),
    ("간염", "abdominal", "소화기내과", 3, "황달;피로;소변색진함;간수치;식욕저하", "피부와 눈이 노랗게 변했습니다."),
    ("신장결석", "urology", "비뇨의학과", 3, "옆구리통증;찢어질듯;혈뇨;구역;결석", "옆구리가 찢어질 듯 아픕니다."),
    ("방광염", "urology", "비뇨의학과", 1, "배뇨통;빈뇨;소변자주;잔뇨감;아랫배", "소변 볼 때 따갑고 자주 마렵습니다."),
    ("요로감염", "urology", "비뇨의학과", 3, "열;배뇨통;옆구리통증;소변통증;오한", "열이 나고 소변 볼 때 통증이 있습니다."),
    ("전립선염", "urology", "비뇨의학과", 2, "회음부통증;배뇨불편;빈뇨;골반통증;전립선", "회음부 통증과 배뇨 불편이 있습니다."),
    ("당뇨병", "endocrine", "내분비내과", 2, "물을자주;소변많이;갈증;체중감소;혈당", "물을 자주 마시고 소변을 많이 봅니다."),
    ("갑상선 기능 항진증", "endocrine", "내분비내과", 2, "심장빨리;체중감소;손떨림;더위;갑상선", "심장이 빨리 뛰고 체중이 줄고 있습니다."),
    ("갑상선 기능 저하증", "endocrine", "내분비내과", 1, "피곤;체중증가;추위;붓기;갑상선", "피곤하고 체중이 늘고 있습니다."),
    ("고혈압", "cardio", "심장내과", 2, "혈압;뒷목당김;두통;어지럼;고혈압", "뒷목이 당기고 머리가 아픕니다."),
    ("협심증", "cardio", "심장내과", 4, "운동시흉통;가슴조임;휴식시완화;숨참;협심증", "운동하면 가슴이 조이는 느낌이 납니다."),
    ("심근경색", "cardio", "응급의학과", 5, "짓누르는가슴통증;식은땀;왼팔통증;호흡곤란;흉통", "가슴을 짓누르는 통증과 식은땀이 납니다."),
    ("심부전", "cardio", "심장내과", 4, "조금만걸어도숨참;다리부종;누우면숨참;피로;심부전", "조금만 걸어도 숨이 찹니다."),
    ("아토피", "skin", "피부과", 1, "피부가려움;붉음;건조;습진;아토피", "피부가 가렵고 붉게 변했습니다."),
    ("두드러기", "allergy", "피부과", 2, "붉은발진;가려움;갑자기;두드러기;부풀어오름", "피부에 붉은 발진이 갑자기 생겼습니다."),
    ("대상포진", "skin", "피부과", 3, "한쪽물집;통증;띠모양;화끈거림;대상포진", "몸 한쪽에 물집과 통증이 있습니다."),
    ("무좀", "skin", "피부과", 1, "발가락사이;가려움;벗겨짐;진물;무좀", "발가락 사이가 가렵고 벗겨집니다."),
    ("류마티스 관절염", "musculoskeletal", "류마티스내과", 2, "아침뻣뻣;손가락관절;붓기;관절통;대칭", "아침에 손가락 관절이 뻣뻣합니다."),
    ("통풍", "musculoskeletal", "류마티스내과", 3, "엄지발가락;붓기;극심한통증;통풍;관절", "엄지발가락이 붓고 극심하게 아픕니다."),
    ("디스크", "musculoskeletal", "정형외과", 2, "허리통증;다리저림;방사통;디스크;좌골", "허리가 아프고 다리까지 저립니다."),
    ("오십견", "musculoskeletal", "정형외과", 1, "어깨통증;팔안올라감;운동제한;오십견;밤통증", "어깨가 아프고 팔이 잘 안 올라갑니다."),
    ("빈혈", "hematology", "내과", 2, "어지럼;피곤;창백;숨참;빈혈", "어지럽고 쉽게 피곤합니다."),
]

VARIATIONS = [
    "{example}",
    "어제부터 {example}",
    "{example} 증상이 계속됩니다.",
    "{example} 병원에 가야 할까요?",
    "{keywords} 증상이 있습니다.",
    "{example} 약을 먹어도 불편합니다.",
    "{example} 일상생활이 불편합니다.",
    "{example} 어느 진료과를 가야 하나요?",
]

QUESTION_TEMPLATES = [
    ("증상이 갑자기 심해졌거나 빠르게 악화되고 있나요?", "악화;심해짐;갑자기;지속", 3, 4),
    ("고열, 심한 통증, 숨참, 의식 저하 중 하나라도 동반되나요?", "고열;심한통증;숨참;의식저하", 4, 5),
    ("증상이 3일 이상 지속되거나 반복되고 있나요?", "3일;지속;반복;재발", 2, 3),
]

CUSTOM_QUESTIONS = {
    "감기": [
        ("열이 38도 이상으로 오르거나 숨쉬기 힘든가요?", "38도;고열;숨참;호흡곤란", 3, 5),
        ("콧물, 기침, 목아픔이 1주 이상 지속되나요?", "콧물;기침;목아픔;1주", 2, 4),
        ("누런 가래나 가슴 통증이 함께 있나요?", "누런가래;가슴통증;흉통;가래", 3, 4),
    ],
    "독감": [
        ("38도 이상의 고열과 심한 몸살이 갑자기 시작됐나요?", "38도;39도;고열;몸살", 4, 5),
        ("숨이 차거나 가슴 통증이 동반되나요?", "숨참;호흡곤란;가슴통증;흉통", 5, 5),
        ("고령자, 임산부, 만성질환자이거나 증상이 빠르게 악화되나요?", "고령;임산부;만성질환;악화", 4, 4),
    ],
    "코로나19": [
        ("후각이나 미각이 떨어지고 열 또는 기침이 있나요?", "후각저하;미각저하;열;기침", 3, 5),
        ("숨이 차거나 산소가 부족한 느낌이 있나요?", "숨참;호흡곤란;산소;가슴답답", 5, 5),
        ("확진자 접촉이나 최근 유행 노출이 있었나요?", "확진자;접촉;유행;노출", 2, 4),
    ],
    "편도염": [
        ("침 삼키기 힘들 정도로 목 통증이 심한가요?", "침삼킴곤란;목통증;인후통;편도", 3, 5),
        ("편도에 하얀 분비물이나 고열이 있나요?", "편도;하얀분비물;고열;열", 4, 4),
        ("숨쉬기 어렵거나 목이 심하게 붓는 느낌이 있나요?", "숨쉬기어려움;목부음;호흡곤란;부종", 5, 5),
    ],
    "장염": [
        ("설사가 하루 6회 이상 반복되거나 물처럼 나오나요?", "6회;설사;물설사;반복", 3, 5),
        ("피가 섞인 변, 검은 변, 심한 복통 중 하나가 있나요?", "혈변;검은변;심한복통;복통", 4, 5),
        ("소변이 줄거나 입이 마르고 어지러운 탈수 증상이 있나요?", "소변감소;입마름;어지럼;탈수", 4, 4),
    ],
    "맹장염": [
        ("오른쪽 아랫배 통증이 점점 심해지거나 걸을 때 울리나요?", "오른쪽아랫배;걸을때통증;악화;충수염", 4, 5),
        ("구역질, 미열, 식욕 저하가 함께 있나요?", "구역;미열;식욕저하;발열", 3, 4),
        ("배를 눌렀다 뗄 때 통증이 더 심해지나요?", "반발통;누르면통증;복통;심한통증", 5, 5),
    ],
    "골절": [
        ("다친 부위가 붓거나 움직이기 어렵나요?", "붓기;움직임제한;걷기힘듦;통증", 4, 5),
        ("다칠 때 뚝 소리가 났거나 체중을 싣기 힘든가요?", "뚝소리;체중부하불가;걷기힘듦;무릎", 4, 4),
        ("손발 끝이 저리거나 차갑고 감각이 둔한가요?", "저림;차가움;감각저하;창백", 5, 5),
    ],
    "뇌수막염": [
        ("목이 뻣뻣하거나 고개를 숙일 때 두통이 심해지나요?", "목뻣뻣;고개숙임;두통;수막염", 5, 5),
        ("고열과 심한 두통, 구토가 함께 있나요?", "고열;두통;구토;오심", 5, 5),
        ("의식이 흐리거나 빛을 보기 힘든가요?", "의식저하;빛공포;혼돈;경련", 5, 5),
    ],
}


def build_case_rows(existing: pd.DataFrame) -> pd.DataFrame:
    start_id = int(pd.to_numeric(existing["case_id"], errors="coerce").max()) + 1
    rows = []
    row_id = start_id

    for disease, group, department, severity, keywords, example in COMMON_DISEASES:
        keyword_words = keywords.replace(";", " ")
        for variation in VARIATIONS:
            text = variation.format(example=example, keywords=keyword_words)
            rows.append(
                {
                    "case_id": row_id,
                    "source_url": "curated://common-disease-coverage",
                    "raw_text": text,
                    "cleaned_text": text,
                    "symptom_keywords": keywords,
                    "symptom_group": group,
                    "department": department,
                    "suspected_disease": disease,
                    "severity_level": severity,
                }
            )
            row_id += 1

    return pd.DataFrame(rows, columns=CASE_COLUMNS)


def build_question_rows(existing_questions: pd.DataFrame) -> pd.DataFrame:
    existing_ids = set(existing_questions["question_id"].astype(str))
    rows = []

    for index, (disease, group, _department, _severity, keywords, _example) in enumerate(COMMON_DISEASES, start=1):
        question_set = CUSTOM_QUESTIONS.get(disease, QUESTION_TEMPLATES)
        for q_index, (question, positive_keywords, risk_score, importance) in enumerate(question_set, start=1):
            question_id = f"DQ_COMMON_{index:03d}_{q_index:03d}"
            if question_id in existing_ids:
                continue
            rows.append(
                {
                    "question_id": question_id,
                    "suspected_disease": disease,
                    "symptom_group": group,
                    "question": question,
                    "positive_keywords": positive_keywords,
                    "risk_score": risk_score,
                    "required_resource_code": "ER_GENERAL",
                    "importance": importance,
                }
            )

    return pd.DataFrame(rows, columns=QUESTION_COLUMNS)


def main() -> None:
    cases = pd.read_csv(CASES_PATH)
    questions = pd.read_csv(QUESTIONS_PATH)

    new_cases = build_case_rows(cases)
    combined_cases = pd.concat([cases[CASE_COLUMNS], new_cases], ignore_index=True)
    combined_cases = combined_cases.drop_duplicates(
        subset=["cleaned_text", "suspected_disease"],
        keep="first",
    ).reset_index(drop=True)
    combined_cases["case_id"] = range(1, len(combined_cases) + 1)
    combined_cases.to_csv(
        CASES_PATH,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    questions = questions[~questions["question_id"].astype(str).str.startswith("DQ_COMMON_")]
    new_questions = build_question_rows(questions)
    combined_questions = pd.concat([questions[QUESTION_COLUMNS], new_questions], ignore_index=True)
    combined_questions = combined_questions.drop_duplicates(
        subset=["question_id"],
        keep="first",
    )
    combined_questions.to_csv(
        QUESTIONS_PATH,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    print("===== Common disease coverage expanded =====")
    print(f"Added/updated case rows: {len(new_cases)}")
    print(f"Training rows: {len(combined_cases)}")
    print(f"Suspected diseases: {combined_cases['suspected_disease'].nunique()}")
    print(f"Added question rows: {len(new_questions)}")
    print(f"Question diseases: {combined_questions['suspected_disease'].nunique()}")


if __name__ == "__main__":
    main()
