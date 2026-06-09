# 실시간 ETA 연동

## 목적

기존 추천 병원 이동시간은 직선거리와 ETA 예측 모델을 기반으로 계산했다. 이 방식은 빠르고 API 키가 필요 없지만, 실제 도로망과 실시간 교통 상황을 충분히 반영하지 못한다.

이번 업그레이드는 사용자 위치가 제공되고 API 키가 설정된 경우 Kakao Mobility 자동차 길찾기 API를 사용해 추천 후보 병원의 실제 주행 예상 시간을 보정한다. 또한 사용자가 현재 위치 권한을 허용하지 않아도 주소나 장소명을 검색해 좌표를 설정할 수 있도록 Kakao Local API 기반 위치 검색을 제공한다.

## 동작 방식

1. 사용자가 현재 위치를 허용하거나 위도/경도를 입력한다.
2. 병원 후보를 기존 방식으로 먼저 계산한다.
3. 상위 후보군에 대해 Kakao Mobility Directions API를 호출한다.
4. API 응답의 `duration`, `distance`를 `eta_min`, `distance_km`에 반영한다.
5. 실시간 ETA가 반영된 후보를 다시 정렬한다.
6. API 키가 없거나 호출 실패 시 기존 ETA 모델로 자동 fallback한다.

## 위치 검색

프론트엔드의 `지도 검색` 입력창에서 주소나 장소명을 검색하면 백엔드가 Kakao Local API를 호출한다.

사용 API:

- 주소 검색: `https://dapi.kakao.com/v2/local/search/address.json`
- 키워드 장소 검색: `https://dapi.kakao.com/v2/local/search/keyword.json`

검색 결과를 선택하면 위도/경도 입력칸이 자동으로 채워지고, 이후 병원 추천과 실시간 ETA 계산에 사용된다.

## 환경 변수

백엔드 배포 환경에 다음 값을 추가한다.

```bash
KAKAO_REST_API_KEY=발급받은_REST_API_KEY
KAKAO_MOBILITY_REST_API_KEY=발급받은_REST_API_KEY
```

로컬 개발 시에는 `backend/.env`에 같은 값을 넣으면 된다.

`KAKAO_REST_API_KEY`는 Kakao Local 주소/장소 검색에 우선 사용한다. 값이 없으면 기존 `KAKAO_MOBILITY_REST_API_KEY`를 fallback으로 사용한다.

## 프론트 표시

추천 병원 카드의 예상 이동시간 아래에 ETA 출처를 표시한다.

- `실시간 길찾기`: Kakao Mobility Directions API 반영
- `모델 추정`: API 키가 없거나 호출 실패로 기존 ETA 모델 사용

## 주의사항

- 브라우저 위치 정보는 사용자가 `현재 위치 사용`을 눌러 권한을 허용해야 사용할 수 있다.
- 위치 권한을 허용하지 않아도 `지도 검색`으로 출발 위치를 설정할 수 있다.
- Kakao Developers 앱 설정에서 Kakao Map/Local API 사용 설정이 필요할 수 있다.
- Kakao Mobility 길찾기 API 키와 Kakao Local API 키 권한이 다르게 설정되어 있으면, ETA는 동작하지만 지도 검색은 실패할 수 있다.
- 위치 권한을 자동으로 강제 요청하는 방식은 개인정보 관점에서 좋지 않고, 브라우저 정책상 사용자 제스처 없이 제한될 수 있다.
- API 호출 비용과 쿼터가 있으므로 모든 병원이 아니라 추천 상위 후보군에 대해서만 실시간 ETA를 계산한다.
- 응급 상황에서는 ETA가 참고 정보일 뿐이며, 매우 긴급한 경우 119 신고 안내가 우선이다.
