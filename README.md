# Laythe
![](https://koreanbots.dev/api/widget/bots/votes/872349051620831292.svg) ![](https://koreanbots.dev/api/widget/bots/servers/872349051620831292.svg)  
레이테, 다기능 관리봇.

## 직접 돌리기 (권장하지 않음)
레이테의 소스 코드는 단순 참고용으로만 제공되며, 라이센스를 지키는 범위 내에서 자유롭게 이용 가능합니다.  
만약 코드를 직접 돌리고 싶다면, 다음 내용을 따라주세요.  
**레이테 코드를 직접 돌리는 것에 대한 책임은 사용자에게 있으며, Team EG에서는 어떤 책임 또는 지원도 없습니다.**
1. MySQL 또는 MariaDB 데이터베이스를 하나 준비해주시고, (생성 쿼리 준비중) 쿼리를 실행해주세요.
2. `example-config.json`을 `config.json`으로 이름을 바꾸고, 안의 내용들을 채워주세요.
3. `extlib`와 관련된 모든 코드를 제거해주세요. 해당 모듈은 현재는 보안 문제로 코드가 제공되지 않습니다.
4. `main.py`를 실행해주세요.