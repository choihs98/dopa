# 도파미 exe 빌드

이 저장소는 `dopamine_buddy.pyw`를 GitHub Actions(Windows 서버)에서 `Dopami.exe`로 빌드합니다.
파이썬이 없는 PC에서도 exe 하나만 있으면 실행됩니다.

## exe 받는 법
1. 이 저장소의 **Actions** 탭 → **Build Dopami exe** 선택
2. **Run workflow** 클릭 (main에 push해도 자동 실행)
3. 1~3분 뒤 실행 결과 페이지 맨 아래 **Artifacts → Dopami-exe** 다운로드
4. zip을 풀면 `Dopami.exe` — 더블클릭하면 콘솔 창 없이 실행

## 참고
- 종료: 캐릭터를 3.5초 안에 5번 연타 (또는 작업 관리자에서 Dopami.exe 종료)
- 썰 추가: exe와 같은 폴더에 `stories.txt` (한 줄에 하나)
- 서명 없는 exe라서 SmartScreen/백신 경고가 뜰 수 있습니다
- `api_key.txt`는 `.gitignore`에 들어 있으니 키를 저장소에 올리지 마세요
