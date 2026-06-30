# Confluence Parser

Confluence 페이지 및 하위 문서 전체를 다양한 포맷으로 변환하는 도구입니다.

## 지원 포맷

| 파일 | 설명 |
|---|---|
| `to_md.py` | Markdown (`.md`) |
| `to_docx.py` | Microsoft Word (`.docx`) |
| `to_excel.py` | Microsoft Excel (`.xlsx`) |
| `to_pdf.py` | PDF (`.pdf`) |

## 환경 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

> PDF 변환은 추가로 [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html) 설치 필요

### 2. 환경변수 설정

**Windows (CMD)**
```bat
set CONFLUENCE_BASE_URL=https://your-instance.atlassian.net/wiki
set CONFLUENCE_EMAIL=your@email.com
set CONFLUENCE_API_TOKEN=your_api_token
set CONFLUENCE_ROOT_PAGE_ID=123456789
```

**Windows (PowerShell)**
```powershell
$env:CONFLUENCE_BASE_URL = "https://your-instance.atlassian.net/wiki"
$env:CONFLUENCE_EMAIL = "your@email.com"
$env:CONFLUENCE_API_TOKEN = "your_api_token"
$env:CONFLUENCE_ROOT_PAGE_ID = "123456789"
```

**Linux/macOS**
```bash
export CONFLUENCE_BASE_URL=https://your-instance.atlassian.net/wiki
export CONFLUENCE_EMAIL=your@email.com
export CONFLUENCE_API_TOKEN=your_api_token
export CONFLUENCE_ROOT_PAGE_ID=123456789
```

## 실행

```bash
python to_md.py
python to_docx.py
python to_excel.py
python to_pdf.py
```

## 출력 파일

각 스크립트는 실행 디렉터리에 다음 파일을 생성합니다:

- `output.md`
- `output.docx`
- `output.xlsx`
- `output.pdf`
