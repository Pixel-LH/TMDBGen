import asyncio
import re
import traceback
import aiohttp
import logging

from aiohttp import ClientConnectorError

logger = logging.getLogger("TMDBGen")
BASE_API = "https://api.themoviedb.org/3"
BASE_IMAGE_URL = "https://image.tmdb.org/t/p/w600_and_h900_bestv2"

class TmdbGen:


    def __init__(self, api_access_token:str,proxy:str = None):
        """
        :param api_access_token: TMDB API Key，请在 https://www.themoviedb.org/settings/api 获取 "API Read Access Token"
        """
        self.access_token = api_access_token
        self.headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
        }
        self.proxy = proxy

    async def gen_description(self, media_link:str,language="zh-CN",season_number=1) -> tuple[bool, str]:
        """生成简介
        :param media_link: TMDB 媒体链接，例如：https://www.themoviedb.org/movie/550
        :param language: 语言代码，默认为 "zh-CN"
        :param season_number: 电视剧的季数，默认为 1
        :return: (成功/失败, 生成的简介/错误信息)
        """

        def extract_media_type(link: str):
            """从链接中提取媒体类型"""
            if "tv" in link:
                return True
            elif "movie" in link:
                return False
            else:
                raise ValueError("无法识别的媒体链接类型")

        def extract_tmdb_id(url):
            """从链接中提取 TMDB ID"""
            if "?" in url:
                url = url.split("?")[0]
            match = re.search(r'/(movie|tv)/(\d+)', url)
            return match.group(2) if match else None


        try:
            if not (tmdb_id := extract_tmdb_id(media_link)):
                logger.error(f"无法从链接中提取 TMDB ID,请检查链接格式是否填写完整。")
                return False,"无法从链接中提取 TMDB ID,请检查链接格式是否填写完整。"

            tv_mode = extract_media_type(media_link)
            media_type = "tv" if tv_mode else "movie"

            async with aiohttp.ClientSession(headers=self.headers,proxy=self.proxy) as session:

                tasks = [
                    session.get(f"{BASE_API}/{media_type}/{tmdb_id}", params={"language": language}),
                    session.get(f"{BASE_API}/{media_type}/{tmdb_id}/credits", params={"language": language}),
                    session.get(f"{BASE_API}/{media_type}/{tmdb_id}/alternative_titles"),
                    session.get(f"{BASE_API}/{media_type}/{tmdb_id}/external_ids"),
                ]

                # 添加季数据请求（如果是电视剧）
                if media_type == "tv":
                    if season_number is None:
                        season_number = 1
                    tasks.append(
                        session.get(
                            f"{BASE_API}/tv/{tmdb_id}/season/{season_number}",
                            params={"language": language}
                        )
                    )
                try:
                    responses = await asyncio.gather(*tasks)
                except ClientConnectorError:
                    return False, "无法连接到TMDB，请检查网络连接或代理设置。"


                details_resp, credits_resp, alt_titles_resp, external_ids_resp, *season_resp = responses
                tv_season_details = await season_resp[0].json() if season_resp else None

                details = await details_resp.json()
                if details.get("success") is not None and not details.get("success"):
                    logger.error(f"无法获取媒体详情，请检查 TMDB链接是否正确: {tmdb_id},返回信息：{details}")
                    return False, "无法获取对应媒体详情，请检查 TMDB链接是否正确。"

                credits = await credits_resp.json()
                alt_titles = await alt_titles_resp.json()
                external_ids = await external_ids_resp.json()

                if not details:
                    return False, "无法获取媒体详情，请检查 TMDB ID 是否正确。"

            year = (details.get("first_air_date") if media_type == "tv" else details.get("release_date", ""))
            if year:
                year = year.split('-')[0]
            else:
                year = "Unknown"

            processed_data = {
                "title": details.get("name" if media_type == "tv" else "title"),
                "original_title": details.get("original_name" if media_type == "tv" else "original_title"),
                "poster_path": f"{BASE_IMAGE_URL}{details['poster_path']}" if details.get("poster_path") else "",
                "year": year,
                "country": ", ".join([c["name"] for c in details.get("production_countries", [])][:1]),
                "genres": " / ".join(g["name"] for g in details.get("genres", [])),
                "language": " / ".join([l["name"] for l in details.get("spoken_languages", [])][:1]),
                "release_date": details.get("first_air_date" if media_type == "tv" else "release_date", ""),
                "tmdb_url": f"https://www.themoviedb.org/{media_type}/{tmdb_id}",
                "tmdb_rating": f"{details.get('vote_average', 0):.1f}/{details.get('vote_count', 0)}",
                "rating": f"{details.get('vote_average', 0):.1f}/10",
                "imdb_id": external_ids.get("imdb_id", ""),
                "season": season_number or "N/A",
                "episodes": details.get("number_of_episodes", 0),
                "overview": details.get("overview", "暂无简介"),
                "directors": [p["name"] for p in credits.get("crew", []) if p.get("job") == "Director"],
                "writers": [p["name"] for p in credits.get("crew", []) if p.get("department") == "Writing"],
                "cast": [p["name"] for p in credits.get("cast", [])][:6],
                "chinese_title": next((t["title"] for t in alt_titles.get("results", []) if t.get("iso_3166_1") == "CN"),""),
                "type": media_type
            }

            if media_type == "tv" and tv_season_details is not None:
                """如果有电视剧季数据，则更新相关信息"""
                processed_data['overview'] = tv_season_details.get("overview") if tv_season_details.get(
                    "overview") else processed_data['overview']
                processed_data['tmdb_rating'] = tv_season_details.get("vote_average", processed_data['tmdb_rating'])
                processed_data['first_air_date'] = (tv_season_details.get("air_date") or
                                                    tv_season_details['episodes'][0]['air_date']) or processed_data[
                                                       'release_date']
                processed_data['episodes'] = len(tv_season_details.get("episodes", [])) or processed_data['episodes']
                processed_data['year'] = tv_season_details.get("air_date", processed_data['year'])[
                                         :4] if tv_season_details.get(
                    "air_date") else processed_data['year']
                processed_data["episodes_name_list"] = [
                    {f"{ep['episode_number']}": f"{ep['name']}"} for ep in
                    tv_season_details.get("episodes", [])] if tv_season_details else []

            result = self.format_output(processed_data)
            return True,result

        except Exception:
            traceback.print_exc()
            if tv_season_details:
                print(f"{tv_season_details}")
            return False, f"获取TMDB媒体信息发生异常"



    def format_output(self, data, bbcode=True):
        """格式化输出影视信息，确保对齐"""

        def align_text(label, content, label_width=8):
            """辅助函数：对齐文本"""
            # 计算中文字符的宽度
            chinese_char_count = sum(1 for char in label if '\u4e00' <= char <= '\u9fff')
            total_label_width = len(label) + chinese_char_count
            padding = "　" * (label_width - total_label_width)  # 使用全角空格对齐
            if bbcode and label != "":
                return f"[b][color=DarkRed]{label}[/color][/b]{padding}{content}"
            return f"{label}{padding}{content}"

        title = data["chinese_title"] or data["title"]
        if data['title'] and data["chinese_title"]:
            title = f"{title} / {data['title']}"
        output = [
            f'[img]{data["poster_path"]}[/img]\n',
            align_text('◎译　　名', title),
            align_text('◎原　　名', data["original_title"]),
            align_text('◎年　　代', data["year"]),
            align_text('◎产　　地', data.get("country", "N/A")),
            align_text('◎类　　别', data["genres"]),
            align_text('◎语　　言', data.get("language", "N/A")),
            align_text('◎上映日期  ', f" {data['release_date']}"),
        ]

        # IMDb信息（如果有）
        if data["imdb_id"]:
            output.extend([
                align_text('◎IMDb评分 ', f' {data["rating"]}'),
                align_text('◎TMDB评分 ', f' {data["tmdb_rating"]}'),
                align_text('◎IMDb链接 ', f' https://www.imdb.com/title/{data["imdb_id"]}/'),
                align_text('◎TMDB链接 ', f' {data["tmdb_url"]}'),
            ])
        else:
            # TMDB信息
            output.extend([
                align_text('◎TMDB评分', f' {data["tmdb_rating"]}'),
                align_text('◎TMDB链接', f' {data["tmdb_url"]}'),
            ])

        writers = data.get("writers", [])[:2]
        output.append(align_text('◎编　　剧', " / ".join(writers) if writers else "N/A"))

        # 主演列表优化，用 " / " 连接每一个主演，最多显示6个，最后一个用 "..." 代替
        cast = data.get("cast", [])
        output.append(align_text('◎主　　演', " / ".join(cast[:6]) if cast else "N/A"))
        if len(cast) > 6:
            output.append(f'　　　　　...')
        # 电视剧集数
        if data["type"] == "tv":
            anime = False
            if "动画" in data["genres"]:
                anime = True
            output.append(align_text('◎季　　度', f"第 {data['season']} 季"))
            output.append(align_text('◎集　　数', f"共 {data['episodes']} 集"))
            first_ep = data['episodes_name_list'][0]
            if not re.match(r'第\s*\d+\s*集', str(list(first_ep.values())[0])):
                if not anime:
                    output.append(align_text('◎集　　名',
                                             f"第{str(list(first_ep.keys())[0]).zfill(2)}集:  {str(list(first_ep.values())[0])}"))
                else:
                    output.append(align_text('◎集　　名',
                                             f"第{str(list(first_ep.keys())[0]).zfill(2)}集:  [color=#e77c8e][b]{str(list(first_ep.values())[0])}[/b][/color]"))
            count = 0
            no_runtime = False
            ep_name_list = []
            for ep in data['episodes_name_list'][1:]:
                ep_value = str(list(ep.values())[0])
                if re.match(r'第\s*\d+\s*集', ep_value):
                    ep_value = ' ......'
                    no_runtime = True
                if anime and bbcode:
                    # 对动画使用特殊颜色的BBCode 颜色，可自定义
                    content = f" 第{str(list(ep.keys())[0]).zfill(2)}集:  [color=#e77c8e][b]{ep_value}[/b][/color]"
                else:
                    content = f" 第{str(list(ep.keys())[0]).zfill(2)}集:  {str(list(ep.values())[0])}"
                if bbcode:
                    content = " " + content
                ep_name_list.append(
                    align_text(label='',
                               content=content,
                               label_width=5))
                if no_runtime:
                    # 遇到集数名字是数字时，代表后续集数没具体名称，跳出循环
                    break
                count += 1
                if count == 30:
                    # 最大显示30集 (可自定义)
                    ep_name_list.append(align_text(label='', content=' ......', label_width=5))
                    break
            if len(ep_name_list) > 1:
                output.append('\n'.join(ep_name_list))
        output.append(align_text('◎简　　介', ""))  # 简介标题单独对齐
        output.append(f'　　           {data.get("overview", "暂无简介")}')

        return '\n'.join(output)


