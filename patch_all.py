import requests
import json
import os
import time
import logging

OUT_PUT_BASE_PATH = "output"

# MyAnimeList API 설정
BASE_URL_SEASON = "https://api.myanimelist.net/v2/anime/season"
BASE_URL_DETAILS = "https://api.myanimelist.net/v2/anime"

HEADERS = {
    "X-MAL-CLIENT-ID": "e663791116677d1ee7e162ad749d2e34"
}

FIELDS = [
    "sid", "title", "main_picture", "alternative_titles", "start_date",
    "end_date", "synopsis", "nsfw", "created_at", "updated_at", "media_type",
    "status", "genres", "my_list_status", "num_episodes", "start_season",
    "broadcast", "source", "average_episode_duration", "rating", "studios",
    "available_at", "platforms", "resources"
]

# 시즌 목록
SEASONS = ["winter", "spring", "summer", "fall"]

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("anime_scraper.log", mode="a+", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


# 디렉터리 생성
def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Created directory: {path}")

# 이미지 다운로드
def download_image(url, path):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            logging.info(f"Image saved to {path}.")
        else:
            logging.warning(f"Failed to download image from {url}. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error downloading image from {url}: {e}")

# 애니메이션 데이터 가져오기
def fetch_anime_by_season(year, season):
    offset = 0
    limit = 100
    season_anime = []

    while True:
        url = f"{BASE_URL_SEASON}/{year}/{season}?limit={limit}&offset={offset}"
        logging.info(f"Fetching {year} {season} anime with offset {offset}.")
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            logging.error(f"Error {response.status_code} while fetching {year} {season} anime.")
            break

        data = response.json()
        season_anime.extend(data.get("data", []))

        if "paging" not in data or "next" not in data["paging"]:
            break  # 더 이상 데이터가 없음

        offset += limit
        time.sleep(1)  # API Rate Limit을 피하기 위해 대기

    return season_anime


# 상세 정보 가져오기
def fetch_anime_details(anime_id):
    fields_param = ",".join(FIELDS)
    url = f"{BASE_URL_DETAILS}/{anime_id}?fields={fields_param}"
    logging.info(f"Fetching details for Anime ID {anime_id}.")
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        logging.error(f"Error {response.status_code} while fetching details for Anime ID {anime_id}.")
        return None

    return response.json()


# 전체 데이터 수집
if __name__ == "__main__":
    try:
        for year in range(1960, 2025):
            for season in SEASONS:
                logging.info(f"Fetching {year} {season} anime...")
                season_anime = fetch_anime_by_season(year, season)

                # 시즌별 디렉터리 생성
                season_path = os.path.join(OUT_PUT_BASE_PATH, str(year), season)
                ensure_directory(season_path)

                for anime in season_anime:
                    anime_id = anime["node"]["id"]
                    details = fetch_anime_details(anime_id)
                    if details:
                        # JSON 저장
                        json_path = os.path.join(season_path, f"{anime_id}.json")
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(details, f, ensure_ascii=False, indent=4)
                        logging.info(f"Saved anime ID {anime_id} to {json_path}.")

                        # 이미지 저장
                        if "main_picture" in details:
                            for size, url in details["main_picture"].items():
                                image_path = os.path.join(season_path, f"{anime_id}_{size}.jpg")
                                download_image(url, image_path)

                    time.sleep(1)  # API Rate Limit 대기

        logging.info("All data has been successfully fetched and saved.")

    except Exception as e:
        logging.exception("An error occurred during the scraping process.")