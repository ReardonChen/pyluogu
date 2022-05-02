"""
PyLuogu
=======

A model-based Python implement for Luogu API client

洛谷 API 客户端基于模型的 Python 实现
"""

from pprint import pformat

import requests

USER_AGENT = "Mozilla/5.0"


def cached_method(func):
    def wrapper(self, *args):
        if not hasattr(self, "__cache"):
            self.__cache = {}
        cache = self.__cache
        if args not in cache:
            cache[args] = func(self, *args)
        return cache[args]

    return wrapper


class NotFoundHttpException(Exception):
    pass


def _dict_without_underscores(d: dict):
    return dict(filter(lambda i: not i[0].startswith("_"), d.items()))


class Model:
    def _get(self, url, params=None):
        r = requests.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT, "X-Luogu-Type": "content-only"},
        )
        r.raise_for_status()
        data = r.json()
        if data["code"] == 404:
            raise NotFoundHttpException(data["currentData"]["errorMessage"])
        return data

    def __repr__(self):
        return pformat(
            _dict_without_underscores(self.__dict__),
            sort_dicts=False,
        )

    def __eq__(self, other):
        if hasattr(self, "_current_data") and hasattr(other, "_current_data"):
            return self._current_data == other._current_data
        return _dict_without_underscores(
            self.__dict__
        ) == _dict_without_underscores(other.__dict__)


class LazyList(list):
    def __init__(self, iterable, getitem=lambda i: i):
        if iterable is None:
            super().__init__()
        else:
            super().__init__(iterable)
        self._getitem = getitem

    @cached_method
    def __getitem__(self, index):
        return self._getitem(super().__getitem__(index))


class User(Model):
    """用户

    :param uid: 用户 ID
    :type uid: int

    :raises NotFoundHttpException: 用户未找到

    :var int register_time: 注册时间
    :var str introduction: 个人介绍
    :var list[Prize] prize: 获奖信息
    :var str blog_address: 个人博客地址
    :var passed_problem_count: 已通过题目数量
    :vartype passed_problem_count: int | None
    :var submitted_problem_count: 提交题目数量
    :vartype submitted_problem_count: int | None
    :var int uid: 用户 ID
    :var str name: 用户名
    :var str slogan: 个性签名
    :var badge: 徽章
    :vartype badge: str | None
    :var bool is_admin: 是否管理员
    :var bool is_banned: 是否被封禁
    :var str color: 颜色
    :var int ccf_level: CCF 等级
    :var int following_count: 关注数量
    :var int follower_count: 粉丝数量
    :var int ranking: 排名
    :var str background: 封面
    :var is_root: 是否为 root
    :vartype is_root: bool | None
    :var passed_problems: 已通过的题目
    :vartype passed_problems: list[Problem] | None
    :var submitted_problems: 尝试过的题目
    :vartype submitted_problems: list[Problem] | None
    """

    class Prize(Model):
        """获奖信息

        :var year: 年份
        :vartype year: int
        :var contest_name: 竞赛名称
        :vartype contest_name: str
        :var prize: 奖项
        :vartype prize: str
        """

        def __init__(self, year: int, contestName: str, prize: str) -> None:
            self.year = year
            self.contest_name = contestName
            self.prize = prize

    def __init__(self, uid: int) -> None:
        self._current_data: dict[str] = self._get(
            f"https://www.luogu.com.cn/user/{uid}"
        )["currentData"]

        user: dict[str] = self._current_data["user"]
        self.register_time: int = user["registerTime"]
        self.introduction: str = user["introduction"]
        self.prize = [self.Prize(**prize) for prize in user["prize"]]
        self.blog_address: str = user["blogAddress"]
        self.passed_problem_count: int | None = user["passedProblemCount"]
        self.submitted_problem_count: int | None = user[
            "submittedProblemCount"
        ]
        self.uid: int = user["uid"]
        self.name: str = user["name"]
        self.slogan: str = user["slogan"]
        self.badge: str | None = user["badge"]
        self.is_admin: bool = user["isAdmin"]
        self.is_banned: bool = user["isBanned"]
        self.color: str = user["color"]
        self.ccf_level: int = user["ccfLevel"]
        self.following_count: int = user["followingCount"]
        self.follower_count: int = user["followerCount"]
        self.ranking: int = user["ranking"]
        self.background: str = user["background"]
        self.is_root: bool = user["isRoot"] if "isRoot" in user else None

        def get_problem(p: dict) -> Problem:
            return Problem(p["pid"])

        self._passed_problems: list[dict] = (
            self._current_data["passedProblems"]
            if "passedProblems" in self._current_data
            else None
        )
        self.passed_problems: list[Problem] = LazyList(
            self._passed_problems,
            get_problem,
        )
        self._submitted_problems: list[dict] = (
            self._current_data["submittedProblems"]
            if "submittedProblems" in self._current_data
            else None
        )
        self.submitted_problems: list[Problem] = LazyList(
            self._submitted_problems,
            get_problem,
        )


class Problem(Model):
    """题目

    :param pid: 题目 ID
    :type pid: str

    :raises NotFoundHttpException: 题目未找到

    :var str background: 题目背景
    :var str description: 题目描述
    :var str input_format: 输入格式
    :var str output_format: 输出格式
    :var samples: 样例
    :vartype samples: list[tuple[str, str]]
    :var str hint: 说明/提示
    :var User provider: 题目提供者
    :var list[dict] attachments: 附件
    :var bool can_edit: 可编辑
    :var limits: 限制
    :vartype limits: dict[str, list[int]]
    :var str std_code: 标准代码
    :var list[int] tags: 标签
    :var bool wants_translation: 需要翻译
    :var int total_submit: 总提交
    :var int total_accepted: 总通过
    :var int flag:
    :var str pid: 题目 ID
    :var str title: 题目标题
    :var int difficulty: 难度
    :var int full_score: 满分
    :var str type: 题目类型
    """

    def __init__(self, pid: str) -> None:
        self._current_data: dict[str] = self._get(
            f"https://www.luogu.com.cn/problem/{pid}"
        )["currentData"]

        problem: dict[str] = self._current_data["problem"]
        self.background: str = problem["background"]
        self.description: str = problem["description"]
        self.input_format: str = problem["inputFormat"]
        self.output_format: str = problem["outputFormat"]
        self.samples: list[tuple[str, str]] = [
            (s[0], s[1]) for s in problem["samples"]
        ]
        self.hint: str = problem["hint"]
        self._provider: str = problem["provider"]
        self.attachments: list = problem["attachments"]  # TODO: Attachment
        self.can_edit: bool = problem["canEdit"]
        self.limits: dict[str, list[int]] = problem["limits"]
        self.std_code: str = problem["stdCode"]
        self.tags: list[int] = problem["tags"]
        self.wants_translation: bool = problem["wantsTranslation"]
        self.total_submit: int = problem["totalSubmit"]
        self.total_accepted: int = problem["totalAccepted"]
        self.flag: int = problem["flag"]
        self.pid: str = problem["pid"]
        self.title: str = problem["title"]
        self.difficulty: int = problem["difficulty"]
        self.full_score: int = problem["fullScore"]
        self.type: str = problem["type"]

    @property
    @cached_method
    def provider(self):
        return User(self._provider["uid"])
