"""T0 a: workspace and merged-main facts. Evidence only."""
import json, platform, subprocess, sys

def run(args):
    return subprocess.check_output(args, text=True).strip()

def git(args):
    return run(["git", *args])

print("os", platform.freedesktop_os_release().get("PRETTY_NAME", "unknown"))
print("kernel", platform.release())
print("python", sys.version.split()[0])
print("branch", git(["branch", "--show-current"]))
print("main_sha", git(["rev-parse", "origin/main"]))
main_tree = git(["rev-parse", "origin/main^{tree}"])
pr2_tree = git(["rev-parse", "90fac066475aec153786c0973e791b18879cbc45^{tree}"])
print("main_tree", main_tree)
print("pr2_head_tree", pr2_tree)
print("tree_equal", main_tree == pr2_tree)
pr = json.loads(run(["gh", "pr", "view", "2", "--json", "state,mergeCommit,headRefOid"]))
print("pr2_state", pr["state"])
print("pr2_merge_commit", pr["mergeCommit"]["oid"])
print("pr2_head", pr["headRefOid"])
