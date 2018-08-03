# -*- coding: UTF-8 -*-
from errbot import BotPlugin, botcmd, arg_botcmd
import github
import re
import os

REPO = os.getenv("REPOSITORY")
RESULT_COUNT =  int(os.getenv("RESULT_COUNT"))
DIFF = os.getenv("DIFF_FILE")


def filename_to_source_url(filename):
    return "{}/{}".format(
        "https://github.com/istio/istio.github.io/tree/master",
        filename
    )


def filename_to_web_url(filename):
    regex = r"^(content(_zh)?)(.*?).md"
    res = re.search(regex, filename)
    if res is None:
        return ""
    name = res.group(3)
    prefix = res.group(1)
    if prefix == "content":
        return "https://istio.io/{}{}".format(name, ".htm")
    else:
        return "https://istio.io/zh/{}{}".format(name, ".htm")


def get_labels(issue):
    label_list = issue.get_labels()
    name_list = []
    for label_obj in label_list:
        name_list.append(label_obj.name)
    return name_list


class mesherbot(BotPlugin):
    """
    This is a chatbot for ServiceMesher.com
    """

    @arg_botcmd('token', type=str)
    def github_bind(self, msg, token):
        client = github.Github(token)
        from_user = msg.frm.person
        message = "You are not member of Service Mesher."
        try:
            user = client.get_user()
            for org in user.get_orgs():
                if org.login == "servicemesher":
                    self[from_user + "github_token"] = token
                    self[from_user + "github_login"] = user.login
                    message = "Now you can do something in Servicemeser."
                    break
        except github.GithubException as e:
            message = e.data
        return message

    @botcmd
    def github_whoami(self, msg, args):
        from_user = msg.frm.person
        try:
            yield("Github Token:" + self[from_user + "github_token"])
            yield("Github Login:" + self[from_user + "github_login"])
        except:
            yield("Bind your Github token please.")

    def github_binded(self, person):
        result = True
        try:
            result = len(self[person + "github_token"]) > 0
        except:
            result = False
        return result

    @botcmd
    def whatsnew(self, msg, args):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        issues_list = repo.get_issues(assignee="none",
                                      state="open",
                                      labels=[repo.get_label("welcome")])
        count = 0
        for issue in issues_list:
            count += 1
            if count <= RESULT_COUNT or (not msg.is_group):
                yield(issue.html_url)
        yield("Totle results {}".format(count))

    @arg_botcmd('issue_id', type=int)
    def confirm_issue(self, msg, issue_id):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        issue = repo.get_issue(issue_id)
        label_list = get_labels(issue)
        if "welcome" not in label_list or issue.state != "open":
            return "This is not a new issue"
        issue.remove_from_labels("welcome")
        issue.add_to_labels("pending")
        yield(issue.html_url)

    @arg_botcmd('--title', dest='title', type=str)
    @arg_botcmd('--body', dest='body', type=str)
    def create_issue(self, msg, title, body):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        issue = repo.create_issue(title, body)
        if issue != None:
            yield("New issue created")
            yield(issue.html_url)

    @arg_botcmd('title', type=str)
    def search_title(self, msg, title):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        issue_list = client.search_issues(
            "{} in:title type:issue repo:{}".format(title, REPO))
        count = 0
        for issue in issue_list:
            count += 1
            if count <= RESULT_COUNT or (not msg.is_group):
                yield(issue.html_url)
        yield("Totle results {}".format(count))

    @arg_botcmd('query', type=str)
    def search_issues(self, msg, query):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        issue_list = client.search_issues(
            "type:issue repo:{} {}".format(REPO, query))
        count = 0
        for issue in issue_list:
            if count <= RESULT_COUNT or (not msg.is_group):
                yield(issue.html_url)
        yield("Totle results {}".format(count))

    @arg_botcmd('issue_id', type=int)
    @arg_botcmd('--comment', type=str)
    def comment_issue(self, msg, issue_id, comment):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        issue = repo.get_issue(issue_id)
        issue.create_comment(comment)
        yield(issue.html_url)

    @arg_botcmd('issue_id', type=int)
    @arg_botcmd('--label', type=str)
    def label_issue(self, msg, issue_id, label):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        issue = repo.get_issue(issue_id)
        obj = repo.get_label(label)
        if obj == None:
            return "Invalid label"
        issue.add_to_labels(label)
        yield("Label added to")
        yield(issue.html_url)

    @botcmd
    def mesher_sync_list(self, msg, args):
        regex = r"^(content(_zh)?)\/(.*?)\s+\|\s+(\d+)"
        with open(DIFF) as diff:
            for line in diff:
                line = line.strip()
                res = re.search(regex, line)
                if res == None:
                    yield("-1\t" + line)
                    continue
                filename = "{}/{}".format(res.group(1), res.group(3))
                yield("{}\t{}/{}".format(res.group(4), res.group(1), res.group(3), ))
                yield("\t" + filename_to_source_url(filename))
                yield("\t" + filename_to_web_url(filename))

    @arg_botcmd('filename', type=str)
    def file_issue(self, msg, filename):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        title = filename
        body = "文件路径：{}\n\n[源码]({})\n\n[网址]({})".format(
            filename, filename_to_source_url(filename),
            filename_to_web_url(filename)
        )
        issue = repo.create_issue(title, body)
        if issue != None:
            yield("New issue created")
            yield(issue.html_url)

    @botcmd
    def commands(self, msg, args):
        yield("**可用命令说明**")
        yield("`github bind [token]`：绑定 github token 才能正常使用， **必须在私聊窗口中使用** ，Token 需要权限 `read:user, repo, write:discussion`")
        yield("`whatsnew`：查找 `welcome` 标签的新 Issue")
        yield("`github whoami`：显示 Github 账号绑定信息")
        yield("`label issue [issue-id] --label [label-text]`：为指定 Issue 添加标签")
        yield("`comment issue [issue-id] --comment [comment]`：为指定 Issue 添加 Comment")
        yield("`search issues [query]`：搜索 Issue，使用[官方查询语法](https://help.github.com/articles/searching-issues-and-pull-requests/)")
        yield("`search title [title]`：根据标题搜索 Issue")
        yield("`file issue [file name]`：根据文件名创建 Issue，文件名形如： `content/docs/..`")
        yield("`confirm issue [issue id]`：确认将新 Issue 转入 Pending 状态")
