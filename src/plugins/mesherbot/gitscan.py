#!/usr/bin/env python3

import glob
import os
import subprocess

REPOSITORY = os.getenv("GITREPO")
LOG_CMD = ["git", "log", "-1", "--pretty=format:'%ad'", "--date=iso8601"]
HASH_CMD = ["git", "log", "-1", "--pretty=format:'%H'"]
DIFF_CMD = ["git", "diff", "HEAD"]


def update_repo(REPO):
    pwd = os.curdir
    os.chdir(REPO)
    try:
        msg = subprocess.check_output(["git", "pull"])
    finally:
        os.chdir(pwd)
    return msg

def find_orphan_files(REPO):
    pwd = os.curdir
    os.chdir(REPO)
    en_list = glob.glob(os.path.join(
        "content/**", "*.md"), recursive=True)
    en_list = [filename.replace("content/", "") for filename in en_list]
    zh_list = glob.glob(os.path.join(
        "content_zh/**", "*.md"), recursive=True)
    os.chdir(pwd)
    zh_list = [filename.replace("content_zh/", "") for filename in zh_list]
    added = list(set(en_list) - set(zh_list))
    tobe_del = list(set(zh_list) - set(en_list))
    added.sort()
    tobe_del.sort()
    return tobe_del


def find_new_files(REPO):
    pwd = os.curdir
    os.chdir(REPO)
    en_list = glob.glob(os.path.join(
        "content/**", "*.md"), recursive=True)
    en_list = [filename.replace("content/", "") for filename in en_list]
    zh_list = glob.glob(os.path.join(
        "content_zh/**", "*.md"), recursive=True)
    zh_list = [filename.replace("content_zh/", "") for filename in zh_list]
    added = list(set(en_list) - set(zh_list))
    added.sort()
    os.chdir(pwd)
    return [os.path.join("content", item) for item in added]


def find_updated_files(REPO):
    pwd = os.curdir
    os.chdir(REPO)
    result = {}
    # check each file in 'content_zh'
    zh_list = glob.glob(os.path.join(
        "content_zh/**", "*.md"), recursive=True)

    zh_list.sort()
    for filename in zh_list:
        # filename = filename.replace(os.path.join(REPO, "content_zh/"), "")
        zh_filename = filename
        en_filename = os.path.join(
            "content", filename.replace("content_zh/", ""))
        if not os.path.exists(en_filename):
            continue
        zh_last_commit_time = subprocess.check_output(
            LOG_CMD + [zh_filename]).decode("UTF-8")
        en_last_hash = subprocess.check_output(
            HASH_CMD + ["--before", zh_last_commit_time, en_filename]).decode("UTF-8").strip("'")
        diff_content = subprocess.check_output(
            DIFF_CMD + [en_last_hash, en_filename]).decode("UTF-8")

        if (len(diff_content) > 0):
            result[en_filename] = {"diff": diff_content}
    os.chdir(pwd)
    return result

def get_release(repository, count):
    release_list = repository.get_releases()
    result_list = []
    for release in release_list:
        result_list.append(release)
        if len(result_list) >= count and count != 0:
            break
    return result_list