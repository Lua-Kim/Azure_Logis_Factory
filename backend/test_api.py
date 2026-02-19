import requests

BASE_URL = "http://localhost:8000"

print("=== API 테스트 ===\n")

# 1. 모든 병목 조회
print("1️⃣ 모든 병목 조회:")
response = requests.get(f"{BASE_URL}/api/bottlenecks", params={"limit": 10})
print(f"상태: {response.status_code}")
print(f"데이터 개수: {len(response.json())}")
if response.json():
    print(f"첫 번째 레코드: {response.json()[0]}")

# 2. 라인별 병목 조회
print("\n2️⃣ Line 1010107 병목 조회:")
response = requests.get(f"{BASE_URL}/api/bottlenecks", params={"line_id": 1010107, "limit": 10})
print(f"상태: {response.status_code}")
print(f"데이터 개수: {len(response.json())}")
if response.json():
    print(f"첫 번째 레코드: {response.json()[0]}")

# 3. 센터별 병목 조회
print("\n3️⃣ Center 100 병목 조회:")
response = requests.get(f"{BASE_URL}/api/bottlenecks", params={"center_id": 100, "limit": 10})
print(f"상태: {response.status_code}")
print(f"데이터 개수: {len(response.json())}")

# 4. 라인 상태 조회
print("\n4️⃣ 라인 상태 조회:")
response = requests.get(f"{BASE_URL}/api/line/status")
print(f"상태: {response.status_code}")
print(f"라인 개수: {len(response.json())}")
if response.json():
    for line in response.json()[:3]:
        print(f"  - {line.get('name')}: ID={line.get('id')}, Center={line.get('center_id')}")
