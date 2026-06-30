# Confluence Parser — GUI

Confluence 페이지를 **Markdown / Word / Excel / PDF** 로 변환하는 PyQt6 데스크톱 앱입니다.

## 아키텍처

```
confluence_parser/
├── gui.py                  # PyQt6 메인 윈도우 (View)
├── worker.py               # QThread 백그라운드 워커
├── confluence_client.py    # Confluence REST API 클라이언트 (Model)
├── html_cleaner.py         # HTML 정제 모듈
├── config.py               # .env 설정 로더/저장
├── converters/
│   ├── to_md.py
│   ├── to_docx.py
│   ├── to_excel.py
│   └── to_pdf.py
├── requirements.txt
└── .env                    # 자동 생성 (이메일/토큰 저장)
```

## 설치

```bash
pip install -r requirements.txt
```

> PDF 변환은 추가로 **wkhtmltopdf** 설치 필요
> → https://wkhtmltopdf.org/downloads.html

## 실행

```bash
python gui.py
```

## 사용법

1. **⚙ 설정** 버튼 클릭 → Confluence 이메일 + API Token 입력 → 저장 (`.env` 에 자동 저장)
2. 변환하려는 **Confluence 페이지 URL** 붙여넣기
3. **출력 형식** 드롭다운에서 선택 (md / docx / xlsx / pdf)
4. **하위 문서 포함** 체크박스로 하위 페이지 포함 여부 결정
5. **📂 찾기** 버튼으로 저장 경로 지정
6. **▶ 변환 시작** 클릭

> 변환은 백그라운드 스레드에서 수행되어 UI가 멈추지 않습니다.

## 지원 URL 형식

```
https://your-instance.atlassian.net/wiki/spaces/SPACE/pages/123456/page-title
https://your-instance.atlassian.net/wiki/pages/viewpage.action?pageId=123456
```

## API Token 발급

https://id.atlassian.com/manage-profile/security/api-tokens
