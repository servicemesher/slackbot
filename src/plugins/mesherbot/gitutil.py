import github
import re


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

def search_dupe_file_issue(client, file_name):
    query_str = "is:issue state:open in:title {}".format(file_name.strip("/"))
    res = client.search_issues(query_str)
    dupe = []
    for issue in res:
        dupe.append(issue)
    return dupe
