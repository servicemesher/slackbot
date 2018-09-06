# -*- coding: UTF-8 -*-
from errbot import BotPlugin, botcmd, arg_botcmd
import github
import re
import os
import json
import gitutil
import gitscan
import time

REPO = os.getenv("REPOSITORY")
LOCAL_REPO = os.getenv("LOCAL_REPO")
RESULT_COUNT = int(os.getenv("RESULT_COUNT"))
DICT = os.getenv("DICT")
SLEEP = 2

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
            message = "**Github Token: {}**\n\n**Github Login:**: {}"
            message = message.format(self[from_user + "github_token"], 
            self[from_user + "github_login"])
        except:
            message = "**Bind your Github token please.**"
        return message

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
        id_list = []
        for issue in issues_list:
            count += 1
            if count <= RESULT_COUNT or (not msg.is_group):
                id_list.append(issue.number)
        return(" ".join(id_list)) 

    @arg_botcmd('issue_id', type=int)
    def confirm_issue(self, msg, issue_id):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        issue = repo.get_issue(issue_id)
        label_list = gitutil.get_labels(issue)
        if "welcome" not in label_list or issue.state != "open":
            return "This is not a new issue"
        issue.remove_from_labels("welcome")
        issue.add_to_labels("pending")
        return issue.html_url

    @arg_botcmd('--title', dest='title', type=str)
    @arg_botcmd('--body', dest='body', type=str)
    def create_issue(self, msg, title, body):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        issue = repo.create_issue(title, body)
        if issue != None:
            return("New issue created: [{}]({})".format(title, issue.html_url))

    @arg_botcmd('title', type=str)
    def search_title(self, msg, title):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        issue_list = client.search_issues(
            "{} in:title type:issue repo:{}".format(title, REPO))
        count = 0
        issue_list = []
        for issue in issue_list:
            count += 1
            if count <= RESULT_COUNT or (not msg.is_group):
                yield(issue.html_url)
        yield("Total results {}".format(count))

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
        yield("Total results {}".format(count))

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

    @arg_botcmd('filename', type=str)
    def file_issue(self, msg, filename):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        title = filename
        body = "文件路径：{}\n\n[源码]({})\n\n[网址]({})".format(
            filename, gitutil.filename_to_source_url(filename),
            gitutil.filename_to_web_url(filename)
        )
        issue = repo.create_issue(title, body)
        if issue != None:
            yield("New issue created")
            yield(issue.html_url)

    @botcmd
    def commands(self, msg, args):
        yield("**可用命令说明**")
        yield("`comment issue [issue-id] --comment [comment]`：为指定 Issue 添加 Comment")
        yield("`confirm issue [issue id]`：确认将新 Issue 转入 Pending 状态")
        yield("`file issue [file name]`：根据文件名创建 Issue，文件名形如： `content/docs/..`")
        yield("`find new files [--create_issue]`：查找中文版中缺失的英文版文件，如果 --create_issue=1，则根据文件名称新建 Issue。")
        yield("`find update files [--create_issue]`：中文版文件最后一次 Commit 之后，对应英文版发生更新的文件列表。如果 --create_issue=1，则根据文件名称新建 Issue。")
        yield("`github bind [token]`：绑定 github token 才能正常使用， **必须在私聊窗口中使用** ，Token 需要权限 `read:user, repo, write:discussion`")
        yield("`github whoami`：显示 Github 账号绑定信息")
        yield("`label issue [issue-id] --label [label-text]`：为指定 Issue 添加标签")        
        yield("`search issues [query]`：搜索 Issue，使用[官方查询语法](https://help.github.com/articles/searching-issues-and-pull-requests/)")
        yield("`search title [title]`：根据标题搜索 Issue")
        yield("`update repository`：更新代码库。")
        yield("`whatsnew`：查找 `welcome` 标签的新 Issue")
        yield("`list release [repository] --count`：列出指定仓库的最新 Release。")
    @arg_botcmd('term', type=str)
    def search_term(self, msg, term):
        with open(DICT, "r") as file:
            dic = json.load(file)
            for key in dic.keys():
                if key.find(term) >= 0:
                    return "**{}**：{}".format(key, dic.get(key))
        return "Found nothing."

    @botcmd
    def update_repository(self, msg, args):
        return gitscan.update_repo(LOCAL_REPO)

    @arg_botcmd('--create_issue', type=int, default=0)
    def find_new_files(self, msg, create_issue):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        new_file_list = gitscan.find_new_files(LOCAL_REPO)
        if create_issue == 0:
            for filename in new_file_list:
                yield(filename)
            yield("{} files created".format(len(new_file_list)))
            return
        issue_count = 0
        for filename in new_file_list:
            time.sleep(SLEEP)
            if (len(gitutil.search_dupe_file_issue(client, REPO, filename)) > 0):
                yield(filename + " duplicated.")
                continue
            title = filename
            body = "文件路径：{}\n\n[源码]({})\n\n[网址]({})".format(
                filename, gitutil.filename_to_source_url(filename),
                gitutil.filename_to_web_url(filename)
            )
            issue = repo.create_issue(title, body)
            issue.add_to_labels("sync/new")
            issue_count += 1
        yield("{} issues had been created.".format(issue_count))

    @arg_botcmd('--create_issue', type=int, default=0)
    def find_update_files(self, msg, create_issue):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(REPO)
        update_list = gitscan.find_updated_files(LOCAL_REPO)
        message = ""
        issue_count = 0
        for filename in update_list.keys():
            diff = update_list.get(filename)
            if (create_issue != 0):
                title = filename
                time.sleep(SLEEP)
                if (len(gitutil.search_dupe_file_issue(client, REPO, filename)) > 0):
                    yield("{} duplicated.".format(filename))
                    continue
                body = "文件路径：{}\n\n[源码]({})\n\n[网址]({})".format(
                    filename, gitutil.filename_to_source_url(
                        filename),
                    gitutil.filename_to_web_url(
                        filename)
                )
                body += "\n\n ```diff\n{}\n```\n\n".format(
                    update_list.get(filename).get("diff"))
                issue = repo.create_issue(title, body)
                issue.add_to_labels("sync/update")
                issue_count += 1
                yield(issue.html_url)
            else:
                yield(filename)
        if (create_issue != 0):
            yield("{} issues had been created.".format(issue_count))
        if (create_issue == 0):
            yield(
                "{} files updated.".format(len(update_list))
            )

    @arg_botcmd('repository', type=str)
    @arg_botcmd('--count', type=int, default=10)
    def list_release(self, msg, repository, count):
        if not self.github_binded(msg.frm.person):
            return "Bind your Github token please."        
        client = github.Github(self[msg.frm.person + "github_token"])
        repo = client.get_repo(repository)
        result = gitscan.get_release(repo, count)
        for release in result:
            yield("{}: {}".format(release.title, release.html_url))
